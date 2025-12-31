"""Main window for Flight Display."""

import subprocess
import tkinter as tk
from typing import List

from ..models import Flight
from .flight_table import FlightTable
from .status_bar import StatusBar
from .theme import COLORS, FONTS


class MainWindow(tk.Tk):
    """Main application window with fullscreen support."""

    def __init__(self, fullscreen: bool = True, show_cursor: bool = False, demo_mode: bool = False):
        """
        Initialize the main window.

        Args:
            fullscreen: Whether to run in fullscreen mode
            show_cursor: Whether to show the mouse cursor
            demo_mode: Whether running in demo mode with fake data
        """
        super().__init__()

        self.demo_mode = demo_mode
        self.title("Flight Display" + (" [DEMO]" if demo_mode else ""))
        self.configure(bg=COLORS["bg_primary"])

        # Window size - default to 800x480 for Pi display
        if fullscreen:
            self.attributes("-fullscreen", True)
        else:
            self.geometry("800x480")

        # Hide cursor if requested
        if not show_cursor:
            self.config(cursor="none")

        # Bind escape key to exit (useful for testing)
        self.bind("<Escape>", lambda e: self.destroy())

        # Prevent screen from blanking (runs periodically)
        self.after(60000, self._prevent_screen_blank)

        # Create layout
        self._create_widgets()

    def _create_widgets(self):
        """Create the main window layout."""
        # Title bar
        title_frame = tk.Frame(self, bg=COLORS["bg_header"], height=40)
        title_frame.pack(fill=tk.X, side=tk.TOP)
        title_frame.pack_propagate(False)

        title_label = tk.Label(
            title_frame,
            text="FLIGHT DISPLAY",
            font=FONTS["title"],
            fg=COLORS["text_header"],
            bg=COLORS["bg_header"],
        )
        title_label.pack(side=tk.LEFT, padx=10, pady=5)

        # Demo mode indicator
        if self.demo_mode:
            demo_label = tk.Label(
                title_frame,
                text="[DEMO MODE]",
                font=FONTS["status"],
                fg=COLORS["warning"],
                bg=COLORS["bg_header"],
            )
            demo_label.pack(side=tk.LEFT, padx=10, pady=5)

        # Connection indicator
        self.connection_indicator = tk.Label(
            title_frame,
            text="\u25cf",  # Filled circle
            font=("Helvetica", 16),
            fg=COLORS["warning"],  # Start as warning until first update
            bg=COLORS["bg_header"],
        )
        self.connection_indicator.pack(side=tk.RIGHT, padx=10)

        # Status bar (bottom)
        self.status_bar = StatusBar(self)
        self.status_bar.pack(fill=tk.X, side=tk.BOTTOM)

        # Flight table (center, fills remaining space)
        self.flight_table = FlightTable(self)
        self.flight_table.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    def update_flights(self, flights: List[Flight]):
        """
        Update the flight table with new data.

        Args:
            flights: List of Flight objects to display
        """
        self.flight_table.set_flights(flights)

    def update_status(
        self,
        last_update: str,
        flight_count: int,
        connected: bool = True,
        status: str = None,
    ):
        """
        Update the status bar and connection indicator.

        Args:
            last_update: Time string of last update
            flight_count: Number of flights displayed
            connected: Whether connection is active
            status: Optional status message (defaults based on connected)
        """
        if status is None:
            status = "Connected" if connected else "Disconnected"

        self.status_bar.update(
            last_update=last_update,
            flight_count=flight_count,
            status=status,
            connected=connected,
        )

        self.connection_indicator.configure(
            fg=COLORS["success"] if connected else COLORS["error"]
        )

    def _prevent_screen_blank(self):
        """Periodically reset screen saver/blanking timer."""
        try:
            # Try xset (works on X11)
            subprocess.run(
                ["xset", "s", "reset"],
                capture_output=True,
                timeout=1,
            )
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass  # xset not available or timed out

        # Schedule next reset
        self.after(60000, self._prevent_screen_blank)
