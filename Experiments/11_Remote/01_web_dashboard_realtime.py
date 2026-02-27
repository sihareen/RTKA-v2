#!/usr/bin/env python3
"""
Bab 11: Advanced Web Dashboard - Remote Robot Control
======================================================
Web dashboard lengkap untuk kontrol robot dengan fitur:
1. Real-time sensor monitoring (WebSocket)
2. Motor control (maju/mundur/belok)
3. LED & Buzzer control
4. Live video stream (optional)
5. Data logging & visualization
6. Mobile-responsive design

Technology Stack:
- Flask: Web framework
- WebSocket: Real-time communication
- JavaScript: Frontend interactivity
- Chart.js: Data visualization
- Bootstrap: Responsive design

Install:
  pip3 install flask flask-socketio python-socketio simple-websocket
"""

from flask import Flask, render_template_string, jsonify, request
from flask_socketio import SocketIO, emit
import threading
import time
import json
from datetime import datetime

# Try import GPIO
try:
    from gpiozero import Robot, LED, Buzzer, DistanceSensor
    from gpiozero.pins.lgpio import LGPIOFactory
    
    factory = LGPIOFactory()
    robot = Robot(left=(22, 27), right=(17, 18), pin_factory=factory)
    status_led = LED(7, pin_factory=factory)
    buzzer = Buzzer(4, pin_factory=factory)
    sensor = DistanceSensor(echo=20, trigger=26, max_distance=4.0, pin_factory=factory)
    
    GPIO_AVAILABLE = True
except:
    GPIO_AVAILABLE = False
    print("⚠️  Running in simulation mode")

# Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'robot_secret_2024'
socketio = SocketIO(app, cors_allowed_origins="*")

# Global state
robot_state = {
    'moving': False,
    'direction': 'stopped',
    'speed': 0.7,
    'led_on': False,
    'distance': 0,
    'uptime': 0,
    'commands_executed': 0
}

sensor_data_log = []

