# DWM3001C UWB Indoor Positioning Tracker

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A **real-time 3D indoor positioning system** using **Qorvo DWM3001C Ultra-Wideband (UWB)** modules. This project provides a robust solution for tracking moving objects in GNSS-denied environments like rooms, basements, or tunnels where GPS is unavailable.

The system uses one module as a mobile **initiator** (the "tag" to be tracked) and multiple modules as fixed **responders** (the "anchors"). By measuring the distances between the tag and anchors, we can estimate the tag's **3D position (x, y, z)** in real-time. The data is processed using Python for filtering, tracking, and **3D visualization**.

---

## Key Features

-   **High-Precision 3D Tracking:** Leverages UWB technology for accurate distance measurements in 3D space.
-   **GNSS-Denied Navigation:** Designed specifically for indoor environments.
-   **Simple Hardware Setup:** Uses off-the-shelf DWM3001CDK development kits.
-   **Dockerized Build:** Simplifies the firmware build process with a pre-configured Docker image.
-   **Python Data Analysis:** Includes Python scripts for serial data collection, filtering (Kalman Filter), and **3D visualization**.
-   **Raw Data Transmission:** Raspberry Pi sends raw distance data, analysis performed on computer.
-   **Height Decision Algorithm:** Intelligent height estimation based on room dimensions and distance patterns.
-   **Extensible & Open Source:** A great starting point for robotics projects, asset tracking, or interactive installations.

---

## System Architecture

### Current Process Flow:

1. **Raspberry Pi** (`raspberrypi-files/position_sender.py`)
   - Reads UWB data from serial port
   - Sends **raw distance data** via UDP broadcast
   - Includes **height decision algorithm** for 3D positioning
   - No heavy computation on Pi

2. **Computer** (`uwb-python-analysis/udp_visualizer.py`)
   - Receives raw distance data via UDP
   - Performs **Kalman filtering** on distances
   - Performs **3D trilateration** for position calculation
   - Shows **real-time 3D visualization**

### Data Format:
```json
{
  "distances": {
    "0x0001": 1234,  // mm
    "0x0002": 2345,  // mm
    "0x0003": 3456   // mm
  },
  "height_z_mm": 1200,  // mm
  "timestamp": 1234567890.123
}
```

---

## Firmware Setup

