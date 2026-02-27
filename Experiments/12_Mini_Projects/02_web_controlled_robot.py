#!/usr/bin/env python3
"""
Bab 12 Mini Project #2: Web-Controlled Robot with Live Monitoring
==================================================================
Robot yang bisa dikontrol via web dengan fitur:
1. Real-time video stream (optional dengan Pi Camera)
2. WebSocket untuk kontrol real-time
3. Sensor monitoring dashboard
4. Keyboard & touch control
5. Route recording & playback

Install:
  pip3 install flask flask-socketio opencv-python picamera2

Note: Picamera2 hanya untuk Raspberry Pi dengan camera module
"""

from flask import Flask, render_template_string, Response
from flask_socketio import SocketIO, emit
from gpiozero import Robot, DistanceSensor, LED, Buzzer
from gpiozero.pins.lgpio import LGPIOFactory
import time
import json
from datetime import datetime
import threading

# Try import camera (optional)
try:
    from picamera2 import Picamera2
    import cv2
    CAMERA_AVAILABLE = True
except:
    CAMERA_AVAILABLE = False
    print("⚠️  Camera not available (PiCamera2 not installed)")

# Setup
factory = LGPIOFactory()
robot = Robot(left=(22, 27), right=(17, 18), pin_factory=factory)
sensor = DistanceSensor(echo=20, trigger=26, max_distance=4.0, pin_factory=factory)
status_led = LED(7, pin_factory=factory)
buzzer = Buzzer(4, pin_factory=factory)

app = Flask(__name__)
app.config['SECRET_KEY'] = 'web_robot_2024'
socketio = SocketIO(app, cors_allowed_origins="*")

# Global state
robot_state = {
    'speed': 0.7,
    'direction': 'stopped',
    'distance': 0,
    'recording': False,
    'route': []
}

# ============================================================================
# COMPLETE HTML INTERFACE
# ============================================================================

