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
sock.settimeout(0.01)

# === Plot Setup ===
fig = plt.figure(figsize=(8, 8))
ax = fig.add_subplot(111, projection='3d')

last_position = None
last_update = time.time()
current_position = None

# Interpolation settings
interp_steps = 10  # Number of frames to interpolate between positions
interp_counter = 0
interp_start = None
interp_end = None

def update_plot(est):
    ax.clear()
    ax.set_xlim(0, room_width)
    ax.set_ylim(0, room_depth)
    ax.set_zlim(0, room_height)
    ax.set_xlabel("X (mm)")
    ax.set_ylabel("Y (mm)")
    ax.set_zlabel("Z (mm)")
    ax.set_title("3D Position Visualization (Smooth)")
    ax.grid(True)

    # Plot anchors
    for addr, pos in responder_positions.items():
        ax.scatter(pos[0], pos[1], pos[2], c='r', marker='o', s=60)
        ax.text(pos[0], pos[1], pos[2]+100, addr, color='red', fontsize=8)

    # Plot estimated position
    ax.scatter(est[0], est[1], est[2], c='g', marker='o', s=80)
    ax.text(est[0], est[1], est[2]+100, "Estimated", color='green', fontsize=10)

    plt.pause(0.01)

try:
    while True:
        got_new = False
        try:
            data, addr = sock.recvfrom(1024)
            position = json.loads(data.decode())
            new_position = np.array([position['x'], position['y'], position['z']])
            print(f"Received position: x={new_position[0]:.1f} mm, y={new_position[1]:.1f} mm, z={new_position[2]:.1f} mm")
            if current_position is None:
                current_position = new_position
                interp_start = new_position
                interp_end = new_position
                interp_counter = 0
            else:
                interp_start = current_position
                interp_end = new_position
                interp_counter = 0
            got_new = True
        except socket.timeout:
            pass

        # Interpolate if we have a new target
        if interp_start is not None and interp_end is not None:
            t = min(interp_counter / interp_steps, 1.0)
            interp_pos = (1 - t) * interp_start + t * interp_end
            update_plot(interp_pos)
            current_position = interp_pos
            if t < 1.0:
                interp_counter += 1
        else:
            # No data yet, just wait
            time.sleep(0.01)
except KeyboardInterrupt:
    print("Stopped.")