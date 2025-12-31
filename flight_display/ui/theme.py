"""Dark theme colors and fonts for Flight Display."""

# Color scheme - dark navy theme
COLORS = {
    "bg_primary": "#1a1a2e",  # Dark navy background
    "bg_secondary": "#16213e",  # Slightly lighter for alternating rows
    "bg_header": "#0f3460",  # Header background
    "bg_status": "#0a0a14",  # Status bar background
    "text_primary": "#e0e0e0",  # Main text color
    "text_secondary": "#a0a0a0",  # Secondary/dimmed text
    "text_header": "#ffffff",  # Header text
    "accent": "#e94560",  # Accent color (red)
    "accent_alt": "#00d9ff",  # Alternative accent (cyan)
    "success": "#00c853",  # Connection OK indicator
    "warning": "#ffc107",  # Warning indicator
    "error": "#ff5252",  # Error/disconnected indicator
    "row_alt": "#1e2a4a",  # Alternating row background
    "border": "#2d3a5a",  # Border color
}

# Font definitions
FONTS = {
    "title": ("Helvetica", 14, "bold"),
    "header": ("Helvetica", 11, "bold"),
    "data": ("Courier", 10, "normal"),  # Monospace for alignment
    "data_small": ("Courier", 9, "normal"),
    "status": ("Helvetica", 9, "normal"),
}

# Column definitions for flight table
# (id, header_text, width_pixels, anchor)
# Total width ~780px for 800px display with padding
COLUMNS = [
    ("callsign", "CALLSIGN", 90, "w"),
    ("airline", "AIRLINE", 70, "center"),
    ("aircraft", "A/C", 60, "center"),
    ("route", "ROUTE", 140, "center"),
    ("altitude", "ALT ft", 80, "e"),
    ("speed", "SPD kt", 70, "e"),
    ("heading", "HDG", 50, "e"),
    ("distance", "DIST km", 80, "e"),
]
