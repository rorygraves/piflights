"""Demo/mock data generator for testing without an API key."""

import random
import math
from typing import List

from .models import Flight

# Sample airlines with ICAO codes
AIRLINES = [
    ("BAW", "British Airways"),
    ("RYR", "Ryanair"),
    ("EZY", "easyJet"),
    ("VIR", "Virgin Atlantic"),
    ("DLH", "Lufthansa"),
    ("AFR", "Air France"),
    ("KLM", "KLM"),
    ("UAE", "Emirates"),
    ("QTR", "Qatar Airways"),
    ("SAS", "SAS"),
    ("IBE", "Iberia"),
    ("ACA", "Air Canada"),
    ("AAL", "American Airlines"),
    ("UAL", "United Airlines"),
    ("DAL", "Delta"),
]

# Sample aircraft types
AIRCRAFT_TYPES = [
    "A320",
    "A321",
    "A319",
    "A380",
    "A350",
    "B738",
    "B739",
    "B77W",
    "B787",
    "B744",
    "E190",
    "E195",
    "CRJ9",
    "AT76",
    "DH8D",
]

# Sample airports (IATA codes)
AIRPORTS = [
    "LHR",
    "LGW",
    "STN",
    "LTN",
    "MAN",
    "BHX",
    "EDI",
    "GLA",
    "BRS",
    "NCL",
    "CDG",
    "AMS",
    "FRA",
    "MAD",
    "BCN",
    "FCO",
    "JFK",
    "LAX",
    "DXB",
    "SIN",
    "HKG",
    "DOH",
    "IST",
    "ZRH",
    "VIE",
    "CPH",
    "OSL",
    "ARN",
    "HEL",
    "DUB",
]


class DemoDataGenerator:
    """Generates realistic fake flight data for demo/testing purposes."""

    def __init__(
        self,
        center_lat: float = 51.47,
        center_lon: float = -0.45,
        radius_km: float = 100.0,
        num_flights: int = 25,
    ):
        """
        Initialize the demo data generator.

        Args:
            center_lat: Center latitude for generating flights
            center_lon: Center longitude for generating flights
            radius_km: Radius in km for flight positions
            num_flights: Number of flights to generate
        """
        self.center_lat = center_lat
        self.center_lon = center_lon
        self.radius_km = radius_km
        self.num_flights = num_flights
        self._flights: List[Flight] = []
        self._initialize_flights()

    def _initialize_flights(self):
        """Create initial set of flights."""
        self._flights = []

        for i in range(self.num_flights):
            flight = self._create_random_flight(i)
            self._flights.append(flight)

    def _create_random_flight(self, index: int) -> Flight:
        """Create a single random flight."""
        # Random position within radius
        angle = random.uniform(0, 2 * math.pi)
        distance = random.uniform(5, self.radius_km)

        # Convert to lat/lon offset (approximate)
        lat_offset = (distance / 111.0) * math.cos(angle)
        lon_offset = (distance / (111.0 * math.cos(math.radians(self.center_lat)))) * math.sin(angle)

        lat = self.center_lat + lat_offset
        lon = self.center_lon + lon_offset

        # Random airline and flight number
        airline_code, airline_name = random.choice(AIRLINES)
        flight_num = random.randint(100, 9999)
        callsign = f"{airline_code}{flight_num}"

        # Random airports (ensure they're different)
        origin = random.choice(AIRPORTS)
        destination = random.choice([a for a in AIRPORTS if a != origin])

        # Random but realistic values
        altitude = random.choice([
            0,  # On ground
            random.randint(2000, 8000),  # Climbing/descending
            random.randint(28000, 41000),  # Cruise
        ])

        # Speed based on altitude
        if altitude == 0:
            ground_speed = random.randint(0, 30)
        elif altitude < 10000:
            ground_speed = random.randint(180, 280)
        else:
            ground_speed = random.randint(380, 520)

        heading = random.randint(0, 359)

        return Flight(
            flight_id=f"DEMO{index:04d}",
            callsign=callsign,
            airline=airline_code,
            aircraft_type=random.choice(AIRCRAFT_TYPES),
            origin=origin,
            destination=destination,
            latitude=lat,
            longitude=lon,
            altitude=altitude,
            ground_speed=ground_speed,
            heading=heading,
            distance_km=distance,
            registration=f"G-{random.choice('ABCDEFGHIJKLMNOPQRSTUVWXYZ')}{random.choice('ABCDEFGHIJKLMNOPQRSTUVWXYZ')}{random.choice('ABCDEFGHIJKLMNOPQRSTUVWXYZ')}{random.choice('ABCDEFGHIJKLMNOPQRSTUVWXYZ')}",
        )

    def get_flights(self) -> List[Flight]:
        """
        Get current list of flights with updated positions.

        Each call slightly updates flight positions to simulate movement.

        Returns:
            List of Flight objects
        """
        # Update each flight's position slightly
        updated_flights = []

        for flight in self._flights:
            # Move flight in its heading direction
            if flight.ground_speed > 0:
                # Calculate movement (simplified)
                speed_kmh = flight.ground_speed * 1.852  # knots to km/h
                # Movement per update (assuming ~10 second intervals)
                movement_km = speed_kmh / 360  # km per 10 seconds

                heading_rad = math.radians(flight.heading)
                lat_change = (movement_km / 111.0) * math.cos(heading_rad)
                lon_change = (movement_km / (111.0 * math.cos(math.radians(flight.latitude)))) * math.sin(heading_rad)

                new_lat = flight.latitude + lat_change
                new_lon = flight.longitude + lon_change

                # Recalculate distance
                new_distance = self._calculate_distance(new_lat, new_lon)

                # If flight has moved too far, respawn it
                if new_distance > self.radius_km * 1.5:
                    flight = self._create_random_flight(int(flight.flight_id[4:]))
                else:
                    # Update flight with new position
                    flight = Flight(
                        flight_id=flight.flight_id,
                        callsign=flight.callsign,
                        airline=flight.airline,
                        aircraft_type=flight.aircraft_type,
                        origin=flight.origin,
                        destination=flight.destination,
                        latitude=new_lat,
                        longitude=new_lon,
                        altitude=flight.altitude + random.randint(-100, 100),  # Slight altitude change
                        ground_speed=flight.ground_speed + random.randint(-5, 5),
                        heading=(flight.heading + random.randint(-2, 2)) % 360,
                        distance_km=round(new_distance, 1),
                        registration=flight.registration,
                    )

            updated_flights.append(flight)

        self._flights = updated_flights

        # Occasionally add/remove a flight
        if random.random() < 0.1:  # 10% chance
            if len(self._flights) > 15 and random.random() < 0.5:
                # Remove a random flight
                self._flights.pop(random.randint(0, len(self._flights) - 1))
            elif len(self._flights) < 35:
                # Add a new flight
                self._flights.append(self._create_random_flight(len(self._flights)))

        return self._flights.copy()

    def _calculate_distance(self, lat: float, lon: float) -> float:
        """Calculate distance from center point."""
        from .utils import haversine_distance
        return haversine_distance(self.center_lat, self.center_lon, lat, lon)