Firmware setup is being done using the [DWM3001CDK-demo-firmware](https://github.com/Uberi/DWM3001CDK-demo-firmware) from Uberi. The recommended setup uses Docker to ensure a consistent and easy build environment.

### 1. Build the Firmware

First, clone the firmware repository.

```bash
# Clone the official demo firmware
git clone [https://github.com/Uberi/DWM3001CDK-demo-firmware](https://github.com/Uberi/DWM3001CDK-demo-firmware)
cd DWM3001CDK-demo-firmware
```

Next, build and flash the firmware onto each of your DWM3001C modules.

```bash
# Build the firmware
make build

# Flash the firmware to a connected module
make flash
```

### 2. Configure the Devices

After flashing, connect to each module's **upper USB port (J20)** using a serial terminal. You can use the provided `make` command or your preferred tool like `screen`.

```bash
# Connect with a baud rate of 115200
screen /dev/ttyACM0 115200

# Or, use the makefile shortcut
make serial-terminal
```

Once connected, run the appropriate command to configure each device's role.

#### **Initiator (Tag) Configuration**

This device will be the moving target.

```bash
# Command: initf [channel] [data_rate] [preamble_len] [preamble_code] [sfd_mode] [pan_id] [device_id] [slot_period] [ranging_period] [tx_power] [num_responders]
initf 4 2400 200 25 2 42 01:02:03:04:05:06:07:08 1 0 0 1 2
SAVE
```

#### **Responder (Anchor) Configuration**

These devices are your fixed reference points. Configure each one with a unique final parameter (e.g., `1`, `2`, `3`...).

```bash
# Command: respf [channel] [data_rate] [preamble_len] [preamble_code] [sfd_mode] [pan_id] [device_id] [slot_period] [ranging_period] [tx_power] [responder_slot]
respf 4 2400 200 25 2 42 01:02:03:04:05:06:07:08 1 0 0 1
SAVE

respf 4 2400 200 25 2 42 01:02:03:04:05:06:07:08 1 0 0 2
SAVE
```

A successful command will return `ok`.

---

## Python Data Processing & Usage

### 1. Install Dependencies

Install all required Python libraries:

```bash
pip install -r requirements.txt
```

### 2. Room Configuration

Update the room dimensions and anchor positions in both files:

**Raspberry Pi** (`raspberrypi-files/position_sender.py`):
```python
# No room configuration needed - only height decision parameters
HEIGHT_DECISION = {
    "min_height_z": 500,      # mm
    "max_height_z": 2500,     # mm
    "default_height_z": 1200   # mm
}
```

**Computer** (`uwb-python-analysis/udp_visualizer.py`):
```python
responder_positions_3d = {
    "0x0001": [3000, 0, 1200],      # mm (x, y, z)
    "0x0002": [0, 4000, 1050],      # mm (x, y, z)
    "0x0003": [6850, 4400, 1200]    # mm (x, y, z)
}
```

### 3. Run the System

1. **Set Up Anchors:** Place your configured responders (anchors) at known, fixed locations. A sample layout is provided in `uwb_room.pdf`.
2. **Connect Initiator:** Connect the initiator (tag) to your Raspberry Pi via USB.
3. **Start Raspberry Pi:** Run the position sender on your Raspberry Pi:
   ```bash
   python raspberrypi-files/position_sender.py
   ```
4. **Start Visualization:** Run the 3D visualizer on your computer:
   ```bash
   python uwb-python-analysis/udp_visualizer.py
   ```

Both devices must be on the same WiFi network for UDP communication.

---

## Automatic Startup (Raspberry Pi)

To automatically start the position sender when the Raspberry Pi boots up:

1. **Clone the repository** to your Raspberry Pi:
   ```bash
   cd /home/romer
   git clone <your-repo-url> UWB-positioning-main
   ```

2. **Install dependencies**:
   ```bash
   cd UWB-positioning-main
   pip3 install -r requirements.txt
   ```

3. **Install the systemd service**:
   ```bash
   cd systemd
   chmod +x install_service.sh
   sudo ./install_service.sh
   ```

The service will now automatically start when the Raspberry Pi boots up. See `systemd/README.md` for detailed service management instructions.

## 🚀 New User Setup

**For complete setup from scratch**, see the comprehensive [SETUP_GUIDE.md](SETUP_GUIDE.md) which includes:
- Initial Raspberry Pi setup
- Python environment configuration (pyenv or system)
- Repository cloning and dependency installation
- Room configuration
- UWB hardware setup
- Systemd service installation
- Testing and troubleshooting

---

## Height Decision Algorithm

The system includes an intelligent height decision algorithm that estimates the z-coordinate based on:

- **Room dimensions** (width_x, depth_y, height_z in mm)
- **Distance patterns** to anchors
- **Physical constraints** (min/max reasonable heights)
- **Historical patterns** (if available)

The algorithm uses distance ratios to estimate if the tag is likely higher or lower in the room, providing more accurate 3D positioning.

---

## Project Status & Roadmap

This project is actively in development. The current focus is on building a complete, room-scale **3D indoor localization system** for real-world robotics applications.

### Completed:
- ✅ **3D positioning system** with height decision algorithm
- ✅ **Raw data transmission** from Raspberry Pi to computer
- ✅ **Real-time 3D visualization** with matplotlib
- ✅ **Kalman filtering** for smooth position estimates
- ✅ **UDP broadcasting** to multiple receivers

### Roadmap:
-   [ ] **Improve height decision algorithm** - Add machine learning for better height estimation
-   [ ] **Add IMU fusion** - Fuse UWB data with IMU for drift correction during fast movements
-   [ ] **Path tracking** - Visualize the tracked path in real-time
-   [ ] **Multiple tag support** - Track multiple tags simultaneously
-   [ ] **Accuracy validation** - Validate system accuracy with physical robot performing pre-defined course
-   [ ] **Web interface** - Add web-based visualization for remote monitoring

---

## License

This project is licensed under the **MIT License**. See the `LICENSE` file for more details.
