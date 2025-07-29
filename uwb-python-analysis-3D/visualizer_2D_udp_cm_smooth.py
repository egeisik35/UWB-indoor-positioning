import numpy as np
import matplotlib.pyplot as plt
import socket
import json
import time

# Room dimensions (in cm)
room_width = 785
room_depth = 730
room_height = 320

# Anchor positions (in cm)
responder_positions = {
    "0x0001": [300, 0, 120],
    "0x0002": [0, 400, 105],
    "0x0003": [685, 440, 120]
}

# UDP setup
UDP_IP = "0.0.0.0"
UDP_PORT = 5005
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((UDP_IP, UDP_PORT))
sock.settimeout(0.01)

# === Plot Setup ===
fig = plt.figure(figsize=(10, 5))
ax_xy = fig.add_subplot(1, 2, 1)
ax_z = fig.add_subplot(1, 20, 20)

last_position = None
last_update = time.time()
current_position = None

# Interpolation settings
interp_steps = 10  # Number of frames to interpolate between positions
interp_counter = 0
interp_start = None
interp_end = None

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

    plt.pause(0.01)

try:
    while True:
        got_new = False
        try:
            data, addr = sock.recvfrom(1024)
            position = json.loads(data.decode())
            new_position = np.array([position['x'], position['y'], position['z']])
            print(f"Received position: x={new_position[0]/10:.1f} cm, y={new_position[1]/10:.1f} cm, z={new_position[2]/10:.1f} cm")
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