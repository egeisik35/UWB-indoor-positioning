
import serial
import json
import sys
import time
import numpy as np
import serial.tools.list_ports
from filterpy.kalman import KalmanFilter
from filterpy.common import Q_discrete_white_noise

BAUD_RATE = 115200
INITIAL_DT = 0.1
MEASUREMENT_NOISE = 10
PROCESS_NOISE = 0.1

def find_serial_port():
    ports = serial.tools.list_ports.comports()
    for port, desc, hwid in sorted(ports):
        if "ACM" in port or "USB" in port or "VCP" in port:
            print(f"Found suitable port: {port}")
            return port
    return None

def create_kalman_filter():
    kf = KalmanFilter(dim_x=2, dim_z=1)
    kf.x = np.zeros((2, 1))
    kf.F = np.array([[1., INITIAL_DT], [0., 1.]])
    kf.H = np.array([[1., 0.]])
    kf.R = np.array([[MEASUREMENT_NOISE]])
    kf.Q = Q_discrete_white_noise(dim=2, dt=INITIAL_DT, var=PROCESS_NOISE)
    return kf

if __name__ == "__main__":
    PORT = find_serial_port()
    if PORT is None:
        print("Error: No suitable serial port found.")
        sys.exit(1)

    kalman_filters = {}
    last_time = {}

    try:
        with serial.Serial(PORT, BAUD_RATE, timeout=1) as ser:
            print(f"Connected to {PORT}")
            while True:
                try:
                    line = ser.readline().decode("utf-8").strip()
                    if not line.startswith("{"):
                        continue

                    data = json.loads(line)
                    results = data.get("results", [])
                    all_distances = {}

                    for result in results:
                        addr = result.get("Addr")
                        status = result.get("Status")
                        dist = result.get("D_cm")

                        if not addr or status != "Ok" or dist is None:
                            continue

                        now = time.time()
                        if addr not in kalman_filters:
                            kalman_filters[addr] = create_kalman_filter()
                            kalman_filters[addr].x[0] = dist
                            last_time[addr] = now
                            continue

                        dt = now - last_time[addr]
                        if dt <= 0: continue
                        last_time[addr] = now

                        kf = kalman_filters[addr]
                        kf.F[0, 1] = dt
                        kf.Q = Q_discrete_white_noise(dim=2, dt=dt, var=PROCESS_NOISE)

                        kf.predict()
                        kf.update(np.array([[dist]]))

                        filtered_dist = kf.x[0, 0]
                        all_distances[addr] = filtered_dist

                    if all_distances:
                        with open("latest_distances.json", "w") as f:
                            json.dump(all_distances, f)

                        sys.stdout.write("\r" + " | ".join(
                            [f"[{addr}] {d:.1f} cm" for addr, d in all_distances.items()]
                        ) + " " * 10)
                        sys.stdout.flush()

                except (json.JSONDecodeError, UnicodeDecodeError):
                    continue
                except Exception as e:
                    print(f"\nError: {e}")

    except serial.SerialException as e:
        print(f"Serial Error: {e}")
    except KeyboardInterrupt:
        print("\nStopped.")
    finally:
        sys.exit(0)
