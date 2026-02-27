#!/usr/bin/env python3
"""
Bab 10: Test MQTT Publish - Basic
==================================
Program sederhana untuk test MQTT publish

Install:
  pip3 install paho-mqtt
"""

import paho.mqtt.client as mqtt
import time

print("="*50)
print("Test MQTT Publish - Basic")
print("="*50)

def on_connect(client, userdata, flags, rc):
    """Callback saat koneksi berhasil/gagal"""
    if rc == 0:
        print("✅ Connected to MQTT Broker")
    else:
        print(f"❌ Connection failed with code {rc}")

client = mqtt.Client("RTKA_Publisher")
client.on_connect = on_connect

BROKER = "broker.hivemq.com"
PORT = 1883
TOPIC = "rtka/test"

print(f"\nConnecting to {BROKER}:{PORT}...")

try:
    client.connect(BROKER, PORT, 60)
    client.loop_start()
    
    time.sleep(2)
    
    print(f"\n📤 Publishing messages to topic: {TOPIC}")
    
    for i in range(5):
        message = f"Message {i+1} from RTKA Robot!"
        print(f"   Sending: {message}")
        client.publish(TOPIC, message)
        time.sleep(1)
    
    client.loop_stop()
    client.disconnect()
    
    print("\n✅ Publishing selesai!")
    print(f"   Total messages sent: 5")
    
except Exception as e:
    print(f"\n❌ Error: {e}")

"""
PENJELASAN PROGRAM:
==================
Program ini fokus pada MQTT publishing - mengirim messages ke broker untuk diterima
oleh subscribers.

MQTT Publish Basics:
Publishing adalah proses mengirim data/message ke MQTT broker. Broker kemudian akan
forward message tersebut ke semua clients yang subscribe ke topic yang sama.

Publisher Role:
- Sensor/device yang generate data
- Tidak perlu tahu siapa yang akan terima data
- Publish ke topic tertentu
- Fire-and-forget (default QoS 0)

Cara Kerja Program:
1. Setup Publisher Client:
   - Create MQTT client dengan ID "RTKA_Publisher"
   - Unique client ID penting untuk distinguish multiple clients
   - Set on_connect callback untuk konfirmasi koneksi

2. Connect to Broker:
   - Public broker HiveMQ untuk testing
   - Keepalive 60 detik (auto ping jika no activity)
   - loop_start() jalankan network loop di background

3. Publish Messages:
   - Topic: "rtka/test" (custom topic name)
   - Payload: string message
   - Loop 5 kali dengan delay 1 detik
   - client.publish(topic, payload) send message

4. Cleanup:
   - loop_stop() stop background loop
   - disconnect() close connection ke broker

Publish Method Parameters:
client.publish(topic, payload, qos=0, retain=False)

- topic: string, topic name (case sensitive)
- payload: string atau bytes, data yang dikirim
- qos: Quality of Service (0, 1, atau 2)
  * 0: At most once (fire and forget, fastest)
  * 1: At least once (acknowledged delivery)
  * 2: Exactly once (slowest, guaranteed)
- retain: bool, broker simpan last message untuk new subscribers

Topic Naming Conventions:
- Use / untuk hierarchy: "sensor/temperature/living-room"
- Lowercase recommended: "rtka/sensor/distance"
- No spaces: use underscore atau dash
- Descriptive: "robot/battery/voltage" bukan "data"
- Avoid leading /: "home/temp" bukan "/home/temp"

Wildcard Topics (untuk subscribe, bukan publish):
- Single level +: "sensor/+/temperature" 
- Multi level #: "sensor/#" (all sensors)

Message Payload:
- String: "Hello World"
- JSON: '{"temp": 25, "humidity": 60}'
- Binary: sensor data, images (dalam bytes)
- Empty: "" (valid, untuk signaling)

Best Practices:
1. Meaningful Topics:
   - Organize logically: "location/device/measurement"
   - Example: "rtka/robot1/distance", "rtka/robot1/battery"

2. Message Format:
   - Use JSON untuk structured data
   - Include timestamp jika needed
   - Keep payload small (bandwidth efficiency)

3. QoS Selection:
   - QoS 0: sensor readings (ok jika miss beberapa)
   - QoS 1: commands (need to arrive)
   - QoS 2: critical commands (exactly once)

4. Error Handling:
   - Check connection success (rc == 0)
   - Handle publish failures
   - Retry logic jika needed

Publishing Patterns:

1. Periodic Publishing (Sensor Data):
   while True:
       data = read_sensor()
       client.publish("sensor/temp", str(data))
       time.sleep(60)  # Every minute

2. Event-Based Publishing (Triggered):
   if motion_detected():
       client.publish("security/motion", "detected")

3. Batch Publishing (Multiple Topics):
   client.publish("robot/speed", str(speed))
   client.publish("robot/direction", direction)
   client.publish("robot/battery", str(battery))

4. JSON Publishing (Structured Data):
   import json
   data = {"temp": 25, "humidity": 60, "time": time.time()}
   client.publish("sensor/data", json.dumps(data))

Return Values:
publish() returns MQTTMessageInfo object dengan properties:
- rc: result code (MQTT_ERR_SUCCESS = 0)
- mid: message ID (untuk tracking)
- is_published(): check jika sudah published
- wait_for_publish(): block sampai published

Example Advanced Publishing:
```python
info = client.publish("topic", "data", qos=1)
info.wait_for_publish()  # Wait for acknowledgment
if info.is_published():
    print("Published successfully")
```

Retained Messages:
client.publish("status/online", "yes", retain=True)
- Broker saves last message
- New subscribers immediately get last value
- Useful untuk status ("online"/"offline")
- Clear retained: publish empty with retain=True

Use Cases:
1. IoT Sensor Networks:
   - Raspberry Pi publish sensor data
   - Smartphone subscribe untuk monitoring
   - Server subscribe untuk logging

2. Robot Control:
   - Joystick/controller publish commands
   - Robot subscribe untuk receive commands
   - Cloud publish firmware updates

3. Home Automation:
   - Sensors publish temperature, motion
   - Smart devices subscribe untuk automation
   - Phone app untuk monitoring

4. Telemetry:
   - Vehicle publish GPS, speed, fuel
   - Server collect dan analyze data
   - Dashboard visualize real-time

Testing:
- Run this publisher program
- Use MQTT client untuk subscribe:
  * mosquitto_sub -h broker.hivemq.com -t "rtka/test"
  * MQTT.fx GUI client
  * Mobile apps: IoT MQTT Panel
- Akan lihat messages yang dipublish

Debugging:
1. Connection failed:
   - Check internet connection
   - Verify broker address dan port
   - Check firewall settings

2. Messages tidak terima:
   - Verify topic name (case sensitive)
   - Check subscriber running
   - Try retain=True untuk testing

3. Performance issues:
   - Reduce publish frequency
   - Use QoS 0 untuk faster
   - Check network latency

Public MQTT Brokers (Free Testing):
- broker.hivemq.com:1883
- test.mosquitto.org:1883
- broker.emqx.io:1883

⚠️ Production: Jangan gunakan public brokers! Setup private broker dengan:
- Mosquitto (open source)
- HiveMQ (commercial)
- EMQX (scalable)
- AWS IoT Core
- Azure IoT Hub
- Add authentication dan encryption (TLS/SSL)
"""
