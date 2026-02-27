# Bab 12: Mini Projects - Integrated Robot Systems

Tiga proyek lengkap yang mengintegrasikan semua pembelajaran dari Bab 1-11.

## 🎯 Overview

Setiap project mengkombinasikan:
- ✅ Motor control & navigation (Bab 7-8)
- ✅ Networking & web interface (Bab 9)
- ✅ IoT & cloud connectivity (Bab 10)
- ✅ Remote monitoring & logging (Bab 11)

## 📚 Projects

### Project 1: Autonomous Obstacle Avoidance Robot
**File**: `01_autonomous_robot.py`

Robot otonom yang bisa navigate dan avoid obstacles secara mandiri.

#### Features:
- 🤖 **State Machine**: Clean decision-making logic
- 👁️ **Multi-zone Detection**: Emergency stop, slow down, safe zones
- 🧠 **Smart Navigation**: Scan environment untuk find best path
- 📊 **Statistics Tracking**: Real-time performance metrics
- 🔊 **Audio/Visual Alerts**: LED & buzzer warnings
- 🛡️ **Safety Features**: Emergency stop, collision prevention

#### State Machine:
```
IDLE → MOVING_FORWARD → SLOWING_DOWN → OBSTACLE_DETECTED
         ↑                                    ↓
         └── TURNING ← BACKING_UP ←──────────┘
```

#### Configuration:
```python
STOP_DISTANCE = 15 cm    # Emergency stop
SLOW_DISTANCE = 30 cm    # Start slowing
SAFE_DISTANCE = 50 cm    # Full speed OK
NORMAL_SPEED = 0.7       # 70% speed
TURN_DURATION = 0.8s     # ~90 degree turn
```

#### Run Modes:
1. **Timed Mode**: Run for specific duration (30s)
2. **Continuous**: Run until Ctrl+C
3. **Test Mode**: Sensor diagnostics

#### Usage:
```bash
./01_autonomous_robot.py

# Select:
# 1 = Run 30 seconds autonomous
# 2 = Run continuous
# 3 = Test sensors
```

#### Statistics:
- Total distance checks
- Obstacles avoided
- Turns made
- Backup count
- Average check rate

---

### Project 2: Web-Controlled Robot
**File**: `02_web_controlled_robot.py`

Full-featured web control dengan real-time monitoring dan route recording.

#### Features:
- 🌐 **Web Interface**: Modern responsive dashboard
- 🎮 **Multiple Control**: Touch, keyboard, web buttons
- 📹 **Camera Ready**: Placeholder untuk Pi Camera
- 📍 **Route Recording**: Record & playback movements
- 🔌 **WebSocket**: Real-time bidirectional communication
- 📱 **Mobile Optimized**: Touch-friendly controls

#### Control Methods:
1. **Web Buttons**: Touch/click joystick interface
2. **Keyboard**: WASD or Arrow keys
3. **Speed Control**: Slider 0-100%

#### Route Recording:
```
1. Click "Start Recording"
2. Drive robot (web/keyboard)
3. Click "Stop Recording"
4. Click "Play Route" to replay

Recorded:
- Direction (forward/backward/left/right)
- Speed (0.0 - 1.0)
- Duration (seconds)
```

#### Technology Stack:
- **Backend**: Flask + Flask-SocketIO
- **Frontend**: HTML5 + JavaScript + CSS3
- **Protocol**: WebSocket (Socket.io)
- **Charts**: Real-time updates

#### Usage:
```bash
./02_web_controlled_robot.py

# Open browser:
http://localhost:5000

# From smartphone (same WiFi):
http://[RPI_IP]:5000
```

#### Interface Features:
- Virtual joystick (5 directions)
- Speed slider
- LED toggle
- Buzzer honk
- Distance sensor display
- Route list viewer
- Connection status

---

### Project 3: IoT Monitoring Robot
**File**: `03_iot_monitoring_robot.py`

Robot dengan full IoT integration, cloud connectivity, dan monitoring dashboard.

#### Features:
- ☁️ **MQTT Cloud**: Connect to broker (HiveMQ, Eclipse, EMQX)
- 📡 **Telemetry**: Real-time data publishing
- 📥 **Remote Commands**: Control via MQTT from anywhere
- 💾 **Data Logging**: SQLite untuk historical data
- 🚨 **Alert System**: Automatic alerts (obstacles, low battery)
- 📊 **Monitoring Dashboard**: Web-based analytics

#### MQTT Topics:
```
rtka/[DEVICE_ID]/telemetry  → Sensor data (publish)
rtka/[DEVICE_ID]/command    → Control commands (subscribe)
rtka/[DEVICE_ID]/status     → Device status (publish)
rtka/[DEVICE_ID]/alert      → Alert messages (publish)
```

