import json
import requests
from geopy.geocoders import Nominatim

# Khởi tạo Map API bên thứ 3 (Geocoding)
geolocator = Nominatim(user_agent="xanh_sm_assistant_v3")

def load_user_db():
    try:
        # Load trực tiếp file trong cùng thư mục
        with open("users.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"ERROR: Không thể đọc users.json: {e}")
        return {}

def search_location(query: str, user_id: str):
    db = load_user_db()
    user_data = db.get(user_id, {})
    clean_query = query.lower().strip()

    # 1. Ưu tiên tra cứu nhãn (label) trong dữ liệu cá nhân
    if user_data:
        for loc in user_data.get("saved_locations", []):
            label_in_db = loc["label"].lower().strip()
            # Khớp chính xác nhãn "nhà" hoặc "công ty"
            if clean_query == label_in_db:
                return {
                    "status": "found",
                    "data": {
                        "label": loc["label"],
                        "address": loc["address"],
                        "lat": loc["lat"],
                        "lng": loc["lng"]
                    }
                }

    # 2. Nếu không phải nhãn riêng, gọi Map thật (Third-party)
    try:
        location = geolocator.geocode(f"{query}, Việt Nam", timeout=10)
        if location:
            return {
                "status": "found",
                "data": {
                    "label": "", # Địa chỉ mới không có nhãn
                    "address": location.address,
                    "lat": location.latitude,
                    "lng": location.longitude
                }
            }
    except Exception as e:
        print(f"WARNING: Geopy failed: {e}")

    return {"status": "not_found"}

def get_real_distance(lat1, lon1, lat2, lon2):
    # OSRM tính quãng đường di chuyển thực tế (Driving distance)
    url = f"http://router.project-osrm.org/route/v1/driving/{lon1},{lat1};{lon2},{lat2}?overview=false"
    try:
        response = requests.get(url, timeout=5)
        data = response.json()
        if data.get('code') == 'Ok':
            # Trả về km
            return round(data['routes'][0]['distance'] / 1000, 2)
    except Exception as e:
        print(f"ERROR: OSRM failed: {e}")
    return None