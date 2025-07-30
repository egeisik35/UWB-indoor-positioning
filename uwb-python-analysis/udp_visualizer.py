import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import socket
import json
import time
from filterpy.kalman import KalmanFilter
from filterpy.common import Q_discrete_white_noise

# Room dimensions in mm (x, y, z) - configured on computer side
ROOM_DIMENSIONS = {
    "width_x": 8428,    # mm (x-axis) - 8.428m
    "depth_y": 7822,    # mm (y-axis) - 7.822m
    "height_z": 3200    # mm (z-axis) - 3.2m
}

# Anchor positions in mm (x, y, z) - 3D coordinates
responder_positions_3d = {
    "0x0001": [2968, 0, 2040],      # mm (x, y, z) - (2.968, 0, 2.04) m
    "0x0002": [0, 4007, 2250],      # mm (x, y, z) - (0, 4.007, 2.25) m
    "0x0003": [4432, 7375, 1800]    # mm (x, y, z) - (4.432, 7.375, 1.80) m
}

# UDP setup
UDP_IP = "0.0.0.0"
UDP_PORT = 5005
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((UDP_IP, UDP_PORT))
sock.settimeout(0.005)

# Kalman filter settings
INITIAL_DT = 0.1
MEASUREMENT_NOISE = 10
PROCESS_NOISE = 0.1

# Kalman filters for each anchor
kalman_filters = {}
last_time = {}

def create_kalman_filter():
    kf = KalmanFilter(dim_x=2, dim_z=1)
    kf.x = np.zeros((2, 1))
    kf.F = np.array([[1., INITIAL_DT], [0., 1.]])
    kf.H = np.array([[1., 0.]])
    kf.R = np.array([[MEASUREMENT_NOISE]])
    kf.Q = Q_discrete_white_noise(dim=2, dt=INITIAL_DT, var=PROCESS_NOISE)
    return kf

def improve_height_decision(distances, room_dimensions):
    """
    Improve height decision using room dimensions and anchor positions
    This runs on the computer side with full room context
    """
    if not distances or len(distances) < 2:
        return 1600  # Default height in mm
    
    # Calculate average distance to anchors
    avg_distance = sum(distances.values()) / len(distances)
    
    # Calculate maximum possible distance in this room
    max_possible_distance = ((room_dimensions["width_x"]**2 + 
                            room_dimensions["depth_y"]**2 + 
                            room_dimensions["height_z"]**2)**0.5)
    
    # Normalize average distance
    distance_ratio = avg_distance / max_possible_distance
    
    # Use distance ratio and room context to improve height estimate
    if distance_ratio > 0.7:
        # Far from anchors, likely higher up
        improved_height = min(room_dimensions["height_z"] * 0.8, 2800)
    elif distance_ratio < 0.3:
        # Close to anchors, likely lower down
        improved_height = max(room_dimensions["height_z"] * 0.2, 800)
    else:
        # Middle range, use default
        improved_height = 1600
    
    # Ensure height is within room bounds
    improved_height = max(100, min(room_dimensions["height_z"] - 100, improved_height))
    
    print(f"Height improvement: Computer={improved_height}mm, ratio={distance_ratio:.2f}")
    
    return improved_height

def trilaterate_3d(p1, r1, p2, r2, p3, r3):
    """
    3D trilateration using three anchor points
    p1, p2, p3: anchor positions in mm (x, y, z)
    r1, r2, r3: distances to anchors in mm
    Returns: estimated position in mm (x, y, z)
    """
    P1 = np.array(p1)
    P2 = np.array(p2)
    P3 = np.array(p3)
    
    # Calculate the unit vectors
    ex = (P2 - P1) / np.linalg.norm(P2 - P1)
    i = np.dot(ex, P3 - P1)
    ey = P3 - P1 - i * ex
    ey = ey / np.linalg.norm(ey)
    ez = np.cross(ex, ey)
    
    # Calculate distances between anchors
    d = np.linalg.norm(P2 - P1)
    j = np.dot(ey, P3 - P1)
    
    # Calculate x and y coordinates
    x = (r1**2 - r2**2 + d**2) / (2 * d)
    y = (r1**2 - r3**2 + i**2 + j**2 - 2 * i * x) / (2 * j)
    
    # Calculate z coordinate
    try:
        z = np.sqrt(abs(r1**2 - x**2 - y**2))
    except:
        z = 0
    
    # Return 3D position
    return P1 + x * ex + y * ey + z * ez

# === 3D Plot Setup ===
fig = plt.figure(figsize=(12, 8))
ax_3d = fig.add_subplot(111, projection='3d')

