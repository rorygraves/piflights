"""Scrollable flight table widget for Flight Display."""

import tkinter as tk
from typing import List

from ..models import Flight
from .theme import COLORS, FONTS, COLUMNS


class FlightTable(tk.Frame):
    """Scrollable table displaying flight information with touch support."""

    def __init__(self, parent):
        """
        Initialize the flight table.

        Args:
            parent: Parent Tkinter widget
        """
        super().__init__(parent, bg=COLORS["bg_primary"])
        self._last_y = 0
        self.flight_rows: List[tk.Frame] = []
        self._create_widgets()

    def _create_widgets(self):
        """Create table header and scrollable content area."""
        # Header row
        header_frame = tk.Frame(self, bg=COLORS["bg_header"], height=30)
        header_frame.pack(fill=tk.X)
        header_frame.pack_propagate(False)

        for col_id, col_name, width_px, anchor in COLUMNS:
            # Use a frame with fixed width to ensure alignment
            cell_frame = tk.Frame(header_frame, bg=COLORS["bg_header"], width=width_px, height=30)
            cell_frame.pack(side=tk.LEFT, padx=1)
            cell_frame.pack_propagate(False)

            label = tk.Label(
                cell_frame,
                text=col_name,
                font=FONTS["header"],
                fg=COLORS["text_header"],
                bg=COLORS["bg_header"],
                anchor=anchor,
            )
            label.pack(fill=tk.BOTH, expand=True)

        # Scrollable canvas for flight rows
        self.canvas = tk.Canvas(
            self,
            bg=COLORS["bg_primary"],
            highlightthickness=0,
        )

        self.scrollbar = tk.Scrollbar(
            self,
            orient=tk.VERTICAL,
            command=self.canvas.yview,
            bg=COLORS["bg_secondary"],
            troughcolor=COLORS["bg_primary"],
        )

        self.scrollable_frame = tk.Frame(
            self.canvas,
            bg=COLORS["bg_primary"],
        )

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")),
        )

        self.canvas_window = self.canvas.create_window(
            (0, 0),
            window=self.scrollable_frame,
            anchor="nw",
        )

        # Make canvas window resize with canvas
        self.canvas.bind(
            "<Configure>",
            lambda e: self.canvas.itemconfig(self.canvas_window, width=e.width),
        )

        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        # Enable touch/mouse scrolling
        self.canvas.bind("<Button-1>", self._start_scroll)
        self.canvas.bind("<B1-Motion>", self._do_scroll)
        self.scrollable_frame.bind("<Button-1>", self._start_scroll)
        self.scrollable_frame.bind("<B1-Motion>", self._do_scroll)

        # Mouse wheel scrolling
        self.canvas.bind("<MouseWheel>", self._on_mousewheel)
        self.canvas.bind("<Button-4>", self._on_mousewheel)
        self.canvas.bind("<Button-5>", self._on_mousewheel)

        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def _start_scroll(self, event):
        """Record starting position for touch scroll."""
        self._last_y = event.y

    def _do_scroll(self, event):
        """Handle touch/drag scrolling."""
        delta = self._last_y - event.y
        self.canvas.yview_scroll(int(delta / 10), "units")
        self._last_y = event.y

    def _on_mousewheel(self, event):
        """Handle mouse wheel scrolling."""
        if event.num == 4:  # Linux scroll up
            self.canvas.yview_scroll(-1, "units")
        elif event.num == 5:  # Linux scroll down
            self.canvas.yview_scroll(1, "units")
        else:  # Windows/macOS
            self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def set_flights(self, flights: List[Flight]):
        """
        Update the displayed flights.

        Args:
            flights: List of Flight objects to display
        """
        self.clear()

        for idx, flight in enumerate(flights):
            bg_color = COLORS["bg_secondary"] if idx % 2 == 0 else COLORS["row_alt"]
            row = self._create_row(flight, bg_color)
            row.pack(fill=tk.X, pady=1)
            self.flight_rows.append(row)

            # Bind scroll events to row and its children
            row.bind("<Button-1>", self._start_scroll)
            row.bind("<B1-Motion>", self._do_scroll)
            for child in row.winfo_children():
                child.bind("<Button-1>", self._start_scroll)
                child.bind("<B1-Motion>", self._do_scroll)

    def _create_row(self, flight: Flight, bg_color: str) -> tk.Frame:
        """
        Create a row frame for a flight.

        Args:
            flight: Flight data
            bg_color: Background color for the row

        Returns:
            Frame containing the flight row
        """
        row = tk.Frame(self.scrollable_frame, bg=bg_color, height=26)
        row.pack_propagate(False)

        # Format route as "ORG -> DST"
        route = f"{flight.origin} -> {flight.destination}"
        if flight.origin == "---" and flight.destination == "---":
            route = "---"

        # Create cell values matching column order
        values = [
            flight.callsign,
            flight.airline,
            flight.aircraft_type,
            route,
            f"{flight.altitude:,}" if flight.altitude else "---",
            str(flight.ground_speed) if flight.ground_speed else "---",
            f"{flight.heading:03d}" if flight.heading else "---",
            f"{flight.distance_km:.1f}",
        ]

        for (col_id, _, width_px, anchor), value in zip(COLUMNS, values):
            # Use a frame with fixed width to match header
            cell_frame = tk.Frame(row, bg=bg_color, width=width_px, height=26)
            cell_frame.pack(side=tk.LEFT, padx=1)
            cell_frame.pack_propagate(False)

            label = tk.Label(
                cell_frame,
                text=value,
                font=FONTS["data"],
                fg=COLORS["text_primary"],
                bg=bg_color,
                anchor=anchor,
            )
            label.pack(fill=tk.BOTH, expand=True)

        return row

    def clear(self):
        """Remove all flight rows."""
        for row in self.flight_rows:
            row.destroy()
        self.flight_rows.clear()
