# rplidar_osc.py
# 使い方: python3 rplidar_osc.py /dev/tty.usbserial-0001 8000
import sys, time
from rplidar import RPLidar
from pythonosc.udp_client import SimpleUDPClient

PORT_DEFAULT = 8000
HOST = "127.0.0.1"

def main():
    if len(sys.argv) < 2:
        print("Usage: python rplidar_osc.py <serial_port> [osc_port]")
        sys.exit(1)
    serial = sys.argv[1]
    osc_port = int(sys.argv[2]) if len(sys.argv) > 2 else PORT_DEFAULT

    client = SimpleUDPClient(HOST, osc_port)
    lidar = RPLidar(serial, baudrate=115200, timeout=3)

    print(f"Connected to {serial}. Sending OSC to {HOST}:{osc_port}")
    scan_data = [0.0]*360
    fps, last = 10, time.time()

    try:
        for _, _, angle, distance in lidar.iter_measurments():
            a = int(angle) % 360
            scan_data[a] = float(distance)  # mm
            if time.time() - last > 1.0/fps:
                # /rplidar/scan [d0, d1, ..., d359] (mm)
                for start in (0, 120, 240):
                     segment = scan_data[start:start+120]
                     # 先頭に開始インデックスを付けて送る: /rplidar/scan [start, d0..d119]
                     client.send_message("/rplidar/scan", [start] + segment)
                last = time.time()
    except KeyboardInterrupt:
        pass
    finally:
        lidar.stop()
        lidar.disconnect()

if __name__ == "__main__":
    main()
