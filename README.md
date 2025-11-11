# 🛰️ RPLIDAR → OSC Sender

Read RPLIDAR A1 via Python and broadcast frames over OSC/UDP.
Ready for Processing / Max / TouchDesigner / Unity. Ships frames as 3×120 samples to avoid UDP buffer overflow.

<p align="left"> <img alt="macOS" src="https://img.shields.io/badge/macOS-12%2B-000?logo=apple&logoColor=white"> <img alt="Python" src="https://img.shields.io/badge/Python-3.9–3.12-3776AB?logo=python&logoColor=white"> <img alt="License" src="https://img.shields.io/badge/License-MIT-05b64e"> </p>


# ✨ Features

- One-click streaming: pick serial port → Start
- Robust OSC: /rplidar/scan with [start, d0..d119] × 3 (millimeters)
- Stable over UDP: avoids oversized datagrams
- Cross-platform: macOS .app, Windows .exe build recipes
- Viewer included: minimal Processing oscP5 sketch

# 🎥 Demo
<video src="docs/demo720.mp4" width="800" autoplay loop muted playsinline></video>


# 📦 Repository Layout
```bash
rplidar-osc-app/
├─ src/
│  └─ rplidar_osc_app.py      # GUI sender (pure Tk version)
├─ receiver/
│  └─ RPLidarOscViewer.pde    # Processing viewer (oscP5)
├─ icons/
│  ├─ app.icns                # mac icon (optional)
│  └─ app.ico                 # win icon (optional)
├─ requirements.txt
└─ README.md
```

# ⚡ Quick Start (Binary)

1. Connect RPLIDAR A1 via USB (motor should spin).
2. Launch app:
   - macOS: RPLidarOSC.app (first run: right-click → Open)
   - Windows: RPLidarOSC.exe
3. Select Serial Port (e.g., /dev/tty.usbserial-0001 or COM3).
4. Confirm OSC Host/Port (default 127.0.0.1:8000).
5. Click Start and receive /rplidar/scan on your target app.

# 🛠️ Run from Source
```bash
git clone <YOUR_REPO_URL> rplidar-osc-app
cd rplidar-osc-app

python -m venv .venv
# mac/linux
source .venv/bin/activate
# windows (powershell)
# .\.venv\Scripts\Activate.ps1

pip install --upgrade pip
pip install -r requirements.txt

python src/rplidar_osc_app.py
```

requirements.txt
```
rplidar
python-osc
pyserial
```
On macOS: if you see Tk deprecation warnings, set export TK_SILENCE_DEPRECATION=1.
If the UI appears blank on some mac setups, use the pure Tk app (included) or install the python.org build (ships Tk 8.6).


# 🧪 Processing Viewer (oscP5)

```java
// Minimal receiver: collects 3 segments into 360 samples
import oscP5.*;
OscP5 osc; float[] scan=new float[360]; boolean hasFrame=false;

void setup(){ size(900,900); osc=new OscP5(this,8000); }
void draw(){
  background(0); translate(width/2,height/2); stroke(60); noFill();
  for(int m=1;m<=3;m++) circle(0,0,240*m); // meter-ish rings
  if(hasFrame){ stroke(255);
    for(int a=0;a<360;a++){
      float d=scan[a]; if(d<100||d>6000) continue;
      float r=(d/1000.0)*120; point(r*cos(radians(a)), r*sin(radians(a)));
    }
  }
}
void oscEvent(OscMessage m){
  if(!m.checkAddrPattern("/rplidar/scan")) return;
  int argc = m.arguments().length; if(argc<2) return;
  int start = (int)m.get(0).floatValue();
  for(int i=1;i<argc;i++){ int idx=start+(i-1); if(0<=idx&&idx<360) scan[idx]=m.get(i).floatValue(); }
  if(start>=240) hasFrame=true;
}
```


# 📡 OSC Message Format

- Address: /rplidar/scan
- Args: [start, d0, d1, …, d119] (mm, float preferred; int ok)
   - start ∈ {0, 120, 240}
   - 3 messages compose one 360-sample frame
- Client hint: reconstruct with scan[start+i] = d[i].

# 🏗️ Build Binaries (PyInstaller)
## macOS (.app)
```bash
pip install pyinstaller
pyinstaller --name "RPLidarOSC" --windowed --onefile \
  --icon icons/app.icns \
  src/rplidar_osc_app.py

# zip for release
cd dist && zip -r RPLidarOSC-mac.zip RPLidarOSC.app
```

# 🚀 Release on GitHub (Manual)

1. Create tag, e.g. v0.1.0 and push it.
2. Releases → Draft a new release.
3. Upload RPLidarOSC-mac.zip and/or RPLidarOSC.exe as assets → Publish.
(Want auto-build on tag push? Add a GitHub Actions workflow. I can provide a ready-to-use YAML.)

# 🧯 Troubleshooting

- No serial port listed → install USB-serial driver (CH340/CP210x), try another cable/port.
- Processing ArrayIndexOutOfBounds → don’t send 360 in one packet; this app uses 3×120.
- Type errors on receive → handle both float/int by typetag or cast robustly.
- mac UI blank → pure Tk app / theme_use("clam") with explicit colors / python.org Python.

🗺️ Roadmap
-  Persist last used serial/host/port
-  FPS & range controls in UI
-  Sector minima streams (/rplidar/min/{left,center,right})
-  GitHub Actions: build & attach assets per tag

# 📜 License
MIT © kikpond15