import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import socket
import json
import time

# Room dimensions (in mm)
room_width = 7850
room_depth = 7300
room_height = 3200

# Anchor positions (in mm)
responder_positions = {
    "0x0001": [3000, 0, 1200],
    "0x0002": [0, 4000, 1050],
    "0x0003": [6850, 4400, 1200]
}

# UDP setup
UDP_IP = "0.0.0.0"
UDP_PORT = 5005
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((UDP_IP, UDP_PORT))
sock.settimeout(1.0)

# === Plot Setup ===
fig = plt.figure(figsize=(8, 8))
ax = fig.add_subplot(111, projection='3d')

last_position = None
last_update = time.time()

def update_plot(est):
    ax.clear()
    ax.set_xlim(0, room_width)
    ax.set_ylim(0, room_depth)
    ax.set_zlim(0, room_height)
    ax.set_xlabel("X (mm)")
    ax.set_ylabel("Y (mm)")
    ax.set_zlabel("Z (mm)")
    ax.set_title("3D Position Visualization")
    ax.grid(True)

    # Plot anchors
    for addr, pos in responder_positions.items():
        ax.scatter(pos[0], pos[1], pos[2], c='r', marker='o', s=60)
        ax.text(pos[0], pos[1], pos[2]+100, addr, color='red', fontsize=8)

    # Plot estimated position
    ax.scatter(est[0], est[1], est[2], c='g', marker='o', s=80)
    ax.text(est[0], est[1], est[2]+100, "Estimated", color='green', fontsize=10)

    plt.pause(0.05)

# === Main Loop ===
try:
    while True:
        try:
            data, addr = sock.recvfrom(1024)
            position = json.loads(data.decode())
            est = [position['x'], position['y'], position['z']]
            last_position = est
            last_update = time.time()
            print(f"Received position: x={est[0]:.1f} mm, y={est[1]:.1f} mm, z={est[2]:.1f} mm")
            update_plot(est)
        except socket.timeout:
            # If no new data, re-plot last position for smoothness
            if last_position is not None and time.time() - last_update < 2.0:
                update_plot(last_position)
            else:
                print("Waiting for position data...")
                time.sleep(0.05)
except KeyboardInterrupt:
    print("Stopped.")