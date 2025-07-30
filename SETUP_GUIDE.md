# UWB Positioning System - Complete Setup Guide

This guide will help you set up the UWB positioning system from scratch on a Raspberry Pi.

## Prerequisites

- Raspberry Pi (3 or 4 recommended)
- UWB DWM3001C modules (1 initiator + 3 responders)
- USB cables
- WiFi network access

## Step 1: Initial Raspberry Pi Setup

### 1.1 Install Raspberry Pi OS
1. Download Raspberry Pi Imager from [raspberrypi.org](https://www.raspberrypi.org/software/)
2. Flash Raspberry Pi OS (Bullseye or newer) to your SD card
3. Enable SSH and WiFi during setup

### 1.2 First Boot and Updates
```bash
# Connect to your Raspberry Pi via SSH
ssh pi@your-raspberry-pi-ip

# Update system
sudo apt update && sudo apt upgrade -y

# Install essential packages
sudo apt install -y git python3-pip python3-venv
```

## Step 2: Python Environment Setup

### 2.1 Install pyenv (Recommended)
```bash
# Install pyenv dependencies
sudo apt install -y make build-essential libssl-dev zlib1g-dev \
libbz2-dev libreadline-dev libsqlite3-dev wget curl llvm \
libncursesw5-dev xz-utils tk-dev libxml2-dev libxmlsec1-dev libffi-dev liblzma-dev

# Install pyenv
curl https://pyenv.run | bash

# Add pyenv to shell
echo 'export PYENV_ROOT="$HOME/.pyenv"' >> ~/.bashrc
echo 'command -v pyenv >/dev/null || export PATH="$PYENV_ROOT/bin:$PATH"' >> ~/.bashrc
echo 'eval "$(pyenv init -)"' >> ~/.bashrc

# Reload shell
source ~/.bashrc

# Install Python 3.11 (or your preferred version)
pyenv install 3.11.0
pyenv global 3.11.0
```

### 2.2 Alternative: Use System Python
If you prefer not to use pyenv, the system Python will work fine:
```bash
# Verify Python installation
python3 --version
```

## Step 3: Clone and Setup Repository

### 3.1 Clone the Repository
```bash
# Navigate to home directory
cd ~

# Clone the repository
git clone https://github.com/your-username/UWB-positioning-main.git
cd UWB-positioning-main
```

### 3.2 Install Python Dependencies
```bash
# Install dependencies
pip install -r requirements.txt

# Or if using system Python:
pip3 install -r requirements.txt
```

## Step 4: Configure Room Settings

### 4.1 Update Room Dimensions
Edit `uwb-python-analysis/udp_visualizer.py`:
```python
# Room dimensions in mm (x, y, z) - update for your room
ROOM_DIMENSIONS = {
    "width_x": 7850,    # mm (x-axis) - update this
    "depth_y": 7300,    # mm (y-axis) - update this
    "height_z": 3000    # mm (z-axis) - update this
}

# Anchor positions in mm (x, y, z) - update for your setup
responder_positions_3d = {
    "0x0001": [3000, 0, 1200],      # mm (x, y, z) - update this
    "0x0002": [0, 4000, 1050],      # mm (x, y, z) - update this
    "0x0003": [6850, 4400, 1200]    # mm (x, y, z) - update this
}
```

### 4.2 Update Height Decision Parameters (Optional)
Edit `raspberrypi-files/position_sender.py`:
```python
HEIGHT_DECISION = {
    "min_height_z": 500,      # mm - minimum reasonable height
    "max_height_z": 2500,     # mm - maximum reasonable height
    "default_height_z": 1200,  # mm - default height
}
```

## Step 5: UWB Hardware Setup

### 5.1 Flash UWB Firmware
Follow the firmware setup instructions in the main README to configure your UWB modules.

### 5.2 Physical Setup
1. **Place anchors** at the configured positions in your room
2. **Connect initiator** to Raspberry Pi via USB
3. **Power all devices**

## Step 6: Install Systemd Service

### 6.1 Install the Service
```bash
# Navigate to systemd directory
cd systemd

# Make install script executable
chmod +x install_service.sh

# Install the service (replace 'pi' with your username)
sudo ./install_service.sh pi
```

### 6.2 Verify Installation
```bash
# Check service status
sudo systemctl status uwb-position-sender@pi.service

# View logs
sudo journalctl -u uwb-position-sender@pi.service -f
```

## Step 7: Test the System

### 7.1 Start the Service
```bash
# Start the service
sudo systemctl start uwb-position-sender@pi.service

# Check if it's running
sudo systemctl is-active uwb-position-sender@pi.service
```

### 7.2 Run Visualizer on Computer
On your computer (same WiFi network):
```bash
# Clone repository
git clone https://github.com/your-username/UWB-positioning-main.git
cd UWB-positioning-main

# Install dependencies
pip install -r requirements.txt

# Run visualizer
python uwb-python-analysis/udp_visualizer.py
```

## Troubleshooting

### Common Issues

#### 1. Service Won't Start
```bash
# Check logs for errors
sudo journalctl -u uwb-position-sender@pi.service -n 50

# Test script manually
cd ~/UWB-positioning-main/raspberrypi-files
python position_sender.py
```

#### 2. No UWB Device Found
```bash
# Check USB devices
lsusb

# Check serial ports
ls /dev/tty*

# Check permissions
sudo usermod -a -G dialout pi
```

#### 3. Network Issues
```bash
# Check if devices are on same network
ip addr show

# Test UDP connectivity
nc -u -l 5005  # On computer
nc -u computer-ip 5005  # On Raspberry Pi
```

#### 4. Python Environment Issues
```bash
# Check Python path
which python

# Check pyenv installation
pyenv versions

# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

### Service Management

```bash
# Start service
sudo systemctl start uwb-position-sender@pi.service

# Stop service
sudo systemctl stop uwb-position-sender@pi.service

# Enable auto-start
sudo systemctl enable uwb-position-sender@pi.service

# Disable auto-start
sudo systemctl disable uwb-position-sender@pi.service

# View real-time logs
sudo journalctl -u uwb-position-sender@pi.service -f

# Restart service
sudo systemctl restart uwb-position-sender@pi.service
```

## Next Steps

1. **Calibrate anchor positions** for better accuracy
2. **Adjust room dimensions** to match your space
3. **Fine-tune height decision algorithm** for your use case
4. **Add multiple tags** if needed
5. **Integrate with other systems** (ROS, etc.)

## Support

- Check the main README for detailed documentation
- Review the systemd README for service-specific help
- Open an issue on GitHub for bugs or feature requests 