# ============================================================================
# HTML TEMPLATE
# ============================================================================

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Robot Control Dashboard</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <script src="https://cdn.socket.io/4.5.4/socket.io.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        .header {
            text-align: center;
            color: white;
            margin-bottom: 30px;
        }
        .header h1 { font-size: 2.5em; margin-bottom: 10px; }
        .status-bar {
            background: rgba(255,255,255,0.2);
            padding: 15px;
            border-radius: 10px;
            color: white;
            margin-bottom: 20px;
            display: flex;
            justify-content: space-around;
            flex-wrap: wrap;
        }
        .status-item {
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .status-dot {
            width: 12px;
            height: 12px;
            border-radius: 50%;
            background: #4ade80;
            animation: pulse 2s infinite;
        }
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }
        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 20px;
        }
        .card {
            background: white;
            border-radius: 15px;
            padding: 25px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }
        .card h2 {
            color: #667eea;
            margin-bottom: 20px;
            font-size: 1.5em;
        }
        .control-buttons {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 10px;
            margin-top: 15px;
        }
        .btn {
            padding: 15px;
            border: none;
            border-radius: 10px;
            font-size: 1.1em;
            cursor: pointer;
            transition: all 0.3s;
            font-weight: bold;
        }
        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(0,0,0,0.2);
        }
        .btn:active {
            transform: translateY(0);
        }
        .btn-forward { background: #4ade80; grid-column: 2; }
        .btn-left { background: #fbbf24; grid-column: 1; grid-row: 2; }
        .btn-stop { background: #ef4444; grid-column: 2; grid-row: 2; }
        .btn-right { background: #fbbf24; grid-column: 3; grid-row: 2; }
        .btn-backward { background: #4ade80; grid-column: 2; grid-row: 3; }
        .btn-led { background: #60a5fa; }
        .btn-buzzer { background: #f87171; }
        .sensor-display {
            text-align: center;
            padding: 30px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-radius: 10px;
            color: white;
        }
        .sensor-value {
            font-size: 3em;
            font-weight: bold;
            margin: 10px 0;
        }
        .speed-control {
            margin: 20px 0;
        }
        .speed-slider {
            width: 100%;
            height: 8px;
            border-radius: 5px;
            outline: none;
        }
        #distanceChart {
            max-height: 250px;
        }
        .log-container {
            max-height: 200px;
            overflow-y: auto;
            background: #f3f4f6;
            padding: 15px;
            border-radius: 8px;
            font-family: monospace;
            font-size: 0.9em;
        }
        .log-entry {
            padding: 5px;
            border-bottom: 1px solid #e5e7eb;
        }
        @media (max-width: 768px) {
            .control-buttons {
                grid-template-columns: repeat(3, 1fr);
            }
            .header h1 { font-size: 1.8em; }
            .btn { padding: 12px; font-size: 1em; }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🤖 Robot Control Dashboard</h1>
            <p>Real-time Monitoring & Control</p>
        </div>
        
        <div class="status-bar">
            <div class="status-item">
                <div class="status-dot" id="connectionDot"></div>
                <span id="connectionStatus">Connecting...</span>
            </div>
            <div class="status-item">
                <span>⏱️ Uptime: <span id="uptime">0</span>s</span>
            </div>
            <div class="status-item">
                <span>📊 Commands: <span id="commandCount">0</span></span>
            </div>
            <div class="status-item">
                <span>🎮 Status: <span id="robotStatus">Stopped</span></span>
            </div>
        </div>
        
        <div class="grid">
            <!-- Movement Control -->
            <div class="card">
                <h2>🎮 Movement Control</h2>
                <div class="speed-control">
                    <label>Speed: <span id="speedValue">70</span>%</label>
                    <input type="range" class="speed-slider" id="speedSlider" 
                           min="0" max="100" value="70">
                </div>
                <div class="control-buttons">
                    <button class="btn btn-forward" onclick="moveRobot('forward')">⬆️</button>
                    <button class="btn btn-left" onclick="moveRobot('left')">⬅️</button>
                    <button class="btn btn-stop" onclick="moveRobot('stop')">⏹️</button>
                    <button class="btn btn-right" onclick="moveRobot('right')">➡️</button>
                    <button class="btn btn-backward" onclick="moveRobot('backward')">⬇️</button>
                </div>
            </div>
            
            <!-- Sensors -->
            <div class="card">
                <h2>📡 Sensors</h2>
                <div class="sensor-display">
                    <div>Distance Sensor</div>
                    <div class="sensor-value" id="distance">--</div>
                    <div>centimeters</div>
                </div>
            </div>
            
            <!-- Accessories -->
            <div class="card">
                <h2>💡 Accessories</h2>
                <button class="btn btn-led" onclick="toggleLED()" style="width: 100%; margin-bottom: 10px;">
                    LED: <span id="ledStatus">OFF</span>
                </button>
                <button class="btn btn-buzzer" onclick="buzzerBeep()" style="width: 100%;">
                    🔊 Buzzer Beep
                </button>
            </div>
        </div>
        
        <!-- Chart & Logs -->
        <div class="grid">
            <div class="card">
                <h2>📈 Distance Chart</h2>
                <canvas id="distanceChart"></canvas>
            </div>
            
            <div class="card">
                <h2>📜 Activity Log</h2>
                <div class="log-container" id="logContainer"></div>
            </div>
        </div>
    </div>
    
    <script>
        const socket = io();
        let chart;
        const maxDataPoints = 20;
        const distanceData = {
            labels: [],
            datasets: [{
                label: 'Distance (cm)',
                data: [],
                borderColor: '#667eea',
                backgroundColor: 'rgba(102, 126, 234, 0.1)',
                tension: 0.4,
                fill: true
            }]
        };
        
        // Initialize chart
        const ctx = document.getElementById('distanceChart').getContext('2d');
        chart = new Chart(ctx, {
            type: 'line',
            data: distanceData,
            options: {
                responsive: true,
                maintainAspectRatio: true,
                scales: {
                    y: { beginAtZero: true, max: 100 }
                },
                animation: { duration: 500 }
            }
        });
        
        // Socket events
        socket.on('connect', () => {
            updateConnectionStatus(true);
            addLog('Connected to robot');
        });
        
        socket.on('disconnect', () => {
            updateConnectionStatus(false);
            addLog('Disconnected from robot');
        });
        
        socket.on('sensor_update', (data) => {
            document.getElementById('distance').textContent = data.distance.toFixed(1);
            document.getElementById('uptime').textContent = data.uptime;
            document.getElementById('commandCount').textContent = data.commands;
            
            // Update chart
            const time = new Date().toLocaleTimeString();
            distanceData.labels.push(time);
            distanceData.datasets[0].data.push(data.distance);
            
            if (distanceData.labels.length > maxDataPoints) {
                distanceData.labels.shift();
                distanceData.datasets[0].data.shift();
            }
            
            chart.update();
        });
        
        socket.on('robot_status', (data) => {
            document.getElementById('robotStatus').textContent = data.status;
            document.getElementById('ledStatus').textContent = data.led_on ? 'ON' : 'OFF';
        });
        
        socket.on('log_message', (msg) => {
            addLog(msg);
        });
        
        // Control functions
        function moveRobot(direction) {
            const speed = document.getElementById('speedSlider').value / 100;
            socket.emit('move_command', { direction, speed });
            addLog(`Move: ${direction} (${(speed*100).toFixed(0)}%)`);
        }
        
        function toggleLED() {
            socket.emit('led_toggle');
        }
        
        function buzzerBeep() {
            socket.emit('buzzer_beep');
            addLog('Buzzer activated');
        }
        
        function updateConnectionStatus(connected) {
            const dot = document.getElementById('connectionDot');
            const status = document.getElementById('connectionStatus');
            if (connected) {
                dot.style.background = '#4ade80';
                status.textContent = 'Connected';
            } else {
                dot.style.background = '#ef4444';
                status.textContent = 'Disconnected';
            }
        }
        
        function addLog(message) {
            const container = document.getElementById('logContainer');
            const time = new Date().toLocaleTimeString();
            const entry = document.createElement('div');
            entry.className = 'log-entry';
            entry.textContent = `[${time}] ${message}`;
            container.insertBefore(entry, container.firstChild);
            
            // Keep max 50 entries
            while (container.children.length > 50) {
                container.removeChild(container.lastChild);
            }
        }
        
        // Speed slider
        document.getElementById('speedSlider').addEventListener('input', (e) => {
            document.getElementById('speedValue').textContent = e.target.value;
        });
        
        // Keyboard control
        document.addEventListener('keydown', (e) => {
            if (e.repeat) return;
            
            const key = e.key.toLowerCase();
            const keyMap = {
                'w': 'forward',
                'arrowup': 'forward',
                's': 'backward',
                'arrowdown': 'backward',
                'a': 'left',
                'arrowleft': 'left',
                'd': 'right',
                'arrowright': 'right',
                ' ': 'stop'
            };
            
            if (keyMap[key]) {
                e.preventDefault();
                moveRobot(keyMap[key]);
            }
        });
    </script>
</body>
</html>
'''

# ============================================================================
# WEBSOCKET HANDLERS
# ============================================================================

@socketio.on('connect')
def handle_connect():
    print('📱 Client connected')
    emit('robot_status', robot_state)

@socketio.on('disconnect')
def handle_disconnect():
    print('📱 Client disconnected')
    if GPIO_AVAILABLE:
        robot.stop()

@socketio.on('move_command')
def handle_move(data):
    direction = data.get('direction')
    speed = data.get('speed', 0.7)
    
    robot_state['commands_executed'] += 1
    
    if GPIO_AVAILABLE:
        if direction == 'forward':
            robot.forward(speed)
            robot_state['direction'] = 'forward'
            robot_state['moving'] = True
        elif direction == 'backward':
            robot.backward(speed)
            robot_state['direction'] = 'backward'
            robot_state['moving'] = True
        elif direction == 'left':
            robot.left(speed)
            robot_state['direction'] = 'left'
            robot_state['moving'] = True
        elif direction == 'right':
            robot.right(speed)
            robot_state['direction'] = 'right'
            robot_state['moving'] = True
        elif direction == 'stop':
            robot.stop()
            robot_state['direction'] = 'stopped'
            robot_state['moving'] = False
    else:
        robot_state['direction'] = direction
        robot_state['moving'] = direction != 'stop'
    
    robot_state['speed'] = speed
    emit('robot_status', robot_state, broadcast=True)
    emit('log_message', f"Command: {direction}", broadcast=True)

@socketio.on('led_toggle')
def handle_led_toggle():
    if GPIO_AVAILABLE:
        status_led.toggle()
        robot_state['led_on'] = status_led.is_lit
    else:
        robot_state['led_on'] = not robot_state['led_on']
    
    emit('robot_status', robot_state, broadcast=True)
    emit('log_message', f"LED: {'ON' if robot_state['led_on'] else 'OFF'}", broadcast=True)

@socketio.on('buzzer_beep')
def handle_buzzer():
    if GPIO_AVAILABLE:
        buzzer.beep(on_time=0.1, n=2)
    emit('log_message', "Buzzer activated", broadcast=True)

# ============================================================================
# ROUTES
# ============================================================================

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/status')
def api_status():
    return jsonify(robot_state)

# ============================================================================
# BACKGROUND TASKS
# ============================================================================

def sensor_update_loop():
    """Broadcast sensor data periodically"""
    start_time = time.time()
    
    while True:
        try:
            # Get distance
            if GPIO_AVAILABLE:
                try:
                    distance = sensor.distance * 100
                except:
                    distance = 0
            else:
                import random
                distance = random.uniform(10, 100)
            
            robot_state['distance'] = round(distance, 1)
            robot_state['uptime'] = int(time.time() - start_time)
            
            # Broadcast to all clients
            socketio.emit('sensor_update', {
                'distance': robot_state['distance'],
                'uptime': robot_state['uptime'],
                'commands': robot_state['commands_executed']
            })
            
            time.sleep(0.5)  # Update every 500ms
        
        except Exception as e:
            print(f"Error in sensor loop: {e}")
            time.sleep(1)

# ============================================================================
# MAIN
# ============================================================================

def main():
    print("\n" + "="*70)
    print("🌐 Advanced Web Dashboard - Robot Control")
    print("="*70)
    print()
    print("Features:")
    print("  ✓ Real-time sensor monitoring")
    print("  ✓ WebSocket communication")
    print("  ✓ Live distance chart")
    print("  ✓ Keyboard control (WASD/Arrows)")
    print("  ✓ Mobile-responsive design")
    print("  ✓ Activity logging")
    print()
    print("Starting server...")
    print()
    
    # Start sensor update thread
    sensor_thread = threading.Thread(target=sensor_update_loop, daemon=True)
    sensor_thread.start()
    
    # Get local IP
    import socket
    hostname = socket.gethostname()
    local_ip = socket.gethostbyname(hostname)
    
    print("✅ Server ready!")
    print()
    print(f"🌐 Open in browser:")
    print(f"   Local:   http://localhost:5000")
    print(f"   Network: http://{local_ip}:5000")
    print()
    print("⌨️  Keyboard Controls:")
    print("   W/↑ = Forward")
    print("   S/↓ = Backward")
    print("   A/← = Left")
    print("   D/→ = Right")
    print("   Space = Stop")
    print()
    print("Press Ctrl+C to stop")
    print()
    
    # Run Flask-SocketIO
    socketio.run(app, host='0.0.0.0', port=5000, debug=False)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n🛑 Server stopped")
        if GPIO_AVAILABLE:
            robot.stop()
            status_led.off()
