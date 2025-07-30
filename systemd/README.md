# UWB Position Sender Systemd Service

This directory contains the systemd service configuration to automatically run the UWB position sender when the Raspberry Pi boots up.

## Files

- `uwb-position-sender.service` - The systemd service configuration file
- `install_service.sh` - Installation script to set up the service

## Installation

### Prerequisites

1. Clone the repository to your Raspberry Pi:
   ```bash
   cd /home/romer
   git clone <your-repo-url> UWB-positioning-main
   ```

2. Install Python dependencies:
   ```bash
   cd UWB-positioning-main
   pip install -r requirements.txt  # Uses pyenv Python
   ```

### Install the Service

1. Navigate to the systemd directory:
   ```bash
   cd systemd
   ```

2. Make the install script executable:
   ```bash
   chmod +x install_service.sh
   ```

3. Run the installation script as root:
   ```bash
   sudo ./install_service.sh
   ```

The script will:
- Copy the service file to `/etc/systemd/system/`
- Update the paths for your user (`romer`)
- Enable the service to start on boot
- Reload systemd to recognize the new service

## Service Management

### Start the service immediately:
```bash
sudo systemctl start uwb-position-sender.service
```

### Check service status:
```bash
sudo systemctl status uwb-position-sender.service
```

### View real-time logs:
```bash
sudo journalctl -u uwb-position-sender.service -f
```

### Stop the service:
```bash
sudo systemctl stop uwb-position-sender.service
```

### Disable auto-start (if needed):
```bash
sudo systemctl disable uwb-position-sender.service
```

## Service Configuration

The service is configured to:
- Start after network is available
- Restart automatically if it crashes
- Run as user `romer`
- Use pyenv Python environment (if available)
- Use the working directory `/home/romer/UWB-positioning-main/raspberrypi-files`
- Log output to systemd journal

## Troubleshooting

### Check if the service is running:
```bash
sudo systemctl is-active uwb-position-sender.service
```

### View recent logs:
```bash
sudo journalctl -u uwb-position-sender.service --since "1 hour ago"
```

### Check for errors:
```bash
sudo journalctl -u uwb-position-sender.service -p err
```

### Test the script manually:
```bash
cd /home/romer/UWB-positioning-main/raspberrypi-files
python position_sender.py  # Uses pyenv Python
```

## Notes

- The service will automatically restart if it crashes
- Logs are available through `journalctl`
- The service waits for network connectivity before starting
- Make sure your UWB device is connected via USB before the service starts 