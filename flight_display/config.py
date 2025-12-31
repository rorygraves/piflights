"""Configuration management for Flight Display."""

import os
import math
import yaml
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Tuple


@dataclass
class APIConfig:
    """API configuration settings."""

    key: str
    timeout: int = 30
    endpoint_type: str = "light"  # "light" or "full"


@dataclass
class LocationConfig:
    """Location configuration for center point and bounding box."""

    center_lat: float
    center_lon: float
    bounding_box_km: float = 100.0


@dataclass
class DisplayConfig:
    """Display and refresh configuration."""

    refresh_interval: int = 10
    max_flights: int = 50
    sort_by: str = "distance"
    sort_ascending: bool = True


@dataclass
class UIConfig:
    """UI configuration."""

    fullscreen: bool = True
    show_cursor: bool = False


@dataclass
class Config:
    """Main configuration container."""

    api: APIConfig
    location: LocationConfig
    display: DisplayConfig = field(default_factory=DisplayConfig)
    ui: UIConfig = field(default_factory=UIConfig)

    @classmethod
    def load(cls, path: Optional[str] = None) -> "Config":
        """
        Load configuration from a YAML file.

        Args:
            path: Path to config file. If None, searches default locations.

        Returns:
            Config object with loaded settings.

        Raises:
            FileNotFoundError: If no config file is found.
            ValueError: If API key is not configured.
        """
        if path is None:
            search_paths = [
                Path.home() / ".config" / "flight-display" / "config.yaml",
                Path("/etc/flight-display/config.yaml"),
                Path("config.yaml"),
            ]
            for p in search_paths:
                if p.exists():
                    path = str(p)
                    break

        if path is None or not Path(path).exists():
            raise FileNotFoundError(
                "Configuration file not found. "
                "Create config.yaml or specify path with --config"
            )

        with open(path, "r") as f:
            data = yaml.safe_load(f)

        # Check for API key in environment variable first
        api_key = os.environ.get("FR24_API_KEY", data.get("api", {}).get("key"))
        if not api_key or api_key == "your-fr24-api-key-here":
            raise ValueError(
                "API key must be set in config.yaml or FR24_API_KEY environment variable"
            )

        return cls(
            api=APIConfig(
                key=api_key,
                timeout=data.get("api", {}).get("timeout", 30),
                endpoint_type=data.get("api", {}).get("endpoint_type", "light"),
            ),
            location=LocationConfig(
                center_lat=data["location"]["center_lat"],
                center_lon=data["location"]["center_lon"],
                bounding_box_km=data["location"].get("bounding_box_km", 100.0),
            ),
            display=DisplayConfig(
                refresh_interval=data.get("display", {}).get("refresh_interval", 10),
                max_flights=data.get("display", {}).get("max_flights", 50),
                sort_by=data.get("display", {}).get("sort_by", "distance"),
                sort_ascending=data.get("display", {}).get("sort_ascending", True),
            ),
            ui=UIConfig(
                fullscreen=data.get("ui", {}).get("fullscreen", True),
                show_cursor=data.get("ui", {}).get("show_cursor", False),
            ),
        )

    def get_bounds(self) -> Tuple[float, float, float, float]:
        """
        Calculate bounding box from center point and radius.

        Returns:
            Tuple of (north, south, west, east) coordinates.
        """
        # Approximate: 1 degree latitude = 111 km
        # Longitude varies with latitude, use cosine correction
        km_per_degree_lat = 111.0
        km_per_degree_lon = 111.0 * math.cos(
            math.radians(self.location.center_lat)
        )

        lat_delta = self.location.bounding_box_km / km_per_degree_lat
        lon_delta = self.location.bounding_box_km / km_per_degree_lon

        north = self.location.center_lat + lat_delta
        south = self.location.center_lat - lat_delta
        west = self.location.center_lon - lon_delta
        east = self.location.center_lon + lon_delta

        return (north, south, west, east)
