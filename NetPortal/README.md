# NetPortal (RTKA Wi-Fi Manager)

Konsep baru (tanpa watchdog):

1. Jalankan script manual.
2. RTKA auto-connect ke jaringan known (jika ada).
3. RTKA scan Wi-Fi sekitar selama 10 detik.
4. RTKA aktifkan AP `EdupiRobo_AP` + captive portal.
5. Di portal ada 2 opsi:
   - Connect ke jaringan known (saved profile)
   - Connect manual dengan SSID/password baru
6. Jika koneksi Wi-Fi terputus setelah online, script otomatis kembali ke AP.

## File

- `wifi_manager.py` - daemon utama + captive portal.
- `logs/portal.log` - log runtime.

## Jalankan manual

```bash
cd /home/pi/RTKAv2/NetPortal
sudo python3 wifi_manager.py
```

## Jalankan via systemd (tanpa watchdog)

```bash
sudo cp /home/pi/RTKAv2/NetPortal/netportal.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now netportal.service
sudo systemctl status netportal.service
```

## Environment variable (opsional)

- `RTKA_WIFI_IFACE` (default: `wlan0`)
- `RTKA_AP_NAME` (default: `EdupiRobo_AP`)
- `RTKA_AP_SSID` (default: `EdupiRobo_AP`)
- `RTKA_AP_PASSWORD` (default: 'edupi888')
- `RTKA_AP_IPV4` (default: `192.168.1.101/24`)
- `RTKA_PORTAL_PORT` (default: `80`)
- `RTKA_CONNECT_TIMEOUT` (default: `25` detik)
- `RTKA_SCAN_WINDOW_SEC` (default: `10` detik)
- `RTKA_MONITOR_INTERVAL_SEC` (default: `3` detik)
- `RTKA_PREFERRED_IP_OCTET` (default: `101`)

## Catatan

- Tidak perlu `watchdog.sh`.
- Jika sudah selesai konfigurasi, tekan `Ctrl+C` untuk stop script.
