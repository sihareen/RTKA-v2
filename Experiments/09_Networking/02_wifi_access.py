#!/usr/bin/env python3
"""
Bab 9.2: Mengakses Raspberry Pi via WiFi
=========================================
Setup dan akses Raspberry Pi melalui jaringan WiFi

Topik:
1. WiFi Configuration
2. SSH Access
3. VNC (Remote Desktop)
4. File Transfer (SCP/SFTP)
5. mDNS (raspberrypi.local)

SSH Command:
  ssh pi@192.168.1.100
  ssh pi@raspberrypi.local

SCP Transfer:
  scp file.txt pi@raspberrypi.local:~/
  scp pi@raspberrypi.local:~/data.csv ./
"""

import subprocess
import socket
import os
from datetime import datetime

print("="*70)
print("WiFi Access & Remote Connection")
print("="*70)

def show_wifi_status():
    """Tampilkan status WiFi"""
    print("\n📡 WiFi Status:")
    print("-" * 70)
    
    try:
        # Get SSID (network name)
        result = subprocess.run(['iwgetid', '-r'], 
                              capture_output=True, 
                              text=True)
        ssid = result.stdout.strip()
        
        if ssid:
            print(f"✅ Connected to: {ssid}")
        else:
            print(f"❌ Not connected to WiFi")
        
        # Get IP address
        result = subprocess.run(['hostname', '-I'], 
                              capture_output=True, 
                              text=True)
        ips = result.stdout.strip()
        
        if ips:
            print(f"📍 IP Address: {ips}")
        
        # Signal strength
        result = subprocess.run(['iwconfig', 'wlan0'], 
                              capture_output=True, 
                              text=True,
                              stderr=subprocess.DEVNULL)
        
        for line in result.stdout.split('\n'):
            if 'Link Quality' in line:
                print(f"📶 {line.strip()}")
        
    except FileNotFoundError:
        print("⚠️  WiFi tools not available")
    except Exception as e:
        print(f"❌ Error: {e}")

def check_ssh_status():
    """Cek apakah SSH service aktif"""
    print("\n🔐 SSH Service Status:")
    print("-" * 70)
    
    try:
        result = subprocess.run(['systemctl', 'is-active', 'ssh'], 
                              capture_output=True, 
                              text=True)
        status = result.stdout.strip()
        
        if status == "active":
            print("✅ SSH service is running")
            print(f"\nConnect using:")
            
            hostname = socket.gethostname()
            ip = subprocess.run(['hostname', '-I'], 
                              capture_output=True, 
                              text=True).stdout.strip().split()[0]
            
            print(f"  ssh pi@{ip}")
            print(f"  ssh pi@{hostname}.local")
        else:
            print("❌ SSH service is not running")
            print("\nTo enable SSH:")
            print("  sudo systemctl enable ssh")
            print("  sudo systemctl start ssh")
    
    except Exception as e:
        print(f"Error checking SSH: {e}")

def scan_local_network():
    """Scan perangkat di local network"""
    print("\n🔍 Scanning Local Network:")
    print("-" * 70)
    print("Mencari Raspberry Pi devices...")
    
    try:
        # Get local subnet
        ip = subprocess.run(['hostname', '-I'], 
                          capture_output=True, 
                          text=True).stdout.strip().split()[0]
        
        subnet = '.'.join(ip.split('.')[0:3]) + '.0/24'
        
        print(f"Subnet: {subnet}")
        print("\nScanning... (ini akan memakan waktu ~30 detik)")
        print("Tekan Ctrl+C untuk skip\n")
        
        # Use arp-scan if available
        result = subprocess.run(['which', 'arp-scan'], 
                              capture_output=True)
        
        if result.returncode == 0:
            # arp-scan available
            result = subprocess.run(['sudo', 'arp-scan', '--localnet'], 
                                  capture_output=True, 
                                  text=True,
                                  timeout=30)
            print(result.stdout)
        else:
            # Fallback to nmap
            result = subprocess.run(['which', 'nmap'], 
                                  capture_output=True)
            
            if result.returncode == 0:
                result = subprocess.run(['nmap', '-sn', subnet], 
                                      capture_output=True, 
                                      text=True,
                                      timeout=30)
                print(result.stdout)
            else:
                print("❌ arp-scan or nmap not installed")
                print("\nInstall dengan:")
                print("  sudo apt install arp-scan")
                print("  atau")
                print("  sudo apt install nmap")
    
    except subprocess.TimeoutExpired:
        print("\n⏱️  Scan timeout")
    except KeyboardInterrupt:
        print("\n\n⏸️  Scan cancelled")
    except Exception as e:
        print(f"Error: {e}")

