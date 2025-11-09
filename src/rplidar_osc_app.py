#!/usr/bin/env python3
# rplidar_osc_app.py
# GUIでRPLIDAR A1→OSC送信（3分割） macOS/Windows 両対応
# pip install rplidar python-osc pyserial

import threading
import time
import sys
import tkinter as tk
from tkinter import ttk, messagebox

from pythonosc.udp_client import SimpleUDPClient
from serial.tools import list_ports

# rplidarはプラットフォームによってはhidのoptional依存が噛むことがあります。
# インポート失敗時にメッセージを出すようにしています。
try:
    from rplidar import RPLidar
except Exception as e:
    raise RuntimeError("rplidar ライブラリの読み込みに失敗しました。`pip install rplidar` を実行してください。") from e


APP_TITLE = "RPLIDAR → OSC Sender"
DEFAULT_OSC_HOST = "127.0.0.1"
DEFAULT_OSC_PORT = 8000
FPS = 10  # 送信フレームレート
BAUD = 115200

class LidarSenderApp:
    def __init__(self, master):
        self.master = master
        master.title(APP_TITLE)
        master.geometry("520x260")

        self.running = False
        self.thread = None
        self.lidar = None

        # Widgets
        row = 0

        ttk.Label(master, text="Serial Port:").grid(row=row, column=0, sticky="e", padx=8, pady=8)
        self.port_combo = ttk.Combobox(master, width=40, state="readonly")
        self.port_combo.grid(row=row, column=1, columnspan=2, sticky="w", padx=8, pady=8)

        self.refresh_btn = ttk.Button(master, text="Refresh", command=self.refresh_ports)
        self.refresh_btn.grid(row=row, column=3, sticky="w", padx=4, pady=8)

        row += 1
        ttk.Label(master, text="OSC Host:").grid(row=row, column=0, sticky="e", padx=8, pady=4)
        self.host_var = tk.StringVar(value=DEFAULT_OSC_HOST)
        self.host_entry = ttk.Entry(master, textvariable=self.host_var, width=20)
        self.host_entry.grid(row=row, column=1, sticky="w", padx=8, pady=4)

        ttk.Label(master, text="OSC Port:").grid(row=row, column=2, sticky="e", padx=8, pady=4)
        self.port_var = tk.StringVar(value=str(DEFAULT_OSC_PORT))
        self.osc_port_entry = ttk.Entry(master, textvariable=self.port_var, width=8)
        self.osc_port_entry.grid(row=row, column=3, sticky="w", padx=8, pady=4)

        row += 1
        self.start_btn = ttk.Button(master, text="Start", command=self.start)
        self.start_btn.grid(row=row, column=1, sticky="e", padx=8, pady=12)
        self.stop_btn = ttk.Button(master, text="Stop", command=self.stop, state="disabled")
        self.stop_btn.grid(row=row, column=2, sticky="w", padx=8, pady=12)

        row += 1
        ttk.Label(master, text="Status:").grid(row=row, column=0, sticky="ne", padx=8, pady=4)
        self.status_text = tk.Text(master, height=6, width=60, state="disabled")
        self.status_text.grid(row=row, column=1, columnspan=3, sticky="w", padx=8, pady=4)

        # 初回ポート列挙
        self.refresh_ports()

        # 終了ハンドラ
        master.protocol("WM_DELETE_WINDOW", self.on_close)

    def log(self, s):
        self.status_text.configure(state="normal")
        self.status_text.insert("end", s + "\n")
        self.status_text.see("end")
        self.status_text.configure(state="disabled")

    def refresh_ports(self):
        ports = list_ports.comports()
        items = [p.device for p in ports]
        # 代表例：mac: /dev/tty.usbserial-0001, Win: COM3
        self.port_combo["values"] = items
        if items:
            self.port_combo.current(0)
        self.log(f"[INFO] Found ports: {items if items else 'None'}")

    def start(self):
        if self.running:
            return
        port = self.port_combo.get()
        if not port:
            messagebox.showerror("Error", "シリアルポートが選択されていません。")
            return
        try:
            osc_port = int(self.port_var.get())
        except ValueError:
            messagebox.showerror("Error", "OSCポート番号が不正です。")
            return
        host = self.host_var.get().strip() or DEFAULT_OSC_HOST

        self.running = True
        self.start_btn.configure(state="disabled")
        self.stop_btn.configure(state="normal")

        self.thread = threading.Thread(target=self._worker, args=(port, host, osc_port), daemon=True)
        self.thread.start()

    def stop(self):
        self.running = False
        self.stop_btn.configure(state="disabled")
        self.start_btn.configure(state="normal")
        self.log("[INFO] Stopping...")

    def _worker(self, serial_port, host, osc_port):
        self.log(f"[INFO] Opening {serial_port} @ {BAUD}, sending OSC to {host}:{osc_port}")
        scan_data = [0.0] * 360
        last = time.time()

        try:
            client = SimpleUDPClient(host, osc_port)
            self.lidar = RPLidar(serial_port, baudrate=BAUD, timeout=3)
            self.log("[INFO] Connected to RPLIDAR.")

            for _, _, angle, distance in self.lidar.iter_measurments():
                if not self.running:
                    break
                a = int(angle) % 360
                scan_data[a] = float(distance)  # mm
                now = time.time()
                if now - last > 1.0 / FPS:
                    # 120本×3分割 [start, d0..d119]
                    for start in (0, 120, 240):
                        segment = scan_data[start:start+120]
                        client.send_message("/rplidar/scan", [start] + segment)
                    last = now

        except Exception as e:
            self.log(f"[ERROR] {e}")
            messagebox.showerror("Error", str(e))
        finally:
            try:
                if self.lidar:
                    self.lidar.stop()
                    self.lidar.disconnect()
            except Exception:
                pass
            self.lidar = None
            self.running = False
            self.stop_btn.configure(state="disabled")
            self.start_btn.configure(state="normal")
            self.log("[INFO] Worker terminated.")

    def on_close(self):
        self.stop()
        # スレッド終了待ち（短時間）
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=1.0)
        self.master.destroy()


def main():
    root = tk.Tk()
    # macのダークモード等で見辛い場合はテーマ指定も可
    try:
        style = ttk.Style()
        if sys.platform == "darwin":
            style.theme_use("aqua")
    except Exception:
        pass
    app = LidarSenderApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
