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

# Height decision algorithm parameters
HEIGHT_DECISION = {
    "min_height_z": 500,      # mm - minimum reasonable height
    "max_height_z": 2500,     # mm - maximum reasonable height
    "default_height_z": 1200,  # mm - default height if no good estimate
    "confidence_threshold": 0.7 # confidence threshold for height decisions
}

def find_serial_port():
    ports = serial.tools.list_ports.comports()
    for port, desc, hwid in sorted(ports):
        if "ACM" in port or "USB" in port or "VCP" in port:
            print(f"Found suitable port: {port}")
            return port
    return None

def decide_height_z(distances, height_params):
    """
    Decision algorithm for choosing reasonable height_z value based on:
    - Distance measurements
    - Physical constraints
    - Historical patterns
    """
    if not distances or len(distances) < 2:
        return height_params["default_height_z"]
    
    # Calculate average distance to anchors
    avg_distance = sum(distances.values()) / len(distances)
    
    # Simple height estimation based on average distance
    # If distances are very large, likely higher up
    # If distances are small, likely lower down
    if avg_distance > 5000:  # mm - far from anchors
        estimated_height = height_params["max_height_z"]
    elif avg_distance < 2000:  # mm - close to anchors
        estimated_height = height_params["min_height_z"]
    else:
        # Middle range, use default
        estimated_height = height_params["default_height_z"]
    
    # Ensure height is within reasonable bounds
    estimated_height = max(height_params["min_height_z"], 
                          min(height_params["max_height_z"], estimated_height))
    
    print(f"Height decision: avg_dist={avg_distance:.1f}mm, height_z={estimated_height:.1f}mm")
    
    return estimated_height

if __name__ == "__main__":
    PORT = find_serial_port()
    if PORT is None:
        print("Error: No suitable serial port found.")
        sys.exit(1)

    try:
        with serial.Serial(PORT, BAUD_RATE, timeout=1) as ser:
            print(f"Connected to {PORT}")
            print(f"Height decision params: {HEIGHT_DECISION}")
            
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
                        # Decide on height_z using the decision algorithm
                        height_z = decide_height_z(raw_distances, HEIGHT_DECISION)
                        
                        # Create simplified data structure with only essential data
                        raw_data = {
                            "distances": raw_distances,
                            "height_z_mm": height_z,
                            "timestamp": time.time()
                        }
                        
                        sock.sendto(json.dumps(raw_data).encode(), (UDP_IP, UDP_PORT))
                        print("Sent raw data:", raw_data)

                except Exception as e:
                    print("Error in loop:", e)
                    time.sleep(0.1)
    except KeyboardInterrupt:
        print("Stopped.") 