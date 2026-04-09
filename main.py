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
    pickup_text = req.pickup_text or "Home"
    pickup_text_norm = pickup_text.strip().lower()
    
    if pickup_text_norm in ["đây", "here", "current"]:
        if not is_valid_gps(req.current_gps):
            return {"status": "INCOMPLETE", "message": "Thiếu GPS hiện tại."}
        pickup_data = {
            "label": "Vị trí hiện tại",
            "address": "Vị trí hiện tại của bạn",
            "lat": req.current_gps["lat"],
            "lng": req.current_gps["lng"]
        }
    else:
        # Mapping Vietnamese -> English for DB
        p_query = pickup_text
        if pickup_text_norm == "nhà": p_query = "Home"
        elif pickup_text_norm == "công ty": p_query = "Company"
        
        p_res = search_location(p_query, req.user_id)
        if p_res["status"] == "found":
            pickup_data = p_res["data"]
        else:
            # Set cứng nếu vẫn không thấy
            if pickup_text_norm in ["nhà", "home"]:
                pickup_data = {
                    "label": "Home",
                    "address": "Sapphire S1.11, Ocean Park, Gia Lâm, Hà Nội",
                    "lat": 20.9961015, "lng": 105.944009
                }
            else:
                return {"status": "INCOMPLETE", "message": f"Không tìm thấy điểm đón: {req.pickup_text}"}

    # 2. XỬ LÝ ĐIỂM ĐẾN
    dest_text = req.destination_text
    dest_text_norm = dest_text.strip().lower()
    
    # Mapping Vietnamese -> English for DB
    d_query = dest_text
    if dest_text_norm == "nhà": d_query = "Home"
    elif dest_text_norm == "công ty": d_query = "Company"
    
    d_res = search_location(d_query, req.user_id)

    if d_res["status"] == "not_found":
        # Check hardcoded fallback first
        if dest_text_norm in ["nhà", "home"]:
            dest_data = {
                "label": "Home",
                "address": "Sapphire S1.11, Ocean Park, Gia Lâm, Hà Nội",
                "lat": 20.9961015, "lng": 105.944009
            }
        elif dest_text_norm in ["công ty", "company"]:
            dest_data = {
                "label": "Company",
                "address": "VinUni, Gia Lâm, Hà Nội",
                "lat": 20.9885973, "lng": 105.9460279
            }
        else:
            return {"status": "INCOMPLETE", "message": f"Không tìm thấy điểm đến: {req.destination_text}"}
    else:
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