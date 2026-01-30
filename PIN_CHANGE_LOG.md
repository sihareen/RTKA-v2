# PERUBAHAN PIN - RTKAv2
# Tanggal: 30 Januari 2026

## PIN YANG DIGANTI:

1. **PIN_FR_FWD**: 24 → 10
   - Alasan: GPIO 24 tidak bisa membuat roda depan kanan maju
   - Status: Motor tidak bergerak

2. **PIN_RR_BWD**: 6 → 16
   - Alasan: GPIO 6 membuat motor mundur terus (tidak terkontrol)
   - Status: Motor aktif walau tidak ada perintah

3. **PIN_BUZZER**: 116 → 1
   - Alasan: GPIO 116 tidak valid (max GPIO 27 di Raspberry Pi)
   - Status: Typo/error konfigurasi

## WIRING BARU YANG HARUS DILAKUKAN:

### Motor Driver Kanan (Driver 2):
- **IN3** (FR Forward): Pindahkan dari GPIO 24 → GPIO 10
- **IN4** (RR Backward): Pindahkan dari GPIO 6 → GPIO 16

### Buzzer:
- **Signal Pin**: Pindahkan dari GPIO 116 → GPIO 1

## LANGKAH SELANJUTNYA:

1. **Rewiring Hardware**:
   ```
   Cabut kabel jumper:
   - GPIO 24 dari driver → Pindah ke GPIO 10
   - GPIO 6 dari driver → Pindah ke GPIO 16
   - GPIO 116 (jika ada) → Pindah ke GPIO 1
   ```

2. **Test Setelah Rewiring**:
   ```bash
   # Test motor baru
   python3 test/motor_wiring_test.py
   
   # Test cepat
   python3 test/quick_pin_test.py
   ```

3. **Restart Robot**:
   ```bash
   # Jika menggunakan systemd
   sudo systemctl restart raspbot
   
   # Atau restart manual
   python3 main.py
   ```

## BACKUP KONFIGURASI LAMA:

```python
# OLD CONFIG (SEBELUM PERUBAHAN):
PIN_FR_FWD = 24  # Bermasalah
PIN_RR_BWD = 6   # Bermasalah
PIN_BUZZER = 116 # Invalid
```

## VERIFIKASI:

Setelah rewiring, pastikan:
- ✓ Roda depan kanan bisa maju (GPIO 10)
- ✓ Roda belakang kanan tidak mundur sendiri (GPIO 16)
- ✓ Buzzer berfungsi (GPIO 1)

Jika masih ada masalah, kemungkinan hardware (driver/motor) rusak.