last_position = None
last_update = time.time()
current_position = None

# Interpolation settings
interp_steps = 5
interp_counter = 0
interp_start = None
interp_end = None

def update_3d_plot(est_3d):
    ax_3d.clear()
    
    # Set plot limits in mm
    ax_3d.set_xlim(0, ROOM_DIMENSIONS["width_x"])
    ax_3d.set_ylim(0, ROOM_DIMENSIONS["depth_y"])
    ax_3d.set_zlim(0, ROOM_DIMENSIONS["height_z"])
    
    ax_3d.set_title("3D UWB Positioning System")
    ax_3d.set_xlabel("X (mm)")
    ax_3d.set_ylabel("Y (mm)")
    ax_3d.set_zlabel("Z (mm)")
    
    # Plot anchor positions
    for addr, pos in responder_positions_3d.items():
        ax_3d.scatter(pos[0], pos[1], pos[2], c='red', s=100, marker='o')
        ax_3d.text(pos[0] + 50, pos[1] + 50, pos[2] + 50, addr, fontsize=8)
    
    # Plot estimated position
    ax_3d.scatter(est_3d[0], est_3d[1], est_3d[2], c='green', s=200, marker='*')
    ax_3d.text(est_3d[0] + 100, est_3d[1] + 100, est_3d[2] + 100, 
                f"Tag\n({est_3d[0]/10:.1f}cm, {est_3d[1]/10:.1f}cm, {est_3d[2]/10:.1f}cm)", 
                fontsize=9)
    
    plt.pause(0.005)

try:
    while True:
        got_new = False
        try:
            data, addr = sock.recvfrom(1024)
            raw_data = json.loads(data.decode())
            
            # Extract data (simplified format)
            distances = raw_data.get("distances", {})
            timestamp = raw_data.get("timestamp", time.time())
            
            print(f"Received raw data: distances={distances}")
            
            # Apply Kalman filtering to distances
            filtered_distances = {}
            for anchor_addr, distance in distances.items():
                if anchor_addr not in kalman_filters:
                    kalman_filters[anchor_addr] = create_kalman_filter()
                    kalman_filters[anchor_addr].x[0] = distance
                    last_time[anchor_addr] = timestamp
                    filtered_distances[anchor_addr] = distance
                    continue
                
                dt = timestamp - last_time.get(anchor_addr, timestamp)
                if dt <= 0: 
                    filtered_distances[anchor_addr] = distance
                    continue
                    
                last_time[anchor_addr] = timestamp
                
                kf = kalman_filters[anchor_addr]
                kf.F[0, 1] = dt
                kf.Q = Q_discrete_white_noise(dim=2, dt=dt, var=PROCESS_NOISE)
                
                kf.predict()
                kf.update(np.array([[distance]]))
                
                filtered_distances[anchor_addr] = kf.x[0, 0]
            
            # Perform 3D trilateration if we have all 3 distances
            if all(k in filtered_distances for k in responder_positions_3d):
                d1 = filtered_distances["0x0001"]
                d2 = filtered_distances["0x0002"]
                d3 = filtered_distances["0x0003"]
                
                est_3d = trilaterate_3d(
                    responder_positions_3d["0x0001"], d1,
                    responder_positions_3d["0x0002"], d2,
                    responder_positions_3d["0x0003"], d3
                )
                
                # Improve height decision using room context
                improved_height = improve_height_decision(filtered_distances, ROOM_DIMENSIONS)
                est_3d[2] = improved_height
                
                new_position_3d = np.array([est_3d[0], est_3d[1], est_3d[2]])
                print(f"Calculated 3D position: x={new_position_3d[0]/10:.1f}cm, y={new_position_3d[1]/10:.1f}cm, z={new_position_3d[2]/10:.1f}cm")
                
                if current_position is None:
                    current_position = new_position_3d
                    interp_start = new_position_3d
                    interp_end = new_position_3d
                    interp_counter = 0
                else:
                    interp_start = current_position
                    interp_end = new_position_3d
                    interp_counter = 0
                got_new = True
                
        except socket.timeout:
            pass

        # Interpolate if we have a new target
        if interp_start is not None and interp_end is not None:
            t = min(interp_counter / interp_steps, 1.0)
            interp_pos = (1 - t) * interp_start + t * interp_end
            update_3d_plot(interp_pos)
            current_position = interp_pos
            if t < 1.0:
                interp_counter += 1
        else:
            # No data yet, just wait
            time.sleep(0.005)
except KeyboardInterrupt:
    print("Stopped.")