#### Telemetry Data:
```json
{
  "device_id": "rtka_robot_raspberrypi",
  "timestamp": "2024-01-15T10:30:45",
  "distance_cm": 45.3,
  "mode": "moving_forward",
  "battery_level": 85,
  "uptime": 1234,
  "commands_received": 5,
  "telemetry_sent": 247
}
```

#### Remote Commands:
- `forward` - Move forward
- `backward` - Move backward
- `left` - Turn left
- `right` - Turn right
- `stop` - Stop motors
- `beep` - Activate buzzer
- `status` - Request status update
- `scan` - Trigger sensor scan

#### Database Schema:
```sql
-- Telemetry storage
telemetry: timestamp, distance, state, battery, cpu_temp, uptime

-- Command history
commands: timestamp, command, source, executed

-- Alerts
alerts: timestamp, type, message, severity
```

#### Usage:

**Mode 1: Run IoT Robot**
```bash
./03_iot_monitoring_robot.py
# Select: 1

# Robot connects to MQTT broker
# Publishes telemetry every 5 seconds
# Listens for commands
```

**Mode 2: Monitoring Dashboard**
```bash
./03_iot_monitoring_robot.py
# Select: 2

# Web dashboard: http://localhost:8080
# View statistics, telemetry, alerts
```

**Mode 3: Send Remote Command**
```bash
./03_iot_monitoring_robot.py
# Select: 4

# Enter command: forward
# Command sent via MQTT to robot
```

**External MQTT Client:**
```bash
# Subscribe to telemetry
mosquitto_sub -h broker.hivemq.com -t 'rtka/+/telemetry' -v

# Send command
mosquitto_pub -h broker.hivemq.com \
  -t 'rtka/rtka_robot_raspberrypi/command' \
  -m '{"command":"forward"}'
```

#### Alert Conditions:
- Distance < 15cm → Obstacle warning
- Battery < 20% → Low battery warning
- Connection lost → Offline alert

---

## 🔧 Hardware Requirements

All projects menggunakan hardware yang sama:

| Component | GPIO Pins | Quantity |
|-----------|-----------|----------|
| Motor DC (Left) | GPIO 22, 27 | 2 |
| Motor DC (Right) | GPIO 17, 18 | 2 |
| Ultrasonic Trigger | GPIO 26 | 1 |
| Ultrasonic Echo | GPIO 20 | 1 |
| LED Status | GPIO 7 | 1 |
| Buzzer | GPIO 4 | 1 |

**Additional:**
- L298N motor driver
- Power supply (6-12V untuk motor)
- WiFi connection (untuk web/IoT projects)

## 📦 Software Requirements

### Project 1 (Autonomous)
```bash
# Hanya gpiozero
pip3 install gpiozero lgpio
```

### Project 2 (Web Control)
```bash
# WebSocket support
pip3 install flask flask-socketio python-socketio simple-websocket
```

### Project 3 (IoT)
```bash
# MQTT support
pip3 install paho-mqtt flask requests

# MQTT broker (optional, untuk local testing)
sudo apt install mosquitto mosquitto-clients
```

## 🎓 Learning Progression

### Beginner → Intermediate → Advanced

**Week 1-2: Autonomous Robot**
- State machine concepts
- Sensor-based decision making
- Navigation algorithms
- Performance optimization

**Week 3-4: Web Control**
- Web server setup (Flask)
- WebSocket programming
- Frontend development
- Mobile-responsive design

**Week 5-6: IoT Integration**
- MQTT protocol
- Cloud connectivity
- Data analytics
- Remote monitoring

## 🚀 Usage Scenarios

### Scenario 1: Warehouse Patrol
```bash
# Deploy autonomous robot
./01_autonomous_robot.py
# Mode: Continuous

# Robot patrols area
# Avoids obstacles automatically
# Reports statistics
```

### Scenario 2: Remote Inspection
```bash
# Control from distance
./02_web_controlled_robot.py

# Access from smartphone
# Navigate using touch controls
# Record inspection route
# Replay route for verification
```

### Scenario 3: Smart Home Robot
```bash
# IoT-enabled robot
./03_iot_monitoring_robot.py

# Cloud monitoring from anywhere
# Send commands via MQTT
# Receive alerts (obstacles, battery)
# View historical data
```

## 📊 Performance Comparison

| Feature | Autonomous | Web Control | IoT Monitoring |
|---------|-----------|-------------|----------------|
| Autonomy | ✅ Full | ❌ Manual | ⚠️ Hybrid |
| Control Range | N/A | Same WiFi | 🌍 Global |
| Real-time | ✅ Yes | ✅ Yes | ⚠️ 5s delay |
| Data Storage | ❌ No | ❌ No | ✅ SQLite |
| Internet Needed | ❌ No | ❌ No | ✅ Yes |
| Complexity | ⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ |

