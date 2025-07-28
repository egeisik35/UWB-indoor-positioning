import serial, json, sys
import numpy as np
from collections import deque
from numba import njit
import serial.tools.list_ports

def find_serial_port():
    for port, _, _ in serial.tools.list_ports.comports():
        if "ACM" in port or "USB" in port:
            return port
    return None

PORT = find_serial_port()
if not PORT:
    sys.exit("No suitable port found")

ser = serial.Serial(PORT, 115200, timeout=1)
distance_history = {}
spike_streak = {}
WINDOW, MAX_JUMP, RESET_AFTER = 10, 25, 3

@njit
def moving_average(arr): return np.mean(arr)
@njit
def check_jump(last, current, threshold): return abs(current - last) > threshold

try:
    while True:
        try:
            line = ser.readline().decode().strip()
            if not line.startswith('{'): continue
            data = json.loads(line)
            for result in data.get("results", []):
                addr, status, dist = result.get("Addr"), result.get("Status"), result.get("D_cm")
                if status != "Ok": continue

                if addr not in distance_history:
                    distance_history[addr] = deque([dist], maxlen=WINDOW)
                    spike_streak[addr] = 0
                else:
                    last = distance_history[addr][-1]
                    if check_jump(last, dist, MAX_JUMP):
                        spike_streak[addr] += 1
                        if spike_streak[addr] >= RESET_AFTER:
                            half = WINDOW // 2
                            recent = list(distance_history[addr])[:half]
                            distance_history[addr] = deque([dist]*half + recent, maxlen=WINDOW)
                            spike_streak[addr] = 0
                        else:
                            dist = last * 0.7 + dist * 0.3
                            distance_history[addr].append(dist)
                    else:
                        spike_streak[addr] = 0
                        distance_history[addr].append(dist)

                avg = moving_average(np.array(distance_history[addr]))
                sys.stdout.write(f"\r[{addr}] {avg:.1f} cm    ")
                sys.stdout.flush()
        except (json.JSONDecodeError, UnicodeDecodeError):
            continue
except KeyboardInterrupt:
    print("\nStopped by user.")
