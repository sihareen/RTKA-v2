# Bab 21 - Face Attendance

Project absensi wajah berbasis OpenCV + YuNet + SFace embedding.

## Mode Baru: 1 Script Web (Recommended)

Jalankan satu script ini:

```bash
python3 04_face_attendance_web.py --host 0.0.0.0 --port 5000
```

Lalu buka di browser:

```text
http://<IP_RASPBERRY_PI>:5000
```

Fitur pada halaman web:
- Live camera stream
- Start enroll (code, name, samples)
- Start attendance mode
- Stop mode
- Export CSV per tanggal
- Config jam kedatangan & kepulangan

Catatan admin:
- Aksi `Save Enroll` dan `Save Config` meminta PIN admin.
- Default PIN awal: `123456`

## Dependencies

```bash
pip3 install opencv-python opencv-contrib-python numpy flask
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
python3 01_enroll_face.py --code EMP001 --name "Budi" --samples 70
```

Mode enroll terbaru:
- 7 sudut wajib: Depan, Menoleh Kiri, Menoleh Kanan, Tengadah, Menunduk, Miring Kiri, Miring Kanan
- Delay 3 detik saat mulai tiap sudut
- Total 70 foto fixed (10 foto per sudut)
- Deteksi wajah memakai YuNet, identifikasi memakai embedding SFace (cosine similarity)

3. Jalankan absensi realtime:

```bash
python3 02_attendance_realtime.py --threshold 0.36
```

4. Export laporan:

```bash
python3 03_export_report.py --date 2026-02-27
```

## Output Data

- Database: `data/attendance.db`
- Dataset wajah: `data/dataset/<person_code>/`
- Model detector: `models/face_detection_yunet_2023mar.onnx`
- Model recognizer: `models/face_recognition_sface_2021dec.onnx`
- Embedding index: `models/face_embeddings.json`
- Laporan CSV: `exports/`
