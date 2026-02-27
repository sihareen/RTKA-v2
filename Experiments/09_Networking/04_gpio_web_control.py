#!/usr/bin/env python3
"""
Bab 9.4: Kontrol GPIO via Browser
==================================
Web interface untuk kontrol LED, motor, dan sensor

Features:
- Control LED on/off via web button
- Read sensor value via AJAX
- Motor control with web joystick (simple version)
- Real-time status update

Akses di browser: http://

<raspberry-pi-ip>:5000
"""

from flask import Flask, render_template_string, jsonify, request
from flask_cors import CORS
from gpiozero import LED, Motor, DistanceSensor, Buzzer
import socket
from datetime import datetime

app = Flask(__name__)
CORS(app)

# Setup GPIO (using safe pins)
try:
    led_red = LED(7)
    led_yellow = LED(8)
    led_green = LED(24)
    
    # Motor (simplified - 1 motor for demo)
    motor = Motor(forward=17, backward=27)
    
    # Sensor
    sensor = DistanceSensor(echo=20, trigger=26, max_distance=4.0)
    
    # Buzzer
    buzzer = Buzzer(16)
    
    gpio_available = True
except Exception as e:
    print(f"⚠️  GPIO Initialization Error: {e}")
    print("Running in simulation mode...")
    gpio_available = False

print("="*70)
print("GPIO Web Control")
print("="*70)

# ============================================================================
# WEB INTERFACE
# ============================================================================

