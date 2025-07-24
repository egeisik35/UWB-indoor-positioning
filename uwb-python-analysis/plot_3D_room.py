import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
import time
import os

# Room dimensions
room_width = 6980
room_depth = 6800
room_height = 3200
initiator = np.array([0, 0, 0])
direction = np.array([1, 1, 1]) / np.linalg.norm([1, 1, 1])

def get_distance():
    try:
        with open("latest_distance.txt", "r") as f:
            return float(f.read().strip()) * 10  # cm to mm
    except:
        return 4000  # fallback

def draw_scene(ax, dist_mm):
    ax.clear()

    # Room box
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

    # Initiator
    ax.scatter(*initiator, color='blue', s=50, label="Initiator")

    # Responder position (example on sphere)
    responder = initiator + direction * dist_mm
    ax.scatter(*responder, color='red', s=50, label="Responder (on sphere)")

    # Sphere
    u, v = np.mgrid[0:2*np.pi:30j, 0:np.pi:15j]
    x = dist_mm * np.cos(u) * np.sin(v)
    y = dist_mm * np.sin(u) * np.sin(v)
    z = dist_mm * np.cos(v)
    ax.plot_wireframe(x, y, z, color='red', alpha=0.3)

    # Labels and limits
    ax.set_xlim(0, room_width)
    ax.set_ylim(0, room_depth)
    ax.set_zlim(0, room_height)
    ax.set_xlabel("X (mm)")
    ax.set_ylabel("Y (mm)")
    ax.set_zlabel("Z (mm)")
    ax.set_title("Live UWB Responder Sphere")
    ax.legend()

# ---------- Live loop ----------
fig = plt.figure()
ax = fig.add_subplot(111, projection='3d')

try:
    while True:
        dist = get_distance()
        draw_scene(ax, dist)
        plt.pause(1.0)  # refresh every second
except KeyboardInterrupt:
    print("Stopped.")

