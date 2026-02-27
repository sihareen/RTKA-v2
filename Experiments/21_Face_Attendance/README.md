# Bab 21 - Face Attendance

Project absensi wajah berbasis OpenCV + LBPH.

## Dependencies

```bash
pip3 install opencv-python opencv-contrib-python numpy
```

Opsional untuk Raspberry Pi Camera:

```bash
pip3 install picamera2
```

## Urutan Menjalankan

1. Test kamera:

```bash
python3 00_test_camera.py
```

2. Enroll user:

```bash
python3 01_enroll_face.py --code EMP001 --name "Budi" --samples 30
```

3. Jalankan absensi realtime:

```bash
python3 02_attendance_realtime.py --threshold 60
```

4. Export laporan:

```bash
python3 03_export_report.py --date 2026-02-27
```

## Output Data

- Database: `data/attendance.db`
- Dataset wajah: `data/dataset/<person_code>/`
- Model recognition: `models/lbph_trainer.yml`
- Mapping labels: `models/labels.json`
- Laporan CSV: `exports/`
