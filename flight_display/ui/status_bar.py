"""Status bar widget for Flight Display."""

import tkinter as tk

from .theme import COLORS, FONTS


class StatusBar(tk.Frame):
    """Status bar showing update time, flight count, and connection status."""

    def __init__(self, parent):
        """
        Initialize the status bar.

        Args:
            parent: Parent Tkinter widget
        """
        super().__init__(parent, bg=COLORS["bg_status"], height=25)
        self.pack_propagate(False)
        self._create_widgets()

    def _create_widgets(self):
        """Create status bar widgets."""
        # Last update time
        self.last_update_label = tk.Label(
            self,
            text="Updated: --:--:--",
            font=FONTS["status"],
            fg=COLORS["text_secondary"],
            bg=COLORS["bg_status"],
        )
        self.last_update_label.pack(side=tk.LEFT, padx=10)

        # Flight count
        self.flight_count_label = tk.Label(
            self,
            text="Flights: 0",
            font=FONTS["status"],
            fg=COLORS["text_secondary"],
            bg=COLORS["bg_status"],
        )
        self.flight_count_label.pack(side=tk.LEFT, padx=20)

        # Connection status
        self.status_label = tk.Label(
            self,
            text="Initializing...",
            font=FONTS["status"],
            fg=COLORS["accent_alt"],
            bg=COLORS["bg_status"],
        )
        self.status_label.pack(side=tk.RIGHT, padx=10)

    def update(
        self,
        last_update: str,
        flight_count: int,
        status: str = "Connected",
        connected: bool = True,
    ):
        """
        Update status bar information.

        Args:
            last_update: Time string of last successful update
            flight_count: Number of flights displayed
            status: Status message to display
            connected: Whether connection is active
        """
        self.last_update_label.configure(text=f"Updated: {last_update}")
        self.flight_count_label.configure(text=f"Flights: {flight_count}")
        self.status_label.configure(
            text=status,
            fg=COLORS["success"] if connected else COLORS["error"],
        )
