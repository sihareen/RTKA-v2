#!/usr/bin/env python3
"""
Bab 11.2: Data Logging & Visualization Dashboard
=================================================
Dashboard untuk monitoring dan visualisasi data sensor dengan:
1. SQLite database untuk persistent storage
2. Real-time charts (Chart.js)
3. Export data (CSV, JSON)
4. Historical data analysis
5. Alert system

Install:
  pip3 install flask pandas matplotlib
"""

from flask import Flask, render_template_string, jsonify, send_file, request
import sqlite3
import json
import csv
import io
import time
from datetime import datetime, timedelta
import threading

# Try import GPIO
try:
    from gpiozero import DistanceSensor, Robot
    from gpiozero.pins.lgpio import LGPIOFactory
    
    factory = LGPIOFactory()
    sensor = DistanceSensor(echo=20, trigger=26, max_distance=4.0, pin_factory=factory)
    robot = Robot(left=(22, 27), right=(17, 18), pin_factory=factory)
    
    GPIO_AVAILABLE = True
except:
    GPIO_AVAILABLE = False

app = Flask(__name__)

# Database setup
DB_FILE = 'robot_data.db'

def init_database():
    """Initialize SQLite database"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sensor_readings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            distance_cm REAL,
            robot_state TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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

def log_sensor_data(distance, state='idle'):
    """Log sensor data to database"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO sensor_readings (distance_cm, robot_state)
        VALUES (?, ?)
    ''', (distance, state))
    
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
# HTML TEMPLATE WITH DASHBOARD
# ============================================================================

HTML_DASHBOARD = '''
<!DOCTYPE html>
<html>
<head>
    <title>Data Logging Dashboard</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', sans-serif;
            background: #0f172a;
            color: white;
            padding: 20px;
        }
        .header {
            text-align: center;
            margin-bottom: 30px;
        }
        .header h1 { 
            font-size: 2.5em; 
            background: linear-gradient(45deg, #06b6d4, #3b82f6);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .stat-card {
            background: linear-gradient(135deg, #1e293b, #334155);
            padding: 25px;
            border-radius: 15px;
            text-align: center;
            border: 1px solid rgba(255,255,255,0.1);
        }
        .stat-value {
            font-size: 2.5em;
            font-weight: bold;
            color: #06b6d4;
        }
        .stat-label {
            color: #94a3b8;
            margin-top: 10px;
        }
        .chart-container {
            background: linear-gradient(135deg, #1e293b, #334155);
            padding: 30px;
            border-radius: 15px;
            margin-bottom: 20px;
            border: 1px solid rgba(255,255,255,0.1);
        }
        .chart-container h2 {
            color: #06b6d4;
            margin-bottom: 20px;
        }
        .controls {
            display: flex;
            gap: 15px;
            margin-bottom: 20px;
            flex-wrap: wrap;
        }
        .btn {
            padding: 12px 24px;
            border: none;
            border-radius: 8px;
            font-weight: bold;
            cursor: pointer;
            transition: all 0.3s;
        }
        .btn-primary { background: #06b6d4; color: white; }
        .btn-success { background: #10b981; color: white; }
        .btn-danger { background: #ef4444; color: white; }
        .btn:hover { transform: translateY(-2px); box-shadow: 0 5px 15px rgba(0,0,0,0.3); }
        .table-container {
            background: linear-gradient(135deg, #1e293b, #334155);
            padding: 25px;
            border-radius: 15px;
            overflow-x: auto;
            border: 1px solid rgba(255,255,255,0.1);
        }
        table {
            width: 100%;
            border-collapse: collapse;
        }
        th, td {
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid rgba(255,255,255,0.1);
        }
        th {
            background: rgba(6, 182, 212, 0.2);
            color: #06b6d4;
        }
        .alert {
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 10px;
            border-left: 4px solid;
        }
        .alert-warning { background: rgba(251, 191, 36, 0.2); border-color: #fbbf24; }
        .alert-danger { background: rgba(239, 68, 68, 0.2); border-color: #ef4444; }
        .alert-info { background: rgba(6, 182, 212, 0.2); border-color: #06b6d4; }
    </style>
</head>
<body>
    <div class="header">
        <h1>📊 Data Logging Dashboard</h1>
        <p>Real-time Monitoring & Analytics</p>
    </div>
    
    <div class="stats-grid">
        <div class="stat-card">
            <div class="stat-value" id="totalReadings">0</div>
            <div class="stat-label">Total Readings</div>
        </div>
        <div class="stat-card">
            <div class="stat-value" id="avgDistance">0</div>
            <div class="stat-label">Avg Distance (cm)</div>
        </div>
        <div class="stat-card">
            <div class="stat-value" id="minDistance">0</div>
            <div class="stat-label">Min Distance (cm)</div>
        </div>
        <div class="stat-card">
            <div class="stat-value" id="maxDistance">0</div>
            <div class="stat-label">Max Distance (cm)</div>
        </div>
    </div>
    
    <div class="controls">
        <button class="btn btn-primary" onclick="refreshData()">🔄 Refresh Data</button>
        <button class="btn btn-success" onclick="exportCSV()">📥 Export CSV</button>
        <button class="btn btn-success" onclick="exportJSON()">📥 Export JSON</button>
        <button class="btn btn-danger" onclick="clearData()">🗑️ Clear Database</button>
    </div>
    
    <div class="chart-container">
        <h2>📈 Distance Trend (Last 50 Readings)</h2>
        <canvas id="trendChart"></canvas>
    </div>
    
    <div class="chart-container">
        <h2>📊 Distance Distribution</h2>
        <canvas id="histogramChart"></canvas>
    </div>
    
    <div class="table-container">
        <h2 style="color: #06b6d4; margin-bottom: 15px;">🚨 Recent Alerts</h2>
        <div id="alertsContainer"></div>
    </div>
    
    <div class="table-container" style="margin-top: 20px;">
        <h2 style="color: #06b6d4; margin-bottom: 15px;">📋 Recent Readings</h2>
        <table id="dataTable">
            <thead>
                <tr>
                    <th>Timestamp</th>
                    <th>Distance (cm)</th>
                    <th>Robot State</th>
                </tr>
            </thead>
            <tbody></tbody>
        </table>
    </div>
    
    <script>
        let trendChart, histogramChart;
        
        // Initialize charts
        const trendCtx = document.getElementById('trendChart').getContext('2d');
        trendChart = new Chart(trendCtx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    label: 'Distance (cm)',
                    data: [],
                    borderColor: '#06b6d4',
                    backgroundColor: 'rgba(6, 182, 212, 0.1)',
                    tension: 0.4,
                    fill: true
                }]
            },
            options: {
                responsive: true,
                scales: {
                    y: { beginAtZero: true }
                }
            }
        });
        
        const histCtx = document.getElementById('histogramChart').getContext('2d');
        histogramChart = new Chart(histCtx, {
            type: 'bar',
            data: {
                labels: ['0-20', '20-40', '40-60', '60-80', '80-100', '100+'],
                datasets: [{
                    label: 'Count',
                    data: [0, 0, 0, 0, 0, 0],
                    backgroundColor: '#06b6d4'
                }]
            },
            options: {
                responsive: true,
                scales: {
                    y: { beginAtZero: true }
                }
            }
        });
        
        async function refreshData() {
            // Get statistics
            const statsRes = await fetch('/api/statistics');
            const stats = await statsRes.json();
            
            document.getElementById('totalReadings').textContent = stats.total || 0;
            document.getElementById('avgDistance').textContent = (stats.avg || 0).toFixed(1);
            document.getElementById('minDistance').textContent = (stats.min || 0).toFixed(1);
            document.getElementById('maxDistance').textContent = (stats.max || 0).toFixed(1);
            
            // Get trend data
            const trendRes = await fetch('/api/trend');
            const trend = await trendRes.json();
            
            trendChart.data.labels = trend.map(r => new Date(r.timestamp).toLocaleTimeString());
            trendChart.data.datasets[0].data = trend.map(r => r.distance);
            trendChart.update();
            
            // Get histogram
            const histRes = await fetch('/api/histogram');
            const hist = await histRes.json();
            histogramChart.data.datasets[0].data = hist;
            histogramChart.update();
            
            // Get recent readings
            const readingsRes = await fetch('/api/recent?limit=20');
            const readings = await readingsRes.json();
            
            const tbody = document.querySelector('#dataTable tbody');
            tbody.innerHTML = '';
            
            readings.forEach(r => {
                const row = tbody.insertRow();
                row.innerHTML = `
                    <td>${new Date(r.timestamp).toLocaleString()}</td>
                    <td>${r.distance.toFixed(2)}</td>
                    <td>${r.state}</td>
                `;
            });
            
            // Get alerts
            const alertsRes = await fetch('/api/alerts');
            const alerts = await alertsRes.json();
            
            const alertsContainer = document.getElementById('alertsContainer');
            alertsContainer.innerHTML = '';
            
            if (alerts.length === 0) {
                alertsContainer.innerHTML = '<div class="alert alert-info">No alerts</div>';
            } else {
                alerts.forEach(a => {
                    const alertDiv = document.createElement('div');
                    alertDiv.className = `alert alert-${a.severity}`;
                    alertDiv.innerHTML = `
                        <strong>${new Date(a.timestamp).toLocaleString()}</strong> - ${a.message}
                    `;
                    alertsContainer.appendChild(alertDiv);
                });
            }
        }
        
        async function exportCSV() {
            window.open('/api/export/csv', '_blank');
        }
        
        async function exportJSON() {
            window.open('/api/export/json', '_blank');
        }
        
        async function clearData() {
            if (confirm('Clear all data from database?')) {
                await fetch('/api/clear', { method: 'POST' });
                refreshData();
            }
        }
        
        // Auto refresh every 5 seconds
        setInterval(refreshData, 5000);
        refreshData();
    </script>
</body>
</html>
'''

# ============================================================================
# API ROUTES
# ============================================================================

@app.route('/')
def index():
    return render_template_string(HTML_DASHBOARD)

@app.route('/api/statistics')
def api_statistics():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT 
            COUNT(*) as total,
            AVG(distance_cm) as avg,
            MIN(distance_cm) as min,
            MAX(distance_cm) as max
        FROM sensor_readings
    ''')
    
    row = cursor.fetchone()
    conn.close()
    
    return jsonify({
        'total': row[0] or 0,
        'avg': row[1] or 0,
        'min': row[2] or 0,
        'max': row[3] or 0
    })

@app.route('/api/trend')
def api_trend():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT timestamp, distance_cm, robot_state
        FROM sensor_readings
        ORDER BY id DESC
        LIMIT 50
    ''')
    
    rows = cursor.fetchall()
    conn.close()
    
    return jsonify([{
        'timestamp': r[0],
        'distance': r[1],
        'state': r[2]
    } for r in reversed(rows)])

@app.route('/api/histogram')
def api_histogram():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    cursor.execute('SELECT distance_cm FROM sensor_readings')
    distances = [row[0] for row in cursor.fetchall()]
    conn.close()
    
    # Create histogram bins
    bins = [0, 0, 0, 0, 0, 0]
    for d in distances:
        if d < 20:
            bins[0] += 1
        elif d < 40:
            bins[1] += 1
        elif d < 60:
            bins[2] += 1
        elif d < 80:
            bins[3] += 1
        elif d < 100:
            bins[4] += 1
        else:
            bins[5] += 1
    
    return jsonify(bins)

@app.route('/api/recent')
def api_recent():
    limit = request.args.get('limit', 20, type=int)
    
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT timestamp, distance_cm, robot_state
        FROM sensor_readings
        ORDER BY id DESC
        LIMIT ?
    ''', (limit,))
    
    rows = cursor.fetchall()
    conn.close()
    
    return jsonify([{
        'timestamp': r[0],
        'distance': r[1],
        'state': r[2]
    } for r in rows])

@app.route('/api/alerts')
def api_alerts():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT timestamp, alert_type, message, severity
        FROM alerts
        ORDER BY id DESC
        LIMIT 10
    ''')
    
    rows = cursor.fetchall()
    conn.close()
    
    return jsonify([{
        'timestamp': r[0],
        'type': r[1],
        'message': r[2],
        'severity': r[3]
    } for r in rows])

@app.route('/api/export/csv')
def export_csv():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM sensor_readings ORDER BY id DESC')
    rows = cursor.fetchall()
    conn.close()
    
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['ID', 'Timestamp', 'Distance (cm)', 'Robot State', 'Created At'])
    writer.writerows(rows)
    
    output.seek(0)
    return send_file(
        io.BytesIO(output.getvalue().encode()),
        mimetype='text/csv',
        as_attachment=True,
        download_name=f'robot_data_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
    )

@app.route('/api/export/json')
def export_json():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM sensor_readings ORDER BY id DESC')
    rows = cursor.fetchall()
    conn.close()
    
    data = [{
        'id': r[0],
        'timestamp': r[1],
        'distance_cm': r[2],
        'robot_state': r[3],
        'created_at': r[4]
    } for r in rows]
    
    return send_file(
        io.BytesIO(json.dumps(data, indent=2).encode()),
        mimetype='application/json',
        as_attachment=True,
        download_name=f'robot_data_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
    )

@app.route('/api/clear', methods=['POST'])
def clear_database():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    cursor.execute('DELETE FROM sensor_readings')
    cursor.execute('DELETE FROM alerts')
    
    conn.commit()
    conn.close()
    
    return jsonify({'status': 'cleared'})

# ============================================================================
# BACKGROUND DATA COLLECTION
# ============================================================================

def data_collection_loop():
    """Collect sensor data periodically"""
    while True:
        try:
            if GPIO_AVAILABLE:
                try:
                    distance = sensor.distance * 100
                except:
                    distance = 50
            else:
                import random
                distance = random.uniform(10, 100)
            
            # Log to database
            log_sensor_data(distance, 'monitoring')
            
            # Create alerts
            if distance < 10:
                create_alert('obstacle', f'Obstacle detected at {distance:.1f} cm', 'danger')
            elif distance < 20:
                create_alert('warning', f'Close object at {distance:.1f} cm', 'warning')
            
            time.sleep(2)  # Log every 2 seconds
        
        except Exception as e:
            print(f"Error in data collection: {e}")
            time.sleep(5)

# ============================================================================
# MAIN
# ============================================================================

def main():
    print("\n" + "="*70)
    print("📊 Data Logging & Visualization Dashboard")
    print("="*70)
    print()
    
    # Initialize database
    init_database()
    
    # Start data collection thread
    collector_thread = threading.Thread(target=data_collection_loop, daemon=True)
    collector_thread.start()
    
    print("✅ Dashboard ready!")
    print()
    print("🌐 Open: http://localhost:5000")
    print()
    print("Features:")
    print("  ✓ Real-time statistics")
    print("  ✓ Trend charts")
    print("  ✓ Data export (CSV/JSON)")
    print("  ✓ Alert system")
    print("  ✓ Auto-refresh every 5 seconds")
    print()
    
    app.run(host='0.0.0.0', port=5000, debug=False)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n🛑 Server stopped")
