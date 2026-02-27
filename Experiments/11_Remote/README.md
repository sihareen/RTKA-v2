# Bab 11: Remote Control & Monitoring

Sistem kontrol jarak jauh dan monitoring real-time untuk robot.

## 📚 Daftar Program

### 1. Web Dashboard Real-time (`01_web_dashboard_realtime.py`)
Dashboard web lengkap dengan WebSocket untuk kontrol robot secara real-time:

**Fitur Utama:**
- 🎮 **Real-time Control**: WebSocket untuk zero-delay control
- 📊 **Live Charts**: Chart.js untuk visualisasi sensor real-time
- ⌨️ **Keyboard Control**: WASD/Arrow keys untuk control
- 📱 **Mobile Responsive**: Touch-friendly interface
- 🎨 **Modern UI**: Gradient design dengan backdrop filter
- 📜 **Activity Log**: Real-time logging semua aktivitas

**Control Methods:**
1. Web button (click/touch)
2. Keyboard shortcuts (W/A/S/D or Arrow keys)
3. Speed slider (0-100%)

**Technology:**
- Flask-SocketIO untuk WebSocket
- Chart.js untuk real-time graphs
- Embedded HTML/CSS/JavaScript (single file)
- AJAX untuk sensor updates

**Sensor Monitoring:**
- Ultrasonic distance dengan trend chart
- Update rate: 500ms (2 Hz)
- Auto-scaling charts
- Maximum 20 data points visible

**Hardware Control:**
- Motor speed control (PWM)
- LED toggle
- Buzzer beep
- Real-time status updates

### 2. Data Logging Dashboard (`02_data_logging_dashboard.py`)
Dashboard untuk logging dan analisis data sensor dengan visualisasi:

**Fitur Logging:**
- 💾 **SQLite Database**: Persistent storage
- 📈 **Statistics**: Real-time aggregation (avg, min, max)
- 📊 **Charts**: Trend line & histogram
- 📥 **Export**: CSV & JSON download
- 🚨 **Alert System**: Automatic alerts dengan severity levels

**Data Analytics:**
1. **Trend Chart**: Last 50 readings timeline
2. **Histogram**: Distance distribution (0-20, 20-40, etc)
3. **Statistics Dashboard**: Total records, averages, extremes

**Database Schema:**
```sql
-- Sensor readings
CREATE TABLE sensor_readings (
    id INTEGER PRIMARY KEY,
    timestamp DATETIME,
    distance_cm REAL,
    robot_state TEXT,
    created_at TIMESTAMP
);

-- Alerts
CREATE TABLE alerts (
    id INTEGER PRIMARY KEY,
    timestamp DATETIME,
    alert_type TEXT,
    message TEXT,
    severity TEXT  -- 'info', 'warning', 'danger'
);
```

**Alert Conditions:**
- Distance < 10cm: Critical obstacle alert
- Distance < 20cm: Warning alert
- Configurable thresholds

**Export Formats:**
- CSV: Compatible dengan Excel/Google Sheets
- JSON: Untuk processing dengan Python/JavaScript
- Include all metadata (timestamp, sensor values, state)

## 🔧 Setup Requirements

### Install Dependencies
```bash
# WebSocket support
pip3 install flask flask-socketio python-socketio simple-websocket

# Optional: For data analysis
pip3 install pandas matplotlib
```

### Hardware Requirements
- Raspberry Pi dengan WiFi
- HC-SR04 Ultrasonic sensor
- Motor DC dengan L298N driver
- LED & Buzzer (optional)

### Network Setup
```bash
# Check local IP
hostname -I

# Robot akan accessible di:
# http://[IP_ADDRESS]:5000
```

## 🌐 Access Methods

### Local Access
```bash
# Di Raspberry Pi
./01_web_dashboard_realtime.py

# Buka browser:
http://localhost:5000
```

### Remote Access (Same Network)
```bash
# Di Raspberry Pi
./01_web_dashboard_realtime.py

# Dari smartphone/laptop di WiFi yang sama:
http://192.168.1.100:5000  # Ganti dengan IP Raspberry Pi
```

### Internet Access (Advanced)
```bash
# Option 1: Port forwarding di router
# Forward port 5000 ke Raspberry Pi

# Option 2: ngrok tunnel
ngrok http 5000
# Gunakan URL ngrok untuk access dari internet
```

## 🎮 Usage Examples

### Example 1: Real-time Control
```bash
# Start dashboard
./01_web_dashboard_realtime.py

# Web interface:
1. Open http://[IP]:5000
2. Use arrow buttons atau keyboard (WASD)
3. Adjust speed slider
4. Toggle LED
5. Monitor distance real-time
6. View activity log
```

### Example 2: Data Logging
```bash
# Start logging dashboard
./02_data_logging_dashboard.py

# Features:
1. Auto-collect sensor data every 2 seconds
2. View real-time statistics
3. Export data:
   - Click "Export CSV" untuk spreadsheet
   - Click "Export JSON" untuk programming
4. Monitor alerts
5. View distance trends
```

