#!/usr/bin/env python3
"""
Bab 12 Mini Project #3: IoT Monitoring Robot
=============================================
Robot dengan IoT cloud connectivity dan monitoring:
1. MQTT cloud integration
2. Real-time telemetry
3. Remote commands
4. Data analytics
5. Alert system
6. Historical tracking

Install:
  sudo apt install mosquitto mosquitto-clients
  pip3 install paho-mqtt flask requests

Cloud MQTT Brokers (Free):
- HiveMQ: broker.hivemq.com:1883
- Eclipse: mqtt.eclipseprojects.io:1883
- EMQX: broker.emqx.io:1883
"""

from gpiozero import Robot, DistanceSensor, LED, Buzzer
from gpiozero.pins.lgpio import LGPIOFactory
import paho.mqtt.client as mqtt
import json
import time
from datetime import datetime
import threading
import sqlite3
from flask import Flask, render_template_string, jsonify
import socket

# Setup GPIO
factory = LGPIOFactory()
robot = Robot(left=(22, 27), right=(17, 18), pin_factory=factory)
sensor = DistanceSensor(echo=20, trigger=26, max_distance=4.0, pin_factory=factory)
status_led = LED(7, pin_factory=factory)
buzzer = Buzzer(4, pin_factory=factory)

# MQTT Configuration
MQTT_BROKER = "broker.hivemq.com"  # Free public broker
MQTT_PORT = 1883
DEVICE_ID = f"rtka_robot_{socket.gethostname()}"
TOPIC_TELEMETRY = f"rtka/{DEVICE_ID}/telemetry"
TOPIC_COMMAND = f"rtka/{DEVICE_ID}/command"
TOPIC_STATUS = f"rtka/{DEVICE_ID}/status"
TOPIC_ALERT = f"rtka/{DEVICE_ID}/alert"

# Database
DB_FILE = "iot_robot.db"

# Flask app for monitoring dashboard
app = Flask(__name__)

# ============================================================================
# DATABASE SETUP
# ============================================================================

def init_database():
    """Initialize database for telemetry storage"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS telemetry (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            distance_cm REAL,
            robot_state TEXT,
            battery_level INTEGER,
            cpu_temp REAL,
            uptime INTEGER
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS commands (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            command TEXT,
            source TEXT,
            executed BOOLEAN DEFAULT 0
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            alert_type TEXT,
            message TEXT,
            severity TEXT
        )
    ''')
    
    conn.commit()
    conn.close()
    print("💾 Database initialized")

def log_telemetry(distance, state, battery=100, cpu_temp=50, uptime=0):
    """Log telemetry data"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO telemetry (distance_cm, robot_state, battery_level, cpu_temp, uptime)
        VALUES (?, ?, ?, ?, ?)
    ''', (distance, state, battery, cpu_temp, uptime))
    
    conn.commit()
    conn.close()

def log_command(command, source):
    """Log received command"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO commands (command, source, executed)
        VALUES (?, ?, 1)
    ''', (command, source))
    
    conn.commit()
    conn.close()

