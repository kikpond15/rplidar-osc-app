#!/usr/bin/env python3
# rplidar_osc_app.py - 純Tk版（ttk不使用・確実に見えるUI）
# pip install rplidar python-osc pyserial

import sys, time, threading, tkinter as tk
from tkinter import messagebox
from pythonosc.udp_client import SimpleUDPClient
from serial.tools import list_ports

try:
    from rplidar import RPLidar
except Exception as e:
    raise RuntimeError("rplidar の読み込みに失敗。`pip install rplidar` を実行してください。") from e

APP_TITLE = "RPLIDAR → OSC Sender (pure Tk)"
DEFAULT_OSC_HOST = "127.0.0.1"
DEFAULT_OSC_PORT = 8000
FPS = 10
BAUD = 115200

BG = "#f4f4f4"
FG = "#000000"

class LidarSenderApp:
    def __init__(self, root):
        self.root = root
        root.title(APP_TITLE)
        root.geometry("620x360")
        root.configure(bg=BG)

        self.running = False
        self.thread = None
        self.lidar = None

        # 上段：設定
        top = tk.Frame(root, bg=BG)
        top.pack(fill="x", padx=10, pady=10)

        row1 = tk.Frame(top, bg=BG); row1.pack(fill="x", pady=4)
        tk.Label(row1, text="Serial Port:", width=12, bg=BG, fg=FG).pack(side="left")
        self.port_var = tk.StringVar()
        self.port_menu = tk.OptionMenu(row1, self.port_var, [])
        self.port_menu.configure(bg="white")
        self.port_menu.pack(side="left", padx=6)
        tk.Button(row1, text="Refresh", command=self.refresh_ports).pack(side="left", padx=6)

        row2 = tk.Frame(top, bg=BG); row2.pack(fill="x", pady=4)
        tk.Label(row2, text="OSC Host:", width=12, bg=BG, fg=FG).pack(side="left")
        self.host_var = tk.StringVar(value=DEFAULT_OSC_HOST)
        tk.Entry(row2, textvariable=self.host_var, width=18).pack(side="left", padx=6)
        tk.Label(row2, text="OSC Port:", bg=BG, fg=FG).pack(side="left", padx=(12,4))
        self.osc_port_var = tk.StringVar(value=str(DEFAULT_OSC_PORT))
        tk.Entry(row2, textvariable=self.osc_port_var, width=8).pack(side="left")

        row3 = tk.Frame(top, bg=BG); row3.pack(fill="x", pady=8)
        self.start_btn = tk.Button(row3, text="Start", command=self.start)
        self.stop_btn  = tk.Button(row3, text="Stop",  command=self.stop, state="disabled")
        self.start_btn.pack(side="left")
        self.stop_btn.pack(side="left", padx=8)

        # ログ
        log_frame = tk.LabelFrame(root, text="Status", bg=BG, fg=FG)
        log_frame.pack(fill="both", expand=True, padx=10, pady=(0,10))
        self.log_text = tk.Text(log_frame, height=10, bg="white", fg="black")
        self.log_text.pack(fill="both", expand=True, padx=6, pady=6)

        self.refresh_ports()
        self.log(f"[INFO] UI initialized. Python={sys.version.split()[0]}, Tk={root.tk.eval('info patchlevel')}")
        root.protocol("WM_DELETE_WINDOW", self.on_close)

    def _set_optionmenu_items(self, menu_widget, var, items):
        menu = menu_widget["menu"]
        menu.delete(0, "end")
        for it in items:
            menu.add_command(label=it, command=lambda v=it: var.set(v))
        if items:
            var.set(items[0])
        else:
            var.set("")

    def log(self, s):
        self.log_text.insert("end", s + "\n")
        self.log_text.see("end")

    def refresh_ports(self):
        items = [p.device for p in list_ports.comports()]
        self._set_optionmenu_items(self.port_menu, self.port_var, items)
        self.log(f"[INFO] Found ports: {items if items else 'None'}")

    def start(self):
        if self.running: return
        port = self.port_var.get()
        if not port:
            messagebox.showerror("Error", "シリアルポートが選択されていません。"); return
        try:
            osc_port = int(self.osc_port_var.get())
        except ValueError:
            messagebox.showerror("Error", "OSCポート番号が不正です。"); return
        host = (self.host_var.get() or DEFAULT_OSC_HOST).strip()

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
        scan_data = [0.0]*360
        last = time.time()

        try:
            client = SimpleUDPClient(host, osc_port)
            self.lidar = RPLidar(serial_port, baudrate=BAUD, timeout=3)
            self.log("[INFO] Connected to RPLIDAR.")

            for _, _, angle, distance in self.lidar.iter_measurments():
                if not self.running: break
                scan_data[int(angle) % 360] = float(distance)
                now = time.time()
                if now - last > 1.0 / FPS:
                    for start in (0, 120, 240):
                        client.send_message("/rplidar/scan", [start] + scan_data[start:start+120])
                    last = now

        except Exception as e:
            self.log(f"[ERROR] {e}")
            try: messagebox.showerror("Error", str(e))
            except Exception: pass
        finally:
            try:
                if self.lidar:
                    self.lidar.stop(); self.lidar.disconnect()
            except Exception: pass
            self.lidar = None
            self.running = False
            self.stop_btn.configure(state="disabled")
            self.start_btn.configure(state="normal")
            self.log("[INFO] Worker terminated.")

    def on_close(self):
        self.stop()
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=1.0)
        self.root.destroy()

def main():
    root = tk.Tk()
    app = LidarSenderApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
