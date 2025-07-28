
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
import json
import time

# Room dimensions (in mm)
room_width = 7850
room_depth = 7300
room_height = 3200
initiator = np.array([0, 0, 0])  # this is just visual; real position is estimated

# Fixed anchor positions
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

    ex = (P2 - P1)
    ex = ex / np.linalg.norm(ex)
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
    except ValueError:
        z = 0

    return P1 + x * ex + y * ey + z * ez

def draw_scene(ax, distances):
    ax.clear()

    # Draw room
    room = [
        [0, 0, 0], [room_width, 0, 0], [room_width, room_depth, 0], [0, room_depth, 0],
        [0, 0, room_height], [room_width, 0, room_height],
        [room_width, room_depth, room_height], [0, room_depth, room_height]
    ]
    faces = [
        [room[0], room[1], room[2], room[3]], [room[4], room[5], room[6], room[7]],
        [room[0], room[1], room[5], room[4]], [room[2], room[3], room[7], room[6]],
        [room[1], room[2], room[6], room[5]], [room[0], room[3], room[7], room[4]]
    ]
    ax.add_collection3d(Poly3DCollection(faces, facecolors='lightgrey', alpha=0.1, edgecolors='black'))

    # Draw responders
    for addr, pos in responder_positions.items():
        ax.scatter(*pos, color='red', s=50, label=f"{addr}")

    # Draw trilaterated position
    if all(k in distances for k in responder_positions):
        d1 = distances["0x0001"] * 10
        d2 = distances["0x0002"] * 10
        d3 = distances["0x0003"] * 10

        est = trilaterate(responder_positions["0x0001"], d1,
                          responder_positions["0x0002"], d2,
                          responder_positions["0x0003"], d3)

        ax.scatter(*est, color='green', s=80, label="Estimated Position")
        print(f"Estimated Position: x={est[0]:.1f}, y={est[1]:.1f}, z={est[2]:.1f} mm")

    ax.set_xlim(0, room_width)
    ax.set_ylim(0, room_depth)
    ax.set_zlim(0, room_height)
    ax.set_xlabel("X (mm)")
    ax.set_ylabel("Y (mm)")
    ax.set_zlabel("Z (mm)")
    ax.set_title("UWB Trilateration Visualization")
    ax.legend(loc='upper right', fontsize=7)

# Live loop
fig = plt.figure()
ax = fig.add_subplot(111, projection='3d')

try:
    while True:
        distances = get_all_distances()
        draw_scene(ax, distances)
        plt.pause(1.0)
except KeyboardInterrupt:
    print("Stopped.")
