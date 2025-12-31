#!/bin/bash
#
# Flight Display Installation Script for Raspberry Pi
#
# This script installs dependencies, sets up autostart, and configures
# the display settings for the Flight Display application.
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
INSTALL_DIR="/home/pi/flight-display"
USER="${SUDO_USER:-pi}"

echo "=== Flight Display Installer ==="
echo ""

# Check if running on Raspberry Pi
if [[ ! -f /proc/device-tree/model ]] || ! grep -q "Raspberry Pi" /proc/device-tree/model 2>/dev/null; then
    echo "Warning: This script is designed for Raspberry Pi."
    echo "Continuing anyway..."
fi

# Check for root privileges for system-wide setup
if [[ $EUID -ne 0 ]]; then
    echo "Note: Running without sudo. Some setup steps may be skipped."
    SUDO_AVAILABLE=false
else
    SUDO_AVAILABLE=true
fi

echo "1. Installing system dependencies..."
if $SUDO_AVAILABLE; then
    apt-get update
    apt-get install -y python3-tk python3-pip unclutter
else
    echo "   Skipped (requires sudo). Run: sudo apt install python3-tk python3-pip unclutter"
fi

echo ""
echo "2. Installing Python dependencies with Poetry..."
if command -v poetry &> /dev/null; then
    cd "$PROJECT_DIR"
    poetry install
else
    echo "   Poetry not found. Installing Poetry first..."
    curl -sSL https://install.python-poetry.org | python3 -
    export PATH="$HOME/.local/bin:$PATH"
    cd "$PROJECT_DIR"
    poetry install
fi

echo ""
echo "3. Setting up configuration..."
CONFIG_DIR="/home/$USER/.config/flight-display"
mkdir -p "$CONFIG_DIR"

if [[ ! -f "$CONFIG_DIR/config.yaml" ]]; then
    cp "$PROJECT_DIR/config.example.yaml" "$CONFIG_DIR/config.yaml"
    echo "   Created config file at $CONFIG_DIR/config.yaml"
    echo "   IMPORTANT: Edit this file to add your API key and location!"
else
    echo "   Config file already exists at $CONFIG_DIR/config.yaml"
fi

echo ""
echo "4. Setting up desktop autostart..."
AUTOSTART_DIR="/home/$USER/.config/autostart"
mkdir -p "$AUTOSTART_DIR"

cat > "$AUTOSTART_DIR/flight-display.desktop" << EOF
[Desktop Entry]
Type=Application
Name=Flight Display
Comment=FlightRadar24 Display Application
Exec=/usr/bin/bash -c 'cd $PROJECT_DIR && poetry run flight-display'
Terminal=false
Hidden=false
X-GNOME-Autostart-enabled=true
StartupNotify=false
EOF

echo "   Created autostart entry"

echo ""
echo "5. Setting up screen blanking prevention..."
LXSESSION_DIR="/home/$USER/.config/lxsession/LXDE-pi"
if [[ -d "$LXSESSION_DIR" ]]; then
    # Check if entries already exist
    if ! grep -q "xset s off" "$LXSESSION_DIR/autostart" 2>/dev/null; then
        cat >> "$LXSESSION_DIR/autostart" << EOF

# Flight Display - prevent screen blanking
@xset s off
@xset -dpms
@xset s noblank
@unclutter -idle 0.1 -root
EOF
        echo "   Added screen blanking prevention to lxsession autostart"
    else
        echo "   Screen blanking prevention already configured"
    fi
else
    echo "   LXDE session directory not found. You may need to disable screen blanking manually:"
    echo "   Run: sudo raspi-config -> Display Options -> Screen Blanking -> No"
fi

echo ""
echo "6. Setting file permissions..."
chown -R "$USER:$USER" "/home/$USER/.config/flight-display" 2>/dev/null || true
chown -R "$USER:$USER" "$AUTOSTART_DIR/flight-display.desktop" 2>/dev/null || true

echo ""
echo "=== Installation Complete ==="
echo ""
echo "Next steps:"
echo "1. Edit your config file:"
echo "   nano $CONFIG_DIR/config.yaml"
echo ""
echo "2. Add your FlightRadar24 API key and set your location"
echo ""
echo "3. Test the application:"
echo "   cd $PROJECT_DIR && poetry run flight-display --windowed"
echo ""
echo "4. Reboot to start the display automatically:"
echo "   sudo reboot"
echo ""