HTML_INTERFACE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Web Robot Control</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <script src="https://cdn.socket.io/4.5.4/socket.io.min.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: Arial, sans-serif;
            background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
            color: white;
            padding: 15px;
            user-select: none;
        }
        .container { max-width: 1400px; margin: 0 auto; }
        .header {
            text-align: center;
            margin-bottom: 20px;
        }
        .header h1 { font-size: 2.2em; margin-bottom: 5px; }
        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
            gap: 15px;
        }
        .card {
            background: rgba(255,255,255,0.1);
            backdrop-filter: blur(10px);
            border-radius: 15px;
            padding: 20px;
            border: 1px solid rgba(255,255,255,0.2);
        }
        .card h2 {
            margin-bottom: 15px;
            color: #ffd700;
            font-size: 1.3em;
        }
        .video-container {
            width: 100%;
            aspect-ratio: 16/9;
            background: #000;
            border-radius: 10px;
            display: flex;
            align-items: center;
            justify-content: center;
            margin-bottom: 15px;
        }
        .video-container img {
            width: 100%;
            height: 100%;
            object-fit: cover;
            border-radius: 10px;
        }
        .joystick {
            display: grid;
            grid-template-columns: repeat(3, 80px);
            grid-template-rows: repeat(3, 80px);
            gap: 10px;
            justify-content: center;
            margin: 20px 0;
        }
        .joystick-btn {
            border: 2px solid #fff;
            background: rgba(255,255,255,0.2);
            border-radius: 50%;
            font-size: 1.8em;
            cursor: pointer;
            transition: all 0.1s;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .joystick-btn:active {
            background: rgba(255,255,255,0.4);
            transform: scale(0.95);
        }
        .joystick-btn:nth-child(1) { grid-column: 2; grid-row: 1; }
        .joystick-btn:nth-child(2) { grid-column: 1; grid-row: 2; }
        .joystick-btn:nth-child(3) { grid-column: 2; grid-row: 2; }
        .joystick-btn:nth-child(4) { grid-column: 3; grid-row: 2; }
        .joystick-btn:nth-child(5) { grid-column: 2; grid-row: 3; }
        .sensor-panel {
            background: rgba(0,0,0,0.3);
            padding: 20px;
            border-radius: 10px;
            text-align: center;
        }
        .sensor-value {
            font-size: 3.5em;
            font-weight: bold;
            color: #4ade80;
            text-shadow: 0 0 10px rgba(74,222,128,0.5);
        }
        .status-bar {
            display: flex;
            justify-content: space-around;
            padding: 15px;
            background: rgba(0,0,0,0.3);
            border-radius: 10px;
            margin-bottom: 15px;
            flex-wrap: wrap;
            gap: 10px;
        }
        .status-item {
            display: flex;
            align-items: center;
            gap: 8px;
        }
        .btn {
            padding: 12px 20px;
            border: none;
            border-radius: 8px;
            font-weight: bold;
            cursor: pointer;
            transition: all 0.3s;
            width: 100%;
            margin: 5px 0;
        }
        .btn-primary { background: #3b82f6; color: white; }
        .btn-success { background: #10b981; color: white; }
        .btn-danger { background: #ef4444; color: white; }
        .btn-warning { background: #f59e0b; color: white; }
        .btn:active { transform: scale(0.95); }
        .slider-container {
            margin: 15px 0;
        }
        .slider {
            width: 100%;
            height: 6px;
            border-radius: 5px;
            outline: none;
        }
        .route-list {
            max-height: 200px;
            overflow-y: auto;
            background: rgba(0,0,0,0.3);
            padding: 10px;
            border-radius: 8px;
            font-family: monospace;
            font-size: 0.9em;
        }
        .route-item {
            padding: 5px;
            border-bottom: 1px solid rgba(255,255,255,0.1);
        }
        @media (max-width: 768px) {
            .joystick {
                grid-template-columns: repeat(3, 70px);
                grid-template-rows: repeat(3, 70px);
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚗 Web-Controlled Robot</h1>
            <p>Real-time Control & Monitoring</p>
        </div>
        
        <div class="status-bar">
            <div class="status-item">
                <span>🔌 Status:</span>
                <span id="connStatus">Connecting...</span>
            </div>
            <div class="status-item">
                <span>🎮 Mode:</span>
                <span id="robotMode">Manual</span>
            </div>
            <div class="status-item">
                <span>⚡ Speed:</span>
                <span id="speedDisplay">70%</span>
            </div>
            <div class="status-item">
                <span>📏 Distance:</span>
                <span id="distanceDisplay">-- cm</span>
            </div>
        </div>
        
        <div class="grid">
            <!-- Video & Control -->
            <div class="card">
                <h2>📹 Camera Feed</h2>
                <div class="video-container">
                    <img id="videoFeed" src="/video_feed" alt="Video feed" 
                         onerror="this.src='data:image/svg+xml,%3Csvg xmlns=\\'http://www.w3.org/2000/svg\\' width=\\'300\\' height=\\'200\\'%3E%3Crect width=\\'300\\' height=\\'200\\' fill=\\'%23333\\'/%3E%3Ctext x=\\'50%25\\' y=\\'50%25\\' fill=\\'white\\' text-anchor=\\'middle\\'%3ENo Camera%3C/text%3E%3C/svg%3E'">
                </div>
                
                <h2>🎮 Control</h2>
                <div class="joystick">
                    <button class="joystick-btn" onmousedown="move('forward')" onmouseup="move('stop')" ontouchstart="move('forward')" ontouchend="move('stop')">⬆️</button>
                    <button class="joystick-btn" onmousedown="move('left')" onmouseup="move('stop')" ontouchstart="move('left')" ontouchend="move('stop')">⬅️</button>
                    <button class="joystick-btn" onmousedown="move('stop')" ontouchstart="move('stop')">⏹️</button>
                    <button class="joystick-btn" onmousedown="move('right')" onmouseup="move('stop')" ontouchstart="move('right')" ontouchend="move('stop')">➡️</button>
                    <button class="joystick-btn" onmousedown="move('backward')" onmouseup="move('stop')" ontouchstart="move('backward')" ontouchend="move('stop')">⬇️</button>
                </div>
                
                <div class="slider-container">
                    <label>Speed Control</label>
                    <input type="range" class="slider" id="speedSlider" min="0" max="100" value="70" oninput="updateSpeed(this.value)">
                </div>
            </div>
            
            <!-- Sensors -->
            <div class="card">
                <h2>📡 Sensors</h2>
                <div class="sensor-panel">
                    <div>Ultrasonic Distance</div>
                    <div class="sensor-value" id="sensorDistance">--</div>
                    <div style="margin-top: 10px;">centimeters</div>
                </div>
                
                <h2 style="margin-top: 20px;">💡 Accessories</h2>
                <button class="btn btn-primary" onclick="toggleLED()">
                    LED: <span id="ledStatus">OFF</span>
                </button>
                <button class="btn btn-warning" onclick="honk()">
                    🔊 Honk
                </button>
            </div>
            
            <!-- Route Recording -->
            <div class="card">
                <h2>📍 Route Recording</h2>
                <button class="btn btn-success" onclick="startRecording()" id="recBtn">
                    ⏺️ Start Recording
                </button>
                <button class="btn btn-danger" onclick="stopRecording()">
                    ⏹️ Stop Recording
                </button>
                <button class="btn btn-primary" onclick="playRoute()">
                    ▶️ Play Route
                </button>
                <button class="btn btn-danger" onclick="clearRoute()">
                    🗑️ Clear Route
                </button>
                
                <h3 style="margin-top: 15px;">Recorded Steps:</h3>
                <div class="route-list" id="routeList">
                    <div style="text-align: center; color: #888;">No route recorded</div>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        const socket = io();
        let recording = false;
        
        socket.on('connect', () => {
            document.getElementById('connStatus').textContent = 'Connected';
        });
        
        socket.on('disconnect', () => {
            document.getElementById('connStatus').textContent = 'Disconnected';
        });
        
        socket.on('sensor_update', (data) => {
            document.getElementById('sensorDistance').textContent = data.distance.toFixed(1);
            document.getElementById('distanceDisplay').textContent = data.distance.toFixed(1) + ' cm';
        });
        
        socket.on('state_update', (data) => {
            document.getElementById('ledStatus').textContent = data.led ? 'ON' : 'OFF';
            recording = data.recording;
            document.getElementById('recBtn').style.background = recording ? '#ef4444' : '#10b981';
        });
        
        socket.on('route_update', (route) => {
            const routeList = document.getElementById('routeList');
            routeList.innerHTML = '';
            
            if (route.length === 0) {
                routeList.innerHTML = '<div style="text-align: center; color: #888;">No route recorded</div>';
            } else {
                route.forEach((step, i) => {
                    const div = document.createElement('div');
                    div.className = 'route-item';
                    div.textContent = `${i+1}. ${step.direction} (${step.duration}s)`;
                    routeList.appendChild(div);
                });
            }
        });
        
        function move(direction) {
            const speed = document.getElementById('speedSlider').value / 100;
            socket.emit('move', { direction, speed });
        }
        
        function updateSpeed(value) {
            document.getElementById('speedDisplay').textContent = value + '%';
        }
        
        function toggleLED() {
            socket.emit('toggle_led');
        }
        
        function honk() {
            socket.emit('honk');
        }
        
        function startRecording() {
            socket.emit('start_recording');
        }
        
        function stopRecording() {
            socket.emit('stop_recording');
        }
        
        function playRoute() {
            socket.emit('play_route');
        }
        
        function clearRoute() {
            socket.emit('clear_route');
        }
        
        // Keyboard control
        const keyMap = {
            'w': 'forward', 'W': 'forward', 'ArrowUp': 'forward',
            's': 'backward', 'S': 'backward', 'ArrowDown': 'backward',
            'a': 'left', 'A': 'left', 'ArrowLeft': 'left',
            'd': 'right', 'D': 'right', 'ArrowRight': 'right',
            ' ': 'stop'
        };
        
        document.addEventListener('keydown', (e) => {
            if (keyMap[e.key] && !e.repeat) {
                e.preventDefault();
                move(keyMap[e.key]);
            }
        });
        
        document.addEventListener('keyup', (e) => {
            if (keyMap[e.key] && keyMap[e.key] !== 'stop') {
                e.preventDefault();
                move('stop');
            }
        });
    </script>
</body>
</html>
'''

# ============================================================================
# WEBSOCKET HANDLERS
# ============================================================================

current_move_start = None
current_direction = None
led_on = False

@socketio.on('connect')
def handle_connect():
    print('Client connected')
    emit('state_update', {'led': led_on, 'recording': robot_state['recording']})

@socketio.on('move')
def handle_move(data):
    global current_move_start, current_direction
    
    direction = data['direction']
    speed = data.get('speed', 0.7)
    
    # Stop previous recording
    if robot_state['recording'] and current_direction and current_direction != 'stop':
        duration = time.time() - current_move_start
        robot_state['route'].append({
            'direction': current_direction,
            'speed': speed,
            'duration': round(duration, 2)
        })
        emit('route_update', robot_state['route'], broadcast=True)
    
    # Execute move
    if direction == 'forward':
        robot.forward(speed)
    elif direction == 'backward':
        robot.backward(speed)
    elif direction == 'left':
        robot.left(speed)
    elif direction == 'right':
        robot.right(speed)
    else:
        robot.stop()
    
    robot_state['direction'] = direction
    
    # Start new recording
    if robot_state['recording'] and direction != 'stop':
        current_move_start = time.time()
        current_direction = direction

@socketio.on('toggle_led')
def handle_led():
    global led_on
    status_led.toggle()
    led_on = not led_on
    emit('state_update', {'led': led_on, 'recording': robot_state['recording']}, broadcast=True)

@socketio.on('honk')
def handle_honk():
    buzzer.beep(on_time=0.1, n=2, background=True)

@socketio.on('start_recording')
def handle_start_recording():
    robot_state['recording'] = True
    robot_state['route'] = []
    emit('state_update', {'led': led_on, 'recording': True}, broadcast=True)
    emit('route_update', [], broadcast=True)

@socketio.on('stop_recording')
def handle_stop_recording():
    robot_state['recording'] = False
    emit('state_update', {'led': led_on, 'recording': False}, broadcast=True)

@socketio.on('play_route')
def handle_play_route():
    def play():
        for step in robot_state['route']:
            direction = step['direction']
            speed = step['speed']
            duration = step['duration']
            
            if direction == 'forward':
                robot.forward(speed)
            elif direction == 'backward':
                robot.backward(speed)
            elif direction == 'left':
                robot.left(speed)
            elif direction == 'right':
                robot.right(speed)
            
            time.sleep(duration)
        
        robot.stop()
    
    threading.Thread(target=play, daemon=True).start()

@socketio.on('clear_route')
def handle_clear_route():
    robot_state['route'] = []
    emit('route_update', [], broadcast=True)

# ============================================================================
# ROUTES
# ============================================================================

@app.route('/')
def index():
    return render_template_string(HTML_INTERFACE)

@app.route('/video_feed')
def video_feed():
    """Video streaming route (placeholder)"""
    # Jika camera tersedia, return video stream
    # Untuk demo, return placeholder
    return Response("Camera not configured", mimetype="text/plain")

# ============================================================================
# BACKGROUND SENSOR UPDATE
# ============================================================================

def sensor_loop():
    while True:
        try:
            distance = sensor.distance * 100
            robot_state['distance'] = distance
            socketio.emit('sensor_update', {'distance': distance})
            time.sleep(0.3)
        except:
            time.sleep(1)

# ============================================================================
# MAIN
# ============================================================================

def main():
    print("\n" + "="*70)
    print("🌐 Web-Controlled Robot")
    print("="*70)
    print("\nFeatures:")
    print("  ✓ Real-time control via WebSocket")
    print("  ✓ Touch & keyboard control")
    print("  ✓ Route recording & playback")
    print("  ✓ Live sensor monitoring")
    print("  ✓ Mobile-friendly interface")
    print()
    
    # Start sensor thread
    threading.Thread(target=sensor_loop, daemon=True).start()
    
    import socket
    local_ip = socket.gethostbyname(socket.gethostname())
    
    print("✅ Server ready!")
    print(f"\n🌐 Access from:")
    print(f"   http://localhost:5000")
    print(f"   http://{local_ip}:5000")
    print()
    
    socketio.run(app, host='0.0.0.0', port=5000, debug=False)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n🛑 Server stopped")
        robot.stop()
        status_led.off()
