import unittest
from fastapi.testclient import TestClient
from main import app

class TestBookingAPI(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_booking_intent_success(self):
        payload = {
            "user_id": "bro_01",
            "pickup_text": "đây",
            "destination_text": "VinUni",
            "vehicle_type": "bike",
            "current_gps": {"lat": 21.0, "lng": 105.0}
        }
        response = self.client.post("/api/v1/booking/intent", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "SUCCESS")
        self.assertEqual(data["action_type"], "CONFIRM_BOOKING")

    def test_booking_hardcoded_home(self):
        payload = {
            "user_id": "bro_01",
            "pickup_text": "nhà",
            "destination_text": "công ty",
            "vehicle_type": "luxury",
            "current_gps": {"lat": 21.0, "lng": 105.0}
        }
        response = self.client.post("/api/v1/booking/intent", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "SUCCESS")
        self.assertEqual(data["data"]["pickup"]["label"], "Home")
        self.assertEqual(data["data"]["destination"]["label"], "Company")

    def test_booking_missing_destination(self):
        payload = {
            "user_id": "bro_01",
            "pickup_text": "Home",
            "destination_text": None,
            "current_gps": {"lat": 21.0, "lng": 105.0}
        }
        response = self.client.post("/api/v1/booking/intent", json=payload)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "INCOMPLETE")

if __name__ == "__main__":
    unittest.main()
