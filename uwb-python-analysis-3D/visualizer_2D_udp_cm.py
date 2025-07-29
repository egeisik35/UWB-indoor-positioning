import numpy as np
import matplotlib.pyplot as plt
import socket
import json
import time

##Room dimensions (in cm)
room_width = 799
room_depth = 840
room_height = 320

# Anchor positions (in cm)
responder_positions = {
    "0x0001": [295, 0, 204],
    "0x0002": [155, 390, 74],
    "0x0003": [680, 495, 120]
}

#UDP setup
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
    ax_xy.set_xlabel("X (cm)")
    ax_xy.set_ylabel("Y (cm)")
    ax_xy.grid(True)

    for addr, pos in responder_positions.items():
        ax_xy.plot(pos[0], pos[1], 'ro')
        ax_xy.text(pos[0] + 5, pos[1] + 5, addr, fontsize=8)

    ax_xy.plot(est[0]/10, est[1]/10, 'go', markersize=10)
    ax_xy.text(est[0]/10 + 10, est[1]/10, "Estimated", fontsize=9)

    # Z-height bar
    ax_z.set_ylim(0, room_height)
    ax_z.set_xlim(0, 1)
    ax_z.bar(0.5, est[2]/10, width=0.4, color='green')
    ax_z.set_xticks([])
    ax_z.set_title("Z height (cm)")
    ax_z.text(0.5, est[2]/10 + 5, f"{int(est[2]/10)} cm", ha='center', fontsize=9)
    ax_z.grid(True)

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
            print(f"Received position: x={est[0]/10:.1f} cm, y={est[1]/10:.1f} cm, z={est[2]/10:.1f} cm")
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