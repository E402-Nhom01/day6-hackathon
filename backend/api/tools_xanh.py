import json
import requests
from geopy.geocoders import Nominatim

# Init geocoder
geolocator = Nominatim(user_agent="xanh_sm_assistant_v4")

# ❗ Các từ quá chung chung → không gọi API
GENERIC_WORDS = [
    "home", "house", "company", "office",
    "nhà", "công ty"
]

import os

def load_user_db():
    try:
        base_path = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(base_path, "mock_db/users.json")

        print("LOADING FILE:", file_path)  # 👈 debug

        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)

    except Exception as e:
        print(f"ERROR: Không thể đọc users.json: {e}")
        return {}
def is_valid_query(query: str):
    query = query.strip().lower()

    # ❌ quá ngắn hoặc generic → reject
    if query in GENERIC_WORDS:
        return False

    if len(query) < 3:
        return False

    return True


def search_location(query: str, user_id: str):
    db = load_user_db()
    user_data = db.get(user_id, {})

    clean_query = query.lower().strip()

    # =========================
    # 1. ✅ CHECK SAVED LOCATIONS FIRST (QUAN TRỌNG NHẤT)
    # =========================
    if user_data:
        for loc in user_data.get("saved_locations", []):
            label_in_db = loc["label"].lower().strip()

            # 🎯 match EXACT (không fuzzy)
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

    # =========================
    # 2. ❌ FILTER QUERY NGU NGƠ
    # =========================
    if not is_valid_query(clean_query):
        return {"status": "not_found"}

    # =========================
    # 3. 🌍 CALL MAP API (Nominatim)
    # =========================
    try:
        location = geolocator.geocode(
            f"{query}, Việt Nam",
            timeout=10,
            addressdetails=True
        )

        if location:
            address_lower = location.address.lower()

            # =========================
            # 4. ❗ VALIDATE RESULT (ANTI "HOME HOTEL")
            # =========================
            if clean_query not in address_lower:
                return {"status": "not_found"}

            return {
                "status": "found",
                "data": {
                    "label": "",
                    "address": location.address,
                    "lat": location.latitude,
                    "lng": location.longitude
                }
            }

    except Exception as e:
        print(f"WARNING: Geopy failed: {e}")

    return {"status": "not_found"}


def get_real_distance(lat1, lon1, lat2, lon2):
    url = f"http://router.project-osrm.org/route/v1/driving/{lon1},{lat1};{lon2},{lat2}?overview=false"

    try:
        response = requests.get(url, timeout=5)
        data = response.json()

        if data.get('code') == 'Ok':
            return round(data['routes'][0]['distance'] / 1000, 2)

    except Exception as e:
        print(f"ERROR: OSRM failed: {e}")

    return None