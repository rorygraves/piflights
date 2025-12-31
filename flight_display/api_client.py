"""FlightRadar24 API client."""

import logging
from typing import List, Optional

import requests

from .models import Flight

logger = logging.getLogger(__name__)


class FR24APIError(Exception):
    """Exception raised for FR24 API errors."""

    pass


class FR24Client:
    """Client for the FlightRadar24 API."""

    BASE_URL = "https://fr24api.flightradar24.com/api"

    def __init__(self, api_key: str, timeout: int = 30, endpoint_type: str = "light"):
        """
        Initialize the FR24 API client.

        Args:
            api_key: FlightRadar24 API key
            timeout: Request timeout in seconds
            endpoint_type: "light" or "full" - determines which endpoint to use
        """
        self.api_key = api_key
        self.timeout = timeout
        self.endpoint_type = endpoint_type
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Accept": "application/json",
                "Accept-Version": "v1",
                "Authorization": f"Bearer {api_key}",
            }
        )

    def get_live_flights_light(
        self,
        bounds: tuple[float, float, float, float],
        limit: int = 100,
    ) -> List[Flight]:
        """
        Fetch live flights using the LIGHT endpoint (position data only).

        Args:
            bounds: Tuple of (north, south, west, east) coordinates
            limit: Maximum number of flights to return

        Returns:
            List of Flight objects with position data
        """
        return self._fetch_flights("light", bounds=bounds, limit=limit)

    def get_flight_details(
        self,
        callsigns: List[str],
    ) -> List[Flight]:
        """
        Fetch full details for specific flights by callsign.

        Uses the FULL endpoint to get aircraft type, route, airline info.
        Limited to 15 callsigns per request by the API.

        Args:
            callsigns: List of callsigns to fetch (max 15)

        Returns:
            List of Flight objects with full details
        """
        if not callsigns:
            return []

        # API limit is 15 callsigns per request
        callsigns = callsigns[:15]
        return self._fetch_flights("full", callsigns=callsigns)

    def get_live_flights(
        self,
        bounds: tuple[float, float, float, float],
        limit: int = 100,
    ) -> List[Flight]:
        """
        Fetch live flights within a bounding box (uses configured endpoint type).

        Args:
            bounds: Tuple of (north, south, west, east) coordinates
            limit: Maximum number of flights to return

        Returns:
            List of Flight objects

        Raises:
            FR24APIError: If the API request fails
        """
        return self._fetch_flights(self.endpoint_type, bounds=bounds, limit=limit)

    def _fetch_flights(
        self,
        endpoint_type: str,
        bounds: tuple[float, float, float, float] = None,
        callsigns: List[str] = None,
        limit: int = 100,
    ) -> List[Flight]:
        """
        Internal method to fetch flights from the API.

        Args:
            endpoint_type: "light" or "full"
            bounds: Optional bounding box (north, south, west, east)
            callsigns: Optional list of callsigns to filter
            limit: Maximum number of flights to return

        Returns:
            List of Flight objects
        """
        params = {"limit": str(limit)}

        if bounds:
            north, south, west, east = bounds
            params["bounds"] = f"{north},{south},{west},{east}"

        if callsigns:
            params["callsigns"] = ",".join(callsigns)

        try:
            endpoint = f"{self.BASE_URL}/live/flight-positions/{endpoint_type}"
            logger.debug(f"Fetching from {endpoint} with params: {params}")

            response = self.session.get(
                endpoint,
                params=params,
                timeout=self.timeout,
            )
            response.raise_for_status()
            return self._parse_response(response.json())

        except requests.exceptions.Timeout as e:
            logger.error(f"API request timed out: {e}")
            raise FR24APIError(f"Request timed out: {e}") from e

        except requests.exceptions.ConnectionError as e:
            logger.error(f"Connection error: {e}")
            raise FR24APIError(f"Connection error: {e}") from e

        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP error: {e}")
            if response.status_code == 401:
                raise FR24APIError("Invalid API key") from e
            elif response.status_code == 429:
                raise FR24APIError("Rate limit exceeded") from e
            raise FR24APIError(f"HTTP error: {e}") from e

        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {e}")
            raise FR24APIError(f"Request failed: {e}") from e

    def _parse_response(self, data: dict) -> List[Flight]:
        """
        Parse API response into Flight objects.

        Args:
            data: Raw JSON response from API

        Returns:
            List of Flight objects
        """
        flights = []
        flight_data = data.get("data", [])

        for item in flight_data:
            try:
                # Light endpoint fields:
                # fr24_id, hex, callsign, lat, lon, track, alt, gspeed, vspeed, squawk, timestamp, source
                #
                # Full endpoint has additional fields like origin, destination, aircraft, etc.

                flight = Flight(
                    flight_id=str(item.get("fr24_id", "") or item.get("flightId", "") or item.get("id", "")),
                    callsign=item.get("callsign", "") or "",
                    airline=self._extract_airline(item),
                    aircraft_type=self._extract_aircraft_type(item),
                    origin=self._extract_airport(item, "origin"),
                    destination=self._extract_airport(item, "destination"),
                    latitude=float(item.get("lat", 0) or item.get("latitude", 0) or 0),
                    longitude=float(item.get("lon", 0) or item.get("longitude", 0) or 0),
                    altitude=int(item.get("alt", 0) or item.get("altitude", 0) or 0),
                    ground_speed=int(item.get("gspeed", 0) or item.get("groundSpeed", 0) or item.get("speed", 0) or 0),
                    heading=int(item.get("track", 0) or item.get("heading", 0) or 0),
                    registration=item.get("registration", "") or item.get("hex", "") or "",
                    vertical_speed=int(item.get("vspeed", 0) or 0) if item.get("vspeed") is not None else None,
                )
                flights.append(flight)
            except (KeyError, ValueError, TypeError) as e:
                logger.warning(f"Failed to parse flight data: {e} - item: {item}")
                continue

        logger.debug(f"Parsed {len(flights)} flights from API response")
        return flights

    def _extract_aircraft_type(self, item: dict) -> str:
        """Extract aircraft type from response."""
        # Full endpoint format
        if "aircraft" in item and isinstance(item["aircraft"], dict):
            model = item["aircraft"].get("model", {})
            if isinstance(model, dict):
                return model.get("code", "") or ""
            return str(model) if model else ""

        # Direct field
        return item.get("typecode", "") or item.get("aircraft_type", "") or ""

    def _extract_airport(self, item: dict, field: str) -> str:
        """Extract airport code from response."""
        # Full endpoint format
        if field in item and isinstance(item[field], dict):
            return item[field].get("iata", "") or item[field].get("icao", "") or ""

        # Direct field variations
        if field == "origin":
            return item.get("orig_iata", "") or item.get("origin_iata", "") or ""
        elif field == "destination":
            return item.get("dest_iata", "") or item.get("destination_iata", "") or ""

        return ""

    def _extract_airline(self, item: dict) -> str:
        """
        Extract airline code from response.

        Args:
            item: Flight data dictionary

        Returns:
            Airline code or empty string
        """
        # Try various possible locations for airline info
        if "airline" in item and isinstance(item["airline"], dict):
            return item["airline"].get("icao", "") or item["airline"].get("iata", "")

        if "airline" in item and isinstance(item["airline"], str):
            return item["airline"]

        # Derive from callsign (first 3 chars are often airline code)
        callsign = item.get("callsign", "")
        if callsign and len(callsign) >= 3:
            return callsign[:3]

        return ""

    def close(self):
        """Close the HTTP session."""
        self.session.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
