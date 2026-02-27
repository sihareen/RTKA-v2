#!/usr/bin/env python3
"""
Bab 09: Test Network - Basic
=============================
Program sederhana untuk test koneksi network

Test:
1. IP Address
2. Hostname
3. Internet connection
4. Simple HTTP server
"""

import socket
import subprocess
import http.server
import socketserver
from threading import Thread

print("="*50)
print("Test Network - Basic")
print("="*50)

try:
    hostname = socket.gethostname()
    ip_address = socket.gethostbyname(hostname)
    print(f"\n✅ Hostname: {hostname}")
    print(f"✅ IP Address: {ip_address}")
except Exception as e:
    print(f"❌ Error getting IP: {e}")

print("\nTesting internet connection...")
try:
    result = subprocess.run(['ping', '-c', '1', '8.8.8.8'], 
                          capture_output=True, timeout=3)
    if result.returncode == 0:
        print("✅ Internet: Connected")
    else:
        print("❌ Internet: Not connected")
except:
    print("❌ Internet: Not connected")

print("\n" + "="*50)
choice = input("\nStart simple HTTP server? (y/n): ")

if choice.lower() == 'y':
    PORT = 8080
    
    Handler = http.server.SimpleHTTPRequestHandler
    
    print(f"\n🌐 Starting server at http://{ip_address}:{PORT}")
    print("Press Ctrl+C to stop\n")
    
    try:
        with socketserver.TCPServer(("", PORT), Handler) as httpd:
            httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n\n✅ Server stopped")
else:
    print("✅ Test selesai!")

"""
PENJELASAN PROGRAM:
==================
Program ini untuk test dasar networking pada Raspberry Pi, meliputi network configuration,
internet connectivity, dan simple HTTP server.

Konsep Networking:
1. IP Address - alamat unik device di network (contoh: 192.168.1.100)
   - Private IP: 192.168.x.x, 10.x.x.x (untuk local network/LAN)
   - Public IP: assigned oleh ISP (untuk internet)
   - Localhost: 127.0.0.1 (loopback address, untuk akses device sendiri)

2. Hostname - nama device di network (contoh: raspberrypi, rtka-robot)
   Lebih mudah diingat daripada IP address

3. Port - "pintu" untuk service/aplikasi (0-65535)
   - Port 80: HTTP (web)
   - Port 443: HTTPS (secure web)
   - Port 22: SSH
   - Port 8080: Alternative HTTP

4. Client-Server Architecture:
   Client (phone/laptop) --request--> Server (RPi)
   Client <--response-- Server

Cara Kerja Program:
1. Get IP & Hostname:
   - socket.gethostname() untuk dapat hostname
   - socket.gethostbyname() untuk resolve hostname ke IP
   - Alternatif: buat dummy UDP connection ke 8.8.8.8 untuk dapat active IP

2. Test Internet Connection:
   - Menggunakan subprocess.run() untuk execute 'ping' command
   - Ping ke 8.8.8.8 (Google DNS) 1 kali dengan timeout 3 detik
   - Check returncode: 0 = success, non-zero = failed

3. Simple HTTP Server:
   - SimpleHTTPRequestHandler serve files dari current directory
   - TCPServer listen pada port 8080, semua network interfaces ("")
   - serve_forever() loop infinit untuk handle incoming HTTP requests
   - User bisa akses via browser: http://<ip>:8080

Use Case:
- Debug network issues
- Check IP address untuk remote access (SSH, VNC, web interface)
- Quick file sharing via HTTP server
- Test connectivity sebelum deploy aplikasi networking
"""
