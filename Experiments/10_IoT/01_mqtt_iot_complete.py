#!/usr/bin/env python3
"""
Bab 10: IoT Fundamentals - MQTT & Cloud Integration
====================================================
Comprehensive IoT tutorial mencakup:
1. IoT Architecture
2. MQTT Protocol (Publish/Subscribe)
3. HTTP vs MQTT Comparison
4. Sending Sensor Data to Cloud

MQTT Basics:
- Broker: Server yang manage messages (Mosquitto)
- Publisher: Device yang kirim data
- Subscriber: Device yang terima data
- Topic: Channel untuk publish/subscribe

Install MQTT:
  sudo apt install mosquitto mosquitto-clients
  pip3 install paho-mqtt

Test MQTT:
  # Terminal 1 (Subscribe)
  mosquitto_sub -h localhost -t test/topic
  
  # Terminal 2 (Publish)
  mosquitto_pub -h localhost -t test/topic -m "Hello MQTT"
"""

import paho.mqtt.client as mqtt
import json
import time
from datetime import datetime
import random

# MQTT Configuration
MQTT_BROKER = "localhost"  # Change to cloud broker if needed
MQTT_PORT = 1883
MQTT_TOPIC_SENSOR = "raspberrypi/sensor"
MQTT_TOPIC_CONTROL = "raspberrypi/control"
MQTT_CLIENT_ID = "rpi_trainer_kit"

# Try to import GPIO for real sensor data
try:
    from gpiozero import DistanceSensor
    sensor = DistanceSensor(echo=20, trigger=26, max_distance=4.0)
    GPIO_AVAILABLE = True
except:
    GPIO_AVAILABLE = False
    print("⚠️  Running in simulation mode (no GPIO)")

print("="*70)
print("IoT Fundamentals - MQTT & Cloud Integration")
print("="*70)

# ============================================================================
# MQTT CLIENT SETUP
# ============================================================================

