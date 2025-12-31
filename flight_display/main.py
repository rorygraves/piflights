#!/usr/bin/env python3
"""
Flight Display Application

Displays live flight data from FlightRadar24 on a Raspberry Pi touchscreen.
"""

import argparse
import logging
import sys
from pathlib import Path

from .app import FlightDisplayApp
from .config import Config, APIConfig, LocationConfig, DisplayConfig, UIConfig


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="FlightRadar24 Display for Raspberry Pi",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  flight-display                    # Run with default config
  flight-display -c /path/to/config.yaml
  flight-display --windowed         # Run in windowed mode for testing
  flight-display -v                 # Enable verbose logging
        """,
    )

    parser.add_argument(
        "-c",
        "--config",
        help="Path to configuration file",
        default=None,
    )

    parser.add_argument(
        "-v",
        "--verbose",
        help="Enable verbose/debug logging",
        action="store_true",
    )

    parser.add_argument(
        "--windowed",
        help="Run in windowed mode instead of fullscreen",
        action="store_true",
    )

    parser.add_argument(
        "--show-cursor",
        help="Show mouse cursor",
        action="store_true",
    )

    parser.add_argument(
        "--demo",
        help="Run in demo mode with fake flight data (no API key required)",
        action="store_true",
    )

    parser.add_argument(
        "--lat",
        type=float,
        help="Center latitude for demo mode (default: 51.47)",
        default=51.47,
    )

    parser.add_argument(
        "--lon",
        type=float,
        help="Center longitude for demo mode (default: -0.45)",
        default=-0.45,
    )

    return parser.parse_args()


def setup_logging(verbose: bool):
    """
    Configure logging for the application.

    Args:
        verbose: If True, enable debug logging
    """
    level = logging.DEBUG if verbose else logging.INFO

    # Create formatter
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)

    # File handler - log to /tmp for easy access
    log_file = Path("/tmp/flight-display.log")
    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(formatter)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)

    # Reduce noise from requests library
    logging.getLogger("urllib3").setLevel(logging.WARNING)


def main():
    """Main entry point for the application."""
    args = parse_args()
    setup_logging(args.verbose)

    logger = logging.getLogger(__name__)
    logger.info("Starting Flight Display Application")

    try:
        if args.demo:
            # Demo mode - no config file needed
            logger.info("Running in DEMO mode with fake flight data")
            print("\n" + "=" * 50)
            print("  DEMO MODE - Using simulated flight data")
            print("  No API key required")
            print("=" * 50 + "\n")

            # Create a minimal config for demo mode
            config = Config(
                api=APIConfig(key="demo-mode", timeout=30),
                location=LocationConfig(
                    center_lat=args.lat,
                    center_lon=args.lon,
                    bounding_box_km=100.0,
                ),
                display=DisplayConfig(
                    refresh_interval=5,  # Faster updates in demo
                    max_flights=50,
                    sort_by="distance",
                    sort_ascending=True,
                ),
                ui=UIConfig(
                    fullscreen=not args.windowed,
                    show_cursor=args.show_cursor,
                ),
            )

            app = FlightDisplayApp(config, demo_mode=True)
            app.run()

        else:
            # Normal mode - load configuration
            config = Config.load(args.config)

            # Override config with command line options
            if args.windowed:
                config.ui.fullscreen = False

            if args.show_cursor:
                config.ui.show_cursor = True

            # Create and run application
            app = FlightDisplayApp(config)
            app.run()

    except FileNotFoundError as e:
        logger.error(f"Configuration error: {e}")
        print(f"\nError: {e}", file=sys.stderr)
        print("\nPlease create a config.yaml file. See config.example.yaml for reference.")
        print("\nTip: Run with --demo flag to test without an API key:")
        print("  poetry run flight-display --demo --windowed")
        sys.exit(1)

    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        print(f"\nError: {e}", file=sys.stderr)
        print("\nTip: Run with --demo flag to test without an API key:")
        print("  poetry run flight-display --demo --windowed")
        sys.exit(1)

    except KeyboardInterrupt:
        logger.info("Application terminated by user")

    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        print(f"\nUnexpected error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