@app.route('/')
def index():
    """Main control page"""
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>GPIO Web Control - Raspberry Pi</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body {
                font-family: Arial, sans-serif;
                max-width: 900px;
                margin: 20px auto;
                padding: 20px;
                background: #1a1a1a;
                color: #fff;
            }
            .container {
                background: #2d2d2d;
                padding: 20px;
                border-radius: 10px;
                margin-bottom: 20px;
            }
            h1 {
                color: #00ff88;
                text-align: center;
            }
            h2 {
                color: #00ccff;
                border-bottom: 2px solid #00ccff;
                padding-bottom: 10px;
            }
            .led-control {
                display: flex;
                gap: 20px;
                flex-wrap: wrap;
            }
            .led-box {
                flex: 1;
                min-width: 150px;
                background: #3a3a3a;
                padding: 20px;
                border-radius: 8px;
                text-align: center;
            }
            .btn {
                padding: 15px 30px;
                font-size: 16px;
                border: none;
                border-radius: 5px;
                cursor: pointer;
                width: 100%;
                margin-top: 10px;
                transition: 0.3s;
            }
            .btn-red { background: #ff4444; color: white; }
            .btn-red:hover { background: #cc0000; }
            .btn-yellow { background: #ffaa00; color: white; }
            .btn-yellow:hover { background: #dd8800; }
            .btn-green { background: #44ff44; color: white; }
            .btn-green:hover { background: #00cc00; }
            .btn:active { transform: scale(0.95); }
            .status {
                display: inline-block;
                padding: 5px 15px;
                border-radius: 15px;
                font-weight: bold;
            }
            .status-on { background: #00ff00; color: #000; }
            .status-off { background: #666; color: #fff; }
            .sensor-value {
                font-size: 48px;
                color: #00ff88;
                text-align: center;
                margin: 20px 0;
            }
            .motor-control {
                display: grid;
                grid-template-columns: 1fr 1fr 1fr;
                gap: 10px;
                max-width: 300px;
                margin: 20px auto;
            }
            .motor-control .btn {
                padding: 20px;
                font-size: 24px;
            }
            #buzzer-btn {
                background: #ff6600;
                color: white;
            }
            #buzzer-btn:hover {
                background: #dd4400;
            }
        </style>
    </head>
    <body>
        <h1>🍓 Raspberry Pi GPIO Control</h1>
        
        <!-- LED Control -->
        <div class="container">
            <h2>💡 LED Control</h2>
            <div class="led-control">
                <div class="led-box">
                    <h3>Red LED</h3>
                    <div class="status" id="status-red">OFF</div>
                    <button class="btn btn-red" onclick="toggleLED('red')">Toggle</button>
                </div>
                <div class="led-box">
                    <h3>Yellow LED</h3>
                    <div class="status" id="status-yellow">OFF</div>
                    <button class="btn btn-yellow" onclick="toggleLED('yellow')">Toggle</button>
                </div>
                <div class="led-box">
                    <h3>Green LED</h3>
                    <div class="status" id="status-green">OFF</div>
                    <button class="btn btn-green" onclick="toggleLED('green')">Toggle</button>
                </div>
            </div>
        </div>
        
        <!-- Sensor Reading -->
        <div class="container">
            <h2>📏 Distance Sensor</h2>
            <div class="sensor-value" id="distance">-- cm</div>
            <p style="text-align: center; color: #888;">Auto-updating every second</p>
        </div>
        
        <!-- Motor Control -->
        <div class="container">
            <h2>⚙️ Motor Control</h2>
            <div class="motor-control">
                <div></div>
                <button class="btn" onclick="motorControl('forward')">▲</button>
                <div></div>
                <button class="btn" onclick="motorControl('left')">◄</button>
                <button class="btn" onclick="motorControl('stop')">■</button>
                <button class="btn" onclick="motorControl('right')">►</button>
                <div></div>
                <button class="btn" onclick="motorControl('backward')">▼</button>
                <div></div>
            </div>
        </div>
        
        <!-- Buzzer -->
        <div class="container">
            <h2>🔊 Buzzer</h2>
            <button id="buzzer-btn" class="btn" onclick="triggerBuzzer()">Beep!</button>
        </div>
        
        <script>
            // Toggle LED
            function toggleLED(color) {
                fetch(`/api/led/${color}/toggle`, {method: 'POST'})
                    .then(res => res.json())
                    .then(data => {
                        updateLEDStatus(color, data.state);
                    });
            }
            
            // Update LED status display
            function updateLEDStatus(color, state) {
                const statusEl = document.getElementById(`status-${color}`);
                statusEl.textContent = state.toUpperCase();
                statusEl.className = state === 'on' ? 'status status-on' : 'status status-off';
            }
            
            // Motor control
            function motorControl(direction) {
                fetch(`/api/motor/${direction}`, {method: 'POST'})
                    .then(res => res.json())
                    .then(data => console.log(data));
            }
            
            // Buzzer
            function triggerBuzzer() {
                fetch('/api/buzzer', {method: 'POST'})
                    .then(res => res.json())
                    .then(data => console.log(data));
            }
            
            // Update sensor reading
            function updateSensor() {
                fetch('/api/sensor/distance')
                    .then(res => res.json())
                    .then(data => {
                        document.getElementById('distance').textContent = 
                            data.distance.toFixed(2) + ' cm';
                    });
            }
            
            // Auto-update sensor every second
            setInterval(updateSensor, 1000);
            updateSensor(); // Initial call
            
            // Get initial LED states
            ['red', 'yellow', 'green'].forEach(color => {
                fetch(`/api/led/${color}`)
                    .then(res => res.json())
                    .then(data => updateLEDStatus(color, data.state));
            });
        </script>
    </body>
    </html>
    """
    return html

# =================================================================
# API ENDPOINTS
# ============================================================================

@app.route('/api/led/<color>', methods=['GET'])
def led_status(color):
    """Get LED status"""
    if not gpio_available:
        return jsonify({'state': 'off', 'simulation': True})
    
    led_map = {'red': led_red, 'yellow': led_yellow, 'green': led_green}
    led = led_map.get(color)
    
    if led:
        state = 'on' if led.is_lit else 'off'
        return jsonify({'color': color, 'state': state})
    return jsonify({'error': 'Invalid color'}), 400

@app.route('/api/led/<color>/toggle', methods=['POST'])
def led_toggle(color):
    """Toggle LED"""
    if not gpio_available:
        return jsonify({'state': 'off', 'simulation': True})
    
    led_map = {'red': led_red, 'yellow': led_yellow, 'green': led_green}
    led = led_map.get(color)
    
    if led:
        led.toggle()
        state = 'on' if led.is_lit else 'off'
        return jsonify({'color': color, 'state': state})
    return jsonify({'error': 'Invalid color'}), 400

@app.route('/api/sensor/distance')
def sensor_distance():
    """Get distance sensor reading"""
    if not gpio_available:
        import random
        return jsonify({'distance': random.uniform(5, 100), 'simulation': True})
    
    try:
        distance = sensor.distance * 100  # Convert to cm
        return jsonify({'distance': distance, 'unit': 'cm'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/motor/<direction>', methods=['POST'])
def motor_control_api(direction):
    """Control motor"""
    if not gpio_available:
        return jsonify({'direction': direction, 'simulation': True})
    
    speed = 0.5
    
    if direction == 'forward':
        motor.forward(speed)
    elif direction == 'backward':
        motor.backward(speed)
    elif direction == 'stop':
        motor.stop()
    else:
        return jsonify({'error': 'Invalid direction'}), 400
    
    return jsonify({'direction': direction, 'speed': speed})

@app.route('/api/buzzer', methods=['POST'])
def buzzer_beep():
    """Trigger buzzer beep"""
    if not gpio_available:
        return jsonify({'simulation': True})
    
    try:
        buzzer.on()
        import time
        time.sleep(0.2)
        buzzer.off()
        return jsonify({'status': 'beeped'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============================================================================
# MAIN
# ============================================================================

def get_local_ip():
    """Get local IP"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"

if __name__ == '__main__':
    ip = get_local_ip()
    port = 5000
    
    print(f"\n{'✅' if gpio_available else '⚠️ '} GPIO Status: {'Available' if gpio_available else 'Simulation Mode'}")
    print(f"\n🚀 Starting GPIO Web Control Server...")
    print(f"\n📱 Open in browser:")
    print(f"  http://{ip}:{port}")
    print(f"  http://{socket.gethostname()}.local:{port}")
    
    print(f"\n🎮 Features:")
    print(f"  ✓ LED control (Red, Yellow, Green)")
    print(f"  ✓ Distance sensor real-time reading")
    print(f"  ✓ Motor control (Forward/Backward/Stop)")
    print(f"  ✓ Buzzer beep")
    
    print(f"\n⏹️  Stop: Ctrl+C")
    print("="*70 + "\n")
    
    try:
        app.run(host='0.0.0.0', port=port, debug=True, use_reloader=False)
    except KeyboardInterrupt:
        print("\n\n🛑 Server stopped")
        if gpio_available:
            led_red.off()
            led_yellow.off()
            led_green.off()
            motor.stop()
            buzzer.off()
