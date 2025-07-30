import numpy as np
import matplotlib.pyplot as plt
import socket
import json
import time
from filterpy.kalman import KalmanFilter
from filterpy.common import Q_discrete_white_noise

# Room dimensions in mm (x, y) - 2D view
ROOM_DIMENSIONS = {
    "width_x": 8428,    # mm (x-axis) - 8.428m
    "depth_y": 7822,    # mm (y-axis) - 7.822m
}

# Anchor positions in mm (x, y) - 2D coordinates (top-down view)
responder_positions_2d = {
    "0x0001": [2968, 0],      # mm (x, y) - (2.968, 0) m
    "0x0002": [0, 4007],      # mm (x, y) - (0, 4.007) m
    "0x0003": [4432, 7375]    # mm (x, y) - (4.432, 7.375) m
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

# Sensor status tracking
sensor_status = {
    "0x0001": {"last_seen": 0, "color": "red"},
    "0x0002": {"last_seen": 0, "color": "red"},
    "0x0003": {"last_seen": 0, "color": "red"}
}

def create_kalman_filter():
    kf = KalmanFilter(dim_x=2, dim_z=1)
    kf.x = np.zeros((2, 1))
    kf.F = np.array([[1., INITIAL_DT], [0., 1.]])
    kf.H = np.array([[1., 0.]])
    kf.R = np.array([[MEASUREMENT_NOISE]])
    kf.Q = Q_discrete_white_noise(dim=2, dt=INITIAL_DT, var=PROCESS_NOISE)
    return kf

def trilaterate_2d(p1, r1, p2, r2, p3, r3):
    """
    2D trilateration using three anchor points
    p1, p2, p3: anchor positions in mm (x, y)
    r1, r2, r3: distances to anchors in mm
    Returns: estimated position in mm (x, y)
    """
    P1 = np.array(p1)
    P2 = np.array(p2)
    P3 = np.array(p3)
    
    # Calculate the unit vectors
    ex = (P2 - P1) / np.linalg.norm(P2 - P1)
    i = np.dot(ex, P3 - P1)
    ey = P3 - P1 - i * ex
    ey = ey / np.linalg.norm(ey)
    
    # Calculate distances between anchors
    d = np.linalg.norm(P2 - P1)
    j = np.dot(ey, P3 - P1)
    
    # Calculate x and y coordinates
    x = (r1**2 - r2**2 + d**2) / (2 * d)
    y = (r1**2 - r3**2 + i**2 + j**2 - 2 * i * x) / (2 * j)
    
    # Return 2D position
    return P1 + x * ex + y * ey

def estimate_height_2d(distances, room_dimensions):
    """
    Estimate height based on 2D distance patterns
    This runs on the computer side with full room context
    """
    if not distances or len(distances) < 2:
        return 1600  # Default height in mm
    
    # Calculate average distance to anchors
    avg_distance = sum(distances.values()) / len(distances)
    
    # Calculate maximum possible 2D distance in this room
    max_2d_distance = ((room_dimensions["width_x"]**2 + 
                       room_dimensions["depth_y"]**2)**0.5)
    
    # Normalize average distance
    distance_ratio = avg_distance / max_2d_distance
    
    # Use distance ratio to estimate height
    if distance_ratio > 0.7:
        # Far from anchors, likely higher up
        estimated_height = 2800  # mm (2.8m)
    elif distance_ratio < 0.3:
        # Close to anchors, likely lower down
        estimated_height = 800   # mm (0.8m)
    else:
        # Middle range, use default
        estimated_height = 1600  # mm (1.6m)
    
    print(f"2D Height estimation: avg_dist={avg_distance:.1f}mm, ratio={distance_ratio:.2f}, height_z={estimated_height}mm")
    
    return estimated_height

def update_sensor_status(distances, current_time):
    """
    Update sensor status based on received data
    Green = receiving data, Red = not receiving data
    """
    # Mark all sensors as not seen initially
    for sensor in sensor_status:
        sensor_status[sensor]["color"] = "red"
    
    # Mark sensors that sent data as green
    for sensor in distances:
        if sensor in sensor_status:
            sensor_status[sensor]["color"] = "green"
            sensor_status[sensor]["last_seen"] = current_time

# === 2D Plot Setup ===
fig, ax = plt.subplots(figsize=(12, 10))

last_position = None
last_update = time.time()
current_position = None

# Interpolation settings
interp_steps = 5
interp_counter = 0
interp_start = None
interp_end = None

def update_2d_plot(est_2d, height_z):
    ax.clear()
    
    # Set plot limits in mm
    ax.set_xlim(0, ROOM_DIMENSIONS["width_x"])
    ax.set_ylim(0, ROOM_DIMENSIONS["depth_y"])
    
    ax.set_title(f"2D UWB Positioning System (Height: {height_z/10:.1f}cm)", fontsize=14, weight='bold')
    ax.set_xlabel("X (mm)")
    ax.set_ylabel("Y (mm)")
    ax.grid(True, alpha=0.3)
    
    # Plot anchor positions with sensor icons and status colors
    for addr, pos in responder_positions_2d.items():
        color = sensor_status[addr]["color"]
        # Use a sensor-like icon (filled circle with inner circle)
        ax.scatter(pos[0], pos[1], c=color, s=400, marker='o', edgecolors='black', linewidth=2, zorder=5)
        # Inner circle to make it look like a sensor
        ax.scatter(pos[0], pos[1], c='white', s=200, marker='o', zorder=6)
        ax.scatter(pos[0], pos[1], c=color, s=100, marker='o', zorder=7)
        
        # Add sensor label with status
        status_text = "●" if color == "green" else "○"
        ax.text(pos[0] + 150, pos[1] + 150, f"{addr}\n{status_text}", 
                fontsize=10, weight='bold', ha='center')
    
    # Plot estimated position with tag icon
    if est_2d is not None:
        # Use a tag-like icon (diamond shape)
        ax.scatter(est_2d[0], est_2d[1], c='blue', s=500, marker='D', edgecolors='black', linewidth=2, zorder=6)
        ax.text(est_2d[0] + 200, est_2d[1] + 200, 
                f"Tag\n({est_2d[0]/10:.1f}cm, {est_2d[1]/10:.1f}cm)", 
                fontsize=10, weight='bold')
    
    # Add room dimensions text
    ax.text(50, ROOM_DIMENSIONS["depth_y"] - 200, 
            f"Room: {ROOM_DIMENSIONS['width_x']/10:.1f}cm x {ROOM_DIMENSIONS['depth_y']/10:.1f}cm", 
            fontsize=10, style='italic')
    
    # Add legend
    legend_elements = [
        plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='green', markersize=15, label='Sensor Active'),
        plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='red', markersize=15, label='Sensor Inactive'),
        plt.Line2D([0], [0], marker='D', color='w', markerfacecolor='blue', markersize=15, label='Tag Position')
    ]
    ax.legend(handles=legend_elements, loc='upper right')
    
    plt.pause(0.005)

