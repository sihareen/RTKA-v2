#!/bin/bash
AP_NAME="Raspbot_AP"

echo "Memulai proses aktivasi Hotspot: $AP_NAME"
echo "⚠️  PERINGATAN: Koneksi Wi-Fi ke internet akan diputus!"
echo "----------------------------------------"

if sudo nmcli connection up "$AP_NAME"; then
    echo ""
    echo "✅ SUKSES: Hotspot Raspbot sudah aktif."
    echo "----------------------------------------"
    echo "IP Address Hotspot Anda:"
    # Menampilkan IP address agar Anda tahu harus connect ke mana
    nmcli -g ip4.address connection show "$AP_NAME"
    echo "----------------------------------------"
else
    echo ""
    echo "❌ GAGAL: Tidak bisa mengaktifkan Hotspot."
fi
