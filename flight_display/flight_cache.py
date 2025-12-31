"""Flight details cache for efficient API usage."""

import logging
import time
from dataclasses import dataclass
from typing import Dict, Optional, Set

logger = logging.getLogger(__name__)


@dataclass
class CachedFlightDetails:
    """Cached details for a flight (data that doesn't change during flight)."""

    flight_id: str
    aircraft_type: str
    airline: str
    origin: str
    destination: str
    registration: str
    cached_at: float  # timestamp

    def is_expired(self, ttl_seconds: int = 3600) -> bool:
        """Check if cache entry has expired."""
        return (time.time() - self.cached_at) > ttl_seconds


class FlightCache:
    """
    Cache for flight details to minimize full API calls.

    Strategy:
    - Light endpoint: Called frequently for position updates (cheap)
    - Full endpoint: Called only for NEW flights not in cache (expensive)
    - Cache stores: aircraft type, airline, origin, destination
    - Position data always comes from light endpoint (real-time)
    """

    def __init__(self, ttl_seconds: int = 3600):
        """
        Initialize the flight cache.

        Args:
            ttl_seconds: Time-to-live for cache entries (default 1 hour)
        """
        self._cache: Dict[str, CachedFlightDetails] = {}
        self._ttl_seconds = ttl_seconds
        self._hits = 0
        self._misses = 0

    def get(self, flight_id: str) -> Optional[CachedFlightDetails]:
        """
        Get cached flight details.

        Args:
            flight_id: The flight's fr24_id

        Returns:
            CachedFlightDetails if found and not expired, None otherwise
        """
        entry = self._cache.get(flight_id)
        if entry is None:
            self._misses += 1
            return None

        if entry.is_expired(self._ttl_seconds):
            del self._cache[flight_id]
            self._misses += 1
            return None

        self._hits += 1
        return entry

    def put(
        self,
        flight_id: str,
        aircraft_type: str = "",
        airline: str = "",
        origin: str = "",
        destination: str = "",
        registration: str = "",
    ) -> None:
        """
        Store flight details in cache.

        Args:
            flight_id: The flight's fr24_id
            aircraft_type: Aircraft type code (e.g., A320)
            airline: Airline code
            origin: Origin airport code
            destination: Destination airport code
            registration: Aircraft registration
        """
        self._cache[flight_id] = CachedFlightDetails(
            flight_id=flight_id,
            aircraft_type=aircraft_type,
            airline=airline,
            origin=origin,
            destination=destination,
            registration=registration,
            cached_at=time.time(),
        )
        logger.debug(f"Cached details for flight {flight_id}")

    def get_missing_ids(self, flight_ids: Set[str]) -> Set[str]:
        """
        Get flight IDs that are not in cache (need full API lookup).

        Args:
            flight_ids: Set of flight IDs to check

        Returns:
            Set of flight IDs not in cache or expired
        """
        missing = set()
        for fid in flight_ids:
            if self.get(fid) is None:
                missing.add(fid)
        return missing

    def cleanup_expired(self) -> int:
        """
        Remove expired entries from cache.

        Returns:
            Number of entries removed
        """
        expired = [
            fid for fid, entry in self._cache.items()
            if entry.is_expired(self._ttl_seconds)
        ]
        for fid in expired:
            del self._cache[fid]

        if expired:
            logger.debug(f"Cleaned up {len(expired)} expired cache entries")

        return len(expired)

    def cleanup_departed(self, current_flight_ids: Set[str]) -> int:
        """
        Remove flights that are no longer in the area.

        Args:
            current_flight_ids: Set of flight IDs currently in the area

        Returns:
            Number of entries removed
        """
        departed = set(self._cache.keys()) - current_flight_ids
        for fid in departed:
            del self._cache[fid]

        if departed:
            logger.debug(f"Removed {len(departed)} departed flights from cache")

        return len(departed)

    @property
    def size(self) -> int:
        """Number of entries in cache."""
        return len(self._cache)

    @property
    def stats(self) -> dict:
        """Cache statistics."""
        total = self._hits + self._misses
        hit_rate = (self._hits / total * 100) if total > 0 else 0
        return {
            "size": self.size,
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": f"{hit_rate:.1f}%",
        }

    def clear(self) -> None:
        """Clear all cache entries."""
        self._cache.clear()
        self._hits = 0
        self._misses = 0