### Example 3: Multi-device Monitoring
```bash
# Raspberry Pi:
./01_web_dashboard_realtime.py

# Smartphone: Control robot
http://192.168.1.100:5000

# Laptop: Monitor data
http://192.168.1.100:5000

# Kedua device melihat update yang sama (WebSocket broadcast)
```

## 📊 Dashboard Features Comparison

| Feature | Real-time Dashboard | Data Logging Dashboard |
|---------|-------------------|----------------------|
| WebSocket | ✅ Yes | ❌ No (HTTP only) |
| Live Control | ✅ Yes | ❌ No |
| Data Storage | ❌ No | ✅ SQLite |
| Export Data | ❌ No | ✅ CSV/JSON |
| Charts | ✅ Real-time | ✅ Historical |
| Alert System | ❌ No | ✅ Yes |
| Auto-refresh | ✅ WebSocket push | ✅ 5s polling |

## 🔐 Security Considerations

### Enable HTTPS (Production)
```python
# Generate self-signed certificate
from OpenSSL import SSL

context = SSL.Context(SSL.SSLv23_METHOD)
context.use_privatekey_file('server.key')
context.use_certificate_file('server.crt')

socketio.run(app, ssl_context=context)
```

### Add Authentication
```python
from flask_httpauth import HTTPBasicAuth

auth = HTTPBasicAuth()

@auth.verify_password
def verify(username, password):
    return username == 'admin' and password == 'secret'

@app.route('/')
@auth.login_required
def index():
    return render_template_string(HTML_TEMPLATE)
```

### Rate Limiting
```python
from flask_limiter import Limiter

limiter = Limiter(app, key_func=lambda: request.remote_addr)

@app.route('/api/control')
@limiter.limit("10 per minute")
def control():
    # Limit control commands
    pass
```

## 📱 Mobile Optimization

Dashboard sudah mobile-responsive dengan:
- Touch-friendly buttons (min 44×44px)
- Responsive grid layout
- Viewport meta tag
- Gesture support (swipe, tap)

**Test di Mobile:**
```bash
# Di Raspberry Pi
./01_web_dashboard_realtime.py

# Di smartphone browser:
http://[RPI_IP]:5000

# Add to home screen untuk app-like experience
```

## ⌨️ Keyboard Shortcuts

**Real-time Dashboard:**
- `W` / `↑` : Forward
- `S` / `↓` : Backward
- `A` / `←` : Turn left
- `D` / `→` : Turn right
- `Space` : Stop

**Prevents:**
- Key repeat (no spam commands)
- Accidental page scroll
- Default browser actions

## 🎓 Learning Objectives

Setelah menyelesaikan Bab 11, Anda akan bisa:

1. ✅ Membuat web dashboard dengan Flask
2. ✅ Implementasi WebSocket untuk real-time communication
3. ✅ Visualisasi data dengan Chart.js
4. ✅ Database integration (SQLite)
5. ✅ Export data dalam berbagai format
6. ✅ Membuat mobile-responsive interface
7. ✅ Handle keyboard & touch events
8. ✅ Implement alert & notification system

## 🐛 Troubleshooting

**Problem**: "Address already in use"
```bash
# Kill process di port 5000
sudo lsof -ti:5000 | xargs kill -9

# Atau gunakan port lain
app.run(port=5001)
```

**Problem**: WebSocket connection failed
```bash
# Check firewall
sudo ufw allow 5000

# Check Flask-SocketIO version
pip3 install --upgrade flask-socketio
```

**Problem**: Charts tidak muncul
- Check internet connection (Chart.js dari CDN)
- Atau download Chart.js locally

**Problem**: Mobile tidak bisa access
- Pastikan di WiFi yang sama
- Check IP dengan `hostname -I`
- Disable firewall temporarily untuk test

## 💡 Extensions & Projects

### Extension Ideas:
1. **Video Stream**: Add Pi Camera feed
2. **Voice Control**: Web Speech API
3. **Autonomous Mode**: Toggle manual/auto
4. **Multi-robot**: Control multiple robots
5. **Data Visualization**: Grafana integration
6. **Mobile App**: Convert to PWA (Progressive Web App)

### Project Templates:
```python
# Real-time chat for robot coordination
@socketio.on('chat_message')
def handle_chat(msg):
    emit('new_message', msg, broadcast=True)

# Scheduled tasks
from apscheduler.schedulers.background import BackgroundScheduler

scheduler = BackgroundScheduler()
scheduler.add_job(collect_data, 'interval', seconds=10)
scheduler.start()
```

## 📚 Resources

- [Flask-SocketIO Docs](https://flask-socketio.readthedocs.io/)
- [Chart.js](https://www.chartjs.org/)
- [WebSocket Protocol](https://developer.mozilla.org/en-US/docs/Web/API/WebSocket)
- [SQLite Tutorial](https://www.sqlitetutorial.net/)

## 🚀 Next Steps

- Bab 12: Complete mini projects
- Add camera streaming
- Implement authentication
- Deploy to cloud (Heroku, AWS)
- Create mobile app (React Native, Flutter)
