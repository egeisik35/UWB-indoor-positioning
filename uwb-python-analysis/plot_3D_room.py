import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

# Load last distance from file (in cm)
try:
    with open("latest_distance.txt", "r") as f:
        uwb_distance = float(f.read().strip()) * 10  # cm → mm
except:
    print("No valid distance. Defaulting to 4000 mm.")
    uwb_distance = 4000

# Room dimensions in mm
room_width = 6980
room_depth = 6800
room_height = 3200

# Positions
initiator = np.array([0, 0, 0])
direction = np.array([1, 1, 1]) / np.linalg.norm([1, 1, 1])
responder = initiator + direction * uwb_distance

# Plot
fig = plt.figure()
ax = fig.add_subplot(111, projection='3d')
ax.set_title("3D Room View (UWB Sphere)")

# Draw room
corners = [
    [0, 0, 0], [room_width, 0, 0], [room_width, room_depth, 0], [0, room_depth, 0],
    [0, 0, room_height], [room_width, 0, room_height], [room_width, room_depth, room_height], [0, room_depth, room_height]
]
faces = [
    [corners[0], corners[1], corners[2], corners[3]], [corners[4], corners[5], corners[6], corners[7]],
    [corners[0], corners[1], corners[5], corners[4]], [corners[1], corners[2], corners[6], corners[5]],
    [corners[2], corners[3], corners[7], corners[6]], [corners[3], corners[0], corners[4], corners[7]]
]
ax.add_collection3d(Poly3DCollection(faces, facecolors='lightgray', alpha=0.15, edgecolors='black'))

# Initiator and responder
ax.scatter(*initiator, color='blue', s=50, label="Initiator")
ax.scatter(*responder, color='red', s=50, label="Responder (on sphere)")

# Sphere
u, v = np.mgrid[0:2*np.pi:30j, 0:np.pi:15j]
x = uwb_distance * np.cos(u) * np.sin(v)
y = uwb_distance * np.sin(u) * np.sin(v)
z = uwb_distance * np.cos(v)
ax.plot_wireframe(x, y, z, color='red', alpha=0.3)

# Limits
ax.set_xlim(0, room_width)
ax.set_ylim(0, room_depth)
ax.set_zlim(0, room_height)
ax.set_xlabel("X (mm)")
ax.set_ylabel("Y (mm)")
ax.set_zlabel("Z (mm)")
ax.legend()
plt.show()

