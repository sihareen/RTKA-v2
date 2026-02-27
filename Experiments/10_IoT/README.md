# Bab 10: IoT Fundamentals

Belajar konsep dan implementasi Internet of Things (IoT) untuk robotika.

## 📚 Daftar Program

### 1. MQTT & IoT Complete (`01_mqtt_iot_complete.py`)
Program lengkap MQTT dan IoT fundamentals:
- **IoT Architecture**: Edge, Network, Processing, Application layers
- **MQTT Protocol**: Publish/Subscribe pattern, QoS levels
- **HTTP vs MQTT**: Perbandingan protocol untuk IoT
- **Cloud Integration**: Connect ke MQTT broker (local/cloud)
- **Real-time Messaging**: Publish sensor data, subscribe to commands

**Fitur:**
- MQTT client dengan auto-reconnect
- JSON payload formatting
- Command & control via MQTT
- Message counting dan statistics
- Multi-broker support (local Mosquitto, HiveMQ, Eclipse, EMQX)

**Topics:**
- `raspberrypi/sensor` - Sensor data telemetry
- `raspberrypi/control` - Remote control commands

### 2. Cloud Data Logging (`02_cloud_data_logging.py`)
Logging dan visualisasi data sensor ke cloud:
- **Local Logging**: CSV, JSON, SQLite database
- **Cloud Upload**: HTTP POST ke cloud platforms
- **Data Analytics**: Statistics, trends, histograms
- **Export**: CSV/JSON export untuk analysis
- **Alert System**: Automatic alerts based on thresholds

**Supported Cloud Services:**
- ThingSpeak (IoT analytics platform)
- Adafruit IO
- Custom HTTP APIs

**Database Schema:**
- Sensor readings dengan timestamp
- Data aggregation dan statistics
- Historical data tracking

## 🔧 Setup Requirements

### Install MQTT Broker (Local)
```bash
# Install Mosquitto
sudo apt update
sudo apt install mosquitto mosquitto-clients -y

# Start service
sudo systemctl start mosquitto
sudo systemctl enable mosquitto

# Test broker
mosquitto_sub -h localhost -t test/topic &
mosquitto_pub -h localhost -t test/topic -m "Hello MQTT"
```

### Install Python Packages
```bash
pip3 install paho-mqtt requests
```

### Optional: Cloud Brokers
Tidak perlu install, gunakan public brokers:
- **HiveMQ**: `broker.hivemq.com:1883`
- **Eclipse**: `mqtt.eclipseprojects.io:1883`
- **EMQX**: `broker.emqx.io:1883`

## 🌐 IoT Architecture

```
┌─────────────────────────────────────────┐
│  Cloud / Application Layer              │
│  - Dashboard, Analytics, ML/AI          │
└──────────────┬──────────────────────────┘
               │ MQTT / HTTP
┌──────────────▼──────────────────────────┐
│  MQTT Broker / API Gateway              │
│  - Mosquitto, HiveMQ, AWS IoT           │
└──────────────┬──────────────────────────┘
               │ WiFi / Network
┌──────────────▼──────────────────────────┐
│  Edge Device (Raspberry Pi)             │
│  - Sensors, Actuators, Processing       │
└─────────────────────────────────────────┘
```

## 📊 MQTT vs HTTP

| Feature | HTTP | MQTT |
|---------|------|------|
| Pattern | Request/Response | Pub/Sub |
| Overhead | High (headers) | Low (2 bytes) |
| Connection | Short-lived | Persistent |
| Real-time | Polling | Push |
| Bandwidth | Higher | Lower |
| Ideal for | Web APIs | IoT sensors |

## 🚀 Usage Examples

### Test MQTT Locally
```bash
# Terminal 1: Subscribe to sensor data
mosquitto_sub -h localhost -t 'raspberrypi/#' -v

# Terminal 2: Run robot with MQTT
./01_mqtt_iot_complete.py
# Select option 1 (Connect to MQTT)
# Select option 3 (Publish sensor stream)
```

### Cloud Integration
```bash
# Edit program to use cloud broker
# Change: MQTT_BROKER = "broker.hivemq.com"

./01_mqtt_iot_complete.py
# Data akan dikirim ke cloud broker
# Subscribe dari device lain:
mosquitto_sub -h broker.hivemq.com -t 'raspberrypi/#' -v
```

### Data Logging
```bash
./02_cloud_data_logging.py
# Select option 2: Start continuous logging
# Data tersimpan di:
#   - sensor_logs/sensor_data.csv
#   - sensor_logs/sensor_data.json
#   - sensor_logs/sensor_data.db
```

## 📱 Monitoring Tools

### MQTT.fx / MQTT Explorer
Desktop application untuk monitoring MQTT:
```bash
# Install MQTT Explorer
sudo snap install mqtt-explorer
```

### Node-RED
Visual programming untuk IoT:
```bash
# Install Node-RED
sudo npm install -g --unsafe-perm node-red

# Run
node-red

# Open: http://localhost:1880
```

## 🔐 Security Best Practices

1. **Authentication**: Gunakan username/password untuk MQTT
2. **Encryption**: Gunakan TLS/SSL (port 8883)
3. **Authorization**: Restrict topics per user
4. **API Keys**: Jangan hardcode, gunakan environment variables

```python
# Example secure connection
import os

MQTT_USER = os.getenv('MQTT_USER')
MQTT_PASS = os.getenv('MQTT_PASS')

client.username_pw_set(MQTT_USER, MQTT_PASS)
client.tls_set()  # Enable SSL
client.connect(broker, 8883)  # Secure port
```

## 🎓 Learning Path

1. ✅ Understand MQTT basics (Pub/Sub)
2. ✅ Setup local Mosquitto broker
3. ✅ Send/receive messages
4. ✅ Connect to cloud broker
5. ✅ Log data to database
6. ✅ Create analytics dashboard
7. ⬜ Next: Remote control & monitoring (Bab 11)

## 📚 Resources

- [MQTT.org](https://mqtt.org/) - MQTT specification
- [HiveMQ](https://www.hivemq.com/mqtt-essentials/) - MQTT tutorials
- [ThingSpeak](https://thingspeak.com/) - IoT analytics
- [Adafruit IO](https://io.adafruit.com/) - IoT platform

## 🐛 Troubleshooting

**Problem**: "Connection refused" error
```bash
# Check if Mosquitto is running
sudo systemctl status mosquitto

# Restart if needed
sudo systemctl restart mosquitto
```

**Problem**: "No module named 'paho'"
```bash
# Install MQTT client
pip3 install paho-mqtt
```

**Problem**: Data not appearing in cloud
- Check internet connection
- Verify broker address and port
- Check firewall settings
- Try different cloud broker

## 💡 Next Steps

- Bab 11: Web dashboard untuk monitoring
- Bab 12: Complete IoT robot projects
- Add machine learning for predictions
- Implement alerts & notifications
- Create mobile app interface
