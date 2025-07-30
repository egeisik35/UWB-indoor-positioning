# UWB Position Sender Systemd Service

This directory contains the systemd service configuration to automatically run the UWB position sender when the Raspberry Pi boots up.

## Files

- `uwb-position-sender.service` - The systemd service configuration file
- `install_service.sh` - Installation script to set up the service

## Quick Setup (Exact Commands)

Here are the commands you'll run after cloning the repo to your Raspberry Pi:

### **Step 1: Clone and Navigate**
```bash
cd ~
git clone <your-repo-url> UWB-indoor-positioning
cd UWB-indoor-positioning
```

### **Step 2: Install Dependencies**
```bash
pip install -r requirements.txt
```

### **Step 3: Install Systemd Service**
```bash
cd systemd
chmod +x install_service.sh
sudo ./install_service.sh $USER
```

### **Step 4: Test the Service**
```bash
sudo systemctl start uwb-position-sender@$USER.service
sudo systemctl status uwb-position-sender@$USER.service
```

### **Step 5: Check Logs (Optional)**
```bash
sudo journalctl -u uwb-position-sender@$USER.service -f
```

## Installation

### Prerequisites

1. Clone the repository to your Raspberry Pi:
   ```bash
   cd ~
   git clone <your-repo-url> UWB-indoor-positioning
   ```

2. Install Python dependencies:
   ```bash
   cd UWB-indoor-positioning
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
   sudo ./install_service.sh $USER
   ```

The script will:
- Copy the service file to `/etc/systemd/system/`
- Update the paths for your user
- Enable the service to start on boot
- Reload systemd to recognize the new service

## Service Management

### Start the service immediately:
```bash
sudo systemctl start uwb-position-sender@$USER.service
```

### Check service status:
```bash
sudo systemctl status uwb-position-sender@$USER.service
```

### View real-time logs:
```bash
sudo journalctl -u uwb-position-sender@$USER.service -f
```

### Stop the service:
```bash
sudo systemctl stop uwb-position-sender@$USER.service
```

### Disable auto-start (if needed):
```bash
sudo systemctl disable uwb-position-sender@$USER.service
```

## Service Configuration

The service is configured to:
- Start after network is available
- Restart automatically if it crashes
- Run as the current user
- Use pyenv Python environment (if available)
- Use the working directory `~/UWB-indoor-positioning/raspberrypi-files`
- Log output to systemd journal

## Troubleshooting

### Check if the service is running:
```bash
sudo systemctl is-active uwb-position-sender@$USER.service
```

### View recent logs:
```bash
sudo journalctl -u uwb-position-sender@$USER.service --since "1 hour ago"
```

### Check for errors:
```bash
sudo journalctl -u uwb-position-sender@$USER.service -p err
```

### Test the script manually:
```bash
cd ~/UWB-indoor-positioning/raspberrypi-files
python position_sender.py  # Uses pyenv Python
```

## Common Issues

### **UDP Port Already in Use**
If you get `OSError: [Errno 98] Address already in use` when running visualizers:

**Find and kill the process:**
```bash
# Find what's using port 5005
sudo netstat -tulpn | grep 5005
sudo lsof -i :5005

# Kill the process
sudo fuser -k 5005/udp
```

**Or use a different port:**
Edit both `raspberrypi-files/position_sender.py` and visualizer files:
```python
UDP_PORT = 5006  # Change from 5005 to 5006
```

### **Service Won't Start**
```bash
# Check detailed logs
sudo journalctl -u uwb-position-sender@$USER.service -n 50

# Test manually first
cd ~/UWB-indoor-positioning/raspberrypi-files
python position_sender.py
```

## Notes

- The service will automatically restart if it crashes
- Logs are available through `journalctl`
- The service waits for network connectivity before starting
- Make sure your UWB device is connected via USB before the service starts
- Replace `$USER` with your actual username if needed 