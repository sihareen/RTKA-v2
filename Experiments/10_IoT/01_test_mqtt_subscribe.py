#!/usr/bin/env python3
"""
Bab 10: Test MQTT Subscribe - Basic
====================================
Program sederhana untuk test MQTT subscribe

Install:
  pip3 install paho-mqtt
"""

import paho.mqtt.client as mqtt
import time

print("="*50)
print("Test MQTT Subscribe - Basic")
print("="*50)

message_count = 0

def on_connect(client, userdata, flags, rc):
    """Callback saat koneksi berhasil"""
    if rc == 0:
        print("✅ Connected to MQTT Broker")
        client.subscribe("rtka/test")
        print("✅ Subscribed to topic: rtka/test")
    else:
        print(f"❌ Connection failed with code {rc}")

def on_message(client, userdata, msg):
    """Callback saat menerima message"""
    global message_count
    message_count += 1
    print(f"\n📩 Message #{message_count}:")
    print(f"   Topic: {msg.topic}")
    print(f"   Payload: {msg.payload.decode()}")
    print(f"   QoS: {msg.qos}")

client = mqtt.Client("RTKA_Subscriber")
client.on_connect = on_connect
client.on_message = on_message

BROKER = "broker.hivemq.com"
PORT = 1883

print(f"\nConnecting to {BROKER}:{PORT}...")

try:
    client.connect(BROKER, PORT, 60)
    
    print("\n👂 Listening for messages...")
    print("   Press Ctrl+C to stop\n")
    print("Tip: Run 00_test_mqtt_publish.py di terminal lain")
    print("     untuk send test messages!\n")
    
    client.loop_forever()
    
except KeyboardInterrupt:
    print(f"\n\n✅ Stopped by user")
    print(f"   Total messages received: {message_count}")
    client.disconnect()
    
except Exception as e:
    print(f"\n❌ Error: {e}")

