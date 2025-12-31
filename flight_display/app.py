"""Main application class for Flight Display."""

import logging
from datetime import datetime
from typing import List

from .api_client import FR24Client
from .config import Config
from .models import Flight
from .ui.main_window import MainWindow
from .updater import DataUpdater

logger = logging.getLogger(__name__)


class FlightDisplayApp:
    """Main application that orchestrates all components."""

    def __init__(self, config: Config, demo_mode: bool = False):
        """
        Initialize the Flight Display application.

        Args:
            config: Application configuration
            demo_mode: If True, use fake flight data instead of real API
        """
        self.config = config
        self.demo_mode = demo_mode
        self.connected = False
        self.last_flights: List[Flight] = []

        # Initialize API client (real or demo)
        if demo_mode:
            from .demo_data import DemoClient
            self.api_client = DemoClient(
                center_lat=config.location.center_lat,
                center_lon=config.location.center_lon,
                radius_km=config.location.bounding_box_km,
            )
            logger.info("Using DEMO client with fake flight data")
        else:
            self.api_client = FR24Client(
                api_key=config.api.key,
                timeout=config.api.timeout,
                endpoint_type=config.api.endpoint_type,
            )
            logger.info(f"Using FR24 API endpoint: {config.api.endpoint_type}")

        # Initialize UI
        self.window = MainWindow(
            fullscreen=config.ui.fullscreen,
            show_cursor=config.ui.show_cursor,
            demo_mode=demo_mode,
        )

        # Initialize data updater
        self.updater = DataUpdater(
            api_client=self.api_client,
            config=config,
            on_update=self._on_data_update,
            on_error=self._on_error,
        )

        logger.info(f"Application initialized (demo_mode={demo_mode})")

    def run(self):
        """Start the application."""
        logger.info("Starting Flight Display application")
        logger.info(
            f"Monitoring area: center=({self.config.location.center_lat}, "
            f"{self.config.location.center_lon}), "
            f"radius={self.config.location.bounding_box_km}km"
        )

        # Start background data updates
        self.updater.start()

        # Start queue processing
        self._process_queue()

        # Run Tkinter main loop
        try:
            self.window.mainloop()
        except KeyboardInterrupt:
            logger.info("Application interrupted")
        finally:
            self._cleanup()

    def _process_queue(self):
        """Process data from update thread (runs on main thread)."""
        self.updater.process_queue(self.window)

    def _on_data_update(self, flights: List[Flight]):
        """
        Handle successful data update from the API.

        Args:
            flights: List of Flight objects from API
        """
        self.connected = True
        self.last_flights = flights

        # Sort flights according to configuration
        flights = self._sort_flights(flights)

        # Limit display count
        flights = flights[: self.config.display.max_flights]

        # Update UI
        self.window.update_flights(flights)
        self.window.update_status(
            last_update=datetime.now().strftime("%H:%M:%S"),
            flight_count=len(flights),
            connected=True,
        )

        logger.debug(f"Display updated with {len(flights)} flights")

    def _on_error(self, error_msg: str):
        """
        Handle update error.

        Args:
            error_msg: Error message from updater
        """
        self.connected = False
        logger.warning(f"Update error: {error_msg}")

        # Update status but keep last flight data displayed
        self.window.update_status(
            last_update=datetime.now().strftime("%H:%M:%S"),
            flight_count=len(self.last_flights),
            connected=False,
            status=f"Error: {error_msg[:30]}..." if len(error_msg) > 30 else error_msg,
        )

    def _sort_flights(self, flights: List[Flight]) -> List[Flight]:
        """
        Sort flights according to configuration.

        Args:
            flights: List of flights to sort

        Returns:
            Sorted list of flights
        """
        sort_key = self.config.display.sort_by
        reverse = not self.config.display.sort_ascending

        if sort_key == "distance":
            return sorted(flights, key=lambda f: f.distance_km, reverse=reverse)
        elif sort_key == "altitude":
            return sorted(flights, key=lambda f: f.altitude, reverse=reverse)
        elif sort_key == "callsign":
            return sorted(flights, key=lambda f: f.callsign, reverse=reverse)
        elif sort_key == "speed":
            return sorted(flights, key=lambda f: f.ground_speed, reverse=reverse)
        else:
            return flights

    def _cleanup(self):
        """Clean up resources on shutdown."""
        logger.info("Shutting down...")
        self.updater.stop()
        self.api_client.close()
        logger.info("Cleanup complete")
