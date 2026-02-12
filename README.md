# RTKA v2 - Robot Training Kit AI

![Version](https://img.shields.io/badge/version-2.0-blue.svg)
![Python](https://img.shields.io/badge/python-3.7+-green.svg)
![Platform](https://img.shields.io/badge/platform-Raspberry%20Pi-red.svg)

**RTKA v2** adalah platform robotika pendidikan berbasis Raspberry Pi dengan kemampuan AI, dirancang untuk pembelajaran robotika, computer vision, dan autonomous navigation.

---

## 📋 Daftar Isi

- [Overview](#-overview)
- [Fitur Utama](#-fitur-utama)
- [Arsitektur Sistem](#-arsitektur-sistem)
- [Hardware Requirements](#-hardware-requirements)
- [Instalasi](#-instalasi)
- [Konfigurasi](#-konfigurasi)
- [Penggunaan](#-penggunaan)
- [API Documentation](#-api-documentation)
- [TrainerKit](#-trainerkit)
- [Troubleshooting](#-troubleshooting)
- [Kontribusi](#-kontribusi)

---

## 🎯 Overview

RTKA v2 adalah robot 4WD (4-Wheel Drive) yang dilengkapi dengan:
- **Kamera** untuk video streaming dan computer vision
- **Sensor ultrasonik** untuk deteksi jarak
- **Line follower** dengan 5 channel IR sensor
- **Servo pan/tilt** untuk kontrol kamera
- **AI Processing** menggunakan TensorFlow Lite dan MediaPipe
- **WiFi Manager** untuk koneksi network otomatis
- **Web-based controller** dengan WebSocket real-time

---

## ✨ Fitur Utama

### Mode Operasi

| Mode | Deskripsi | Teknologi |
|------|-----------|-----------|
| **Manual Control** | Kendali manual via joystick web | WebSocket |
| **Auto Pilot** | Navigasi otomatis dengan obstacle avoidance | Ultrasonic + AI |
| **Line Follower** | Mengikuti garis hitam | 5-channel IR sensor |
| **Color Tracking** | Tracking objek berdasarkan warna | OpenCV HSV |
| **Color Following** | Mengikuti objek berwarna | Computer Vision |
| **Face Detection** | Deteksi wajah manusia | MediaPipe Face Detection |
| **Face Tracking** | Tracking wajah dengan servo | MediaPipe + Servo Control |
| **Object Detection** | Deteksi 11 jenis objek | TFLite SSD MobileNet v2 |
| **Gesture Recognition** | Kontrol dengan gesture tangan | MediaPipe Hands |
| **QR Code Scanner** | Membaca QR code | Pyzbar |

### Kemampuan AI

- **Object Detection**: person, car, motorcycle, bottle, cup, chair, couch, potted plant, dining table, cell phone
- **Face Detection**: Real-time face detection dengan confidence score
- **Hand Gesture**: Deteksi gesture untuk kontrol robot
- **Color Recognition**: HSV-based color filtering (red, green, blue, yellow, orange, purple, pink, cyan, black, white)

---

## 🏗️ Arsitektur Sistem

```
┌─────────────────────────────────────────────────────────────┐
│                        Client Layer                          │
│            (Web Browser / Mobile App)                        │
└────────────────────┬────────────────────────────────────────┘
                     │ HTTP/WebSocket
┌────────────────────▼────────────────────────────────────────┐
│                    Application Layer                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  Manager     │  │   Main App   │  │  NetPortal   │      │
│  │  (Port 5000) │  │  (Port 8000) │  │  (Port 80)   │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└────────────────────┬────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────┐
│                    Hardware Layer                            │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐       │
│  │  Motors  │ │  Camera  │ │ Sensors  │ │  Extras  │       │
│  │  4WD     │ │  +AI     │ │ IR/Ultra │ │ Servo/LED│       │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘       │
└─────────────────────────────────────────────────────────────┘
```

### Komponen Software

#### Core Modules

**[main.py](main.py)** - Server utama
- FastAPI application server
- WebSocket endpoints untuk setiap mode
- Video streaming MJPEG
- Async hardware control
- Error logging & crash recovery

**[manager.py](manager.py)** - Service manager
- Start/stop robot service
- System reboot control
- Process management
- Health monitoring

**[config.py](config.py)** - Konfigurasi hardware
- GPIO pin assignments
- Camera settings
- Network configuration
- Default parameters

#### Hardware Drivers

**[modules/motor.py](modules/motor.py)**
- 4WD motor control
- PWM speed mapping (min 40%)
- Differential steering
- Speed limiting

**[modules/camera.py](modules/camera.py)**
- Video capture (V4L2)
- Frame processing
- AI integration
- Adaptive frame skipping

**[modules/sensors.py](modules/sensors.py)**
- HC-SR04 ultrasonic sensor
- BFD-1000 line sensors (5 channel)
- Emergency/obstacle sensors
- Digital input handling

**[modules/extras.py](modules/extras.py)**
- Hardware PWM servo control
- Buzzer dengan melody player
- RGB LED indicators
- Auto PWM chip detection

**[modules/ai.py](modules/ai.py)**
- TensorFlow Lite inference
- MediaPipe face/hand detection
- Color tracking algorithms
- QR code decoding
- Multi-mode AI processing

**[modules/config_loader.py](modules/config_loader.py)**
- Dual-config system (default/user)
- JSON persistence
- Runtime pin remapping
- Hot-reload capability

---

## 🔧 Hardware Requirements

### Komponen Utama

| Komponen | Spesifikasi | Quantity |
|----------|-------------|----------|
| Raspberry Pi | Model 4B/5 (2GB+ RAM) | 1 |
| Motor DC | 6V geared motor | 4 |
| Motor Driver | L298N atau TB6612FNG | 2 |
| Camera | Pi Camera atau USB Camera | 1 |
| Servo | SG90 (Pan/Tilt) | 2 |
| Ultrasonic | HC-SR04 | 1 |
| Line Sensor | BFD-1000 (5 channel IR) | 1 |
| Buzzer | Active/Passive Buzzer | 1 |
| LED | RGB LED | 3 |
| Power Supply | 7.4V LiPo 2S atau 6xAA | 1 |

### GPIO Pin Mapping

#### Motor Pins (4WD Configuration)

```
Front Left  (FL): GPIO 17 (FWD), GPIO 27 (BWD)
Rear Left   (RL): GPIO 22 (FWD), GPIO 23 (BWD)
Front Right (FR): GPIO 10 (FWD), GPIO 25 (BWD)
Rear Right  (RR): GPIO 16 (FWD), GPIO 26 (BWD)
```

#### Servo & Actuators

```
Servo Pan:  GPIO 12 (Hardware PWM Channel 0)
Servo Tilt: GPIO 13 (Hardware PWM Channel 1)
Buzzer:     GPIO 21 (PWM)
```

#### Sensors

```
Ultrasonic HC-SR04:
  - Trigger: GPIO 24
  - Echo:    GPIO 20

Line Follower (BFD-1000):
  - Far Left  (LL): GPIO 4
  - Left      (L):  GPIO 14
  - Middle    (M):  GPIO 15
  - Right     (R):  GPIO 18
  - Far Right (RR): GPIO 11

Emergency Sensors:
  - Near Obstacle: GPIO 19
  - Clap Sensor:   GPIO 0
```

#### Indicators

```
LED Red:    GPIO 7
LED Yellow: GPIO 8
LED Green:  GPIO 1
```

### Wiring Diagram

```
[Raspberry Pi]
    │
    ├─[Motor Driver L/R]─────[4x DC Motors]
    ├─[Camera]
    ├─[Servo Driver]─────────[2x SG90]
    ├─[HC-SR04]
    ├─[BFD-1000 5CH]
    ├─[Buzzer]
    └─[LEDs]
```

**Catatan Penting:**
- Hindari GPIO 2, 3 (I2C), 5, 6, 9 (SPI)
- Gunakan level shifter untuk sensor 5V
- Pisahkan power supply motor dari Raspberry Pi
- Gunakan common ground untuk semua komponen

---

## 💻 Instalasi

### Persiapan Raspberry Pi

1. **Install Raspberry Pi OS (Bookworm recommended)**
   ```bash
   # Update system
   sudo apt update && sudo apt upgrade -y
   ```

2. **Enable Camera & Interfaces**
   ```bash
   sudo raspi-config
   # Interface Options → Camera → Enable
   # Interface Options → I2C → Enable (jika diperlukan)
   ```

3. **Install Dependencies**
   ```bash
   sudo apt install -y python3-pip python3-venv git
   sudo apt install -y network-manager dnsmasq
   ```

### Clone & Setup Project

```bash
# Clone repository
cd ~
git clone https://github.com/your-repo/RTKAv2.git
cd RTKAv2

# Buat virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Python packages
pip install -r TrainerKit/requirements.txt
```

### Install Menggunakan Script Otomatis

```bash
chmod +x install_rtka_rpi.sh
./install_rtka_rpi.sh
```

Script akan:
- Install semua dependencies
- Setup virtual environment
- Konfigurasi GPIO permissions
- Install WiFi Manager service
- Setup systemd services

---

## ⚙️ Konfigurasi

### 1. Konfigurasi Pin (Default)

Edit [config.py](config.py) untuk mengubah pin assignment:

```python
# Motor Settings
PIN_FL_FWD = 17
PIN_FL_BWD = 27
# ... dst
```

### 2. User-Defined Configuration

Buat [user_config.json](user_config.json) untuk override konfigurasi:

```json
{
  "motor": {
    "fl_fwd": 17,
    "fl_bwd": 27,
    "speed_limit": 80
  },
  "camera": {
    "width": 640,
    "height": 480
  },
  "servo": {
    "pan": 12,
    "tilt": 13
  }
}
```

**Switch Mode via API:**
```bash
# Via WebSocket /ws/configSwitch
{
  "cmd": "set_mode",
  "mode": "user"  # atau "default"
}
```

### 3. Network Configuration (NetPortal)

Environment variables untuk WiFi manager ([NetPortal/wifi_manager.py](NetPortal/wifi_manager.py)):

```bash
export RTKA_WIFI_IFACE=wlan0
export RTKA_AP_NAME=EdupiRobo_AP
export RTKA_AP_PASSWORD=edupi888
export RTKA_AP_IPV4=192.168.1.101/24
export RTKA_PORTAL_PORT=80
```

---

## 🚀 Penggunaan

### Menjalankan Robot

#### Metode 1: Manual

```bash
cd ~/RTKAv2
source venv/bin/activate
python main.py
```

#### Metode 2: Via Manager Service

```bash
# Start manager
python manager.py

# Dari client, kirim request:
curl -X POST http://<robot-ip>:5000/ \
  -H "Content-Type: application/json" \
  -d '{"cmd": "command", "mode": "start"}'
```

#### Metode 3: Systemd Service (Recommended)

```bash
# Setup service (jika belum)
sudo systemctl enable rtka-manager.service
sudo systemctl start rtka-manager.service

# Check status
sudo systemctl status rtka-manager.service
```

### Akses Web Interface

1. **Connect ke WiFi robot**: `EdupiRobo_AP` (password: `edupi888`)
2. **Buka browser**: `http://192.168.1.101:8000`
3. **Atau via hostname**: `http://raspberrypi.local:8000`

### Video Stream

```
http://<robot-ip>:8000/video_feed
```

Format: MJPEG stream dengan AI overlay (jika mode aktif)

---

## 📡 API Documentation

### Manager API (Port 5000)

#### POST `/`

**Start Robot:**
```json
{
  "cmd": "command",
  "mode": "start"
}
```

**Stop Robot:**
```json
{
  "cmd": "command",
  "mode": "stop"
}
```

**Reboot System:**
```json
{
  "cmd": "command",
  "mode": "reset"
}
```

### Robot API (Port 8000)

#### WebSocket Endpoints

**1. Manual Control** - `/ws/control`

```json
// Move robot
{
  "cmd": "move",
  "x": 0.0,      // steering (-1.0 to 1.0)
  "y": 0.5,      // throttle (-1.0 to 1.0)
  "speed": 80    // speed limit (0-100%)
}

// Control servo
{
  "cmd": "servo",
  "type": "pan",   // "pan" or "tilt"
  "angle": 90      // 0-180 degrees
}

// Buzzer
{
  "cmd": "buzzer",
  "state": "on"    // "on" or "off"
}

// LED
{
  "cmd": "led",
  "color": "red",  // "red", "yellow", "green"
  "state": "on"    // "on" or "off"
}

// Stop motors
{
  "cmd": "stop"
}
```

**2. Auto Pilot** - `/ws/autoPilot`

```json
{
  "cmd": "toggle",
  "state": true,     // enable/disable
  "speed": 50,       // base speed
  "follow_distance": 30  // target distance (cm)
}
```

**3. Line Follower** - `/ws/lineFollower`

```json
{
  "cmd": "toggle",
  "state": true,
  "speed": 40,
  "kp": 0.8,      // proportional gain
  "ki": 0.0,      // integral gain
  "kd": 0.2       // derivative gain
}
```

**4. Color Tracking** - `/ws/colorTrack`

```json
{
  "cmd": "set_target",
  "color": "red"   // red, green, blue, yellow, etc.
}

{
  "cmd": "toggle",
  "state": true
}
```

**5. Face Tracking** - `/ws/faceTrack`

```json
{
  "cmd": "toggle",
  "state": true
}
```

**6. Object Detection** - `/ws/objectDetect`

```json
{
  "cmd": "toggle",
  "state": true,
  "target": "person"  // opsional, filter objek
}
```

**7. Gesture Control** - `/ws/gestureControl`

```json
{
  "cmd": "toggle",
  "state": true
}
```

**8. Configuration Switch** - `/ws/configSwitch`

```json
// Save config
{
  "cmd": "save_config",
  "config": {
    "motor": { "fl_fwd": 17, ... }
  }
}

// Switch mode
{
  "cmd": "set_mode",
  "mode": "user"  // "user" or "default"
}
```

#### HTTP Endpoints

**GET `/video_feed`**
- Response: MJPEG stream
- Content-Type: `multipart/x-mixed-replace`

**GET `/sensor_data`** (via WebSocket broadcast)
```json
{
  "distance": 25.5,           // cm
  "line_sensors": [0,0,1,0,0], // binary array
  "emergency": false,
  "battery": 7.2              // voltage (jika tersedia)
}
```

---

## 🎓 TrainerKit

Folder [TrainerKit/](TrainerKit) berisi program standalone untuk pembelajaran:

### Program yang Tersedia

| File | Deskripsi | Mode |
|------|-----------|------|
| [auto_pilot.py](TrainerKit/auto_pilot.py) | Navigasi otomatis dengan obstacle avoidance | Autonomous |
| [line_follower.py](TrainerKit/line_follower.py) | PID line following | Sensor-based |
| [color_tracking.py](TrainerKit/color_tracking.py) | Tracking objek berwarna | Vision |
| [color_following.py](TrainerKit/color_following.py) | Mengikuti objek berwarna | Vision + Motion |
| [face_detection.py](TrainerKit/face_detection.py) | Deteksi wajah | AI Vision |
| [face_tracking.py](TrainerKit/face_tracking.py) | Tracking wajah dengan servo | AI + Servo |
| [object_detection.py](TrainerKit/object_detection.py) | Deteksi objek dengan TFLite | AI Vision |
| [gesture.py](TrainerKit/gesture.py) | Deteksi gesture tangan | AI Vision |
| [gesture_command.py](TrainerKit/gesture_command.py) | Kontrol robot dengan gesture | AI + Control |
| [avoid.py](TrainerKit/avoid.py) | Obstacle avoidance | Sensor + Logic |
| [color_detection.py](TrainerKit/color_detection.py) | Color detection & classification | Vision |
| [kiar.py](TrainerKit/kiar.py) | KIAR protocol handler | Protocol |
| [control.py](TrainerKit/control.py) | Basic motor control test | Hardware Test |

### Cara Menggunakan TrainerKit

```bash
cd ~/RTKAv2/TrainerKit
source ../venv/bin/activate

# Jalankan program
python auto_pilot.py
python line_follower.py
# dst...
```

**Catatan:**
- Program TrainerKit berjalan standalone (tidak perlu main.py)
- Cocok untuk pembelajaran step-by-step
- Bisa dimodifikasi untuk eksperimen

---

## 🔍 Troubleshooting

### Masalah Umum

#### 1. Camera tidak terdeteksi

**Solusi:**
```bash
# Check camera
vcgencmd get_camera

# Test manual
raspistill -o test.jpg

# Check OpenCV
python -c "import cv2; print(cv2.VideoCapture(0).read())"
```

#### 2. Motor tidak bergerak

**Check:**
- Power supply motor (minimal 6V 2A)
- Koneksi motor driver
- GPIO permissions: `sudo usermod -a -G gpio $USER`
- Pin mapping di [config.py](config.py)

**Debug mode:**
```python
# Di main.py, set simulation=True
robot_motor = MotorDriver(simulation=True)
```

#### 3. Servo tidak respon

**Check PWM chip:**
```bash
ls /sys/class/pwm/
# Harus ada pwmchip0 atau pwmchip2
```

**Manual test:**
```bash
cd ~/RTKAv2/test
python servo.py
```

#### 4. Import error TFLite

**Install TFLite Runtime:**
```bash
pip install tflite-runtime
# Atau
pip install tensorflow
```

#### 5. WebSocket connection failed

**Check firewall:**
```bash
sudo ufw allow 8000/tcp
sudo ufw allow 5000/tcp
```

**Check service:**
```bash
netstat -tulpn | grep 8000
```

#### 6. GPIO warnings/conflicts

**Reset GPIO:**
```bash
./clean_gpio.sh
```

**Check pin status:**
```bash
cd test
python pin_status_check.py
```

### Log Files

```bash
# Crash log
tail -f ~/RTKAv2/crash_log.txt

# NetPortal log
tail -f ~/RTKAv2/NetPortal/logs/portal.log

# System log
journalctl -u rtka-manager.service -f
```

### Diagnostic Tools

```bash
cd ~/RTKAv2/test

# Test semua pin
python complete_pin_map.py

# Test motor wiring
python motor_wiring_test.py

# Test HC-SR04
python hcsr.py

# Test GPIO status
python gpio_pull_analysis.py
```

---

## 📚 Dependencies

### Python Packages (key libraries)

```
fastapi==0.124.4         # Web framework
uvicorn                  # ASGI server
websockets               # WebSocket support
opencv-python            # Computer vision
mediapipe                # AI hand/face detection
tflite-runtime           # TensorFlow Lite
gpiozero==2.0.1          # GPIO control
lgpio==0.2.2.0           # Low-level GPIO (RPi 5)
rpi-hardware-pwm         # Hardware PWM
pyzbar                   # QR code decoder
numpy                    # Array processing
```

Full list: [TrainerKit/requirements.txt](TrainerKit/requirements.txt)

### System Packages

```bash
sudo apt install -y \
  python3-opencv \
  libatlas-base-dev \
  libhdf5-dev \
  libzbar0 \
  network-manager \
  dnsmasq
```

---

## 📖 Learning Paths

### Beginner

1. **Hardware Setup**
   - Rakit robot sesuai wiring diagram
   - Test motor dengan [test/motor_wiring_test.py](test/motor_wiring_test.py)

2. **Basic Control**
   - Jalankan [TrainerKit/control.py](TrainerKit/control.py)
   - Pelajari manual control via web interface

3. **Sensor Reading**
   - Test sensor dengan [test/hcsr.py](test/hcsr.py)
   - Implementasi line follower

### Intermediate

1. **Computer Vision**
   - Color detection & tracking
   - Face detection
   - QR code scanning

2. **Autonomous Navigation**
   - Auto pilot mode
   - Obstacle avoidance
   - Path planning

3. **AI Integration**
   - Object detection dengan TFLite
   - Gesture recognition
   - Custom AI models

### Advanced

1. **Custom Configuration**
   - Buat custom pin mapping
   - Implementasi dual-config system

2. **API Development**
   - Extend WebSocket endpoints
   - Add custom AI modes

3. **System Integration**
   - Multi-robot coordination
   - Cloud integration
   - Custom sensor fusion

---

## 🤝 Kontribusi

Kontribusi sangat dihargai! Silakan:

1. Fork repository
2. Buat feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add AmazingFeature'`)
4. Push ke branch (`git push origin feature/AmazingFeature`)
5. Buat Pull Request

### Development Guidelines

- Ikuti PEP 8 style guide
- Tambahkan docstring untuk fungsi baru
- Test di Raspberry Pi sebelum PR
- Update dokumentasi jika perlu

---

## 📄 License

Project ini untuk tujuan pendidikan. Silakan gunakan dan modifikasi sesuai kebutuhan.

---

## 🙏 Credits

**Developed by:** Tim Magang RTKA  
**Platform:** Raspberry Pi Foundation  
**AI Models:** Google MediaPipe, TensorFlow Lite  

---

## 📞 Support

- **Issues:** [GitHub Issues](https://github.com/your-repo/RTKAv2/issues)
- **Discussions:** [GitHub Discussions](https://github.com/your-repo/RTKAv2/discussions)
- **Email:** support@rtka.edu

---

## 🔄 Changelog

### v2.0 (Current)
- ✅ Dual configuration system (default/user)
- ✅ NetPortal WiFi manager
- ✅ Multi-mode AI processing
- ✅ WebSocket real-time control
- ✅ RPi 5 support (lgpio)
- ✅ TrainerKit standalone programs
- ✅ Comprehensive error logging

### v1.0
- Basic motor control
- Camera streaming
- Simple obstacle avoidance

---

**Happy Building! 🤖**
