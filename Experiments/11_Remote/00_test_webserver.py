#!/usr/bin/env python3
"""
Bab 11: Test Web Server - Basic
================================
Program sederhana untuk test Flask web server

Install:
  pip3 install flask
"""

from flask import Flask, jsonify
import socket

app = Flask(__name__)

@app.route('/')
def home():
    """Handler untuk homepage - return HTML"""
    return """
    <html>
    <head><title>RTKA Test</title></head>
    <body style="font-family: Arial; padding: 50px; text-align: center;">
        <h1>✅ RTKA Web Server Running!</h1>
        <p>Flask server is working correctly.</p>
        <hr>
        <h3>Test API:</h3>
        <a href="/api/status">/api/status</a>
    </body>
    </html>
    """

@app.route('/api/status')
def status():
    """Handler untuk status API - return JSON"""
    return jsonify({
        'status': 'OK',
        'message': 'RTKA Web Server is running',
        'hostname': socket.gethostname()
    })

if __name__ == '__main__':
    hostname = socket.gethostname()
    ip = socket.gethostbyname(hostname)
    
    print("="*50)
    print("Test Web Server - Basic")
    print("="*50)
    print(f"\n🌐 Server starting...")
    print(f"   URL: http://{ip}:5000")
    print(f"   API: http://{ip}:5000/api/status")
    print("\nPress Ctrl+C to stop\n")
    
    app.run(host='0.0.0.0', port=5000, debug=False)

"""
PENJELASAN PROGRAM:
==================
Program ini untuk test Flask web server pada Raspberry Pi, yang akan digunakan untuk
web-based remote control robot RTKA.

Flask Basics:
Flask adalah micro web framework untuk Python yang mudah digunakan dan lightweight.
Cocok untuk embedded systems seperti Raspberry Pi.

Komponen Utama:
1. Routes (@app.route decorator):
   - Mapping antara URL path ke Python function
   - Route '/' = homepage (root URL)
   - Route '/api/status' = API endpoint
   
2. View Functions:
   - home(): return HTML content untuk homepage
   - status(): return JSON response untuk API
   
3. HTTP Methods:
   - Default adalah GET (untuk retrieve data)
   - Bisa specify POST, PUT, DELETE untuk operations lain

Cara Kerja Program:
1. Import Flask dan socket:
   - Flask untuk web framework
   - socket untuk get hostname dan IP address

2. Create Flask App:
   - app = Flask(__name__) create application instance
   - __name__ adalah module name (untuk template/static files path)

3. Define Routes:
   - @app.route('/') decorator untuk map URL ke function
   - home() return HTML string untuk display di browser
   - status() return JSON menggunakan jsonify() helper

4. Run Server:
   - app.run() start development server
   - host='0.0.0.0' = listen on all network interfaces (accessible dari network)
   - port=5000 = default Flask port
   - debug=False = production mode (no auto-reload, no debug info di browser)

5. Akses dari Browser/Client:
   - Homepage: http://<raspberry-pi-ip>:5000/
   - API: http://<raspberry-pi-ip>:5000/api/status
   - Bisa akses dari phone, laptop, tablet di network yang sama

JSON API Response:
Flask's jsonify() automatically:
- Convert Python dict ke JSON format
- Set proper Content-Type header (application/json)
- Handle serialization dari Python data types

Use Case untuk Robot:
- Web-based control interface (buttons untuk move robot)
- Live camera stream display
- Sensor data visualization (charts, graphs)
- Configuration panel
- Status monitoring

Production Deployment:
Untuk production, sebaiknya gunakan:
- uWSGI atau Gunicorn sebagai WSGI server (bukan Flask development server)
- Nginx sebagai reverse proxy
- systemd untuk auto-start service
"""
