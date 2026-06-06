# Raspberry Pi Installation Guide

Person-following detection project (YOLOv8 + Deep SORT + Flask) on a Raspberry Pi running **Ubuntu 24.04 LTS Server (64-bit)**.

> Recommended hardware: Raspberry Pi 4 (4 GB+) or Pi 5. This is a CPU-only PyTorch workload — more RAM and a newer Pi make a real difference. Use a 32 GB+ A1/A2 microSD card (or an SSD via USB for better performance).

---

## Overview

1. Flash Ubuntu 24.04 Server to the SD card with Raspberry Pi Imager, pre-configuring network + SSH.
2. Boot the Pi, find it on the network, and SSH in.
3. Install system dependencies.
4. Copy the project and set up a Python virtual environment.
5. Install the Python requirements and run the app.

---

## 1. Flash Ubuntu 24.04 Server with Raspberry Pi Imager

### 1.1 Install the Imager

Download and install Raspberry Pi Imager on your computer from <https://www.raspberrypi.com/software/>. Insert the microSD card into your computer's card reader.

### 1.2 Choose OS and storage

Open Raspberry Pi Imager and set:

- **Device** — your Pi model (e.g. *Raspberry Pi 4* or *Raspberry Pi 5*).
- **Operating System** — *Choose OS* → *Other general-purpose OS* → *Ubuntu* → **Ubuntu Server 24.04 LTS (64-bit)**.
  - Make sure it says **Server** (not Desktop) and **64-bit**. The 64-bit build is required for PyTorch.
- **Storage** — select your microSD card. *Double-check this is the card and not another drive — it will be erased.*

### 1.3 Pre-configure OS settings (network + SSH)

Click the **gear / Edit Settings** button (or answer "Yes" when asked to apply OS customisation). This bakes in your network and login so the server boots ready to SSH into — no monitor needed.

On the **General** tab:

