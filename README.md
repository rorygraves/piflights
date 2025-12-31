# Flight Display

A Raspberry Pi application that displays live flight data from FlightRadar24 on the official 7" touchscreen (800x480).

![Demo Mode](https://img.shields.io/badge/demo-available-green) ![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue)

## Features

- Real-time flight tracking within a configurable geographic area
- Dark-themed UI optimized for the 7" touchscreen
- Touch-scrollable flight list
- Shows: callsign, airline, aircraft type, route, altitude, speed, heading, and distance
- Auto-starts on boot
- Graceful handling of network disconnections
- **Demo mode** for testing without an API key

## Quick Start (Demo Mode)

Try the application immediately without any configuration:

```bash
# Clone the repository
git clone <repository-url>
cd flight-display

# Install Poetry (if needed)
curl -sSL https://install.python-poetry.org | python3 -

# Install dependencies
poetry install

# Run in demo mode (no API key required!)
poetry run flight-display --demo --windowed
```

Press `Escape` to exit.

## Requirements

### Hardware
- Raspberry Pi 3B+ or newer (Pi 4 recommended)
- Official Raspberry Pi 7" touchscreen (800x480) or any HDMI display
- Network connectivity (Ethernet or WiFi)

### Software
- Raspberry Pi OS (Bookworm or later) / macOS / Linux
- Python 3.9+
- Poetry (Python package manager)

### API Key (for live data)
- FlightRadar24 API key - [Get one here](https://fr24api.flightradar24.com/)
- Free tier available with limited requests

## Installation

### 1. Clone the repository

```bash
git clone <repository-url> ~/flight-display
cd ~/flight-display
```

### 2. Install Poetry

If you don't have Poetry installed:

```bash
curl -sSL https://install.python-poetry.org | python3 -
```

Add Poetry to your PATH (add to `~/.bashrc` or `~/.zshrc`):
```bash
export PATH="$HOME/.local/bin:$PATH"
```

### 3. Install Python dependencies

```bash
cd ~/flight-display
poetry install
```

### 4. Install system packages (Raspberry Pi only)

```bash
sudo apt update
sudo apt install python3-tk unclutter
```

### 5. Configure the application

```bash
# Create config directory
mkdir -p ~/.config/flight-display

# Copy example config
cp config.example.yaml ~/.config/flight-display/config.yaml

# Edit with your settings
nano ~/.config/flight-display/config.yaml
```

**Important**: Add your FlightRadar24 API key and set your location coordinates.

## Usage

### Demo Mode (No API Key Required)

Test the application with simulated flight data:

```bash
# Basic demo mode (fullscreen)
poetry run flight-display --demo

# Windowed demo mode (for testing)
poetry run flight-display --demo --windowed

# Demo with custom location
poetry run flight-display --demo --windowed --lat 40.7128 --lon -74.0060  # New York
```

### Live Mode (Requires API Key)

```bash
# Run with default config
poetry run flight-display

# Windowed mode for testing
poetry run flight-display --windowed

# With specific config file
poetry run flight-display -c /path/to/config.yaml

# Enable debug logging
poetry run flight-display -v --windowed
```

### All Command Line Options

```
flight-display [-h] [-c CONFIG] [-v] [--windowed] [--show-cursor] [--demo] [--lat LAT] [--lon LON]

Options:
  -h, --help            Show help message and exit
  -c, --config CONFIG   Path to configuration file
  -v, --verbose         Enable debug logging
  --windowed            Run in windowed mode instead of fullscreen
  --show-cursor         Show mouse cursor
  --demo                Run in demo mode with fake flight data (no API key required)
  --lat LAT             Center latitude for demo mode (default: 51.47)
  --lon LON             Center longitude for demo mode (default: -0.45)
```

## Configuration

The configuration file is located at `~/.config/flight-display/config.yaml`.

### Full Configuration Reference

```yaml
# FlightRadar24 API settings
api:
  # Your API key (or set FR24_API_KEY environment variable)
  key: "your-fr24-api-key-here"
  # Request timeout in seconds
  timeout: 30

# Geographic location settings
location:
  # Center point latitude (your location)
  center_lat: 51.4700
  # Center point longitude (your location)
  center_lon: -0.4543
  # Search radius in kilometers (creates a bounding box)
  bounding_box_km: 100

# Display settings
display:
  # Seconds between API updates (minimum: 5)
  refresh_interval: 10
  # Maximum number of flights to show
  max_flights: 50
  # Sort order: distance, altitude, callsign, or speed
  sort_by: distance
  # Sort direction: true = ascending, false = descending
  sort_ascending: true

# UI settings
ui:
  # Run in fullscreen mode
  fullscreen: true
  # Show mouse cursor
  show_cursor: false
```

### Finding Your Coordinates

1. Go to [Google Maps](https://maps.google.com)
2. Right-click on your location
3. Click on the coordinates to copy them
4. Format: `latitude, longitude` (e.g., `51.4700, -0.4543`)

### Using Environment Variables

You can set the API key via environment variable instead of the config file:

```bash
export FR24_API_KEY="your-api-key-here"
poetry run flight-display
```

## Raspberry Pi Setup

### Automatic Setup

Run the installation script:

```bash
cd ~/flight-display
./scripts/install.sh
```

This script will:
- Install system dependencies
- Set up configuration directory
- Create desktop autostart entry
- Configure screen blanking prevention

### Manual Setup

#### 1. Create Desktop Autostart Entry

```bash
mkdir -p ~/.config/autostart

cat > ~/.config/autostart/flight-display.desktop << 'EOF'
[Desktop Entry]
Type=Application
Name=Flight Display
Comment=FlightRadar24 Display Application
Exec=/usr/bin/bash -c 'cd ~/flight-display && poetry run flight-display'
Terminal=false
Hidden=false
X-GNOME-Autostart-enabled=true
StartupNotify=false
EOF
```

#### 2. Disable Screen Blanking

**Option A: Using raspi-config**
```bash
sudo raspi-config
# Navigate to: Display Options -> Screen Blanking -> No
```

**Option B: Using lxsession autostart**
```bash
mkdir -p ~/.config/lxsession/LXDE-pi

cat >> ~/.config/lxsession/LXDE-pi/autostart << 'EOF'
@xset s off
@xset -dpms
@xset s noblank
@unclutter -idle 0.1 -root
EOF
```

#### 3. Using Systemd Service (Alternative)

For headless/kiosk setups, you can use the systemd service:

```bash
# Copy service file
sudo cp scripts/flight-display.service /etc/systemd/system/

# Edit to set your API key (optional)
sudo nano /etc/systemd/system/flight-display.service

# Enable and start
sudo systemctl daemon-reload
sudo systemctl enable flight-display
sudo systemctl start flight-display

# View logs
journalctl -u flight-display -f
```

### Reboot to Start

```bash
sudo reboot
```

The display will start automatically after boot.

## Display Layout

```
+------------------------------------------------------------------------+
|  FLIGHT DISPLAY  [DEMO MODE]                              [● Connected]|
+------------------------------------------------------------------------+
| CALLSIGN | AIRLINE | A/C  |      ROUTE      | ALT ft | SPD kt| HDG|DIST|
+------------------------------------------------------------------------+
| BAW123   |   BAW   | A320 |  LHR -> JFK     | 35,000 |  450  | 270|12.3|
| RYR456   |   RYR   | B738 |  STN -> DUB     | 28,000 |  380  | 310| 8.7|
| EZY789   |   EZY   | A319 |  LGW -> CDG     | 32,000 |  420  | 145|25.1|
| (scrollable via touch or mouse)                                        |
+------------------------------------------------------------------------+
| Updated: 14:32:05 | Flights: 24 | Connected                            |
+------------------------------------------------------------------------+
```

### Display Columns

| Column   | Description                              |
|----------|------------------------------------------|
| CALLSIGN | Flight callsign (e.g., BAW123)           |
| AIRLINE  | Airline ICAO code (e.g., BAW)            |
| A/C      | Aircraft type (e.g., A320, B738)         |
| ROUTE    | Origin -> Destination airports           |
| ALT ft   | Altitude in feet                         |
| SPD kt   | Ground speed in knots                    |
| HDG      | Heading in degrees (000-359)             |
| DIST     | Distance from your location in km        |

## Troubleshooting

### Application won't start

1. **Check logs:**
   ```bash
   cat /tmp/flight-display.log
   ```

2. **Verify your API key is correct:**
   ```bash
   curl -H "Authorization: Bearer YOUR_API_KEY" \
     "https://fr24api.flightradar24.com/api/live/flight-positions/light?bounds=52,50,-1,1&limit=5"
   ```

3. **Test in demo mode first:**
   ```bash
   poetry run flight-display --demo --windowed
   ```

### No flights showing

- Verify your coordinates are correct (use Google Maps to confirm)
- Increase `bounding_box_km` to widen the search area
- Check you're monitoring an area with air traffic
- Verify API key has remaining credits

### Screen goes blank

- Run `sudo raspi-config` and disable screen blanking under Display Options
- Or manually add xset commands to lxsession autostart (see above)

### Touch scrolling not working

- The flight list uses canvas-based scrolling
- Drag up/down on the flight list area to scroll
- On non-touch displays, use the scrollbar or mouse wheel

### API Rate Limiting

If you see "Rate limit exceeded" errors:
- Increase `refresh_interval` in config (minimum recommended: 10 seconds)
- Check your API subscription tier at [fr24api.flightradar24.com](https://fr24api.flightradar24.com/)

### Connection Errors

The application handles network issues gracefully:
- Red indicator shows when disconnected
- Last known flight data remains displayed
- Automatic reconnection when network returns
- Exponential backoff prevents API flooding

## Development

### Project Structure

```
flight-display/
├── pyproject.toml              # Poetry project configuration
├── config.example.yaml         # Example configuration file
├── README.md                   # This file
├── flight_display/             # Main application package
│   ├── __init__.py
│   ├── main.py                 # Entry point and CLI
│   ├── app.py                  # Main application class
│   ├── api_client.py           # FlightRadar24 API client
│   ├── config.py               # Configuration management
│   ├── models.py               # Data models (Flight)
│   ├── updater.py              # Background update thread
│   ├── utils.py                # Utility functions
│   ├── demo_data.py            # Demo mode data generator
│   └── ui/                     # UI components
│       ├── __init__.py
│       ├── main_window.py      # Main Tkinter window
│       ├── flight_table.py     # Scrollable flight list
│       ├── status_bar.py       # Status bar widget
│       └── theme.py            # Colors and fonts
└── scripts/                    # Setup scripts
    ├── install.sh              # Raspberry Pi installer
    └── flight-display.service  # Systemd service file
```

### Running in Development

```bash
# Install with dev dependencies
poetry install

# Run with verbose logging in windowed mode
poetry run flight-display --demo --windowed -v

# Run with live API
poetry run flight-display --windowed -v
```

### Key Technologies

- **Python 3.9+** - Main language
- **Tkinter** - GUI framework (included with Python)
- **Poetry** - Dependency management
- **requests** - HTTP client for API calls
- **PyYAML** - Configuration file parsing

## FlightRadar24 API

This application uses the [FlightRadar24 API](https://fr24api.flightradar24.com/) to fetch live flight data.

### Getting an API Key

1. Visit [fr24api.flightradar24.com](https://fr24api.flightradar24.com/)
2. Create an account
3. Subscribe to a tier (free tier available)
4. Copy your API key from the dashboard

### API Endpoints Used

- `GET /api/live/flight-positions/light` - Fetch live flights in a bounding box

### Rate Limits

Check your subscription tier for rate limits. The application respects these limits through configurable refresh intervals.

## License

MIT License - See LICENSE file for details.

## Credits

- Flight data provided by [FlightRadar24](https://www.flightradar24.com/)
- [FlightRadar24 API Documentation](https://fr24api.flightradar24.com/docs)

## Contributing

Contributions are welcome! Please feel free to submit issues and pull requests.
