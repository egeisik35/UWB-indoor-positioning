import numpy as np
import matplotlib.pyplot as plt
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

def get_all_distances():
    try:
        with open("latest_distances.json", "r") as f:
            return json.load(f)
    except:
        return {}

def trilaterate(p1, r1, p2, r2, p3, r3):
    P1 = np.array(p1)
    P2 = np.array(p2)
    P3 = np.array(p3)

    ex = (P2 - P1) / np.linalg.norm(P2 - P1)
    i = np.dot(ex, P3 - P1)
    ey = P3 - P1 - i * ex
    ey = ey / np.linalg.norm(ey)
    ez = np.cross(ex, ey)
    d = np.linalg.norm(P2 - P1)
    j = np.dot(ey, P3 - P1)

    x = (r1**2 - r2**2 + d**2) / (2 * d)
    y = (r1**2 - r3**2 + i**2 + j**2 - 2 * i * x) / (2 * j)
    try:
        z = np.sqrt(abs(r1**2 - x**2 - y**2))
    except:
        z = 0

    return P1 + x * ex + y * ey + z * ez

# === Plot Setup ===
fig = plt.figure(figsize=(10, 5))
ax_xy = fig.add_subplot(1, 2, 1)
ax_z = fig.add_subplot(1, 20, 20)

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

    plt.pause(0.5)

# === Main Loop ===
try:
    while True:
        distances = get_all_distances()

        if all(k in distances for k in responder_positions):
            d1 = distances["0x0001"] * 10
            d2 = distances["0x0002"] * 10
            d3 = distances["0x0003"] * 10

            est = trilaterate(
                responder_positions["0x0001"], d1,
                responder_positions["0x0002"], d2,
                responder_positions["0x0003"], d3
            )

            print(f"Estimated Position: x={est[0]:.1f}, y={est[1]:.1f}, z={est[2]:.1f} mm")
            update_plot(est)
        else:
            print("Waiting for all 3 distances...")

except KeyboardInterrupt:
    print("Stopped.")

