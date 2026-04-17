# 📚 RTKA v2 - Tutorial & Experiments

**Comprehensive Robotics Tutorial Book**  
From Basic Electronics to Advanced AI & Computer Vision

---

## 🎯 Overview

Folder **Experiments** berisi **tutorial lengkap** untuk RTKA Trainer Kit v2 dalam format hands-on experiments. Tutorial ini dirancang bertingkat dari pemula hingga level kompetisi robotika.

**Total Programs**: 38+ comprehensive examples  
**Duration**: 3-6 bulan pembelajaran  
**Format**: Self-contained Python programs dengan dokumentasi lengkap

---

## 📖 Struktur Tutorial

```
Experiments/
├── 01_GPIO/                # Level 1: Bab 1 - Dasar GPIO
├── 02_Output/              # Level 1: Bab 2 - Output Dasar
├── 03_Input/               # Level 1: Bab 3 - Input Dasar
├── 04_Buzzer/              # Level 1: Bab 4 - Buzzer & Audio Indicator
├── 05_Sensor/              # Level 1: Bab 5 - Sensor Dasar
├── 06_Mini_Project_Beginner/ # Level 1: Bab 6 - Mini Project
├── L2-Intermediate/        # Level 2: IoT & Networking (Bab 7-12)
└── L3-Advanced/            # Level 3: AI & Computer Vision (Bab 14-20)
```

> Level 1 (Beginner) sudah tersedia untuk mencakup dasar GPIO, LED, input, buzzer, dan sensor.

---

## 📚 Level 2 - INTERMEDIATE (Bab 7-12)

**Fokus**: IoT, Networking, Remote Control  
**Prasyarat**: Dasar Python & Linux  
**Durasi**: 4-6 minggu

### 📂 Struktur

```
L2-Intermediate/
├── 07_Motor/                  # Motor Control & PWM
│   ├── 01_motor_dc_basic.py
│   ├── 02_motor_driver_l298n.py
│   ├── 03_pwm_speed_control.py
│   └── 04_motor_calibration.py
│
├── 08_Navigasi/               # Robot Navigation
│   ├── 01_ultrasonic_obstacle.py
│   ├── 02_avoidance_logic.py
│   └── 03_state_machine_robot.py
│
├── 09_Networking/             # Networking Basics
│   ├── 01_network_basics.py
│   ├── 02_wifi_access.py
│   ├── 03_flask_webserver.py
│   └── 04_gpio_web_control.py
│
├── 10_IoT/                    # Internet of Things
│   ├── 01_mqtt_iot_complete.py
│   └── 02_cloud_data_logging.py
│
├── 11_Remote/                 # Remote Control & Monitoring
│   ├── 01_web_dashboard_realtime.py
│   └── 02_data_logging_dashboard.py
│
└── 12_Mini_Projects/          # Integrated Projects
    ├── 01_autonomous_robot.py
    ├── 02_web_controlled_robot.py
    └── 03_iot_monitoring_robot.py
```

### 🎓 Skills Learned (Level 2)

✅ DC Motor control dengan L298N driver  
✅ PWM untuk speed control  
✅ Obstacle avoidance dengan ultrasonik  
✅ State machine programming  
✅ Flask web server development  
✅ MQTT IoT protocols  
✅ WebSocket real-time communication  
✅ SQLite database logging  
✅ Responsive web dashboards  

**Total Programs**: 18 comprehensive examples

**README Detail**: [L2-Intermediate/README.md](L2-Intermediate/README.md)

---

## 🚀 Level 3 - ADVANCED (Bab 14-20)

**Fokus**: AI, Computer Vision, Intelligent Systems  
**Target**: Competition-ready robots  
**Prasyarat**: Level 1 & Level 2  
**Durasi**: 8-12 minggu

### 📂 Struktur

```
L3-Advanced/
├── 14_AI_Introduction/              # AI Fundamentals
│   ├── 01_ai_concepts.py           # AI vs ML vs DL theory
│   └── 02_tflite_inference.py      # TensorFlow Lite inference
│
├── 15_Computer_Vision/              # OpenCV Basics
│   └── 01_camera_opencv.py         # Camera setup & operations
│
├── 16_Face_Detection/               # Face Detection
│   └── 01_face_detection_complete.py  # Haar + DNN methods
│
├── 17_Object_Detection/             # Object Recognition
│   └── 01_mobilenet_ssd.py         # 80+ objects detection
│
├── 18_Gesture_Recognition/          # Hand Tracking
│   └── 01_hand_tracking_mediapipe.py  # MediaPipe gestures
│
├── 19_Intelligent_Systems/          # Autonomous AI
│   └── 01_autonomous_navigation_ai.py  # Sensor fusion + AI
│
└── 20_Capstone_Projects/            # Final Projects
    └── 01_smart_security_robot.py  # Complete AI security system
```

