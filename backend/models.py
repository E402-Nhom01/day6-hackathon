from pydantic import BaseModel
from typing import List, Dict

class Location(BaseModel):
    label: str
    address: str
    lat: float
    lng: float

class UserContext(BaseModel):
    user_id: str
    saved_locations: List[Location]
    recent_trips: List[Dict]