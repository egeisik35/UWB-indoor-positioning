import serial
import json
import sys
import time
import numpy as np
import serial.tools.list_ports
import socket

# UDP setup
UDP_IP = "255.255.255.255"
UDP_PORT = 5005
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

# Room anchor positions (update as needed)
responder_positions = {
    "0x0001": [3000, 0, 1200],
    "0x0002": [0, 4000, 1050],
    "0x0003": [6850, 4400, 1200]
}

BAUD_RATE = 115200
INITIAL_DT = 0.1

def find_serial_port():
    ports = serial.tools.list_ports.comports()
    for port, desc, hwid in sorted(ports):
        if "ACM" in port or "USB" in port or "VCP" in port:
            print(f"Found suitable port: {port}")
            return port
    return None

def trilaterate_2d(p1, r1, p2, r2, p3, r3):
    # 2D trilateration (ignore z)
    P1 = np.array(p1[:2])
    P2 = np.array(p2[:2])
    P3 = np.array(p3[:2])
    ex = (P2 - P1) / np.linalg.norm(P2 - P1)
    i = np.dot(ex, P3 - P1)
    ey = P3 - P1 - i * ex
    ey = ey / np.linalg.norm(ey)
    d = np.linalg.norm(P2 - P1)
    j = np.dot(ey, P3 - P1)
    x = (r1**2 - r2**2 + d**2) / (2 * d)
    y = (r1**2 - r3**2 + i**2 + j**2 - 2 * i * x) / (2 * j)
    pos2d = P1 + x * ex + y * ey
    return pos2d

if __name__ == "__main__":
    PORT = find_serial_port()
    if PORT is None:
        print("Error: No suitable serial port found.")
        sys.exit(1)

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

                        # Use raw distance (no Kalman filter)
                        all_distances[addr] = dist

                    # Only send if all distances are available
                    if all(k in all_distances for k in responder_positions):
                        d1 = all_distances["0x0001"] * 10
                        d2 = all_distances["0x0002"] * 10
                        d3 = all_distances["0x0003"] * 10

                        est2d = trilaterate_2d(
                            responder_positions["0x0001"], d1,
                            responder_positions["0x0002"], d2,
                            responder_positions["0x0003"], d3
                        )

                        position = {"x": float(est2d[0]), "y": float(est2d[1])}
                        sock.sendto(json.dumps(position).encode(), (UDP_IP, UDP_PORT))
                        print("Sent position:", position)

                except Exception as e:
                    print("Error in loop:", e)
                    time.sleep(0.1)
    except KeyboardInterrupt:
        print("Stopped.")