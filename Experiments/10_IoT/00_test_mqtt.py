#!/usr/bin/env python3
"""
Bab 10: Test MQTT - Basic
==========================
Program sederhana untuk test koneksi MQTT

Install:
  pip3 install paho-mqtt

Test dengan public MQTT broker
"""

import paho.mqtt.client as mqtt
import time

print("="*50)
print("Test MQTT - Basic")
print("="*50)

def on_connect(client, userdata, flags, rc):
    """Callback dipanggil saat koneksi ke broker berhasil/gagal"""
    if rc == 0:
        print("✅ Connected to MQTT Broker")
        client.subscribe("test/rtka")
        print("✅ Subscribed to topic: test/rtka")
    else:
        print(f"❌ Connection failed with code {rc}")

def on_message(client, userdata, msg):
    """Callback dipanggil saat menerima message dari topic yang di-subscribe"""
    print(f"\n📩 Received: {msg.topic} = {msg.payload.decode()}")

client = mqtt.Client("RTKA_Test")
client.on_connect = on_connect
client.on_message = on_message

BROKER = "broker.hivemq.com"
PORT = 1883

print(f"\nConnecting to {BROKER}:{PORT}...")

try:
    client.connect(BROKER, PORT, 60)
    client.loop_start()
    
    time.sleep(2)
    
    print("\n📤 Publishing test message...")
    client.publish("test/rtka", "Hello from RTKA!")
    
    print("\nWaiting for messages... (10s)")
    print("Tip: Publish ke topic 'test/rtka' dari MQTT client lain")
    
    time.sleep(10)
    
    client.loop_stop()
    client.disconnect()
    
    print("\n✅ Test selesai!")
    
except Exception as e:
    print(f"\n❌ Error: {e}")

"""
PENJELASAN PROGRAM:
==================
Program ini untuk test koneksi MQTT (Message Queue Telemetry Transport), protokol
messaging yang populer untuk IoT applications.

MQTT Basics:
1. Publisher-Subscriber Pattern:
   - Publisher: device yang send messages ke topic
   - Subscriber: device yang receive messages dari topic
   - Broker: server yang route messages antara publishers dan subscribers
   - Topic: channel untuk kategorisasi messages (contoh: "sensor/temperature")

2. Quality of Service (QoS):
   - QoS 0: At most once (fire and forget)
   - QoS 1: At least once (acknowledged delivery)
   - QoS 2: Exactly once (assured delivery)

3. Retained Messages:
   - Broker simpan last message untuk topic
   - New subscriber langsung dapat last message

Cara Kerja Program:
1. Setup Client:
   - Buat MQTT client dengan unique ID "RTKA_Test"
   - Set callback functions untuk handle events (connect, message)

2. Connect to Broker:
   - Connect ke public broker HiveMQ (broker.hivemq.com:1883)
   - Keepalive 60 detik (send ping jika tidak ada activity)
   - loop_start() jalankan network loop di background thread

3. Callback on_connect:
   - Dipanggil otomatis saat connection established/failed
   - rc=0 berarti success, rc!=0 adalah error codes
   - Subscribe ke topic "test/rtka" setelah connected (best practice)

4. Publish Message:
   - Publish "Hello from RTKA!" ke topic "test/rtka"
   - Message akan diterima oleh semua subscribers di topic tersebut
   - Karena kita juga subscribe, message akan kembali ke kita

5. Callback on_message:
   - Dipanggil otomatis saat receive message dari subscribed topics
   - msg.topic = nama topic
   - msg.payload = message data (bytes, perlu decode ke string)

Keuntungan MQTT:
- Lightweight protocol, efficient untuk low-bandwidth networks
- Support for unreliable networks (auto-reconnect)
- Publish-subscribe decoupling (publishers tidak perlu tahu subscribers)
- Wildcard topics (sensor/# subscribe semua sensor/*)
- Ideal untuk IoT: sensor data, remote control, monitoring

Public MQTT Brokers untuk Testing:
- broker.hivemq.com:1883
- test.mosquitto.org:1883
- broker.emqx.io:1883

Catatan: Public brokers tidak secure (no authentication), jangan untuk production!
"""