### 🎓 Skills Learned (Level 3)

✅ AI/ML concepts & Edge AI optimization  
✅ TensorFlow Lite model deployment  
✅ OpenCV computer vision  
✅ Face detection (Haar Cascade & DNN)  
✅ Real-time object detection (80+ classes)  
✅ Hand gesture recognition (MediaPipe)  
✅ Sensor fusion (camera + ultrasonic)  
✅ AI decision making algorithms  
✅ Autonomous navigation systems  
✅ Web-based robot monitoring  

**Total Programs**: 8 comprehensive examples

**README Detail**: [L3-Advanced/README.md](L3-Advanced/README.md)

---

## 🛠️ Hardware Requirements

### Level 2 (Intermediate)
- Raspberry Pi 4/5 (2GB+ RAM)
- DC Motors + L298N Driver
- HC-SR04 Ultrasonic sensor
- Jumper wires & breadboard
- Power supply (7.4V for motors)

### Level 3 (Advanced)
- Raspberry Pi 4/5 (**4GB+ RAM recommended**, 8GB optimal)
- **Pi Camera v2/v3** atau USB Webcam
- Servo motors (for pan/tilt - optional)
- All Level 2 hardware
- MicroSD 32GB+ (for AI models)

---

## ⚙️ Software Installation

### Core Dependencies

```bash
# System packages
sudo apt update
sudo apt install -y python3-pip python3-opencv

# Python packages for ALL Levels
pip3 install gpiozero lgpio opencv-python numpy flask flask-socketio
```

### Level 3 Additional Requirements

```bash
# AI & Computer Vision
pip3 install tflite-runtime mediapipe pillow

# Optional: Full TensorFlow (untuk development)
# pip3 install tensorflow  # Warning: ~1GB download
```

### Quick Setup Script

```bash
# From RTKA-v2 root directory
cd Experiments/L3-Advanced
chmod +x setup_dependencies.sh  # If exists
./setup_dependencies.sh
```

---

## 🚀 Quick Start

### Level 2 - IoT & Networking

```bash
cd Experiments/L2-Intermediate/07_Motor
./01_motor_dc_basic.py
```

**Menu-driven interface** - setiap program memiliki menu interaktif untuk eksplorasi fitur.

### Level 3 - AI & Computer Vision

```bash
cd Experiments/L3-Advanced/17_Object_Detection
./01_mobilenet_ssd.py
```

Program akan **auto-download models** saat pertama kali dijalankan.

---

## 📊 Learning Progression

```
┌─────────────────────────────────────────────────────────┐
│  START HERE                                              │
│  ↓                                                       │
│  Level 1 (Basic)                                         │
│  └─ GPIO, LED, Input, Buzzer, Ultrasonic, Mini Project  │
│     25+ programs                                         │
│                                                          │
│  Level 2 (Intermediate) ← YOU ARE HERE                  │
│  └─ IoT, Networking, Web Control                        │
│     ✅ 18 programs ready                                 │
│     Duration: 4-6 weeks                                 │
│                                                          │
│  Level 3 (Advanced)                                     │
│  └─ AI, Computer Vision, Autonomous Systems             │
│     ✅ 8 comprehensive programs ready                    │
│     Duration: 8-12 weeks                                │
│                                                          │
│  COMPLETION                                             │
│  └─ Ready for robotics competitions! 🏆                 │
└─────────────────────────────────────────────────────────┘
```

**Recommended Learning Path**:
1. ✅ **Week 1-2**: L2 Bab 7-8 (Motor & Navigation)
2. ✅ **Week 3-4**: L2 Bab 9-10 (Networking & IoT)
3. ✅ **Week 5-6**: L2 Bab 11-12 (Remote Control & Projects)
4. 🚀 **Week 7-10**: L3 Bab 14-17 (AI & Computer Vision)
5. 🏆 **Week 11-14**: L3 Bab 18-20 (Gestures & Capstone)

---

## 📝 Program Features

Setiap program dirancang dengan:

