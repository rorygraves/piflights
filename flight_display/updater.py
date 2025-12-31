"""Background data updater for Flight Display."""

import logging
import queue
import threading
from typing import Callable, List, Optional, Set

from .api_client import FR24Client, FR24APIError
from .config import Config
from .flight_cache import FlightCache
from .models import Flight
from .utils import haversine_distance

logger = logging.getLogger(__name__)


class DataUpdater:
    """Background thread that polls the FR24 API and pushes updates to a queue."""

    def __init__(
        self,
        api_client: FR24Client,
        config: Config,
        on_update: Callable[[List[Flight]], None],
        on_error: Callable[[str], None],
    ):
        """
        Initialize the data updater.

        Args:
            api_client: FR24 API client instance
            config: Application configuration
            on_update: Callback for successful updates (receives flight list)
            on_error: Callback for errors (receives error message)
        """
        self.api_client = api_client
        self.config = config
        self.on_update = on_update
        self.on_error = on_error

        self.data_queue: queue.Queue = queue.Queue()
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._consecutive_errors = 0
        self._max_consecutive_errors = 5

        # Cache for flight details (aircraft type, airline, route)
        self._flight_cache = FlightCache(ttl_seconds=3600)
        self._details_fetch_interval = 5  # Fetch details every N updates
        self._update_count = 0

    def start(self):
        """Start the background update thread."""
        if self._thread is not None and self._thread.is_alive():
            logger.warning("Updater already running")
            return

        self._stop_event.clear()
        self._consecutive_errors = 0
        self._thread = threading.Thread(target=self._worker, daemon=True)
        self._thread.start()
        logger.info("Background updater started")

    def stop(self):
        """Stop the background update thread."""
        self._stop_event.set()
        if self._thread is not None:
            self._thread.join(timeout=5)
            self._thread = None
        logger.info("Background updater stopped")

    def _worker(self):
        """Worker thread that polls the API using hybrid light+full strategy."""
        while not self._stop_event.is_set():
            try:
                self._update_count += 1

                # Step 1: Get position data from light endpoint (cheap)
                flights = self.api_client.get_live_flights_light(
                    bounds=self.config.get_bounds(),
                    limit=self.config.display.max_flights,
                )

                # Get current flight IDs
                current_flight_ids = {f.flight_id for f in flights if f.flight_id}

                # Step 2: Check for new flights not in cache
                missing_ids = self._flight_cache.get_missing_ids(current_flight_ids)

                # Step 3: Fetch full details for new flights (if any and using full endpoint)
                if missing_ids and self.config.api.endpoint_type == "full":
                    # Get callsigns for missing flights
                    missing_callsigns = [
                        f.callsign for f in flights
                        if f.flight_id in missing_ids and f.callsign
                    ]

                    if missing_callsigns:
                        logger.debug(
                            f"Fetching details for {len(missing_callsigns)} new flights"
                        )
                        try:
                            detailed_flights = self.api_client.get_flight_details(
                                callsigns=missing_callsigns[:15]  # API limit
                            )

                            # Cache the details
                            for df in detailed_flights:
                                self._flight_cache.put(
                                    flight_id=df.flight_id,
                                    aircraft_type=df.aircraft_type,
                                    airline=df.airline,
                                    origin=df.origin,
                                    destination=df.destination,
                                    registration=df.registration,
                                )
                        except FR24APIError as e:
                            logger.warning(f"Failed to fetch flight details: {e}")

                # Step 4: Enrich flights with cached details
                for flight in flights:
                    cached = self._flight_cache.get(flight.flight_id)
                    if cached:
                        # Merge cached details with live position data
                        if not flight.aircraft_type and cached.aircraft_type:
                            flight.aircraft_type = cached.aircraft_type
                        if not flight.airline and cached.airline:
                            flight.airline = cached.airline
                        if not flight.origin and cached.origin:
                            flight.origin = cached.origin
                        if not flight.destination and cached.destination:
                            flight.destination = cached.destination
                        if not flight.registration and cached.registration:
                            flight.registration = cached.registration

                    # Calculate distance from center
                    flight.distance_km = haversine_distance(
                        self.config.location.center_lat,
                        self.config.location.center_lon,
                        flight.latitude,
                        flight.longitude,
                    )

                # Step 5: Periodic cache cleanup
                if self._update_count % 10 == 0:
                    self._flight_cache.cleanup_departed(current_flight_ids)
                    self._flight_cache.cleanup_expired()
                    logger.debug(f"Cache stats: {self._flight_cache.stats}")

                self.data_queue.put(("success", flights))
                self._consecutive_errors = 0
                logger.debug(f"Fetched {len(flights)} flights ({len(missing_ids)} new)")

            except FR24APIError as e:
                self._consecutive_errors += 1
                error_msg = str(e)
                self.data_queue.put(("error", error_msg))
                logger.warning(f"API error ({self._consecutive_errors}): {error_msg}")

                # Back off if too many consecutive errors
                if self._consecutive_errors >= self._max_consecutive_errors:
                    logger.error("Too many consecutive errors, backing off")
                    self._stop_event.wait(30)  # Wait 30 seconds before retrying
                    continue

            except Exception as e:
                self._consecutive_errors += 1
                error_msg = f"Unexpected error: {e}"
                self.data_queue.put(("error", error_msg))
                logger.exception(error_msg)

            # Wait for next update interval or stop signal
            self._stop_event.wait(self.config.display.refresh_interval)

    def process_queue(self, root) -> None:
        """
        Process pending updates from the queue.

        This should be called from the main thread using Tkinter's after() method.

        Args:
            root: Tkinter root window for scheduling next check
        """
        try:
            while True:
                status, data = self.data_queue.get_nowait()
                if status == "success":
                    self.on_update(data)
                else:
                    self.on_error(data)
        except queue.Empty:
            pass

        # Schedule next queue check
        root.after(100, lambda: self.process_queue(root))

    @property
    def is_running(self) -> bool:
        """Check if the updater is running."""
        return self._thread is not None and self._thread.is_alive()
