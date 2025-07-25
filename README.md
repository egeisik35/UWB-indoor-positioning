# DWM3001C UWB Indoor Positioning Tracker

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A real-time indoor positioning system using **Qorvo DWM3001C Ultra-Wideband (UWB)** modules. This project provides a robust solution for tracking moving objects in GNSS-denied environments like rooms, basements, or tunnels where GPS is unavailable.

The system uses one module as a mobile **initiator** (the "tag" to be tracked) and multiple modules as fixed **responders** (the "anchors"). By measuring the distances between the tag and anchors, we can estimate the tag's position in real-time. The data is then processed using Python for filtering, tracking, and visualization.


---

## Key Features

-   **High-Precision Tracking:** Leverages UWB technology for accurate distance measurements.
-   **GNSS-Denied Navigation:** Designed specifically for indoor environments.
-   **Simple Hardware Setup:** Uses off-the-shelf DWM3001CDK development kits.
-   **Dockerized Build:** Simplifies the firmware build process with a pre-configured Docker image.
-   **Python Data Analysis:** Includes Python scripts for serial data collection, filtering (Moving Average, Kalman Filter), and analysis.
-   **Extensible & Open Source:** A great starting point for robotics projects, asset tracking, or interactive installations.

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

All Python scripts for data handling are located in the `uwb-python-analysis/` directory.

### 1. Install Dependencies

The scripts rely on a few Python libraries. Install them using `pip`:

```bash
pip install -r uwb-python-analysis/requirements.txt
```

### 2. Run the System

1.  **Set Up Anchors:** Place your configured responders (anchors) at known, fixed locations. A sample layout is provided in `uwb_room.pdf`.
2.  **Connect Initiator:** Connect the initiator (tag) to your computer or Raspberry Pi via USB.
3.  **Run a Script:** Execute one of the Python scripts. It will automatically connect to the serial port, read the JSON-formatted distance data from the initiator, and begin processing.

The scripts can be easily modified to change filtering techniques, log data, or add real-time visualization.

---

### 3. Live 3D Visualization

To visualize the responder’s position in real time, first run the kalman_reader.py and then:

```bash
python uwb-python-analysis/plot_3D_live.py
```

This script reads the filtered distance data (`latest_distance.txt`) and updates a 3D room model every second. It assumes one anchor at (0, 0, 0) and draws a red sphere indicating possible responder locations.

If you're using SSH, enable X11 forwarding (`ssh -X`) or modify the script to save snapshots instead of opening a window.

---

## Project Status & Roadmap

This project is actively in development. The current focus is on building a complete, room-scale indoor localization system for real-world robotics applications.

Our roadmap includes:

-   [ ] Integrate total of 3 UWB responders and 1 initiator for improved coverage and accuracy.
-   [ ] Implement real-time 3D trilateration algorithms.
-   [ ] Fuse UWB data with an IMU for drift correction during fast movements.
-   [ ] Visualize the tracked path in real-time (e.g., with Matplotlib, OpenCV, or ROS).
-   [ ] Validate system accuracy with a physical robot performing a pre-defined course.

---

## License

This project is licensed under the **MIT License**. See the `LICENSE` file for more details.