def test_mdns():
    """Test mDNS (raspberrypi.local)"""
    print("\n🏷️  mDNS Test:")
    print("-" * 70)
    
    hostname = socket.gethostname()
    mdns_name = f"{hostname}.local"
    
    print(f"Hostname: {hostname}")
    print(f"mDNS: {mdns_name}")
    
    try:
        ip = socket.gethostbyname(mdns_name)
        print(f"✅ mDNS working: {mdns_name} → {ip}")
    except:
        print(f"❌ mDNS not resolving")
        print("\nTroubleshooting:")
        print("  1. Install avahi-daemon:")
        print("     sudo apt install avahi-daemon")
        print("  2. Restart service:")
        print("     sudo systemctl restart avahi-daemon")

def show_connection_info():
    """Tampilkan informasi koneksi lengkap"""
    print("\n📋 Connection Information:")
    print("="*70)
    
    hostname = socket.gethostname()
    
    try:
        ip = subprocess.run(['hostname', '-I'], 
                          capture_output=True, 
                          text=True).stdout.strip().split()[0]
    except:
        ip = "unknown"
    
    print(f"\n🖥️  Device Info:")
    print(f"  Hostname: {hostname}")
    print(f"  IP: {ip}")
    print(f"  mDNS: {hostname}.local")
    
    print(f"\n🔐 SSH Access:")
    print(f"  ssh pi@{ip}")
    print(f"  ssh pi@{hostname}.local")
    
    print(f"\n📁 File Transfer (SCP):")
    print(f"  # Upload to RPi")
    print(f"  scp myfile.txt pi@{ip}:~/")
    print(f"  # Download from RPi")
    print(f"  scp pi@{ip}:~/data.csv ./")
    
    print(f"\n🖼️  VNC Access:")
    print(f"  vnc://{ip}:5900")
    print(f"  (Enable VNC in raspi-config)")
    
    print(f"\n🌐 Web Access:")
    print(f"  http://{ip}:5000  (Flask default)")
    print(f"  http://{ip}:8000  (Python HTTP server)")

def create_hotspot_info():
    """Info tentang membuat WiFi hotspot"""
    print("\n📶 WiFi Hotspot Mode:")
    print("-" * 70)
    
    print("\nRaspberry Pi bisa jadi WiFi Access Point!")
    print("\nKegunaan:")
    print("  ✓ Kontrol robot tanpa WiFi eksternal")
    print("  ✓ Demo di lapangan")
    print("  ✓ Setup awal tanpa router")
    
    print("\nSetup Hotspot:")
    print("  1. Install dependencies:")
    print("     sudo apt install hostapd dnsmasq")
    
    print("\n  2. Configure hostapd (/etc/hostapd/hostapd.conf):")
    print("     interface=wlan0")
    print("     ssid=RaspberryPi-Robot")
    print("     wpa_passphrase=robot123")
    print("     channel=7")
    
    print("\n  3. Configure dnsmasq (/etc/dnsmasq.conf):")
    print("     interface=wlan0")
    print("     dhcp-range=192.168.4.2,192.168.4.20,255.255.255.0,24h")
    
    print("\n  4. Set static IP:")
    print("     Add to /etc/dhcpcd.conf:")
    print("     interface wlan0")
    print("     static ip_address=192.168.4.1/24")
    
    print("\n  5. Enable & start services:")
    print("     sudo systemctl unmask hostapd")
    print("     sudo systemctl enable hostapd dnsmasq")
    print("     sudo systemctl start hostapd dnsmasq")
    
    print("\nSetelah reboot, WiFi 'RaspberryPi-Robot' akan muncul")
    print("Connect dengan password: robot123")
    print("Access via: http://192.168.4.1:5000")

# ============================================================================
# MAIN PROGRAM
# ============================================================================

try:
    print("\n💡 Tentang WiFi Access:")
    print("  - Akses Raspberry Pi dari HP/Laptop")
    print("  - Tidak perlu monitor & keyboard")
    print("  - Cocok untuk robot & IoT projects")
    print()
    
    while True:
        print("\n" + "="*70)
        print("MENU:")
        print("  1. Show WiFi Status")
        print("  2. Check SSH Status")
        print("  3. Test mDNS")
        print("  4. Show Connection Info")
        print("  5. Scan Local Network")
        print("  6. WiFi Hotspot Info")
        print("  7. Exit")
        print("="*70)
        
        choice = input("\nPilihan: ").strip()
        
        if choice == "1":
            show_wifi_status()
        elif choice == "2":
            check_ssh_status()
        elif choice == "3":
            test_mdns()
        elif choice == "4":
            show_connection_info()
        elif choice == "5":
            scan_local_network()
        elif choice == "6":
            create_hotspot_info()
        elif choice == "7":
            break
        else:
            print("❌ Pilihan tidak valid")
    
    print("\n✅ Program selesai!")
    print("\n📱 Mobile Apps untuk Remote Access:")
    print("  - JuiceSSH (Android/iOS) - SSH client")
    print("  - VNC Viewer - Remote desktop")
    print("  - Termius - Modern SSH client")

except KeyboardInterrupt:
    print("\n\nProgram dihentikan")
