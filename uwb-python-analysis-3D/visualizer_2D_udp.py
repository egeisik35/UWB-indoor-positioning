import numpy as np
import matplotlib.pyplot as plt
import socket
import json
import time

# Room dimensions (in mm)
room_width = 7850
room_depth = 7300
room_height = 3200

# Anchor positions (exactly as in 3D)
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
fig = plt.figure(figsize=(10, 5))
ax_xy = fig.add_subplot(1, 2, 1)
ax_z = fig.add_subplot(1, 20, 20)

last_position = None
last_update = time.time()

def update_plot(est):
    ax_xy.clear()
    ax_z.clear()

    # 2D XY view
    ax_xy.set_xlim(0, room_width)
    ax_xy.set_ylim(0, room_depth)
    ax_xy.set_title("Top-Down View (X-Y)")
    ax_xy.set_xlabel("X (mm)")
    ax_xy.set_ylabel("Y (mm)")

    for addr, pos in responder_positions.items():
        ax_xy.plot(pos[0], pos[1], 'ro')
        ax_xy.text(pos[0] + 50, pos[1] + 50, addr, fontsize=8)

    ax_xy.plot(est[0], est[1], 'go', markersize=10)
    ax_xy.text(est[0] + 100, est[1], "Estimated", fontsize=9)

    # Z-height bar
    ax_z.set_ylim(0, room_height)
    ax_z.set_xlim(0, 1)
    ax_z.bar(0.5, est[2], width=0.4, color='green')
    ax_z.set_xticks([])
    ax_z.set_title("Z height (mm)")
    ax_z.text(0.5, est[2] + 100, f"{int(est[2])} mm", ha='center', fontsize=9)

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
            print(f"Received position: x={est[0]:.1f}, y={est[1]:.1f}, z={est[2]:.1f} mm")
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