try:
    print("Starting 2D UWB Visualizer...")
    print(f"Room dimensions: {ROOM_DIMENSIONS['width_x']/10:.1f}cm x {ROOM_DIMENSIONS['depth_y']/10:.1f}cm")
    print("Waiting for UDP data...")
    print("Sensor Status: Green = Active, Red = Inactive")
    
    while True:
        got_new = False
        try:
            data, addr = sock.recvfrom(1024)
            raw_data = json.loads(data.decode())
            
            # Extract data (simplified format from Raspberry Pi)
            distances = raw_data.get("distances", {})
            timestamp = raw_data.get("timestamp", time.time())
            
            # Update sensor status
            update_sensor_status(distances, timestamp)
            
            print(f"Received 2D raw data: distances={distances}")
            
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
            
            # Perform 2D trilateration if we have all 3 distances
            if all(k in filtered_distances for k in responder_positions_2d):
                d1 = filtered_distances["0x0001"]
                d2 = filtered_distances["0x0002"]
                d3 = filtered_distances["0x0003"]
                
                est_2d = trilaterate_2d(
                    responder_positions_2d["0x0001"], d1,
                    responder_positions_2d["0x0002"], d2,
                    responder_positions_2d["0x0003"], d3
                )
                
                # Estimate height using 2D distance patterns
                estimated_height = estimate_height_2d(filtered_distances, ROOM_DIMENSIONS)
                
                new_position_2d = np.array([est_2d[0], est_2d[1]])
                print(f"Calculated 2D position: x={new_position_2d[0]/10:.1f}cm, y={new_position_2d[1]/10:.1f}cm, z={estimated_height/10:.1f}cm")
                
                if current_position is None:
                    current_position = new_position_2d
                    interp_start = new_position_2d
                    interp_end = new_position_2d
                    interp_counter = 0
                else:
                    interp_start = current_position
                    interp_end = new_position_2d
                    interp_counter = 0
                got_new = True
                
        except socket.timeout:
            pass

        # Interpolate if we have a new target
        if interp_start is not None and interp_end is not None:
            t = min(interp_counter / interp_steps, 1.0)
            interp_pos = (1 - t) * interp_start + t * interp_end
            update_2d_plot(interp_pos, estimated_height)
            current_position = interp_pos
            if t < 1.0:
                interp_counter += 1
        else:
            # No data yet, just show the plot with inactive sensors
            update_2d_plot(None, 1600)
            time.sleep(0.005)
except KeyboardInterrupt:
    print("Stopped.") 