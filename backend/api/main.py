import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional
from tools_xanh import search_location, get_real_distance

app = FastAPI()

class BookingRequest(BaseModel):
    user_id: str
    pickup_text: Optional[str] = "Home"
    destination_text: Optional[str] = None
    vehicle_type: str = "bike"  # Thêm trường loại phương tiện (bike, standard, luxury)
    current_gps: dict

# Helper check GPS
def is_valid_gps(gps: dict):
    return (
        isinstance(gps, dict)
        and isinstance(gps.get("lat"), (int, float))
        and isinstance(gps.get("lng"), (int, float))
    )

@app.post("/api/v1/booking/intent")
async def process_booking(req: BookingRequest):
    if not req.destination_text:
        return {"status": "INCOMPLETE", "message": "Bro muốn đi đâu?"}

    # 1. XỬ LÝ ĐIỂM ĐÓN
    pickup_text_norm = (req.pickup_text or "Home").strip().lower()
    dest_text_norm = (req.destination_text or "").strip().lower()

    if pickup_text_norm in ["đây", "here", "current"]:
        ...
    elif pickup_text_norm in ["nhà", "home"]:
        # Hardcoded location for testing
        pickup_data = {
            "label": "Nhà",
            "address": "Địa chỉ nhà của user",
            "lat": 21.0285,  # Example lat/lng
            "lng": 105.8542
        }
    else:
        p_res = search_location(pickup_text_norm, req.user_id)  # use normalized
        if p_res["status"] == "found":
            pickup_data = p_res["data"]
        else:
            return {"status": "INCOMPLETE", "message": f"Không tìm thấy điểm đón: {req.pickup_text}"}

    # 2. XỬ LÝ ĐIỂM ĐẾN
    dest_text_norm = req.destination_text.strip().lower()
    d_res = search_location(req.destination_text, req.user_id)

    if d_res["status"] == "not_found":
        # Trường hợp địa chỉ đặc biệt chưa lưu
        if dest_text_norm in ["nhà", "công ty", "home", "company"]:
            return {
                "status": "SUCCESS",
                "action_type": "NEED_SETUP_LOCATION",
                "message": f"Chưa lưu địa chỉ {req.destination_text}, thiết lập không bro?",
                "data": {"pickup": pickup_data, "target_label": dest_text_norm}
            }
        return {"status": "INCOMPLETE", "message": f"Không tìm thấy điểm đến: {req.destination_text}"}

    dest_data = d_res["data"]

    # 3. TÍNH KHOẢNG CÁCH
    distance = get_real_distance(
        pickup_data["lat"], pickup_data["lng"],
        dest_data["lat"], dest_data["lng"]
    )

    # 4. TRẢ VỀ KẾT QUẢ RÚT GỌN
    return {
        "status": "SUCCESS",
        "message": "Đã xác định lộ trình!",
        "action_type": "CONFIRM_BOOKING",
        "data": {
            "pickup": pickup_data,
            "destination": dest_data,
            "distance_km": distance,
            "vehicle_type": req.vehicle_type  # Trả về loại phương tiện đã chọn
        }
    }

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)