class DemoClient:
    """Mock API client that returns demo data instead of calling the real API."""

    def __init__(
        self,
        center_lat: float = 51.47,
        center_lon: float = -0.45,
        radius_km: float = 100.0,
    ):
        """
        Initialize the demo client.

        Args:
            center_lat: Center latitude
            center_lon: Center longitude
            radius_km: Search radius in km
        """
        self.generator = DemoDataGenerator(
            center_lat=center_lat,
            center_lon=center_lon,
            radius_km=radius_km,
        )

    def get_live_flights(
        self,
        bounds: tuple[float, float, float, float],
        limit: int = 100,
    ) -> List[Flight]:
        """
        Get demo flight data.

        Args:
            bounds: Ignored in demo mode
            limit: Maximum number of flights to return

        Returns:
            List of demo Flight objects
        """
        flights = self.generator.get_flights()
        return flights[:limit]

    def get_live_flights_light(
        self,
        bounds: tuple[float, float, float, float],
        limit: int = 100,
    ) -> List[Flight]:
        """
        Get demo flight data (same as get_live_flights for demo mode).

        In demo mode, we have full data so this is identical to get_live_flights.

        Args:
            bounds: Ignored in demo mode
            limit: Maximum number of flights to return

        Returns:
            List of demo Flight objects
        """
        return self.get_live_flights(bounds, limit)

    def get_flight_details(
        self,
        callsigns: List[str],
    ) -> List[Flight]:
        """
        Get demo flight details by callsign (no-op for demo mode).

        In demo mode, all details are already included in get_live_flights.

        Args:
            callsigns: List of callsigns to fetch

        Returns:
            Empty list (details already in light response for demo)
        """
        return []

    def close(self):
        """No-op for demo client."""
        pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass
