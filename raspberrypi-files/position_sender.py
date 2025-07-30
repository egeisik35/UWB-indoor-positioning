import serial
import json
import sys
import time
import serial.tools.list_ports
import socket

# UDP setup
UDP_IP = "255.255.255.255"
UDP_PORT = 5005
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

BAUD_RATE = 115200

def find_serial_port():
    ports = serial.tools.list_ports.comports()
    for port, desc, hwid in sorted(ports):
        if "ACM" in port or "USB" in port or "VCP" in port:
            print(f"Found suitable port: {port}")
            return port
    return None

if __name__ == "__main__":
    PORT = find_serial_port()
    if PORT is None:
        print("Error: No suitable serial port found.")
        sys.exit(1)

    try:
        with serial.Serial(PORT, BAUD_RATE, timeout=1) as ser:
            print(f"Connected to {PORT}")
            print("Sending raw distance data only - height processing on computer side")
            
            while True:
                try:
                    line = ser.readline().decode("utf-8").strip()
                    if not line.startswith("{"):
                        continue

                    data = json.loads(line)
                    results = data.get("results", [])
                    raw_distances = {}

                    for result in results:
                        addr = result.get("Addr")
                        status = result.get("Status")
                        dist = result.get("D_cm")

                        if not addr or status != "Ok" or dist is None:
                            continue

                        raw_distances[addr] = dist * 10  # Convert cm to mm

                    # Send raw distance data if we have measurements
                    if raw_distances:
                        # Create simplified data structure with only essential data
                        raw_data = {
                            "distances": raw_distances,
                            "timestamp": time.time()
                        }
                        
                        sock.sendto(json.dumps(raw_data).encode(), (UDP_IP, UDP_PORT))
                        print("Sent raw distances:", raw_distances)

                except Exception as e:
                    print("Error in loop:", e)
                    time.sleep(0.1)
    except KeyboardInterrupt:
        print("Stopped.") 