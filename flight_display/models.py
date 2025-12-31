"""Data models for Flight Display."""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Flight:
    """Represents a single flight with position and route information."""

    flight_id: str
    callsign: str
    airline: str
    aircraft_type: str
    origin: str
    destination: str
    latitude: float
    longitude: float
    altitude: int  # feet
    ground_speed: int  # knots
    heading: int  # degrees
    distance_km: float = 0.0
    registration: Optional[str] = None
    vertical_speed: Optional[int] = None  # feet per minute

    def __post_init__(self):
        """Ensure callsign has a default if empty."""
        if not self.callsign:
            self.callsign = "N/A"
        if not self.airline:
            self.airline = self.callsign[:3] if len(self.callsign) >= 3 else "N/A"
        if not self.aircraft_type:
            self.aircraft_type = "N/A"
        if not self.origin:
            self.origin = "---"
        if not self.destination:
            self.destination = "---"
