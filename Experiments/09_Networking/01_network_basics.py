#!/usr/bin/env python3
"""
Bab 9.1: Konsep Networking (IP, Client-Server)
===============================================
Memahami dasar-dasar networking untuk Raspberry Pi

Konsep Dasar:
1. IP Address = alamat unik device di network
2. Port = pintu komunikasi untuk service
3. Client = yang meminta data
4. Server = yang menyediakan data
5. Protocol = aturan komunikasi (TCP, UDP, HTTP, dll)

Arsitektur Client-Server:
┌─────────┐                    ┌─────────┐
│ Client  │ ----Request--->    │ Server  │
│ (Phone) │                    │  (RPi)  │
│         │ <---Response---    │         │
└─────────┘                    └─────────┘

IP Address Classes:
- Localhost: 127.0.0.1 (loopback)
- Private: 192.168.x.x, 10.x.x.x
- Public: Assigned by ISP
"""

import socket
import subprocess
import platform
from datetime import datetime

print("="*70)
print("Network Basics - IP & Client-Server Concept")
print("="*70)

def get_hostname():
    """Dapatkan hostname device"""
    return socket.gethostname()

def get_local_ip():
    """Dapatkan IP address lokal"""
    try:
        # Create dummy connection untuk dapatkan IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))  # Google DNS
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except Exception as e:
        return f"Error: {e}"

def get_all_interfaces():
    """Dapatkan semua network interfaces"""
    if platform.system() == "Linux":
        try:
            result = subprocess.run(['hostname', '-I'], 
                                  capture_output=True, 
                                  text=True)
            return result.stdout.strip().split()
        except:
            return []
    return []

