import serial
import json

ser = serial.Serial('/dev/ttyACM0', 115200, timeout=1)

while True:
    try:
        line = ser.readline().decode('utf-8').strip()
        if line.startswith('{') and line.endswith('}'):
            data = json.loads(line)
            print(data)
    except KeyboardInterrupt:
        break
ser.close()
