#!/bin/bash

# UWB Position Sender Service Installer
# This script installs the systemd service for automatic startup

set -e  # Exit on any error

echo "=== UWB Position Sender Service Installer ==="
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "❌ Error: Please run this script as root (use sudo)"
    echo "   Usage: sudo ./install_service.sh [username]"
    exit 1
fi

# Get username from command line argument or detect current user
if [ -n "$1" ]; then
    USERNAME="$1"
    echo "Using specified username: $USERNAME"
else
    USERNAME=$(logname)
    if [ -z "$USERNAME" ]; then
        echo "❌ Error: Could not detect username automatically"
        echo "   Please specify the username: sudo ./install_service.sh [username]"
        echo "   Example: sudo ./install_service.sh romer"
        exit 1
    fi
    echo "Detected username: $USERNAME"
fi

# Validate username exists
if ! id "$USERNAME" &>/dev/null; then
    echo "❌ Error: User '$USERNAME' does not exist"
    exit 1
fi

USER_HOME=$(eval echo "~$USERNAME")
REPO_PATH="$USER_HOME/UWB-positioning-main"

echo "User home directory: $USER_HOME"
echo "Repository path: $REPO_PATH"
echo ""

# Check if repository exists
if [ ! -d "$REPO_PATH" ]; then
    echo "❌ Error: Repository not found at $REPO_PATH"
    echo "   Please clone the repository first:"
    echo "   cd $USER_HOME"
    echo "   git clone <repository-url> UWB-positioning-main"
    exit 1
fi

# Check if position_sender.py exists
if [ ! -f "$REPO_PATH/raspberrypi-files/position_sender.py" ]; then
    echo "❌ Error: position_sender.py not found at $REPO_PATH/raspberrypi-files/position_sender.py"
    echo "   Please ensure the repository is properly cloned"
    exit 1
fi

# Check Python environment
PYENV_PATH="$USER_HOME/.pyenv"
if [ -d "$PYENV_PATH" ]; then
    echo "✅ Found pyenv installation at $PYENV_PATH"
    PYTHON_PATH="$PYENV_PATH/shims/python"
    
    # Test if pyenv Python works
    if ! sudo -u "$USERNAME" "$PYTHON_PATH" --version &>/dev/null; then
        echo "⚠️  Warning: pyenv Python not working, will use system Python"
        PYTHON_PATH="/usr/bin/python3"
        USE_PYENV=false
    else
        echo "✅ pyenv Python is working"
        USE_PYENV=true
    fi
else
    echo "ℹ️  pyenv not found, will use system Python"
    PYTHON_PATH="/usr/bin/python3"
    USE_PYENV=false
fi

echo "Python path: $PYTHON_PATH"
echo ""

# Create service file with correct paths
SERVICE_FILE="/etc/systemd/system/uwb-position-sender@$USERNAME.service"

echo "Creating service file: $SERVICE_FILE"

# Copy and customize the service template
cp uwb-position-sender.service "$SERVICE_FILE"

# Update the service file for this specific user
sed -i "s/%i/$USERNAME/g" "$SERVICE_FILE"
sed -i "s/%h/$USER_HOME/g" "$SERVICE_FILE"

# Handle Python path
if [ "$USE_PYENV" = false ]; then
    # Use system Python
    sed -i "s|%h/.pyenv/shims/python|$PYTHON_PATH|g" "$SERVICE_FILE"
    # Remove pyenv-specific environment variables
    sed -i '/Environment=PYENV_ROOT/d' "$SERVICE_FILE"
    sed -i '/Environment=PATH.*pyenv/d' "$SERVICE_FILE"
fi

# Set correct permissions
chown root:root "$SERVICE_FILE"
chmod 644 "$SERVICE_FILE"

# Reload systemd to recognize the new service
echo "Reloading systemd..."
systemctl daemon-reload

# Enable the service to start on boot
echo "Enabling service..."
systemctl enable "uwb-position-sender@$USERNAME.service"

echo ""
echo "✅ Service installed successfully!"
echo ""
echo "Service name: uwb-position-sender@$USERNAME.service"
echo "Python path: $PYTHON_PATH"
echo ""
echo "=== Service Management Commands ==="
echo "Start the service:     sudo systemctl start uwb-position-sender@$USERNAME.service"
echo "Check status:          sudo systemctl status uwb-position-sender@$USERNAME.service"
echo "View logs:             sudo journalctl -u uwb-position-sender@$USERNAME.service -f"
echo "Stop the service:      sudo systemctl stop uwb-position-sender@$USERNAME.service"
echo "Disable auto-start:    sudo systemctl disable uwb-position-sender@$USERNAME.service"
echo ""
echo "=== Next Steps ==="
echo "1. Make sure your UWB device is connected via USB"
echo "2. Start the service: sudo systemctl start uwb-position-sender@$USERNAME.service"
echo "3. Check the logs to ensure it's working properly"
echo ""
echo "For troubleshooting, see: $REPO_PATH/systemd/README.md" 