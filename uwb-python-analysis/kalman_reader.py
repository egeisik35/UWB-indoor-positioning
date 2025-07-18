import serial
import json
import sys
import time
from collections import deque
import numpy as np
import serial.tools.list_ports
from filterpy.kalman import KalmanFilter

# -- Configuration --
# UWB Settings
BAUD_RATE = 115200

# Kalman Filter Settings
# Time step (how often we get new data). Assume ~10Hz, but we'll calculate it dynamically.
INITIAL_DT = 0.1
# Measurement uncertainty (how much we trust the UWB reading). Higher means less trust.
MEASUREMENT_NOISE = 10
# Process uncertainty (how much we trust our prediction model). Higher means the model
# expects the object's velocity to change more erratically.
PROCESS_NOISE = 0.1

# -- Helper Functions --
def find_serial_port():
    """Dynamically find the correct serial port."""
    ports = serial.tools.list_ports.comports()
    for port, desc, hwid in sorted(ports):
        if "ACM" in port or "USB" in port or "VCP" in port:
            print(f"Found suitable port: {port}")
            return port
    return None

def create_kalman_filter():
    """Create a 1D Kalman filter for tracking distance and velocity."""
    kf = KalmanFilter(dim_x=2, dim_z=1)
    # State vector: [distance, velocity]
    kf.x = np.zeros((2, 1))
    # State Transition Matrix: predicts the next state based on current state
    # [1, dt]
    # [0,  1]
    kf.F = np.array([[1., INITIAL_DT],
                     [0., 1.]])
    # Measurement Function: maps the state to the measurement
    # [1, 0]
    kf.H = np.array([[1., 0.]])
    # Measurement Noise Covariance
    kf.R = np.array([[MEASUREMENT_NOISE]])
    # Process Noise Covariance
    # We use Q_discrete_white_noise to generate the covariance matrix
    # from our single process noise value and time step.
    from filterpy.common import Q_discrete_white_noise
    kf.Q = Q_discrete_white_noise(dim=2, dt=INITIAL_DT, var=PROCESS_NOISE)
    return kf

# -- Main Application --
if __name__ == "__main__":
    PORT = find_serial_port()
    if PORT is None:
        print("Error: No suitable serial port found. Exiting.")
        sys.exit(1)

    # Dictionary to hold a separate Kalman filter for each responder address
    kalman_filters = {}
    last_time = {}

    try:
        with serial.Serial(PORT, BAUD_RATE, timeout=1) as ser:
            print(f"Successfully connected to {PORT} at {BAUD_RATE} baud.")
            print("Starting UWB data acquisition... Press Ctrl+C to stop.")

            while True:
                try:
                    line = ser.readline().decode("utf-8").strip()
                    if not line.startswith("{"):
                        continue

                    data = json.loads(line)
                    results = data.get("results", [])
                    display_lines = []

                    for result in results:
                        addr = result.get("Addr")
                        status = result.get("Status")
                        dist = result.get("D_cm")

                        if not addr or status != "Ok" or dist is None:
                            continue

                        current_time = time.time()
                        
                        # Initialize a new filter if we see a new address
                        if addr not in kalman_filters:
                            print(f"\nNew responder detected: {addr}. Initializing filter.")
                            kalman_filters[addr] = create_kalman_filter()
                            # Initialize the filter's state with the first measurement
                            kalman_filters[addr].x[0] = dist
                            last_time[addr] = current_time
                            continue

                        # Calculate dynamic time step (dt)
                        dt = current_time - last_time[addr]
                        if dt == 0: continue # Avoid division by zero
                        last_time[addr] = current_time

                        # Update the filter's state transition matrix and noise with the new dt
                        kf = kalman_filters[addr]
                        kf.F[0, 1] = dt
                        from filterpy.common import Q_discrete_white_noise
                        kf.Q = Q_discrete_white_noise(dim=2, dt=dt, var=PROCESS_NOISE)

                        # --- Kalman Filter Steps ---
                        # 1. Predict the next state
                        kf.predict()
                        # 2. Update the state with the new measurement
                        kf.update(np.array([[dist]]))

                        filtered_dist = kf.x[0, 0]
                        velocity = kf.x[1, 0] # in cm/s
                        
                        display_lines.append(f"[{addr}] Dist: {filtered_dist:.1f} cm (V: {velocity:.1f} cm/s)")

                    if display_lines:
                        sys.stdout.write("\r" + " | ".join(display_lines) + " " * 10)
                        sys.stdout.flush()

                except (json.JSONDecodeError, UnicodeDecodeError):
                    # Silently ignore lines that are not valid JSON
                    continue
                except Exception as e:
                    print(f"\nAn unexpected error occurred: {e}")


    except serial.SerialException as e:
        print(f"\nSerial Error: {e}. Please check the connection.")
    except KeyboardInterrupt:
        print("\n\nProgram stopped by user.")
    finally:
        sys.exit(0)