def create_alert(alert_type, message, severity='warning'):
    """Create alert"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO alerts (alert_type, message, severity)
        VALUES (?, ?, ?)
    ''', (alert_type, message, severity))
    
    conn.commit()
    conn.close()

# ============================================================================
# IoT ROBOT CLASS
# ============================================================================

class IoTRobot:
    """IoT-enabled robot with cloud connectivity"""
    
    def __init__(self):
        self.mqtt_client = mqtt.Client(DEVICE_ID)
        self.connected = False
        self.running = False
        
        # State
        self.state = {
            'mode': 'idle',
            'distance': 0,
            'battery': 100,
            'uptime': 0,
            'commands_received': 0,
            'telemetry_sent': 0
        }
        
        self.start_time = time.time()
        
        # MQTT callbacks
        self.mqtt_client.on_connect = self.on_mqtt_connect
        self.mqtt_client.on_disconnect = self.on_mqtt_disconnect
        self.mqtt_client.on_message = self.on_mqtt_message
    
    def log(self, message):
        """Log with timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {message}")
    
    def on_mqtt_connect(self, client, userdata, flags, rc):
        """MQTT connection callback"""
        if rc == 0:
            self.log(f"✅ Connected to MQTT broker: {MQTT_BROKER}")
            self.connected = True
            
            # Subscribe to command topic
            client.subscribe(TOPIC_COMMAND)
            self.log(f"📥 Subscribed to: {TOPIC_COMMAND}")
            
            # Send online status
            self.publish_status("online")
        else:
            self.log(f"❌ MQTT connection failed: {rc}")
    
    def on_mqtt_disconnect(self, client, userdata, rc):
        """MQTT disconnection callback"""
        self.log(f"📡 Disconnected from MQTT broker")
        self.connected = False
    
    def on_mqtt_message(self, client, userdata, msg):
        """MQTT message callback"""
        try:
            payload = msg.payload.decode()
            self.log(f"📨 Command received: {payload}")
            
            # Parse JSON command
            command_data = json.loads(payload)
            command = command_data.get('command')
            
            # Log command
            log_command(command, 'mqtt')
            self.state['commands_received'] += 1
            
            # Execute command
            self.execute_command(command)
        
        except Exception as e:
            self.log(f"⚠️  Error processing message: {e}")
    
    def execute_command(self, command):
        """Execute received command"""
        self.log(f"⚙️  Executing: {command}")
        
        if command == "forward":
            robot.forward(0.7)
            self.state['mode'] = 'moving_forward'
            status_led.on()
        
        elif command == "backward":
            robot.backward(0.7)
            self.state['mode'] = 'moving_backward'
        
        elif command == "left":
            robot.left(0.6)
            self.state['mode'] = 'turning_left'
        
        elif command == "right":
            robot.right(0.6)
            self.state['mode'] = 'turning_right'
        
        elif command == "stop":
            robot.stop()
            self.state['mode'] = 'idle'
            status_led.off()
        
        elif command == "beep":
            buzzer.beep(on_time=0.1, n=2, background=True)
        
        elif command == "status":
            self.publish_status("online")
        
        elif command == "scan":
            distance = sensor.distance * 100
            self.publish_telemetry()
        
        else:
            self.log(f"⚠️  Unknown command: {command}")
    
    def connect_mqtt(self):
        """Connect to MQTT broker"""
        try:
            self.log(f"🔌 Connecting to {MQTT_BROKER}:{MQTT_PORT}...")
            
            # Set last will
            will_payload = json.dumps({
                'device_id': DEVICE_ID,
                'status': 'offline',
                'timestamp': datetime.now().isoformat()
            })
            self.mqtt_client.will_set(TOPIC_STATUS, will_payload, qos=1, retain=True)
            
            # Connect
            self.mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
            self.mqtt_client.loop_start()
            
            # Wait for connection
            timeout = 10
            while not self.connected and timeout > 0:
                time.sleep(0.5)
                timeout -= 0.5
            
            return self.connected
        
        except Exception as e:
            self.log(f"❌ MQTT connection error: {e}")
            return False
    
    def publish_telemetry(self):
        """Publish telemetry data"""
        try:
            # Get sensor data
            distance = sensor.distance * 100
            self.state['distance'] = distance
            
            # Get system stats
            self.state['uptime'] = int(time.time() - self.start_time)
            
            # Simulate battery (would read from ADC in real robot)
            self.state['battery'] = max(10, 100 - (self.state['uptime'] // 60))
            
            # Create telemetry payload
            telemetry = {
                'device_id': DEVICE_ID,
                'timestamp': datetime.now().isoformat(),
                'distance_cm': round(distance, 2),
                'mode': self.state['mode'],
                'battery_level': self.state['battery'],
                'uptime': self.state['uptime'],
                'commands_received': self.state['commands_received'],
                'telemetry_sent': self.state['telemetry_sent']
            }
            
            # Publish
            payload = json.dumps(telemetry)
            result = self.mqtt_client.publish(TOPIC_TELEMETRY, payload, qos=1)
            
            if result.rc == 0:
                self.state['telemetry_sent'] += 1
                
                # Log to database
                log_telemetry(
                    distance, 
                    self.state['mode'],
                    self.state['battery'],
                    50,  # CPU temp placeholder
                    self.state['uptime']
                )
                
                # Check for alerts
                if distance < 15:
                    self.publish_alert('obstacle', f'Obstacle detected at {distance:.1f} cm', 'warning')
                
                if self.state['battery'] < 20:
                    self.publish_alert('low_battery', f'Battery low: {self.state["battery"]}%', 'warning')
                
                return True
            else:
                self.log("❌ Telemetry publish failed")
                return False
        
        except Exception as e:
            self.log(f"⚠️  Error publishing telemetry: {e}")
            return False
    
    def publish_status(self, status):
        """Publish device status"""
        status_data = {
            'device_id': DEVICE_ID,
            'status': status,
            'timestamp': datetime.now().isoformat(),
            'mode': self.state['mode'],
            'uptime': self.state['uptime']
        }
        
        payload = json.dumps(status_data)
        self.mqtt_client.publish(TOPIC_STATUS, payload, qos=1, retain=True)
        self.log(f"📤 Status: {status}")
    
    def publish_alert(self, alert_type, message, severity='warning'):
        """Publish alert"""
        alert_data = {
            'device_id': DEVICE_ID,
            'timestamp': datetime.now().isoformat(),
            'type': alert_type,
            'message': message,
            'severity': severity
        }
        
        payload = json.dumps(alert_data)
        self.mqtt_client.publish(TOPIC_ALERT, payload, qos=1)
        
        # Log to database
        create_alert(alert_type, message, severity)
        
        # Visual/audio alert
        if severity == 'critical':
            buzzer.beep(on_time=0.2, n=3, background=True)
            status_led.blink(on_time=0.1, off_time=0.1)
    
    def run(self):
        """Main run loop"""
        self.running = True
        
        print("\n" + "="*70)
        print("🌐 IoT Monitoring Robot")
        print("="*70)
        print(f"\nDevice ID: {DEVICE_ID}")
        print(f"MQTT Broker: {MQTT_BROKER}")
        print(f"\nTopics:")
        print(f"  📤 Telemetry: {TOPIC_TELEMETRY}")
        print(f"  📥 Commands: {TOPIC_COMMAND}")
        print(f"  📊 Status: {TOPIC_STATUS}")
        print(f"  🚨 Alerts: {TOPIC_ALERT}")
        print()
        print("Press Ctrl+C to stop")
        print()
        
        # Connect to MQTT
        if not self.connect_mqtt():
            self.log("❌ Failed to connect to MQTT broker")
            return
        
        # Main loop
        try:
            while self.running:
                # Publish telemetry every 5 seconds
                self.publish_telemetry()
                
                # Display current stats
                self.log(f"📊 Distance: {self.state['distance']:.1f} cm | "
                        f"Mode: {self.state['mode']} | "
                        f"Battery: {self.state['battery']}% | "
                        f"Uptime: {self.state['uptime']}s")
                
                time.sleep(5)
        
        except KeyboardInterrupt:
            self.log("\n⏸️  Stopped by user")
        
        finally:
            self.stop()
    
    def stop(self):
        """Stop robot and disconnect"""
        self.running = False
        robot.stop()
        status_led.off()
        buzzer.off()
        
        if self.connected:
            self.publish_status("offline")
            self.mqtt_client.loop_stop()
            self.mqtt_client.disconnect()
        
        self.log("🛑 Robot stopped")
        self.print_stats()
    
    def print_stats(self):
        """Print session statistics"""
        print("\n" + "="*70)
        print("📊 Session Statistics")
        print("="*70)
        print(f"Uptime: {self.state['uptime']} seconds")
        print(f"Commands Received: {self.state['commands_received']}")
        print(f"Telemetry Messages Sent: {self.state['telemetry_sent']}")
        print(f"Final Battery: {self.state['battery']}%")
        print("="*70)

# ============================================================================
# MONITORING DASHBOARD (Flask)
# ============================================================================

HTML_DASHBOARD = '''
<!DOCTYPE html>
<html>
<head>
    <title>IoT Robot Monitor</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <meta http-equiv="refresh" content="5">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: Arial, sans-serif;
            background: #0a0e27;
            color: white;
            padding: 20px;
        }
        .container { max-width: 1200px; margin: 0 auto; }
        h1 {
            text-align: center;
            margin-bottom: 20px;
            background: linear-gradient(45deg, #667eea, #764ba2);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        .stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-bottom: 20px;
        }
        .stat-card {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            border-radius: 10px;
            text-align: center;
        }
        .stat-value { font-size: 2.5em; font-weight: bold; }
        .stat-label { margin-top: 10px; opacity: 0.9; }
        table {
            width: 100%;
            background: rgba(255,255,255,0.05);
            border-radius: 10px;
            overflow: hidden;
        }
        th, td {
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid rgba(255,255,255,0.1);
        }
        th {
            background: rgba(102, 126, 234, 0.3);
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🌐 IoT Robot Monitoring Dashboard</h1>
        
        <div class="stats">
            <div class="stat-card">
                <div class="stat-value">{{ total }}</div>
                <div class="stat-label">Total Records</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{{ avg_distance }}</div>
                <div class="stat-label">Avg Distance (cm)</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{{ commands }}</div>
                <div class="stat-label">Commands Executed</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{{ alerts }}</div>
                <div class="stat-label">Alerts</div>
            </div>
        </div>
        
        <h2>Recent Telemetry</h2>
        <table>
            <thead>
                <tr>
                    <th>Timestamp</th>
                    <th>Distance</th>
                    <th>State</th>
                    <th>Battery</th>
                    <th>Uptime</th>
                </tr>
            </thead>
            <tbody>
                {% for row in telemetry %}
                <tr>
                    <td>{{ row[1] }}</td>
                    <td>{{ "%.2f"|format(row[2]) }} cm</td>
                    <td>{{ row[3] }}</td>
                    <td>{{ row[4] }}%</td>
                    <td>{{ row[6] }}s</td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </div>
</body>
</html>
'''

@app.route('/')
def dashboard():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # Get statistics
    cursor.execute('SELECT COUNT(*), AVG(distance_cm) FROM telemetry')
    stats = cursor.fetchone()
    
    cursor.execute('SELECT COUNT(*) FROM commands')
    commands = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM alerts')
    alerts = cursor.fetchone()[0]
    
    # Get recent telemetry
    cursor.execute('SELECT * FROM telemetry ORDER BY id DESC LIMIT 20')
    telemetry = cursor.fetchall()
    
    conn.close()
    
    return render_template_string(HTML_DASHBOARD,
                                total=stats[0] or 0,
                                avg_distance=f"{stats[1]:.2f}" if stats[1] else "0.00",
                                commands=commands,
                                alerts=alerts,
                                telemetry=telemetry)

# ============================================================================
# MAIN
# ============================================================================

def main():
    # Initialize database
    init_database()
    
    print("\n📋 IoT Monitoring Robot")
    print("="*70)
    print("\nSelect mode:")
    print("  1. Run IoT Robot (with MQTT)")
    print("  2. View Monitoring Dashboard")
    print("  3. Test MQTT Connection")
    print("  4. Send Test Command")
    print("  5. Exit")
    
    choice = input("\nChoice: ").strip()
    
    if choice == "1":
        iot_robot = IoTRobot()
        iot_robot.run()
    
    elif choice == "2":
        print("\n🌐 Starting monitoring dashboard...")
        print("   Open http://localhost:8080")
        app.run(host='0.0.0.0', port=8080, debug=False)
    
    elif choice == "3":
        print("\n🔌 Testing MQTT connection...")
        test_client = mqtt.Client("test_client")
        try:
            test_client.connect(MQTT_BROKER, MQTT_PORT, 60)
            print("✅ Connection successful!")
            test_client.disconnect()
        except Exception as e:
            print(f"❌ Connection failed: {e}")
    
    elif choice == "4":
        print("\n📤 Send test command to robot")
        print(f"   Topic: {TOPIC_COMMAND}")
        print("\nCommands: forward, backward, left, right, stop, beep, status")
        command = input("Command: ").strip()
        
        client = mqtt.Client("commander")
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
        payload = json.dumps({'command': command})
        client.publish(TOPIC_COMMAND, payload)
        print(f"✅ Command sent: {command}")
        client.disconnect()
    
    elif choice == "5":
        pass
    
    else:
        print("❌ Invalid choice")

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(f"\n❌ Error: {e}")
    finally:
        robot.stop()
        status_led.off()