def check_port_available(port):
    """Cek apakah port tersedia"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(1)
    try:
        sock.bind(('', port))
        sock.close()
        return True
    except:
        return False

def scan_common_ports():
    """Scan port yang umum digunakan"""
    common_ports = {
        22: "SSH",
        80: "HTTP",
        443: "HTTPS",
        5000: "Flask (default)",
        8000: "Python HTTP Server",
        8080: "Alternative HTTP",
        1883: "MQTT",
        3306: "MySQL"
    }
    
    print("\n📡 Scanning Common Ports:")
    print("-" * 70)
    
    for port, service in common_ports.items():
        available = check_port_available(port)
        status = "✅ Available" if available else "❌ In Use"
        print(f"Port {port:5d} ({service:20s}) → {status}")

def demonstrate_socket_basics():
    """Demonstrasi dasar socket programming"""
    print("\n🔌 Socket Basics:")
    print("-" * 70)
    
    # Create socket
    print("\n1. Creating socket...")
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    print("   ✓ Socket created (TCP/IP)")
    
    # Socket info
    print(f"\n2. Socket info:")
    print(f"   Family: {sock.family}")
    print(f"   Type: {sock.type}")
    print(f"   Protocol: {sock.proto}")
    
    # Close socket
    sock.close()
    print("\n3. Socket closed")

def simple_tcp_server_demo():
    """Demo simple TCP server"""
    print("\n🖥️  Simple TCP Server Demo:")
    print("-" * 70)
    
    HOST = '0.0.0.0'  # Listen on all interfaces
    PORT = 9999
    
    if not check_port_available(PORT):
        print(f"❌ Port {PORT} already in use!")
        return
    
    print(f"\nStarting server on {HOST}:{PORT}")
    print("Akan mendengarkan koneksi selama 10 detik...")
    print(f"\nUntuk test, buka terminal lain dan jalankan:")
    print(f"  nc {get_local_ip()} {PORT}")
    print(f"  atau")
    print(f"  telnet {get_local_ip()} {PORT}")
    
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((HOST, PORT))
    server.listen(1)
    server.settimeout(10)  # 10 second timeout
    
    try:
        print("\n⏳ Waiting for connection...")
        client, address = server.accept()
        print(f"\n✅ Connected by {address}")
        
        # Send welcome message
        message = f"Hello from Raspberry Pi!\nTime: {datetime.now()}\n"
        client.send(message.encode())
        
        # Receive data
        data = client.recv(1024)
        if data:
            print(f"📥 Received: {data.decode()}")
        
        client.close()
        
    except socket.timeout:
        print("\n⏱️  Timeout - no connection received")
    except Exception as e:
        print(f"\n❌ Error: {e}")
    finally:
        server.close()
        print("\n🔒 Server closed")

def network_diagnostics():
    """Network diagnostics & troubleshooting"""
    print("\n🔍 Network Diagnostics:")
    print("-" * 70)
    
    # Hostname
    print(f"\n1. Hostname: {get_hostname()}")
    
    # IP Address
    print(f"\n2. IP Address:")
    print(f"   Primary: {get_local_ip()}")
    
    interfaces = get_all_interfaces()
    if interfaces:
        print(f"   All IPs: {', '.join(interfaces)}")
    
    # Default gateway
    if platform.system() == "Linux":
        try:
            result = subprocess.run(['ip', 'route'], 
                                  capture_output=True, 
                                  text=True)
            for line in result.stdout.split('\n'):
                if 'default' in line:
                    print(f"\n3. Default Gateway: {line.split()[2]}")
                    break
        except:
            pass
    
    # DNS test
    print(f"\n4. DNS Test:")
    try:
        ip = socket.gethostbyname('google.com')
        print(f"   ✓ google.com → {ip}")
    except:
        print(f"   ❌ DNS resolution failed")
    
    # Internet connectivity
    print(f"\n5. Internet Connectivity:")
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(3)
        sock.connect(("8.8.8.8", 53))
        sock.close()
        print(f"   ✓ Internet reachable")
    except:
        print(f"   ❌ No internet connection")

def explain_concepts():
    """Penjelasan konsep networking"""
    print("\n📚 Networking Concepts:")
    print("="*70)
    
    concepts = {
        "IP Address": [
            "Alamat unik untuk setiap device di network",
            "Format: xxx.xxx.xxx.xxx (IPv4)",
            "Contoh: 192.168.1.100"
        ],
        "Port": [
            "Nomor 0-65535 untuk identifikasi service",
            "Well-known ports: 0-1023 (HTTP=80, HTTPS=443)",
            "Dynamic ports: 49152-65535"
        ],
        "Client-Server": [
            "Client: meminta service/data",
            "Server: menyediakan service/data",
            "Komunikasi via socket connection"
        ],
        "TCP vs UDP": [
            "TCP: Connection-oriented, reliable",
            "UDP: Connectionless, fast, no guarantee",
            "TCP untuk data penting, UDP untuk streaming"
        ]
    }
    
    for topic, points in concepts.items():
        print(f"\n📖 {topic}:")
        for point in points:
            print(f"   • {point}")

# ============================================================================
# MAIN PROGRAM
# ============================================================================

try:
    print("\n💡 Tentang Networking:")
    print("  - Raspberry Pi bisa jadi server atau client")
    print("  - Bisa diakses via WiFi/Ethernet")
    print("  - Cocok untuk IoT & remote control")
    print()
    
    while True:
        print("\n" + "="*70)
        print("MENU:")
        print("  1. Show Network Info")
        print("  2. Scan Common Ports")
        print("  3. Socket Basics Demo")
        print("  4. Simple TCP Server Demo")
        print("  5. Network Diagnostics")
        print("  6. Explain Concepts")
        print("  7. Exit")
        print("="*70)
        
        choice = input("\nPilihan: ").strip()
        
        if choice == "1":
            print(f"\n🌐 Network Information:")
            print(f"  Hostname: {get_hostname()}")
            print(f"  IP Address: {get_local_ip()}")
            interfaces = get_all_interfaces()
            if interfaces:
                print(f"  All IPs: {', '.join(interfaces)}")
        
        elif choice == "2":
            scan_common_ports()
        
        elif choice == "3":
            demonstrate_socket_basics()
        
        elif choice == "4":
            simple_tcp_server_demo()
        
        elif choice == "5":
            network_diagnostics()
        
        elif choice == "6":
            explain_concepts()
        
        elif choice == "7":
            break
        
        else:
            print("❌ Pilihan tidak valid")
    
    print("\n✅ Program selesai!")
    print("\n🔗 Useful Commands:")
    print("  hostname -I        # Show all IP addresses")
    print("  ip addr show       # Show network interfaces")
    print("  netstat -tuln      # Show listening ports")
    print("  ping <ip>          # Test connectivity")

except KeyboardInterrupt:
    print("\n\nProgram dihentikan")