class IoTDevice:
    """IoT Device with MQTT capabilities"""
    
    def __init__(self, broker=MQTT_BROKER, port=MQTT_PORT):
        self.broker = broker
        self.port = port
        self.client = mqtt.Client(MQTT_CLIENT_ID)
        self.connected = False
        
        # Set callbacks
        self.client.on_connect = self.on_connect
        self.client.on_disconnect = self.on_disconnect
        self.client.on_message = self.on_message
        
        self.message_count = 0
    
    def on_connect(self, client, userdata, flags, rc):
        """Callback when connected to broker"""
        if rc == 0:
            print(f"✅ Connected to MQTT Broker: {self.broker}")
            self.connected = True
            # Subscribe to control topic
            self.client.subscribe(MQTT_TOPIC_CONTROL)
            print(f"📥 Subscribed to: {MQTT_TOPIC_CONTROL}")
        else:
            print(f"❌ Connection failed with code {rc}")
    
    def on_disconnect(self, client, userdata, rc):
        """Callback when disconnected"""
        print(f"📡 Disconnected from broker (code: {rc})")
        self.connected = False
    
    def on_message(self, client, userdata, msg):
        """Callback when message received"""
        topic = msg.topic
        payload = msg.payload.decode()
        
        print(f"\n📨 Message received:")
        print(f"   Topic: {topic}")
        print(f"   Payload: {payload}")
        
        # Parse JSON if possible
        try:
            data = json.loads(payload)
            print(f"   Parsed: {data}")
            
            # Handle control commands
            if 'command' in data:
                self.handle_command(data['command'])
        except:
            pass
    
    def handle_command(self, command):
        """Handle incoming control commands"""
        print(f"⚙️  Executing command: {command}")
        
        if command == "get_status":
            self.publish_status()
        elif command == "beep":
            print("   🔊 Beep!")
        else:
            print(f"   ⚠️  Unknown command: {command}")
    
    def connect(self):
        """Connect to MQTT broker"""
        try:
            print(f"\n🔌 Connecting to {self.broker}:{self.port}...")
            self.client.connect(self.broker, self.port, 60)
            self.client.loop_start()
            
            # Wait for connection
            timeout = 5
            while not self.connected and timeout > 0:
                time.sleep(0.5)
                timeout -= 0.5
            
            if not self.connected:
                print("❌ Connection timeout")
                return False
            
            return True
        
        except Exception as e:
            print(f"❌ Connection error: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from broker"""
        self.client.loop_stop()
        self.client.disconnect()
        print("🔌 Disconnected from broker")
    
    def publish_sensor_data(self):
        """Publish sensor data"""
        # Get sensor reading (or simulate)
        if GPIO_AVAILABLE:
            try:
                distance = sensor.distance * 100
            except:
                distance = random.uniform(10, 100)
        else:
            distance = random.uniform(10, 100)
        
        # Create data payload
        data = {
            "device_id": MQTT_CLIENT_ID,
            "timestamp": datetime.now().isoformat(),
            "sensor": {
                "distance_cm": round(distance, 2),
                "unit": "cm"
            },
            "count": self.message_count
        }
        
        # Publish as JSON
        payload = json.dumps(data)
        result = self.client.publish(MQTT_TOPIC_SENSOR, payload, qos=1)
        
        if result.rc == 0:
            print(f"📤 Published: {distance:.2f} cm")
            self.message_count += 1
            return True
        else:
            print(f"❌ Publish failed")
            return False
    
    def publish_status(self):
        """Publish device status"""
        status = {
            "device_id": MQTT_CLIENT_ID,
            "status": "online",
            "timestamp": datetime.now().isoformat(),
            "uptime": time.time(),
            "gpio_available": GPIO_AVAILABLE
        }
        
        payload = json.dumps(status)
        self.client.publish(f"{MQTT_TOPIC_SENSOR}/status", payload)
        print(f"📤 Status published")

# ============================================================================
# IOT DEMONSTRATIONS
# ============================================================================

def demo_http_vs_mqtt():
    """Demonstrasi perbandingan HTTP vs MQTT"""
    print("\n" + "="*70)
    print("HTTP vs MQTT Comparison")
    print("="*70)
    
    comparison = """
    ┌─────────────────┬────────────────────┬────────────────────┐
    │   Feature       │       HTTP         │       MQTT         │
    ├─────────────────┼────────────────────┼────────────────────┤
    │ Protocol        │ Request/Response   │ Publish/Subscribe  │
    │ Connection      │ Short-lived        │ Persistent         │
    │ Overhead        │ High (headers)     │ Low (2 bytes)      │
    │ Power Usage     │ Higher             │ Lower              │
    │ Bandwidth       │ Higher             │ Lower              │
    │ Real-time       │ Polling needed     │ Push-based         │
    │ Ideal for       │ Web apps           │ IoT sensors        │
    │ QoS Levels      │ No                 │ Yes (0, 1, 2)      │
    └─────────────────┴────────────────────┴────────────────────┘
    
    Use Cases:
    
    HTTP:
    ✓ Web applications
    ✓ RESTful APIs
    ✓ File downloads
    ✓ Request-response pattern
    
    MQTT:
    ✓ IoT sensors (temperature, motion, etc)
    ✓ Real-time monitoring
    ✓ Low-bandwidth networks
    ✓ Battery-powered devices
    ✓ Pub-sub messaging
    """
    
    print(comparison)

def demo_iot_architecture():
    """Demonstrasi IoT Architecture"""
    print("\n" + "="*70)
    print("IoT Architecture")
    print("="*70)
    
    architecture = """
    IoT System Layers:
    
    ┌─────────────────────────────────────────┐
    │  Layer 4: Application & Analytics       │
    │  - Dashboard, Alerts, ML/AI             │
    └──────────────┬──────────────────────────┘
                   │
    ┌──────────────▼──────────────────────────┐
    │  Layer 3: Data Processing & Storage     │
    │  - Database, Stream processing          │
    └──────────────┬──────────────────────────┘
                   │
    ┌──────────────▼──────────────────────────┐
    │  Layer 2: Network & Communication       │
    │  - MQTT, HTTP, WebSocket, LoRa          │
    └──────────────┬──────────────────────────┘
                   │
    ┌──────────────▼──────────────────────────┐
    │  Layer 1: Sensors & Actuators (Edge)    │
    │  - Raspberry Pi, Arduino, ESP32         │
    └─────────────────────────────────────────┘
    
    Raspberry Pi Position:
    - Edge device (Layer 1)
    - Can also do processing (Layer 3)
    - Acts as gateway between sensors and cloud
    
    Common IoT Protocols:
    - MQTT: Lightweight messaging
    - HTTP/HTTPS: Web APIs
    - WebSocket: Real-time bidirectional
    - CoAP: Constrained devices
    - LoRaWAN: Long-range, low-power
    """
    
    print(architecture)

def publish_sensor_stream(device, duration=30, interval=2):
    """Publish sensor data stream"""
    print(f"\n📊 Publishing sensor data for {duration} seconds...")
    print(f"   Interval: {interval} seconds")
    print(f"   Topic: {MQTT_TOPIC_SENSOR}")
    print("\nPress Ctrl+C to stop\n")
    
    try:
        start_time = time.time()
        while (time.time() - start_time) < duration:
            device.publish_sensor_data()
            time.sleep(interval)
        
        print(f"\n✅ Published {device.message_count} messages")
    
    except KeyboardInterrupt:
        print(f"\n\n⏸️  Stopped by user")
        print(f"Total messages: {device.message_count}")

def simulate_cloud_subscriber():
    """Simulate cloud subscriber"""
    print("\n☁️  Cloud Subscriber Simulation")
    print("-" * 70)
    print("Dalam real scenario, ini adalah:")
    print("  - Cloud server (AWS IoT, Google Cloud IoT, Azure IoT Hub)")
    print("  - Database untuk store data")
    print("  - Dashboard untuk visualisasi")
    print()
    print("Untuk test:")
    print("  1. Buka terminal baru")
    print("  2. Jalankan: mosquitto_sub -h localhost -t 'raspberrypi/#' -v")
    print("  3. Lihat data yang masuk real-time")

# ============================================================================
# MAIN PROGRAM
# ============================================================================

def main():
    print("\n📚 IoT Fundamentals:")
    print("  - MQTT = Message Queue Telemetry Transport")
    print("  - Lightweight protocol untuk IoT")
    print("  - Publish/Subscribe pattern")
    print("  - QoS (Quality of Service) levels")
    print()
    
    print("⚙️  Setup Requirements:")
    print("  1. Install Mosquitto broker:")
    print("     sudo apt install mosquitto mosquitto-clients")
    print("  2. Install Python MQTT client:")
    print("     pip3 install paho-mqtt")
    print()
    
    # Create IoT device
    device = IoTDevice()
    
    while True:
        print("\n" + "="*70)
        print("MENU:")
        print("  1. Connect to MQTT Broker")
        print("  2. Publish Sensor Data (single)")
        print("  3. Publish Sensor Stream (30 sec)")
        print("  4. Publish Device Status")
        print("  5. HTTP vs MQTT Comparison")
        print("  6. IoT Architecture Overview")
        print("  7. Cloud Subscriber Info")
        print("  8. Disconnect")
        print("  9. Exit")
        print("="*70)
        
        choice = input("\nPilihan: ").strip()
        
        if choice == "1":
            device.connect()
        
        elif choice == "2":
            if not device.connected:
                print("❌ Not connected! Connect first (option 1)")
            else:
                device.publish_sensor_data()
        
        elif choice == "3":
            if not device.connected:
                print("❌ Not connected! Connect first (option 1)")
            else:
                publish_sensor_stream(device, duration=30, interval=2)
        
        elif choice == "4":
            if not device.connected:
                print("❌ Not connected! Connect first (option 1)")
            else:
                device.publish_status()
        
        elif choice == "5":
            demo_http_vs_mqtt()
        
        elif choice == "6":
            demo_iot_architecture()
        
        elif choice == "7":
            simulate_cloud_subscriber()
        
        elif choice == "8":
            if device.connected:
                device.disconnect()
        
        elif choice == "9":
            if device.connected:
                device.disconnect()
            break
        
        else:
            print("❌ Pilihan tidak valid")
    
    print("\n✅ Program selesai!")
    print("\n🌐 Cloud MQTT Brokers (Free Tier):")
    print("  - HiveMQ: broker.hivemq.com:1883")
    print("  - Eclipse: mqtt.eclipseprojects.io:1883")
    print("  - EMQX: broker.emqx.io:1883")
    print("\n💡 Next Steps:")
    print("  - Setup cloud database for data storage")
    print("  - Create web dashboard for visualization")
    print("  - Implement alerts & notifications")
    print("  - Add machine learning for predictions")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nProgram dihentikan")