"""
PENJELASAN PROGRAM:
==================
Program ini fokus pada MQTT subscribing - menerima messages dari broker yang dipublish
oleh publishers.

MQTT Subscribe Basics:
Subscribing adalah proses mendaftar untuk menerima messages dari topic tertentu. Setiap
kali ada message dipublish ke topic tersebut, subscriber akan receive notification.

Subscriber Role:
- Client yang ingin terima data dari topic
- Tidak perlu tahu siapa publisher-nya
- Subscribe ke satu atau multiple topics
- Receive messages via callback function

Cara Kerja Program:
1. Setup Subscriber Client:
   - Create MQTT client dengan ID "RTKA_Subscriber"
   - Set on_connect callback
   - Set on_message callback untuk handle incoming messages

2. Connect to Broker:
   - Connect ke broker HiveMQ
   - Keepalive 60 detik

3. Subscribe dalam on_connect:
   - BEST PRACTICE: subscribe di on_connect callback
   - Kenapa? Auto re-subscribe jika connection lost lalu reconnect
   - Topic: "rtka/test"

4. Message Handler (on_message):
   - Dipanggil otomatis saat terima message
   - Extract topic, payload, QoS dari msg object
   - Decode payload dari bytes ke string
   - Display message info

5. Loop Forever:
   - client.loop_forever() blocking loop
   - Keeps connection alive
   - Auto-reconnect jika disconnected
   - Process incoming messages

Callback Functions:

1. on_connect(client, userdata, flags, rc):
   - Called saat connection established
   - rc: result code (0 = success)
   - flags: dict dengan session info
   - Best place untuk subscribe to topics

2. on_message(client, userdata, msg):
   - Called saat receive message dari subscribed topic
   - msg.topic: topic name
   - msg.payload: message data (bytes)
   - msg.qos: quality of service
   - msg.retain: retained message flag

3. on_disconnect(client, userdata, rc):
   - Called saat disconnected
   - rc=0: clean disconnect
   - rc!=0: unexpected disconnect (akan auto-reconnect)

4. on_subscribe(client, userdata, mid, granted_qos):
   - Called saat subscription confirmed
   - mid: message ID
   - granted_qos: tuple of granted QoS levels

Message Object Properties:
- msg.topic: string, topic name
- msg.payload: bytes, message data
- msg.qos: int, QoS level (0, 1, 2)
- msg.retain: bool, retained message
- msg.timestamp: float, receive timestamp

Subscribe Method:
client.subscribe(topic, qos=0)

- Single topic: client.subscribe("sensor/temp")
- Multiple topics: client.subscribe([("sensor/temp", 0), ("sensor/humidity", 1)])
- With QoS: client.subscribe("sensor/temp", qos=1)

Topic Wildcards:
Subscribers bisa use wildcards (publishers tidak bisa):

1. Single Level (+):
   - "sensor/+/temperature" matches:
     * "sensor/room1/temperature"
     * "sensor/room2/temperature"
   - NOT match: "sensor/room1/room2/temperature"

2. Multi Level (#):
   - "sensor/#" matches:
     * "sensor/temperature"
     * "sensor/room1/temperature"
     * "sensor/room1/livingroom/temperature"
   - MUST be last character
   - "sensor/#/temperature" INVALID

3. Examples:
   - "home/+/temperature" → all rooms temperature
   - "home/livingroom/#" → all livingroom sensors
   - "#" → ALL topics (not recommended, too broad)

Loop Methods:

1. loop_forever():
   - Blocking call
   - Runs until disconnect() called
   - Auto-reconnect on connection loss
   - Best untuk dedicated subscriber programs

2. loop_start():
   - Non-blocking, runs di background thread
   - Program continues execution
   - Good untuk programs yang publish DAN subscribe

3. loop():
   - Manual iteration
   - Call repeatedly di your own loop
   - More control tapi more complex

Example loop_start() usage:
```python
client.loop_start()  # Start background loop

while running:
    # Do other things
    sensor_data = read_sensor()
    client.publish("sensor/data", str(sensor_data))
    time.sleep(1)

client.loop_stop()  # Stop background loop
```

QoS Levels untuk Subscribe:

QoS 0 (At most once):
- Fastest, no acknowledgment
- Message bisa hilang
- Good for: frequent sensor readings

QoS 1 (At least once):
- Acknowledged delivery
- Duplicate messages possible
- Good for: important data

QoS 2 (Exactly once):
- Guaranteed, no duplicates
- Slowest (4-way handshake)
- Good for: critical commands

⚠️ Actual QoS = min(publish QoS, subscribe QoS)
If publish QoS=2, subscribe QoS=0 → receive at QoS 0

Message Processing Patterns:

1. Simple Display:
   def on_message(client, userdata, msg):
       print(f"{msg.topic}: {msg.payload.decode()}")

2. JSON Parsing:
   import json
   def on_message(client, userdata, msg):
       data = json.loads(msg.payload.decode())
       temp = data['temperature']
       print(f"Temperature: {temp}°C")

3. Topic-Based Routing:
   def on_message(client, userdata, msg):
       if msg.topic == "sensor/temp":
           handle_temperature(msg.payload)
       elif msg.topic == "sensor/humidity":
           handle_humidity(msg.payload)

4. Data Logging:
   def on_message(client, userdata, msg):
       with open('log.txt', 'a') as f:
           f.write(f"{time.time()},{msg.topic},{msg.payload.decode()}\n")

5. Control Actions:
   def on_message(client, userdata, msg):
       command = msg.payload.decode()
       if command == "FORWARD":
           robot.move_forward()
       elif command == "STOP":
           robot.stop()

Using userdata:
userdata parameter allows passing custom data to callbacks:

```python
class RobotData:
    def __init__(self):
        self.speed = 0
        self.direction = "STOP"

robot_data = RobotData()
client = mqtt.Client("robot", userdata=robot_data)

def on_message(client, userdata, msg):
    # userdata is robot_data object
    if msg.topic == "robot/speed":
        userdata.speed = int(msg.payload)
```

Multiple Subscriptions:
```python
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        # Subscribe to multiple topics
        client.subscribe("sensor/temperature")
        client.subscribe("sensor/humidity")
        client.subscribe("sensor/pressure")
        
        # Or in one call:
        client.subscribe([
            ("sensor/temperature", 0),
            ("sensor/humidity", 1),
            ("sensor/pressure", 0)
        ])
```

Unsubscribe:
```python
client.unsubscribe("sensor/temp")
client.unsubscribe(["sensor/temp", "sensor/humidity"])
```

Testing:
1. Run this subscriber program first
2. In another terminal, run:
   - 00_test_mqtt_publish.py (our publisher)
   - mosquitto_pub -h broker.hivemq.com -t "rtka/test" -m "Hello"
   - MQTT.fx atau mobile app
3. Watch messages appear di subscriber

Debugging:
1. Not receiving messages:
   - Check topic name (case sensitive!)
   - Verify subscriber running dan connected
   - Check publisher sending to same topic
   - Try wildcard: subscribe to "#" untuk see all

2. Duplicate messages:
   - Normal dengan QoS 1 atau 2
   - Check jika multiple subscribers dengan same client ID
   - Implement deduplication jika needed

3. Missing messages:
   - QoS 0 doesn't guarantee delivery
   - Increase QoS level
   - Check network stability

4. Connection drops:
   - Auto-reconnect enabled by default
   - Check keepalive setting
   - Monitor on_disconnect callback

Error Codes (rc):
- 0: Connection successful
- 1: Incorrect protocol version
- 2: Invalid client identifier
- 3: Server unavailable
- 4: Bad username or password
- 5: Not authorized

Use Cases:

1. Remote Monitoring:
   - Robot publish status, battery, position
   - Control panel subscribe untuk display
   - Alerts subscribe untuk notifications

2. Command Control:
   - Joystick publish commands
   - Robot subscribe untuk receive commands
   - Execute actions based on messages

3. Multi-Robot Coordination:
   - Robot1 publish "position/robot1"
   - Robot2 subscribe "position/#"
   - Coordinate movements, avoid collisions

4. Data Collection:
   - Multiple sensors publish data
   - Database subscriber log all data
   - Analytics subscriber process data

5. Broadcast Messages:
   - Server publish "broadcast/announcement"
   - All devices subscribe "broadcast/#"
   - System-wide notifications

Best Practices:
1. Always subscribe di on_connect callback (auto re-subscribe)
2. Handle payload decoding errors (try-except)
3. Don't do heavy processing di on_message (use queue/threading)
4. Use meaningful client IDs
5. Set appropriate QoS levels
6. Handle disconnections gracefully
7. Log important messages
8. Validate message format before processing

This subscriber program dapat run continuously untuk monitor incoming messages,
making it perfect untuk IoT monitoring, robot control, dan real-time data collection.
"""