## 🔬 Experiments & Extensions

### Experiment 1: Optimize Navigation
```python
# Modify 01_autonomous_robot.py
# Test different parameters:
Config.STOP_DISTANCE = 10  # vs 15 vs 20
Config.TURN_DURATION = 0.6  # vs 0.8 vs 1.0

# Measure:
# - Obstacles avoided
# - Smooth navigation
# - Speed vs safety tradeoff
```

### Experiment 2: Multi-user Control
```python
# Modify 02_web_controlled_robot.py
# Add user identification
# Show active users
# Lock controls when in use
```

### Experiment 3: Predictive Maintenance
```python
# Modify 03_iot_monitoring_robot.py
# Track motor usage
# Predict battery life
# Schedule maintenance alerts
```

## 🐛 Troubleshooting

### Autonomous Robot Issues

**Problem**: Robot tidak bergerak
```bash
# Test motor independently
python3 -c "from gpiozero import Motor; m = Motor(22,27); m.forward(); input()"
```

**Problem**: Sensor readings erratic
```bash
# Check wiring
# Add capacitor (10μF) across VCC-GND
# Increase max_distance parameter
```

### Web Control Issues

**Problem**: WebSocket disconnect
```bash
# Check Flask-SocketIO compatibility
pip3 install flask-socketio==5.3.0 python-socketio==5.9.0

# Enable debug logging
socketio.run(app, debug=True, log_output=True)
```

**Problem**: Route playback jerky
```bash
# Increase recording resolution
# Record smaller duration steps
# Add smoothing between waypoints
```

### IoT Issues

**Problem**: MQTT connection timeout
```bash
# Test broker connectivity
ping broker.hivemq.com

# Try different broker
MQTT_BROKER = "mqtt.eclipseprojects.io"

# Check firewall
sudo ufw allow 1883
```

**Problem**: Telemetry not received
```bash
# Verify topic subscription
mosquitto_sub -h broker.hivemq.com -t 'rtka/#' -v

# Check JSON formatting
# Enable debug prints in code
```

## 💡 Project Ideas (Extended)

### 1. Security Patrol Robot
- Combine autonomous + IoT
- Face detection (OpenCV)
- Send photos on intrusion
- Mobile alerts

### 2. Delivery Robot
- Web control + route recording
- Waypoint navigation
- Load sensor (weight detection)
- Return-to-home feature

### 3. Educational Robot
- All three projects combined
- Block-based programming interface
- Learning analytics
- Multi-robot coordination

### 4. Agricultural Monitor
- IoT telemetry
- Soil moisture sensor
- Temperature/humidity
- Automated watering

## 📈 Skill Assessment

Setelah menyelesaikan ketiga projects:

**Fundamental Skills:**
- ✅ GPIO control dengan gpiozero
- ✅ Sensor integration & filtering
- ✅ Motor control & PWM
- ✅ State machine design

**Intermediate Skills:**
- ✅ Web development (Flask)
- ✅ WebSocket programming
- ✅ Database operations (SQLite)
- ✅ Data visualization (Chart.js)

**Advanced Skills:**
- ✅ IoT protocols (MQTT)
- ✅ Cloud integration
- ✅ Real-time systems
- ✅ Full-stack development

## 🏆 Certification Checklist

Untuk menyelesaikan Bab 12:

- [ ] Run autonomous robot for 5 minutes tanpa collision
- [ ] Control robot via web dari smartphone
- [ ] Record dan replay route minimal 10 steps
- [ ] Setup MQTT dan terima telemetry dari cloud
- [ ] Send remote command via MQTT
- [ ] Export 100+ telemetry records ke CSV
- [ ] Customize salah satu project dengan fitur baru

## 📚 Additional Resources

- **Autonomous Robotics**: [robotics.stanford.edu](https://robotics.stanford.edu)
- **IoT Platforms**: [iotify.io](https://iotify.io)
- **MQTT Tutorial**: [hivemq.com/mqtt-essentials](https://hivemq.com/mqtt-essentials)
- **Flask Mega Tutorial**: [flask.palletsprojects.com](https://flask.palletsprojects.com)

## 🎉 Congratulations!

Selamat menyelesaikan **Level 2 - Intermediate**!

Anda sekarang memiliki skill untuk:
- Build autonomous robots
- Create web-based control systems
- Integrate IoT & cloud services
- Develop complete robotics projects

### Next Level: Advanced Topics
- Computer Vision (OpenCV)
- Machine Learning (TensorFlow Lite)
- ROS (Robot Operating System)
- Multi-robot systems
- Advanced path planning (A*, Dijkstra)

---

**Made with ❤️ for RTKA Trainer Kit v2**
