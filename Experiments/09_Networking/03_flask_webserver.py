#!/usr/bin/env python3
"""
Bab 9.3: Web Server Sederhana (Flask)
======================================
Membuat web server dengan Flask framework

Flask adalah micro web framework untuk Python:
- Ringan dan mudah dipelajari
- Cocok untuk prototyping
- Built-in development server
- Template engine (Jinja2)

Install Flask:
  pip3 install flask flask-cors

Basic Flask App:
  from flask import Flask
  app = Flask(__name__)
  
  @app.route('/')
  def home():
      return "Hello World!"
  
  app.run(host='0.0.0.0', port=5000)
"""

from flask import Flask, render_template_string, jsonify, request
from flask_cors import CORS
from datetime import datetime
import socket

# Create Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for cross-origin requests

# Global counter for demo
visit_count = 0

print("="*70)
print("Flask Web Server - Basic Tutorial")
print("="*70)

# ============================================================================
# ROUTES (URL Endpoints)
# ============================================================================

@app.route('/')
def index():
    """Homepage"""
    global visit_count
    visit_count += 1
    
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Flask Demo - Raspberry Pi</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body {
                font-family: Arial, sans-serif;
                max-width: 800px;
                margin: 50px auto;
                padding: 20px;
                background: #f0f0f0;
            }
            .container {
                background: white;
                padding: 30px;
                border-radius: 10px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }
            h1 {
                color: #c51a4a;
                border-bottom: 3px solid #c51a4a;
                padding-bottom: 10px;
            }
            .info-box {
                background: #f8f9fa;
                padding: 15px;
                border-left: 4px solid #007bff;
                margin: 15px 0;
            }
            .btn {
                background: #007bff;
                color: white;
                padding: 10px 20px;
                border: none;
                border-radius: 5px;
                cursor: pointer;
                text-decoration: none;
                display: inline-block;
                margin: 5px;
            }
            .btn:hover {
                background: #0056b3;
            }
            code {
                background: #e9ecef;
                padding: 2px 6px;
                border-radius: 3px;
                font-family: 'Courier New', monospace;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🍓 Raspberry Pi Flask Server</h1>
            
            <div class="info-box">
                <p><strong>Server Time:</strong> {{ time }}</p>
                <p><strong>Hostname:</strong> {{ hostname }}</p>
                <p><strong>IP Address:</strong> {{ ip }}</p>
                <p><strong>Visit Count:</strong> {{ count }}</p>
            </div>
            
            <h2>Available Endpoints:</h2>
            <ul>
                <li><code>GET /</code> - This page</li>
                <li><code>GET /api/status</code> - JSON status</li>
                <li><code>GET /api/time</code> - Current time</li>
                <li><code>POST /api/echo</code> - Echo POST data</li>
                <li><code>GET /about</code> - About page</li>
            </ul>
            
            <div>
                <a href="/api/status" class="btn">View Status (JSON)</a>
                <a href="/api/time" class="btn">Get Time</a>
                <a href="/about" class="btn">About</a>
            </div>
            
            <h2>Test API:</h2>
            <div class="info-box">
                <p>Try in terminal:</p>
                <code>curl http://{{ ip }}:5000/api/status</code>
            </div>
        </div>
    </body>
    </html>
    """
    
    return render_template_string(
        html,
        time=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        hostname=socket.gethostname(),
        ip=request.host.split(':')[0],
        count=visit_count
    )

@app.route('/about')
def about():
    """About page"""
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>About - Flask Demo</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                max-width: 800px;
                margin: 50px auto;
                padding: 20px;
                background: #f0f0f0;
            }
            .container {
                background: white;
                padding: 30px;
                border-radius: 10px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }
            h1 { color: #c51a4a; }
            a { color: #007bff; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>About This Server</h1>
            <p>This is a demo Flask web server running on Raspberry Pi.</p>
            <p><strong>Flask Version:</strong> Micro web framework</p>
            <p><strong>Purpose:</strong> Educational demo for networking & IoT</p>
            <p><a href="/">← Back to Home</a></p>
        </div>
    </body>
    </html>
    """
    return html

@app.route('/api/status')
def api_status():
    """API endpoint - return status as JSON"""
    status = {
        'status': 'online',
        'hostname': socket.gethostname(),
        'time': datetime.now().isoformat(),
        'visits': visit_count,
        'uptime': 'N/A'
    }
    return jsonify(status)

@app.route('/api/time')
def api_time():
    """API endpoint - return current time"""
    return jsonify({
        'time': datetime.now().isoformat(),
        'timestamp': datetime.now().timestamp(),
        'formatted': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    })

@app.route('/api/echo', methods=['POST'])
def api_echo():
    """API endpoint - echo POST data"""
    data = request.get_json()
    return jsonify({
        'received': data,
        'timestamp': datetime.now().isoformat()
    })

@app.errorhandler(404)
def not_found(error):
    """404 Error handler"""
    return jsonify({'error': 'Endpoint not found'}), 404

# ============================================================================
# MAIN
# ============================================================================

def get_local_ip():
    """Get local IP address"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"

if __name__ == '__main__':
    print("\n📚 Flask Basics:")
    print("  - Route: URL pattern (@app.route)")
    print("  - View Function: Python function yang handle request")
    print("  - Template: HTML dengan Jinja2 syntax")
    print("  - JSON API: Return data as JSON")
    
    ip = get_local_ip()
    port = 5000
    
    print(f"\n🚀 Starting Flask server...")
    print(f"\n📍 Access URLs:")
    print(f"  Local:   http://127.0.0.1:{port}")
    print(f"  Network: http://{ip}:{port}")
    print(f"  mDNS:    http://{socket.gethostname()}.local:{port}")
    
    print(f"\n🔌 API Endpoints:")
    print(f"  http://{ip}:{port}/api/status")
    print(f"  http://{ip}:{port}/api/time")
    
    print(f"\n📱 Test dari HP/Laptop:")
    print(f"  1. Pastikan terhubung ke WiFi yang sama")
    print(f"  2. Buka browser")
    print(f"  3. Akses: http://{ip}:{port}")
    
    print(f"\n⏹️  Stop server: Ctrl+C")
    print("="*70 + "\n")
    
    try:
        # Run Flask development server
        app.run(
            host='0.0.0.0',  # Listen on all interfaces
            port=port,
            debug=True,      # Enable debug mode
            use_reloader=False  # Disable reloader untuk avoid double run
        )
    except KeyboardInterrupt:
        print("\n\n🛑 Server stopped")
    except Exception as e:
        print(f"\n❌ Error: {e}")
