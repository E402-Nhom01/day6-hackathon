import json
import uvicorn
import os
from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional
from tools_xanh import search_location, get_real_distance

app = FastAPI()


class BookingRequest(BaseModel):
    user_id: str
    pickup_text: Optional[str] = "đây"
    destination_text: Optional[str] = None
    current_gps: dict  # {"lat": ..., "lng": ...}


def get_services_pricing(distance_km: float):
    # Dùng đường dẫn tuyệt đối để đảm bảo đọc được file services.json
    base_path = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(base_path, "services.json")

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            services = json.load(f)
        # Đảm bảo khoảng cách tối thiểu 1km để có giá
        dist = max(distance_km, 1.0)
        return [
            {
                "service_id": s["id"],
                "name": s["name"],
                "total_price": int(s["base_price"] + (s["price_per_km"] * dist))
            } for s in services
        ]
    except Exception as e:
        print(f"CRITICAL: Lỗi load services.json: {e}")
        return []


@app.post("/api/v1/booking/intent")
async def process_booking(req: BookingRequest):
    if not req.destination_text:
        return {"status": "INCOMPLETE", "message": "Bro muốn đi đâu?"}

    # --- XỬ LÝ PICKUP ---
    p_res = search_location(req.pickup_text, req.user_id)
    if p_res["status"] == "found":
        pickup_data = p_res["data"]
    else:
        # Mặc định lấy GPS hiện tại nếu không tìm thấy text điểm đón
        pickup_data = {
            "label": "",
            "address": "Vị trí hiện tại của bạn",
            "lat": req.current_gps.get("lat", 21.0),
            "lng": req.current_gps.get("lng", 105.8)
        }

    # --- XỬ LÝ DESTINATION ---
    d_res = search_location(req.destination_text, req.user_id)

    # Trường hợp không tìm thấy hoặc là nhãn chưa thiết lập
    if d_res["status"] == "not_found":
        if req.destination_text.lower() in ["nhà", "công ty"]:
            return {
                "status": "SUCCESS",
                "message": f"Chưa lưu địa chỉ {req.destination_text}, thêm không bro?",
                "action_type": "NEED_SETUP_LOCATION",
                "data": {
                    "pickup": pickup_data,
                    "destination": {"label": "", "address": "Thiết lập ngay", "lat": 0, "lng": 0},
                    "distance_km": 0,
                    "options": []
                }
            }
        return {"status": "INCOMPLETE", "message": "Không tìm thấy địa điểm trên bản đồ."}

    dest_data = d_res["data"]

    # --- TÍNH TOÁN KHOẢNG CÁCH & GIÁ ---
    distance = get_real_distance(pickup_data["lat"], pickup_data["lng"], dest_data["lat"], dest_data["lng"])

    options = []
    if distance is not None:
        options = get_services_pricing(distance)

    # Trả về Response duy nhất theo cấu trúc SPEC
    return {
        "status": "SUCCESS",
        "message": "Đã tìm thấy xe cho bro!",
        "action_type": "CONFIRM_BOOKING",
        "data": {
            "pickup": pickup_data,
            "destination": dest_data,
            "distance_km": distance,
            "options": options,
            "payment_method": "Tiền mặt"
        }
    }


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)