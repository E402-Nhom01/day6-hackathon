import logging
import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
from tools_xanh import search_location, get_real_distance

# --- CẤU HÌNH LOGGING ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("booking_api")

app = FastAPI()

# --- CONSTANTS & CONFIG ---
DEFAULT_GPS = {"lat": 21.024209, "lng": 105.855734}

# Bộ từ khóa mở rộng
KEYWORDS = {
    "current": ["đây", "tại đây", "ở đây", "chỗ này", "vị trí này", "vị trí hiện tại", "here", "current"],
    "home": ["nhà", "về nhà", "nhà tôi", "home", "my home"],
    "work": ["công ty", "đến công ty", "chỗ làm", "cơ quan", "work", "company", "office"]
}


class BookingRequest(BaseModel):
    user_id: str
    pickup_text: Optional[str] = "current"
    destination_text: Optional[str] = None
    vehicle_type: str = "bike"
    current_gps: dict


# --- HELPERS ---
def normalize(text: str) -> str:
    return text.strip().lower() if text else ""


def get_location_type(text_norm: str) -> str:
    for key, values in KEYWORDS.items():
        if text_norm in values:
            return key
    return "other"


@app.post("/api/v1/booking/intent")
async def process_booking(req: BookingRequest):
    try:
        logger.info(f"Request: {req.user_id} | {req.pickup_text} -> {req.destination_text}")

        if not req.destination_text:
            return {"status": "INCOMPLETE", "message": "Bro muốn đi đâu?"}

        # 1. Xác định GPS dùng làm fallback
        active_gps = req.current_gps if (req.current_gps.get("lat") and req.current_gps.get("lng")) else DEFAULT_GPS

        # 2. XỬ LÝ ĐIỂM ĐÓN (PICKUP)
        p_norm = normalize(req.pickup_text)
        p_type = get_location_type(p_norm)

        if p_type == "current":
            pickup_data = {"label": "Vị trí hiện tại", "address": "Vị trí hiện tại", **active_gps}
        else:
            # Nếu là "nhà"/"công ty" hoặc địa chỉ cụ thể -> search_location
            search_query = "home" if p_type == "home" else ("company" if p_type == "work" else req.pickup_text)
            p_res = search_location(search_query, req.user_id)
            if p_res["status"] == "found":
                pickup_data = p_res["data"]
            else:
                return {"status": "INCOMPLETE", "message": f"Không thấy điểm đón: {req.pickup_text}"}

        # 3. XỬ LÝ ĐIỂM ĐẾN (DESTINATION)
        d_norm = normalize(req.destination_text)
        d_type = get_location_type(d_norm)

        search_dest = "home" if d_type == "home" else ("company" if d_type == "work" else req.destination_text)
        d_res = search_location(search_dest, req.user_id)

        if d_res["status"] == "not_found":
            if d_type in ["home", "work"]:
                return {
                    "status": "SUCCESS", "action_type": "NEED_SETUP_LOCATION",
                    "message": f"Chưa lưu {req.destination_text}, thiết lập không bro?",
                    "data": {"pickup": pickup_data, "target_label": d_type}
                }
            return {"status": "INCOMPLETE", "message": f"Không thấy điểm đến: {req.destination_text}"}

        dest_data = d_res["data"]

        # 4. TÍNH KHOẢNG CÁCH
        distance = get_real_distance(pickup_data["lat"], pickup_data["lng"], dest_data["lat"], dest_data["lng"])

        return {
            "status": "SUCCESS", "message": "Đã xác định lộ trình!", "action_type": "CONFIRM_BOOKING",
            "data": {"pickup": pickup_data, "destination": dest_data, "distance_km": distance,
                     "vehicle_type": req.vehicle_type}
        }

    except Exception as e:
        logger.error(f"CRITICAL ERROR: {str(e)}", exc_info=True)
        return {"status": "ERROR", "message": "Có lỗi hệ thống, thử lại sau nhé bro!"}


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)