- **Set hostname**: e.g. `raspberrypi` (you'll reach it at `raspberrypi.local`).
- **Set username and password**: e.g. username `ubuntu` and a password you choose. *Remember these — you'll log in with them.*
- **Configure wireless LAN** (skip if using Ethernet):
  - SSID: your Wi-Fi network name
  - Password: your Wi-Fi password
  - Wireless LAN country: your country code (e.g. `US`, `PH`)
- **Set locale settings**: your time zone and keyboard layout.

On the **Services** tab:

- Enable **SSH** → choose **Use password authentication** (or paste a public key if you prefer key-based login).

Click **Save**.

### 1.4 Write the image

Click **Write**, confirm the erase warning, and wait for it to flash and verify. When it finishes, eject the card.

> **Static IP (optional but handy for a robot):** Ubuntu uses netplan. After first boot you can SSH in and edit `/etc/netplan/50-cloud-init.yaml` to assign a fixed address, then run `sudo netplan apply`. A simpler alternative is to reserve a DHCP lease for the Pi's MAC address in your router.

---

## 2. First boot and connect

1. Put the microSD card into the Raspberry Pi.
2. Connect Ethernet (if not using Wi-Fi) and power it on.
3. Wait **2–3 minutes** for the first boot (it expands the filesystem and applies cloud-init network settings).

### 2.1 Find the Pi and SSH in

From your computer's terminal, using the hostname you set:

```bash
ssh ubuntu@raspberrypi.local
```

If `.local` doesn't resolve, find the Pi's IP from your router's client list (or scan with `nmap -sn 192.168.1.0/24`) and use that:

```bash
ssh ubuntu@192.168.1.42
```

Accept the host fingerprint and enter the password you configured in step 1.3.

### 2.2 Update the system

```bash
sudo apt update && sudo apt full-upgrade -y
sudo reboot
```

Wait a minute, then SSH back in.

---

## 3. Install system dependencies

Ubuntu 24.04 ships with Python 3.12. Install Python tooling plus the system libraries OpenCV needs:

```bash
sudo apt update
sudo apt install -y \
  python3 python3-pip python3-venv python3-dev \
  build-essential git \
  libgl1 libglib2.0-0 \
  libsm6 libxext6 libxrender1 \
  ffmpeg
```

- `libgl1`, `libglib2.0-0`, `libsm6`, `libxext6`, `libxrender1` — shared libraries `opencv-python` loads at import time (otherwise you get `ImportError: libGL.so.1`).
- `ffmpeg` — lets OpenCV read RTSP/HTTP camera streams and video files.

> **USB webcam check:** plug it in and run `ls /dev/video*`. If a device shows up, the camera (`CAMERA_MODE = "laptop"`, index 0) will work. For an IP camera you only need network access to its RTSP/HTTP URL.

---

## 4. Get the project onto the Pi

Pick whichever fits how the code lives on your machine.

**Option A — clone from git** (if it's in a repo):

```bash
cd ~
git clone <your-repo-url> raspberry
cd raspberry
```

**Option B — copy from your computer with `scp`** (run this on *your computer*, not the Pi). Copy only the source — skip the Windows virtualenv folders (`Lib`, `Scripts`, `Include`, `pyvenv.cfg`), which won't work on Linux:

```bash
scp api.py detect.py requirements.txt yolov8n.pt task.md PROCESS_FLOW_DOCUMENTATION.md \
  ubuntu@raspberrypi.local:~/raspberry/
```

(Create the folder first if needed: `ssh ubuntu@raspberrypi.local "mkdir -p ~/raspberry"`.)

> **Important:** the `Lib/`, `Scripts/`, `Include/`, and `pyvenv.cfg` in the existing folder are a *Windows* virtualenv (Python 3.9, `C:\Program Files\Python39`). They are useless on the Pi and must not be copied or reused. You'll build a fresh Linux virtualenv below.

---

## 5. Create a virtual environment and install

From inside the project folder on the Pi (`~/raspberry`):

```bash
cd ~/raspberry

# create a fresh, Linux-native virtualenv
python3 -m venv .venv

# activate it
source .venv/bin/activate

# upgrade the installers
pip install --upgrade pip setuptools wheel
```

Your prompt should now start with `(.venv)`.

### 5.1 Install PyTorch (CPU build)

The Raspberry Pi has no CUDA GPU, so install the CPU wheels. Installing torch explicitly first avoids pip pulling a wrong/huge variant via `requirements.txt`:

```bash
pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
```

### 5.2 Install the rest of the requirements

```bash
pip install -r requirements.txt
```

`requirements.txt` contains:

```
ultralytics
opencv-python
flask
flask_cors
deep_sort_realtime
torch
torchvision
setuptools<81
```

> This step downloads several hundred MB and compiles some wheels — on a Pi 4 it can take **10–20 minutes**. If `opencv-python` is slow or fails to build, you can substitute the prebuilt headless wheel, which is lighter and fine for this server app:
> ```bash
> pip uninstall -y opencv-python
> pip install opencv-python-headless
> ```

### 5.3 Verify the install

```bash
python -c "import torch, cv2, ultralytics, flask, deep_sort_realtime; print('OK', torch.__version__, cv2.__version__)"
```

If that prints `OK ...` with no errors, you're set. Confirm the model weights are present too:

```bash
ls -lh yolov8n.pt   # ~6.5 MB
```

---

## 6. Configure the camera

Edit the camera settings near the top of `api.py` (and `detect.py`) to match your setup:

```python
CAMERA_MODE = "laptop"   # "laptop" = USB/built-in webcam (index 0)
                         # "ipcam"  = use the IP_CAM_URL below
IP_CAM_URL  = "rtsp://user:pass@192.168.1.16/stream1"
```

- USB webcam on the Pi → keep `CAMERA_MODE = "laptop"`.
- IP / RTSP camera → set `CAMERA_MODE = "ipcam"` and put your stream URL in `IP_CAM_URL`.

```bash
nano ~/raspberry/api.py   # Ctrl-O to save, Ctrl-X to exit
```

---

## 7. Run the project

With the virtualenv active:

```bash
cd ~/raspberry
source .venv/bin/activate

# Flask API (headless) — bind to 0.0.0.0 so other devices can reach it
python api.py --host 0.0.0.0 --port 5000
```

From another machine on the same network, control it via HTTP:

```bash
curl -X POST http://raspberrypi.local:5000/start
curl       http://raspberrypi.local:5000/status
curl -X POST http://raspberrypi.local:5000/stop
```

To run the standalone detector instead (e.g. for testing with a preview window over a desktop session):

```bash
python detect.py --source 0          # USB webcam
python detect.py --source <rtsp-url>  # IP camera
```

The first run downloads/loads the YOLO model and is slower; subsequent runs are quicker.

---

## 8. (Optional) Run automatically on boot with systemd

So the API starts whenever the Pi powers up:

```bash
sudo nano /etc/systemd/system/detect-api.service
```


## Troubleshooting

| Symptom | Fix |
|---|---|
| `ImportError: libGL.so.1` on `import cv2` | Install system libs (step 3), or switch to `opencv-python-headless` (step 5.2). |
| `pip` killed / out of memory during install | Add swap: `sudo fallocate -l 2G /swapfile && sudo chmod 600 /swapfile && sudo mkswap /swapfile && sudo swapon /swapfile`, then retry. |
| `torch` install pulls a GPU/CUDA wheel or fails | Use the CPU index URL in step 5.1 *before* `pip install -r requirements.txt`. |
| Can't open RTSP stream | Confirm `ffmpeg` is installed (step 3) and the Pi can reach the camera: `ping <camera-ip>`. Verify the exact URL in VLC first. |
| `ssh: raspberrypi.local` not found | Use the Pi's IP address from your router instead; mDNS isn't always available. |
| Webcam not detected | `ls /dev/video*` should list a device; check the USB connection and `dmesg | tail`. |
| Slow / low FPS | Expected on a Pi for `yolov8n` on CPU. Lower the camera resolution, or run detection on every Nth frame. |

---

## Quick reference (all commands, in order)

```bash
# on the Pi, after first SSH login
sudo apt update && sudo apt full-upgrade -y && sudo reboot
# (reconnect)
sudo apt install -y python3 python3-pip python3-venv python3-dev \
  build-essential git libgl1 libglib2.0-0 libsm6 libxext6 libxrender1 ffmpeg

cd ~/raspberry                       # after cloning/scp-ing the project here
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip setuptools wheel
pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
pip install -r requirements.txt
python -c "import torch, cv2, ultralytics; print('OK')"
python api.py --host 0.0.0.0 --port 5000
```