### ✅ Self-Contained
- Tidak memerlukan dependencies eksternal (kecuali library standard)
- Auto-download models jika diperlukan
- Simulation mode jika hardware tidak tersedia

### ✅ Educational
- Detailed comments dalam bahasa Indonesia & English
- Theory explanations dalam program
- Step-by-step learning approach

### ✅ Interactive
- Menu-based interface
- Real-time feedback
- Save/export capabilities

### ✅ Production-Ready
- Error handling lengkap
- Performance monitoring
- Logging & debugging features

---

## 🎯 Program Naming Convention

```
<nomor>_<nama_descriptive>.py
```

**Contoh**:
- `01_motor_dc_basic.py` - Program pertama, motor DC basic
- `02_mobilenet_ssd.py` - Program kedua, MobileNet SSD detection
- `01_smart_security_robot.py` - Capstone project

---

## 🔧 Troubleshooting

### GPIO Errors

```bash
# Pastikan lgpio terinstall (untuk Raspberry Pi 5)
pip3 install lgpio

# Test GPIO
python3 -c "from gpiozero import LED; LED(17).blink()"
```

### Camera Not Working

```bash
# Enable camera
sudo raspi-config
# → Interface Options → Camera → Enable

# Test camera
libcamera-hello

# For USB webcam
ls /dev/video*
```

### Import Errors

```bash
# Reinstall dependencies
pip3 install --force-reinstall opencv-python numpy

# Check Python version (must be 3.7+)
python3 --version
```

### Model Download Issues

Jika auto-download gagal, download manual:

**MobileNet SSD** (Bab 17):
```bash
cd Experiments/L3-Advanced/17_Object_Detection
mkdir -p models
cd models
wget https://storage.googleapis.com/download.tensorflow.org/models/tflite/coco_ssd_mobilenet_v1_1.0_quant_2018_06_29.zip
unzip coco_ssd_mobilenet_v1_1.0_quant_2018_06_29.zip
```

---

## 📖 Additional Resources

### Documentation
- **Main Project**: [/README.md](../README.md)
- **Level 2 Guide**: [L2-Intermediate/README.md](L2-Intermediate/README.md)
- **Level 3 Guide**: [L3-Advanced/README.md](L3-Advanced/README.md)

### Code References
- **Core Modules**: `/modules/` - Reusable library code
- **TrainerKit Examples**: `/TrainerKit/` - Alternative examples

### External Learning
- [OpenCV Python Tutorials](https://docs.opencv.org/4.x/d6/d00/tutorial_py_root.html)
- [TensorFlow Lite Guide](https://www.tensorflow.org/lite/guide)
- [MediaPipe Solutions](https://google.github.io/mediapipe/)
- [gpiozero Documentation](https://gpiozero.readthedocs.io/)

---

## 🤝 Contributing

Punya ide untuk program baru? Ingin improve existing examples?

1. Fork repository ini
2. Buat program di folder yang sesuai
3. Follow naming convention & code style
4. Submit pull request dengan deskripsi jelas

---

## 📜 License

Educational use - RTKA v2 Project  
© 2025 RTKA Development Team

---

## 🎓 Learning Tips

### For Beginners (Level 2)
1. ⏱️ **Jangan terburu-buru** - pahami setiap konsep sebelum lanjut
2. 🔧 **Test hardware** - pastikan semua komponen bekerja
3. 📝 **Modify code** - eksperimen dengan parameter berbeda
4. 🐛 **Debug actively** - error adalah bagian dari pembelajaran

### For Advanced (Level 3)
1. 🎯 **Understand theory first** - baca dokumentasi AI/CV concepts
2. 📊 **Monitor performance** - FPS, inference time, memory usage
3. 🔬 **Experiment with models** - coba confidence threshold berbeda
4. 🚀 **Build your own** - kombinasikan berbagai teknik untuk project unik

---

## 📞 Support

**Issues?** Open issue di repository utama  
**Questions?** Check troubleshooting section atau baca README per-level

---

## 🏆 Success Stories

Setelah menyelesaikan tutorial ini, Anda akan mampu:

✅ Build autonomous robots dari zero  
✅ Implement AI vision systems  
✅ Create IoT-enabled devices  
✅ Compete in robotics competitions  
✅ Develop commercial robotics products  

**Happy Learning & Building! 🤖🚀**

---

*Last Updated: February 2026*  
*Version: 2.0*
