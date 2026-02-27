#!/usr/bin/env python3
"""
Bab 10.2: Cloud Integration & Data Logging
===========================================
Mengirim data sensor ke cloud dan logging

Topics:
1. HTTP POST ke cloud API
2. Data logging ke file/database
3. Timestamp & data formatting
4. Error handling & retry logic

Cloud Services yang bisa digunakan (free tier):
- ThingSpeak (IoT analytics)
- Adafruit IO (IoT platform)
- Firebase (Google)
- AWS IoT Core
- Azure IoT Hub
"""

import requests
import json
import csv
import sqlite3
from datetime import datetime
import time
import os

# Try import GPIO
try:
    from gpiozero import DistanceSensor, LED
    sensor = DistanceSensor(echo=20, trigger=26, max_distance=4.0)
    status_led = LED(7)
    GPIO_AVAILABLE = True
except:
    GPIO_AVAILABLE = False

print("="*70)
print("Cloud Integration & Data Logging")
print("="*70)

# ============================================================================
# DATA LOGGER CLASS
# ============================================================================

class SensorDataLogger:
    """Logger untuk sensor data"""
    
    def __init__(self, log_dir="sensor_logs"):
        self.log_dir = log_dir
        os.makedirs(log_dir, exist_ok=True)
        
        self.csv_file = os.path.join(log_dir, "sensor_data.csv")
        self.json_file = os.path.join(log_dir, "sensor_data.json")
        self.db_file = os.path.join(log_dir, "sensor_data.db")
        
        self.init_csv()
        self.init_database()
    
    def init_csv(self):
        """Initialize CSV file"""
        if not os.path.exists(self.csv_file):
            with open(self.csv_file, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['timestamp', 'distance_cm', 'temperature', 'humidity'])
            print(f"📄 CSV file created: {self.csv_file}")
    
    def init_database(self):
        """Initialize SQLite database"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sensor_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                distance_cm REAL,
                temperature REAL,
                humidity REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
        print(f"💾 Database initialized: {self.db_file}")
    
    def log_to_csv(self, data):
        """Log data to CSV"""
        with open(self.csv_file, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                data.get('timestamp'),
                data.get('distance_cm'),
                data.get('temperature'),
                data.get('humidity')
            ])
        print(f"📝 Logged to CSV")
    
    def log_to_json(self, data):
        """Log data to JSON file (append)"""
        # Read existing data
        if os.path.exists(self.json_file):
            with open(self.json_file, 'r') as f:
                try:
                    existing_data = json.load(f)
                except:
                    existing_data = []
        else:
            existing_data = []
        
        # Append new data
        existing_data.append(data)
        
        # Write back
        with open(self.json_file, 'w') as f:
            json.dump(existing_data, f, indent=2)
        
        print(f"📝 Logged to JSON")
    
    def log_to_database(self, data):
        """Log data to SQLite database"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO sensor_data (timestamp, distance_cm, temperature, humidity)
            VALUES (?, ?, ?, ?)
        ''', (
            data.get('timestamp'),
            data.get('distance_cm'),
            data.get('temperature'),
            data.get('humidity')
        ))
        
        conn.commit()
        conn.close()
        print(f"💾 Logged to database")
    
    def get_recent_data(self, limit=10):
        """Get recent data from database"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT timestamp, distance_cm, temperature, humidity, created_at
            FROM sensor_data
            ORDER BY id DESC
            LIMIT ?
        ''', (limit,))
        
        rows = cursor.fetchall()
        conn.close()
        
        return rows
    
    def get_statistics(self):
        """Get data statistics"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT 
                COUNT(*) as total,
                AVG(distance_cm) as avg_distance,
                MIN(distance_cm) as min_distance,
                MAX(distance_cm) as max_distance
            FROM sensor_data
        ''')
        
        stats = cursor.fetchone()
        conn.close()
        
        return {
            'total_records': stats[0],
            'avg_distance': stats[1],
            'min_distance': stats[2],
            'max_distance': stats[3]
        }

# ============================================================================
# CLOUD INTEGRATION
# ============================================================================

class CloudUploader:
    """Upload data to cloud services"""
    
    def __init__(self, service="thingspeak", api_key="YOUR_API_KEY"):
        self.service = service
        self.api_key = api_key
        
        # Cloud endpoints
        self.endpoints = {
            'thingspeak': 'https://api.thingspeak.com/update',
            'adafruit': 'https://io.adafruit.com/api/v2/{username}/feeds/{feed}/data',
            'custom': 'http://your-server.com/api/sensor'
        }
    
    def upload_to_thingspeak(self, data):
        """Upload to ThingSpeak"""
        url = self.endpoints['thingspeak']
        
        payload = {
            'api_key': self.api_key,
            'field1': data.get('distance_cm'),
            'field2': data.get('temperature'),
            'field3': data.get('humidity')
        }
        
        try:
            response = requests.post(url, data=payload, timeout=10)
            
            if response.status_code == 200:
                print(f"☁️  Uploaded to ThingSpeak: Entry #{response.text}")
                return True
            else:
                print(f"❌ Upload failed: {response.status_code}")
                return False
        
        except requests.exceptions.RequestException as e:
            print(f"❌ Network error: {e}")
            return False
    
    def upload_generic(self, url, data):
        """Upload to custom API endpoint"""
        try:
            headers = {'Content-Type': 'application/json'}
            response = requests.post(url, json=data, headers=headers, timeout=10)
            
            if response.status_code in [200, 201]:
                print(f"☁️  Upload successful: {response.status_code}")
                return True
            else:
                print(f"❌ Upload failed: {response.status_code}")
                return False
        
        except requests.exceptions.RequestException as e:
            print(f"❌ Network error: {e}")
            return False

# ============================================================================
# DEMO FUNCTIONS
# ============================================================================

def collect_sensor_data():
    """Collect sensor data"""
    if GPIO_AVAILABLE:
        try:
            distance = sensor.distance * 100
        except:
            distance = None
    else:
        import random
        distance = random.uniform(10, 100)
    
    # Simulate other sensors
    import random
    temperature = random.uniform(20, 30)
    humidity = random.uniform(40, 80)
    
    data = {
        'timestamp': datetime.now().isoformat(),
        'distance_cm': round(distance, 2) if distance else None,
        'temperature': round(temperature, 1),
        'humidity': round(humidity, 1)
    }
    
    return data

def demo_logging(logger, duration=30, interval=5):
    """Demo data logging"""
    print(f"\n📊 Logging sensor data for {duration} seconds...")
    print(f"   Interval: {interval} seconds\n")
    
    try:
        start_time = time.time()
        count = 0
        
        while (time.time() - start_time) < duration:
            # Collect data
            data = collect_sensor_data()
            
            print(f"\n[{count+1}] {data['timestamp']}")
            print(f"    Distance: {data['distance_cm']} cm")
            print(f"    Temp: {data['temperature']}°C")
            print(f"    Humidity: {data['humidity']}%")
            
            # Log to all formats
            logger.log_to_csv(data)
            logger.log_to_json(data)
            logger.log_to_database(data)
            
            count += 1
            time.sleep(interval)
        
        print(f"\n✅ Logged {count} records")
    
    except KeyboardInterrupt:
        print("\n\n⏸️  Stopped by user")

def view_statistics(logger):
    """View data statistics"""
    print("\n📈 Data Statistics:")
    print("-" * 70)
    
    stats = logger.get_statistics()
    
    print(f"Total Records: {stats['total_records']}")
    print(f"Average Distance: {stats['avg_distance']:.2f} cm")
    print(f"Min Distance: {stats['min_distance']:.2f} cm")
    print(f"Max Distance: {stats['max_distance']:.2f} cm")

def view_recent_data(logger, limit=10):
    """View recent logged data"""
    print(f"\n📋 Recent {limit} Records:")
    print("-" * 70)
    
    rows = logger.get_recent_data(limit)
    
    if not rows:
        print("No data found")
        return
    
    for row in rows:
        print(f"{row[0]} | Distance: {row[1]:.2f} cm | Temp: {row[2]:.1f}°C | Humidity: {row[3]:.1f}%")

# ============================================================================
# MAIN PROGRAM
# ============================================================================

def main():
    print("\n💡 Cloud Integration & Logging:")
    print("  - Local logging (CSV, JSON, SQLite)")
    print("  - Cloud upload (HTTP POST)")
    print("  - Data analytics & visualization")
    print()
    
    # Initialize logger
    logger = SensorDataLogger()
    
    # Initialize cloud uploader (demo only)
    uploader = CloudUploader(service="thingspeak", api_key="DEMO_KEY")
    
    while True:
        print("\n" + "="*70)
        print("MENU:")
        print("  1. Collect & Log Single Reading")
        print("  2. Start Continuous Logging (30 sec)")
        print("  3. View Recent Data (10 records)")
        print("  4. View Statistics")
        print("  5. Test Cloud Upload (Demo)")
        print("  6. View Log Files Location")
        print("  7. Exit")
        print("="*70)
        
        choice = input("\nPilihan: ").strip()
        
        if choice == "1":
            data = collect_sensor_data()
            print(f"\n📊 Sensor Reading:")
            print(json.dumps(data, indent=2))
            
            logger.log_to_csv(data)
            logger.log_to_json(data)
            logger.log_to_database(data)
            
            print("✅ Logged to all formats")
        
        elif choice == "2":
            demo_logging(logger, duration=30, interval=5)
        
        elif choice == "3":
            view_recent_data(logger, limit=10)
        
        elif choice == "4":
            view_statistics(logger)
        
        elif choice == "5":
            data = collect_sensor_data()
            print("\n⚠️  Demo mode (no real upload)")
            print("Setup ThingSpeak account & get API key untuk real upload")
            print(f"Data yang akan diupload: {json.dumps(data, indent=2)}")
        
        elif choice == "6":
            print(f"\n📁 Log Files:")
            print(f"  CSV: {logger.csv_file}")
            print(f"  JSON: {logger.json_file}")
            print(f"  Database: {logger.db_file}")
        
        elif choice == "7":
            break
        
        else:
            print("❌ Pilihan tidak valid")
    
    print("\n✅ Program selesai!")
    print("\n📊 Data Visualization Tools:")
    print("  - Grafana: Real-time dashboards")
    print("  - ThingSpeak: Built-in charts")
    print("  - Python matplotlib: Custom plots")
    print("  - Node-RED: Visual flow programming")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nProgram dihentikan")
