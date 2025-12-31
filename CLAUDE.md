# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Flight Display is a Raspberry Pi application that displays live flight data from FlightRadar24 on a 7" touchscreen (800x480). Built with Python 3.9+ and Tkinter, it supports both live API data and a demo mode with simulated flights.

## Commands

```bash
# Install dependencies
poetry install

# Run in demo mode (no API key required)
poetry run flight-display --demo --windowed

# Run with live API data
poetry run flight-display --windowed

# Run with verbose logging
poetry run flight-display --demo --windowed -v

# Run fullscreen (production mode)
poetry run flight-display
```

## Architecture

### Core Components

- **`app.py`**: `FlightDisplayApp` - Main orchestrator that wires together API client, updater, and UI
- **`api_client.py`**: `FR24Client` - FlightRadar24 API client
- **`demo_data.py`**: `DemoClient` - Generates fake flight data for testing
- **`updater.py`**: `DataUpdater` - Background thread that fetches flight data and queues updates for the main thread
- **`flight_cache.py`**: Caches flight data between updates
- **`config.py`**: YAML configuration loading from `~/.config/flight-display/config.yaml`
- **`models.py`**: `Flight` dataclass representing flight data

### UI Layer (`ui/`)

- **`main_window.py`**: `MainWindow` - Root Tkinter window with fullscreen/windowed modes
- **`flight_table.py`**: Touch-scrollable canvas-based flight list
- **`status_bar.py`**: Connection status and update time display
- **`theme.py`**: Dark theme colors and fonts

### Data Flow

1. `DataUpdater` runs in background thread, calls API client at configured interval
2. Flight data queued and processed on main thread via `process_queue()`
3. `FlightDisplayApp` sorts/filters flights and updates UI
4. `MainWindow` renders data through `FlightTable` and `StatusBar`

## Configuration

Config file: `~/.config/flight-display/config.yaml`
Example: `config.example.yaml`
API key can also be set via `FR24_API_KEY` environment variable.

## Key Dependencies

- **requests**: HTTP client for FR24 API
- **pyyaml**: Config file parsing
- **tkinter**: GUI (included with Python, needs `python3-tk` on Raspberry Pi)
