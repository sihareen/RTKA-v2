# RTKA TrainerKit - Mode Keteng

TrainerKit adalah kumpulan program standalone untuk RTKA dalam mode "keteng" (training kit). Setiap file Python merupakan aplikasi independen yang mendemonstrasikan kemampuan spesifik robot menggunakan computer vision dan AI.

## 📋 Daftar Isi

- [Fitur Utama](#fitur-utama)
- [Persyaratan](#persyaratan)
- [Instalasi](#instalasi)
- [Daftar Program](#daftar-program)
- [Cara Penggunaan](#cara-penggunaan)
- [Konfigurasi](#konfigurasi)
- [Troubleshooting](#troubleshooting)

## 🎯 Fitur Utama

TrainerKit menyediakan berbagai mode operasi robot:

1. **Computer Vision & AI**
   - Face Detection & Tracking
   - Object Detection
   - Gesture Recognition
   - Color Detection & Tracking

2. **Autonomous Navigation**
   - Line Follower (dengan sensor BFD1000)
   - Auto Pilot (berbasis vision)
   - Obstacle Avoidance

3. **Manual Control**
   - Web-based controller
   - Real-time video streaming

## 📦 Persyaratan

### Hardware
- Raspberry Pi (3/4/5)
- Camera module atau USB webcam
- Motor driver (4WD configuration)
- Sensor BFD1000 (untuk line follower)
- Ultrasonic sensor HC-SR04
- Servo motor (Pan/Tilt)
- LED RGB
- Buzzer

### Software
- Python 3.8+
- GPIO access (pigpio/lgpio/gpiozero)
- Lihat `requirements.txt` untuk dependencies lengkap

## 🚀 Instalasi

1. **Install dependencies:**
   ```bash
   cd TrainerKit
   pip install -r requirements.txt
   ```

2. **Pastikan model AI tersedia:**
   - `assets/ssd_mobilenet_v2.tflite` - Object detection
   - `assets/yolov8n-face.pt` - Face detection
   - `assets/yolov8n.pt` - General object detection

3. **Konfigurasi GPIO:**
   Pastikan GPIO daemon berjalan (jika menggunakan pigpio):
   ```bash
   sudo pigpiod
   ```

## 📚 Daftar Program

### 1. **control.py**
Program kontrol manual via web interface dengan video streaming real-time.

**Fitur:**
- WebSocket-based control
- MJPEG video stream
- Motor control (4WD)
- Servo pan/tilt control
- LED RGB control
- Buzzer control

**Jalankan:**
```bash
python3 control.py
```

**Akses:** `http://<ip-robot>:8000`

---

### 2. **line_follower.py**
Robot mengikuti garis menggunakan sensor BFD1000 (5 sensor IR) dengan obstacle avoidance.

**Fitur:**
- 5-sensor line detection (LL, L, M, R, RR)
- Ultrasonic distance sensing
- PID-like control untuk smooth tracking
- Emergency brake pada obstacle
- Web viewer dengan visualisasi sensor

**Pin Configuration:**
- Line sensors: GPIO 4, 14, 15, 18, 21
- Ultrasonic: TRIG=26, ECHO=20

**Jalankan:**
```bash
python3 line_follower.py
```

---

### 3. **auto_pilot.py**
Autonomous navigation menggunakan computer vision (line detection via camera).

**Fitur:**
- Vision-based line detection
- Contour analysis
- Dynamic steering control
- Adjustable speed and gain

**Parameter:**
- BASE_SPEED: 0.30 (default)
- STEER_GAIN: 0.8
- MIN_CONTOUR_AREA: 1200

**Jalankan:**
```bash
python3 auto_pilot.py
```

---

### 4. **face_detection.py**
Deteksi wajah menggunakan MediaPipe dengan filtering dan confidence threshold.

**Fitur:**
- Real-time face detection
- Face ratio filtering (0.02 - 0.60)
- Confidence threshold: 0.75
- Bounding box visualization
- Face count display

**Jalankan:**
```bash
python3 face_detection.py
```

---

### 5. **face_tracking.py**
Robot mengikuti wajah dengan servo pan/tilt dan kontrol motor.

**Fitur:**
- Face detection + tracking
- Servo control untuk centering face
- Motor control untuk menjaga jarak
- Distance estimation
- Auto-stop jika wajah hilang

**Jalankan:**
```bash
python3 face_tracking.py
```

---

### 6. **object_detection.py**
Deteksi objek menggunakan SSD MobileNet v2 TFLite.

**Fitur:**
- Real-time object detection
- Multi-class detection (person, car, bottle, dll)
- Confidence threshold: 0.55
- Area filtering
- Bounding box + label

**Target Objects:**
- 0: person
- 1: bicycle
- 2: car
- 3: motorcycle
- 44: bottle
- 46: cup
- 67: cell phone

**Jalankan:**
```bash
python3 object_detection.py
```

---

### 7. **color_detection.py**
Deteksi warna (merah, hijau, biru, kuning) dengan real-time analysis.

**Fitur:**
- Multi-color detection
- HSV color space analysis
- Contour detection
- Color info display
- Configurable thresholds

**Jalankan:**
```bash
python3 color_detection.py
```

---

### 8. **color_tracking.py**
Kamera tracking objek berwarna menggunakan servo pan/tilt (tanpa motor).

**Fitur:**
- Color-based tracking
- Servo control (pan/tilt)
- Center-lock algorithm
- Smooth servo movement
- Visual feedback

**Jalankan:**
```bash
python3 color_tracking.py
```

---

### 9. **color_following.py**
Robot mengikuti objek berwarna dengan kontrol motor dan servo.

**Fitur:**
- Full body tracking (motor + servo)
- Distance control (area-based)
- Safe zone algorithm
- Auto-centering
- Target area: 12% ± 3%

**Jalankan:**
```bash
python3 color_following.py
```

---

### 10. **gesture_command.py**
Kontrol robot dengan gesture tangan (MediaPipe Hands).

**Fitur:**
- Hand gesture recognition
- Gesture-to-command mapping:
  - ✊ Fist (0 fingers) → STOP
  - ☝️ One (1 finger) → FORWARD
  - ✌️ Peace (2 fingers) → BACKWARD
  - 🖖 Three (3 fingers) → LEFT
  - 🖐️ Four (4 fingers) → RIGHT
- Gesture confirmation (3 frames)
- Auto-stop timeout (0.6s)

**Jalankan:**
```bash
python3 gesture_command.py
```

---

### 11. **gesture.py**
Visualisasi gesture recognition tanpa kontrol motor (demo mode).

**Fitur:**
- Hand detection
- Finger counting
- Gesture visualization
- Real-time feedback

**Jalankan:**
```bash
python3 gesture.py
```

---

### 12. **avoid.py**
Obstacle avoidance menggunakan ultrasonic sensor.

**Fitur:**
- Continuous distance monitoring
- Emergency brake system
- Auto-navigation around obstacles
- Safe distance: 30cm
- Brake distance: 20cm

**Jalankan:**
```bash
python3 avoid.py
```

---

### 13. **kiar.py**
Program khusus untuk demonstrasi atau kalibrasi (KIAR = Kalibrasi Intensif Aktif Robot).

**Jalankan:**
```bash
python3 kiar.py
```

---

## 🎮 Cara Penggunaan

### Menjalankan Program

1. **Pilih program yang ingin dijalankan:**
   ```bash
   cd /home/hreen/Documents/Magang/RTKA-v2/TrainerKit
   python3 <nama_program>.py
   ```

2. **Akses web interface:**
   - Buka browser
   - Masukkan: `http://<IP_RASPBERRY_PI>:8000`
   - Untuk mencari IP: `hostname -I`

3. **Hentikan program:**
   - Tekan `Ctrl+C` di terminal

### Tips Penggunaan

- **Testing tanpa robot:** Beberapa program (face_detection, object_detection, gesture) dapat dijalankan tanpa hardware untuk testing camera
- **Debugging:** Lihat log di terminal untuk informasi real-time
- **Performance:** Untuk performa optimal, gunakan resolusi 640x480
- **Multiple runs:** Hanya jalankan satu program dalam satu waktu untuk menghindari konflik GPIO

## ⚙️ Konfigurasi

### Pin Configuration (Default)

**Motor Pins:**
```python
PIN_FL_FWD = 17  # Front Left Forward
PIN_FL_BWD = 27  # Front Left Backward
PIN_RL_FWD = 22  # Rear Left Forward
PIN_RL_BWD = 23  # Rear Left Backward
PIN_FR_FWD = 24  # Front Right Forward
PIN_FR_BWD = 25  # Front Right Backward
PIN_RR_FWD = 5   # Rear Right Forward
PIN_RR_BWD = 6   # Rear Right Backward
MIN_PWM = 0.40   # Minimum PWM duty cycle
```

**Servo Pins:**
```python
PIN_SERVO_PAN = 12   # Pan servo (horizontal)
PIN_SERVO_TILT = 13  # Tilt servo (vertical)
```

**Sensor Pins:**
```python
PIN_HCSR_TRIG = 26   # Ultrasonic trigger
PIN_HCSR_ECHO = 20   # Ultrasonic echo
PIN_LINE_LL = 4      # Line sensor leftmost
PIN_LINE_L = 14      # Line sensor left
PIN_LINE_M = 15      # Line sensor middle
PIN_LINE_R = 18      # Line sensor right
PIN_LINE_RR = 21     # Line sensor rightmost
```

**Other Pins:**
```python
PIN_BUZZER = 16  # Buzzer
PIN_LED_R = 7    # LED Red
PIN_LED_Y = 8    # LED Yellow
PIN_LED_G = 9    # LED Green
```

### Camera Configuration

```python
VIDEO_SOURCE = -1    # -1 untuk camera pertama, 0, 1, dst untuk camera lain
FRAME_WIDTH = 640    # Resolusi lebar
FRAME_HEIGHT = 480   # Resolusi tinggi
```

### Mengubah Konfigurasi

Edit langsung di bagian `CONFIG INLINE` pada setiap file Python sesuai kebutuhan.

## 🔧 Troubleshooting

### Camera tidak terdeteksi
```bash
# Cek camera devices
ls /dev/video*

# Test camera
raspistill -o test.jpg  # untuk Pi Camera
```

### GPIO Permission Error
```bash
# Tambahkan user ke gpio group
sudo usermod -a -G gpio $USER

# Atau jalankan dengan sudo (tidak disarankan)
sudo python3 <program>.py
```

### Import Error - Module not found
```bash
# Install ulang dependencies
pip install -r requirements.txt

# Atau install satu per satu
pip install opencv-contrib-python mediapipe fastapi uvicorn
```

### Model AI tidak ditemukan
```bash
# Pastikan file model ada di folder assets
ls -l assets/

# Download ulang jika diperlukan
# Model harus ada di TrainerKit/assets/
```

### Motor tidak bergerak
- Cek koneksi motor driver
- Pastikan power supply cukup (motor butuh power terpisah)
- Verifikasi pin configuration
- Test dengan script sederhana

### WebSocket connection failed
```bash
# Cek firewall
sudo ufw allow 8000

# Atau disable firewall sementara
sudo ufw disable

# Pastikan program berjalan
ps aux | grep python
```

### Servo jittering atau tidak stabil
- Cek power supply (servo butuh arus stabil)
- Tambahkan capacitor di power line
- Kurangi PWM frequency jika perlu

## 📝 Catatan Pengembangan

- Setiap program adalah standalone application
- Config inline memudahkan customization per-program
- Tidak ada dependency ke main.py atau manager.py
- Ideal untuk pembelajaran dan eksperimen
- Dapat dimodifikasi sesuai kebutuhan tanpa mempengaruhi program lain

## 📄 Lisensi

Bagian dari proyek RTKA-v2

---

**Dibuat untuk pembelajaran dan pengembangan robot RTKA** 🤖
