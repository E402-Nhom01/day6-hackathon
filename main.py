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
    pickup_text: Optional[str] = "Home"
    destination_text: Optional[str] = None
    current_gps: dict  # {"lat": ..., "lng": ...}


def get_services_pricing(distance_km: float):
    base_path = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(base_path, "services.json")

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            services = json.load(f)

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


# ✅ helper check GPS hợp lệ
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

    pickup_text_norm = req.pickup_text.strip().lower()

    # =========================
    # 🚀 FIX 1: HANDLE CURRENT LOCATION
    # =========================
    if pickup_text_norm in ["đây", "here", "current"]:
        if not is_valid_gps(req.current_gps):
            return {
                "status": "INCOMPLETE",
                "message": "Thiếu GPS hiện tại (lat/lng)."
            }

        pickup_data = {
            "label": "",
            "address": "Vị trí hiện tại của bạn",
            "lat": req.current_gps["lat"],
            "lng": req.current_gps["lng"]
        }

    else:
        # =========================
        # 🚀 FIX 2: FORCE DEBUG SEARCH
        # =========================
        p_res = search_location(req.pickup_text, req.user_id)

        print("DEBUG PICKUP SEARCH:", p_res)  # 👈 QUAN TRỌNG

        if p_res["status"] == "found":
            pickup_data = p_res["data"]
        else:
            # ❗ KHÔNG fallback ngay → tránh che bug
            return {
                "status": "INCOMPLETE",
                "message": f"Không tìm thấy điểm đón: {req.pickup_text}"
            }

    # =========================
    # 🚀 FIX 3: DESTINATION
    # =========================
    dest_text_norm = req.destination_text.strip().lower()

    d_res = search_location(req.destination_text, req.user_id)

    print("DEBUG DEST SEARCH:", d_res)  # 👈 debug

    if d_res["status"] == "not_found":
        if dest_text_norm in ["nhà", "công ty", "home", "company"]:
            return {
                "status": "SUCCESS",
                "message": f"Chưa lưu địa chỉ {req.destination_text}, thêm không bro?",
                "action_type": "NEED_SETUP_LOCATION",
                "data": {
                    "pickup": pickup_data,
                    "destination": {
                        "label": dest_text_norm,
                        "address": "Thiết lập ngay",
                        "lat": 0,
                        "lng": 0
                    },
                    "distance_km": 0,
                    "options": []
                }
            }

        return {
            "status": "INCOMPLETE",
            "message": f"Không tìm thấy điểm đến: {req.destination_text}"
        }

    dest_data = d_res["data"]

    # =========================
    # 🚀 FIX 4: DISTANCE
    # =========================
    distance = get_real_distance(
        pickup_data["lat"],
        pickup_data["lng"],
        dest_data["lat"],
        dest_data["lng"]
    )

    options = []
    if distance is not None:
        options = get_services_pricing(distance)

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