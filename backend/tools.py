from langchain_core.tools import tool

DESTINATION_DB = {
    "user_id": "bro_01",
    "saved_locations": [
        {"label": "Nhà riêng", "address": "Số 1 Chùa Bộc, Hà Nội", "lat": 21.007, "lng": 105.827},
        {"label": "Công ty", "address": "Vinhomes Ocean Park", "lat": 20.995, "lng": 105.942}
    ],
    "recent_trips": [
        {"destination": "Vincom Bà Triệu", "count": 5}
    ]
}

# Giả lập database bản đồ hoặc kết quả trả về từ Google Maps/Mapbox API
MOCK_MAPS_DB = {
    "chùa bộc, hà nội": {"lat": 21.0078976, "lng": 105.8286008},
    "vinhomes ocean park": {"lat": 20.9947937, "lng": 105.9358326},
    "vincom bà triệu": {"lat": 21.010419, "lng": 105.849202},
    "sân bay nội bài": {"lat": 21.218715, "lng": 105.804171}
}

@tool
def search_ride_locations(origin: str, destination: str) -> str:
    """
    Tìm kiếm tọa độ (vĩ độ, kinh độ) của điểm đón và điểm đến để đặt xe.
    Tham số:
    - origin: Tên hoặc địa chỉ điểm khởi hành (VD: 'Chùa Bộc, Hà Nội', 'Nhà riêng')
    - destination: Tên hoặc địa chỉ điểm đến (VD: 'Vinhomes Ocean Park', 'Công ty')
    Trả về chuỗi chứa thông tin tọa độ của 2 địa điểm để tính toán quãng đường và giá cước.
    """
    
    def find_coords(place_name: str):
        place_lower = place_name.lower().strip()
        
        # 1. Ưu tiên tìm trong địa điểm đã lưu của user trước (VD: user gọi "Nhà riêng")
        for loc in DESTINATION_DB.get("saved_locations", []):
            if place_lower == loc["label"].lower() or place_lower in loc["address"].lower():
                return {"lat": loc["lat"], "lng": loc["lng"], "source": f"Đã lưu: {loc['label']}"}
        
        # 2. Nếu không có trong danh sách đã lưu, tìm trong database bản đồ (API)
        for key, coords in MOCK_MAPS_DB.items():
            if place_lower in key or key in place_lower:
                return {"lat": coords["lat"], "lng": coords["lng"], "source": "Bản đồ hệ thống"}
                
        return None

    # Lấy dữ liệu tọa độ
    origin_data = find_coords(origin)
    dest_data = find_coords(destination)
    
    # Kiểm tra xem có tìm thấy cả 2 điểm không
    if not origin_data:
        return f"Lỗi: Không tìm thấy tọa độ cho điểm đón '{origin}'."
    if not dest_data:
        return f"Lỗi: Không tìm thấy tọa độ cho điểm đến '{destination}'."
        
    # Trả về kết quả
    result = (
        f"Tìm thấy thông tin tọa độ cho chuyến đi:\n"
        f"Điểm đón: {origin} ({origin_data['source']})\n"
        f"- Lat: {origin_data['lat']} | Lng: {origin_data['lng']}\n"
        f"Điểm đến: {destination} ({dest_data['source']})\n"
        f"- Lat: {dest_data['lat']} | Lng: {dest_data['lng']}"
    )
    return result