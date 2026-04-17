# Panduan Eksekusi, Tuning, dan Practice Tracker RTKA v2

Dokumen ini dipakai sebagai peta kerja untuk menjalankan program di workspace Experiments, memahami bagian mana yang aman diubah, dan mencatat progres latihan.

## 1. Alur Eksekusi

Ikuti urutan ini agar setiap lapisan sistem divalidasi sebelum pindah ke lapisan berikutnya.

### Fase A - Fondasi Hardware

Tujuan: memastikan motor, sensor, dan wiring benar.

1. Jalankan `07_Motor/00_test_motor.py`
2. Lanjutkan ke `07_Motor/01_motor_dc_basic.py`
3. Coba `07_Motor/02_motor_driver_l298n.py`
4. Tuning kecepatan di `07_Motor/03_pwm_speed_control.py`
5. Kalibrasi kanan-kiri dengan `07_Motor/04_motor_calibration.py`
6. Verifikasi sensor ultrasonik dengan `08_Navigasi/00_test_ultrasonic.py`
7. Uji deteksi obstacle di `08_Navigasi/01_ultrasonic_obstacle.py`
8. Validasi logika avoidance di `08_Navigasi/02_avoidance_logic.py`
9. Jalankan state machine di `08_Navigasi/03_state_machine_robot.py`

### Fase B - Networking dan Web Control

Tujuan: memastikan robot bisa diakses dari jaringan lokal.

1. Jalankan `09_Networking/00_test_network.py`
2. Pelajari dasar jaringan di `09_Networking/01_network_basics.py`
3. Konfigurasi WiFi di `09_Networking/02_wifi_access.py`
4. Coba server dasar di `09_Networking/03_flask_webserver.py`
5. Lanjut ke kontrol GPIO via browser di `09_Networking/04_gpio_web_control.py`

### Fase C - IoT dan Remote Monitoring

Tujuan: menambah publish/subscribe, logging, dan dashboard.

1. Cek MQTT dengan `10_IoT/00_test_mqtt.py`
2. Lihat contoh publish/subscribe lain yang tersedia di folder `10_IoT`
3. Jalankan `10_IoT/01_mqtt_iot_complete.py`
4. Uji logging cloud di `10_IoT/02_cloud_data_logging.py`
5. Baca dan pakai dashboard realtime di `11_Remote/01_web_dashboard_realtime.py`
6. Lihat dashboard logging di `11_Remote/02_data_logging_dashboard.py`

### Fase D - Mini Project Terintegrasi

Tujuan: gabungkan motor, sensor, web, dan IoT.

1. Jalankan `12_Mini_Projects/00_test_autonomous.py`
2. Uji robot otonom di `12_Mini_Projects/01_autonomous_robot.py`
3. Coba kontrol web di `12_Mini_Projects/02_web_controlled_robot.py`
4. Coba monitoring IoT di `12_Mini_Projects/03_iot_monitoring_robot.py`

### Fase E - AI dan Computer Vision

Tujuan: masuk ke kamera, model ringan, dan visi komputer.

1. Verifikasi TensorFlow Lite dengan `14_AI_Introduction/00_test_tflite.py`
2. Pahami konsep AI di `14_AI_Introduction/01_ai_concepts.py`
3. Jalankan inferensi di `14_AI_Introduction/02_tflite_inference.py`
4. Tes kamera dengan `15_Computer_Vision/00_test_camera.py`
5. Pelajari streaming di `15_Computer_Vision/01_camera_opencv.py`
6. Tes deteksi wajah dasar di `16_Face_Detection/00_test_face_detection.py`
7. Jalankan deteksi wajah lengkap di `16_Face_Detection/01_face_detection_complete.py`
8. Tes object detection di `17_Object_Detection/00_test_object_detection.py`
9. Jalankan `17_Object_Detection/01_mobilenet_ssd.py`
10. Tes hand tracking di `18_Gesture_Recognition/00_test_hand_tracking.py`
11. Jalankan `18_Gesture_Recognition/01_hand_tracking_mediapipe.py`
12. Tes sensor fusion di `19_Intelligent_Systems/00_test_sensor_fusion.py`
13. Jalankan `19_Intelligent_Systems/01_autonomous_navigation_ai.py`

### Fase F - Capstone dan Absensi Wajah

Tujuan: validasi sistem lengkap dan aplikasi nyata.

1. Cek integrasi dengan `20_Capstone_Projects/00_test_complete_system.py`
2. Jalankan `20_Capstone_Projects/01_smart_security_robot.py`
3. Tes kamera absensi dengan `21_Face_Attendance/00_test_camera.py`
4. Enroll wajah di `21_Face_Attendance/01_enroll_face.py`
5. Jalankan absensi realtime di `21_Face_Attendance/02_attendance_realtime.py`
6. Export laporan dengan `21_Face_Attendance/03_export_report.py`
7. Jalankan web attendance di `21_Face_Attendance/04_face_attendance_web.py`

## 2. Cara Modify / Tuning yang Aman

Prinsip utama: ubah parameter di blok konfigurasi, bukan logika inti, kecuali Anda benar-benar sedang memperbaiki perilaku algoritmik.

### A. Motor dan PWM

File referensi:
- `07_Motor/03_pwm_speed_control.py`
- `07_Motor/04_motor_calibration.py`
- `08_Navigasi/03_state_machine_robot.py`
- `12_Mini_Projects/01_autonomous_robot.py`

Yang aman diubah:
- `speed` atau `NORMAL_SPEED` dalam rentang `0.3` sampai `0.8`
- `TURN_SPEED` dalam rentang `0.4` sampai `0.7`
- durasi belok/mundur seperti `TURN_DURATION` dan `BACKUP_DURATION`
- faktor kalibrasi kiri dan kanan untuk menyeimbangkan laju

Contoh variabel motor yang bisa di-tuning langsung di program:
- `motor.forward(0.5)` dan `motor.backward(0.5)` di `07_Motor/01_motor_dc_basic.py` dan `07_Motor/02_motor_driver_l298n.py`
- `speeds = [(0.2, ...), (0.4, ...), (0.6, ...), (0.8, ...), (1.0, ...)]` di `07_Motor/03_pwm_speed_control.py`
- `speed_decimal = speed / 100.0` di loop percepatan/perlambatan, kalau ingin langkah tuning lebih halus
- `LEFT_CALIBRATION` dan `RIGHT_CALIBRATION` di `07_Motor/04_motor_calibration.py`
- `base_speed` dan `duration` pada fungsi `calibrated_move(base_speed, duration=2)` di `07_Motor/04_motor_calibration.py`
- `NORMAL_SPEED`, `SLOW_SPEED`, `TURN_SPEED` di program autonomous dan state machine
- `TURN_DURATION` dan `BACKUP_DURATION` jika robot terlalu cepat atau terlalu lama saat manuver

Saran tuning:
- Jika robot cenderung belok kiri saat maju lurus, turunkan speed sisi kanan atau naikkan speed sisi kiri sedikit.
- Jika robot terlalu agresif saat belok, turunkan `TURN_SPEED` atau perpanjang `TURN_DURATION` sedikit demi sedikit.
- Lakukan tuning di lantai datar dan dengan baterai penuh.
- Ubah hanya satu variabel per percobaan, lalu catat efeknya pada tracker.
- Untuk PWM, perubahan kecil lebih aman: misalnya dari `0.5` ke `0.55`, bukan langsung ke `0.8`.

### B. Ultrasonik dan Avoidance

File referensi:
- `08_Navigasi/01_ultrasonic_obstacle.py`
- `08_Navigasi/02_avoidance_logic.py`
- `08_Navigasi/03_state_machine_robot.py`
- `12_Mini_Projects/01_autonomous_robot.py`
- `19_Intelligent_Systems/01_autonomous_navigation_ai.py`

Yang aman diubah:
- `SAFE_DISTANCE` atau `STOP_DISTANCE`
- `SLOW_DISTANCE`
- `SCAN_INTERVAL`
- `BACKUP_DURATION`

Saran tuning:
- Untuk ruangan sempit, turunkan threshold agar robot tidak terlalu sensitif.
- Untuk robot yang sering menabrak, naikkan threshold dan tambah waktu mundur.
- Jika sensor terbaca tidak stabil, tambahkan filtering atau rata-rata beberapa sampel sebelum keputusan.

### C. Networking, Flask, dan Web Control

File referensi:
- `09_Networking/03_flask_webserver.py`
- `09_Networking/04_gpio_web_control.py`
- `11_Remote/01_web_dashboard_realtime.py`
- `11_Remote/02_data_logging_dashboard.py`
- `12_Mini_Projects/02_web_controlled_robot.py`

Yang aman diubah:
- `host` dan `port`
- interval polling sensor di dashboard
- teks UI, endpoint, dan nama tombol
- skema logging ringan di SQLite

Saran tuning:
- Gunakan `0.0.0.0` jika ingin diakses dari device lain di jaringan.
- Gunakan port di atas `1024`, misalnya `5000`, `8080`, atau `8081`.
- Jika dashboard terasa lambat, perbesar interval refresh agar CPU tidak penuh.

### D. MQTT dan IoT

File referensi:
- `10_IoT/01_mqtt_iot_complete.py`
- `10_IoT/02_cloud_data_logging.py`
- `12_Mini_Projects/03_iot_monitoring_robot.py`

Yang aman diubah:
- alamat broker: `localhost` atau broker cloud
- `MQTT_PORT`
- `TOPIC` publish/subscribe
- `QoS`
- interval publish telemetry

Saran tuning:
- Untuk lab lokal, gunakan broker lokal agar lebih stabil.
- Untuk demo remote, gunakan topic yang unik per device agar tidak bentrok.
- Jangan kirim telemetry terlalu rapat jika jaringan tidak stabil atau broker publik sedang padat.

### E. Kamera, Vision, dan AI

File referensi:
- `15_Computer_Vision/01_camera_opencv.py`
- `16_Face_Detection/01_face_detection_complete.py`
- `17_Object_Detection/01_mobilenet_ssd.py`
- `18_Gesture_Recognition/01_hand_tracking_mediapipe.py`
- `19_Intelligent_Systems/01_autonomous_navigation_ai.py`
- `20_Capstone_Projects/01_smart_security_robot.py`

Yang aman diubah:
- resolusi kamera
- confidence threshold deteksi
- jumlah thread inferensi
- kecepatan frame capture
- ukuran input model jika didukung

Saran tuning:
- Kalau deteksi terlalu banyak false positive, naikkan threshold.
- Kalau deteksi terlalu sedikit, turunkan threshold sedikit demi sedikit.
- Di Raspberry Pi, jangan langsung mengejar resolusi tinggi; stabilitas lebih penting daripada tampilan besar.

### F. Face Attendance

File referensi:
- `21_Face_Attendance/attendance_utils.py`
- `21_Face_Attendance/01_enroll_face.py`
- `21_Face_Attendance/02_attendance_realtime.py`
- `21_Face_Attendance/04_face_attendance_web.py`

Yang aman diubah:
- threshold match wajah
- waktu tunggu antar capture
- jumlah sample enroll
- jam attendance arrival/departure
- admin PIN

Saran tuning:
- Jika sering salah kenal, turunkan tolerance secara hati-hati.
- Jika wajah valid sering ditolak, naikkan threshold sedikit.
- Simpan data enroll yang bersih; kualitas foto lebih penting daripada jumlah mentah.

## 3. Referensi Variabel Tuning per Folder 07-21

Bagian ini merangkum variabel yang paling sering dan paling aman untuk diubah pada tiap folder.

### 07_Motor

File referensi:
- `07_Motor/01_motor_dc_basic.py`
- `07_Motor/02_motor_driver_l298n.py`
- `07_Motor/03_pwm_speed_control.py`
- `07_Motor/04_motor_calibration.py`

Variabel yang bisa dituning:

| Variabel | Dipakai di | Efek jika dinaikkan | Efek jika diturunkan |
|---|---|---|---|
| `speed` | motor basic, driver, PWM | Motor lebih cepat | Motor lebih pelan |
| `speeds` | PWM demo | Step speed lebih tinggi jika list diubah | Step speed lebih halus jika diturunkan |
| `LEFT_CALIBRATION` | kalibrasi | Sisi kiri lebih kuat | Sisi kiri lebih lemah |
| `RIGHT_CALIBRATION` | kalibrasi | Sisi kanan lebih kuat | Sisi kanan lebih lemah |
| `TURN_DURATION` | autonomous/state machine | Belokan lebih besar | Belokan lebih kecil |
| `BACKUP_DURATION` | avoidance | Mundur lebih jauh | Mundur lebih singkat |

### 08_Navigasi

File referensi:
- `08_Navigasi/01_ultrasonic_obstacle.py`
- `08_Navigasi/02_avoidance_logic.py`
- `08_Navigasi/03_state_machine_robot.py`

Variabel yang bisa dituning:

| Variabel | Dipakai di | Efek jika dinaikkan | Efek jika diturunkan |
|---|---|---|---|
| `SAFE_DISTANCE` | obstacle/avoidance | Robot lebih waspada | Robot lebih dekat ke obstacle sebelum bereaksi |
| `STOP_DISTANCE` | state machine | Stop lebih cepat | Stop lebih lambat |
| `SLOW_DISTANCE` | autonomous robot | Zona perlambatan lebih luas | Zona perlambatan lebih sempit |
| `SCAN_INTERVAL` | avoidance/sensor loop | Sensor dibaca lebih jarang | Sensor dibaca lebih sering |
| `speed` | movement logic | Gerakan lebih agresif | Gerakan lebih lembut |
| `turn_direction` | autonomous robot | Prioritas belok berubah | Prioritas kembali ke default |

### 09_Networking

File referensi:
- `09_Networking/03_flask_webserver.py`
- `09_Networking/04_gpio_web_control.py`

Variabel yang bisa dituning:

| Variabel | Dipakai di | Efek jika dinaikkan | Efek jika diturunkan |
|---|---|---|---|
| `host` | Flask app | Lebih mudah diakses dari device lain jika `0.0.0.0` | Hanya lokal jika `127.0.0.1` |
| `port` | Flask app | Port berbeda, bisa hindari konflik | Bisa bentrok jika port sudah dipakai |
| `visit_count` | demo web | Counter lebih besar | Counter lebih kecil |
| interval polling sensor | web control | Update lebih lambat tapi ringan | Update lebih cepat tapi berat |
| endpoint path | API web | URL lebih rapi / spesifik | URL lebih sederhana |

### 10_IoT

File referensi:
- `10_IoT/01_mqtt_iot_complete.py`
- `10_IoT/02_cloud_data_logging.py`

Variabel yang bisa dituning:

| Variabel | Dipakai di | Efek jika dinaikkan | Efek jika diturunkan |
|---|---|---|---|
| `MQTT_BROKER` | MQTT client | Pindah ke broker cloud tertentu | Kembali ke broker lokal |
| `MQTT_PORT` | MQTT client | Port non-default sesuai broker | Default 1883 untuk plain MQTT |
| `MQTT_TOPIC_SENSOR` | publish sensor | Topic lebih spesifik | Topic lebih umum |
| `MQTT_TOPIC_CONTROL` | subscribe command | Command channel lebih spesifik | Command channel lebih umum |
| `message_count` | statistik publish | Statistik lebih tinggi | Statistik lebih rendah |
| publish interval | telemetry loop | Traffic lebih rapat | Traffic lebih hemat |
| `QoS` | publish | Jaminan delivery lebih tinggi | Overhead lebih rendah |

### 11_Remote

File referensi:
- `11_Remote/01_web_dashboard_realtime.py`
- `11_Remote/02_data_logging_dashboard.py`

Variabel yang bisa dituning:

| Variabel | Dipakai di | Efek jika dinaikkan | Efek jika diturunkan |
|---|---|---|---|
| `speed` | dashboard control | Robot lebih cepat | Robot lebih pelan |
| `robot_state['distance']` update rate | sensor dashboard | Data lebih responsif | Data lebih ringan |
| refresh/polling interval | logging dashboard | Update lebih lambat | Update lebih cepat |
| chart history length | Chart.js | Riwayat lebih panjang | Chart lebih ringan |
| alert threshold | alert system | Lebih sensitif | Lebih longgar |
| `DB_FILE` | logging | Simpan data ke file berbeda | Tetap file default |

### 12_Mini_Projects

File referensi:
- `12_Mini_Projects/01_autonomous_robot.py`
- `12_Mini_Projects/02_web_controlled_robot.py`
- `12_Mini_Projects/03_iot_monitoring_robot.py`

Variabel yang bisa dituning:

| Variabel | Dipakai di | Efek jika dinaikkan | Efek jika diturunkan |
|---|---|---|---|
| `STOP_DISTANCE` | autonomous robot | Stop lebih aman | Robot lebih berani mendekat |
| `SLOW_DISTANCE` | autonomous robot | Perlambatan lebih awal | Perlambatan lebih akhir |
| `NORMAL_SPEED` | autonomous/web robot | Gerakan umum lebih cepat | Gerakan umum lebih lambat |
| `TURN_SPEED` | autonomous/web robot | Belok lebih cepat | Belok lebih halus |
| `PATROL_SPEED` | IoT/security style | Patrol lebih cepat | Patrol lebih pelan |
| `INTRUSION_ALERT_TIME` | alert system | Alarm lebih lama | Alarm lebih singkat |
| telemetry interval | IoT robot | Update cloud lebih rapat | Lebih hemat bandwidth |

### 14_AI_Introduction

File referensi:
- `14_AI_Introduction/02_tflite_inference.py`

Variabel yang bisa dituning:

| Variabel | Dipakai di | Efek jika dinaikkan | Efek jika diturunkan |
|---|---|---|---|
| `iterations` | benchmark | Benchmark lebih panjang | Benchmark lebih singkat |
| `top_k` | prediksi | Hasil lebih banyak ditampilkan | Hasil lebih sedikit |
| input size model | preprocessing | Bisa cocok model tertentu | Bisa menurunkan akurasi jika salah |
| model path | load model | Ganti model lain | Kembali ke model default |

### 15_Computer_Vision

File referensi:
- `15_Computer_Vision/01_camera_opencv.py`

Variabel yang bisa dituning:

| Variabel | Dipakai di | Efek jika dinaikkan | Efek jika diturunkan |
|---|---|---|---|
| `resolution` | camera stream | Gambar lebih detail | FPS lebih stabil |
| `framerate` | camera stream | Respons lebih cepat jika kamera kuat | Beban CPU lebih ringan |
| `camera_id` | webcam selection | Ganti kamera aktif | Kembali ke default kamera |
| `snapshot_counter` | demo stream | Nama file snapshot berubah | Tidak berdampak ke isi video |

### 16_Face_Detection

File referensi:
- `16_Face_Detection/01_face_detection_complete.py`

Variabel yang bisa dituning:

| Variabel | Dipakai di | Efek jika dinaikkan | Efek jika diturunkan |
|---|---|---|---|
| `confidence_threshold` | DNN detector | Lebih ketat | Lebih banyak deteksi |
| `scaleFactor` | Haar detector | Pencarian ukuran lebih rapat | Pencarian lebih longgar |
| `minNeighbors` | Haar detector | False positive berkurang | Sensitif naik |
| `minSize` | Haar detector | Wajah kecil diabaikan | Wajah kecil tetap terbaca |

### 17_Object_Detection

File referensi:
- `17_Object_Detection/01_mobilenet_ssd.py`

Variabel yang bisa dituning:

| Variabel | Dipakai di | Efek jika dinaikkan | Efek jika diturunkan |
|---|---|---|---|
| `confidence_threshold` | object detector | Deteksi lebih ketat | Deteksi lebih banyak |
| `num_threads` | TFLite interpreter | Bisa lebih cepat di Pi 4/5 | CPU usage lebih rendah |
| `input_width` / `input_height` | preprocess | Input lebih besar dan detail | Input lebih kecil dan cepat |
| `MODEL_DIR` | model storage | Simpan model di folder lain | Kembali ke default |

### 18_Gesture_Recognition

File referensi:
- `18_Gesture_Recognition/01_hand_tracking_mediapipe.py`

Variabel yang bisa dituning:

| Variabel | Dipakai di | Efek jika dinaikkan | Efek jika diturunkan |
|---|---|---|---|
| `max_num_hands` | MediaPipe Hands | Lebih banyak tangan terdeteksi | Lebih ringan |
| `min_detection_confidence` | palm detection | Lebih ketat | Lebih sensitif |
| `min_tracking_confidence` | tracking | Tracking lebih stabil | Tracking lebih cepat lepas |
| gesture distance threshold | pinch/gesture rule | Lebih ketat | Lebih sensitif |

### 19_Intelligent_Systems

File referensi:
- `19_Intelligent_Systems/01_autonomous_navigation_ai.py`

Variabel yang bisa dituning:

| Variabel | Dipakai di | Efek jika dinaikkan | Efek jika diturunkan |
|---|---|---|---|
| `EMERGENCY_STOP_DISTANCE` | safety layer | Lebih aman | Lebih berani mendekat |
| `SAFE_DISTANCE` | nav decision | Lebih konservatif | Lebih agresif |
| `turn_preference` | decision maker | Bias belok berubah | Bias kembali netral |
| `risk_score` threshold | AI decision | Lebih sensitif | Lebih longgar |
| `camera_id` | sensor fusion | Ganti kamera | Kembali ke default |

### 20_Capstone_Projects

File referensi:
- `20_Capstone_Projects/01_smart_security_robot.py`

Variabel yang bisa dituning:

| Variabel | Dipakai di | Efek jika dinaikkan | Efek jika diturunkan |
|---|---|---|---|
| `PATROL_SPEED` | patrol mode | Patroli lebih cepat | Patroli lebih pelan |
| `PATROL_TURN_DURATION` | patrol turn | Putaran lebih besar | Putaran lebih kecil |
| `INTRUSION_ALERT_TIME` | alarm | Alarm lebih lama | Alarm lebih singkat |
| `FACE_RECOGNITION_ENABLED` | security flow | Fitur face recognition aktif | Nonaktif |
| `ALERTS_DIR` | file output | Simpan di folder lain | Default folder |
| `KNOWN_FACES_DIR` | database wajah | Simpan data wajah di folder lain | Default folder |

### 21_Face_Attendance

File referensi:
- `21_Face_Attendance/01_enroll_face.py`
- `21_Face_Attendance/02_attendance_realtime.py`
- `21_Face_Attendance/04_face_attendance_web.py`

Variabel yang bisa dituning:

| Variabel | Dipakai di | Efek jika dinaikkan | Efek jika diturunkan |
|---|---|---|---|
| `DEFAULT_TOTAL_SAMPLES` | enroll | Data wajah lebih banyak | Enroll lebih cepat |
| `ENROLL_ANGLE_DELAY_SEC` | enroll | Waktu adaptasi lebih lama | Enroll lebih cepat |
| `RECOGNITION_THRESHOLD` | matching | Lebih ketat | Lebih longgar |
| `DEFAULT_ADMIN_PIN` | web admin | PIN berubah | PIN default tetap |
| `arrival_start/end` | attendance config | Jadwal kedatangan berubah | Jadwal kembali default |
| `departure_start/end` | attendance config | Jadwal pulang berubah | Jadwal kembali default |
| `recent_mark` cooldown | realtime attendance | Cegah check-in ganda lebih lama | Bisa accept lebih cepat |

## 4. Batasan Yang Sebaiknya Tidak Diubah Sembarangan

## 3. Batasan Yang Sebaiknya Tidak Diubah Sembarangan

Jangan ubah dulu hal berikut kecuali Anda sedang debugging hardware atau refactor besar:

- mapping GPIO pin motor, sensor, LED, buzzer
- nama file model yang diunduh otomatis
- struktur tabel SQLite kecuali Anda paham migrasi datanya
- urutan logika state machine tanpa memahami transisinya
- bagian startup kamera dan cleanup resource

Kalau harus mengubahnya:
- ubah satu per satu
- dokumentasikan perubahan
- test ulang dengan file `00_test_*` yang relevan

## 4. Practice Tracker

Gunakan tracker ini untuk latihan terukur.

### Skor Latihan

- `0` = belum dicoba
- `1` = jalan tapi belum paham
- `2` = paham dasar
- `3` = bisa modifikasi aman
- `4` = bisa tuning sendiri
- `5` = bisa jelaskan dan debug

### Tracker Mingguan

| Minggu | Target | File Utama | Status | Skor | Catatan |
|---|---|---|---|---|---|
| 1 | Motor test dan PWM | `07_Motor/00_test_motor.py` | [ ] | 0 | |
| 1 | Motor basic | `07_Motor/01_motor_dc_basic.py` | [ ] | 0 | |
| 1 | Calibration | `07_Motor/04_motor_calibration.py` | [ ] | 0 | |
| 2 | Ultrasonic and avoidance | `08_Navigasi/01_ultrasonic_obstacle.py` | [ ] | 0 | |
| 2 | State machine | `08_Navigasi/03_state_machine_robot.py` | [ ] | 0 | |
| 3 | Flask and GPIO web control | `09_Networking/03_flask_webserver.py` | [ ] | 0 | |
| 3 | Browser control | `09_Networking/04_gpio_web_control.py` | [ ] | 0 | |
| 4 | MQTT and cloud logging | `10_IoT/01_mqtt_iot_complete.py` | [ ] | 0 | |
| 4 | Remote dashboard | `11_Remote/01_web_dashboard_realtime.py` | [ ] | 0 | |
| 5 | Autonomous robot | `12_Mini_Projects/01_autonomous_robot.py` | [ ] | 0 | |
| 5 | Web robot | `12_Mini_Projects/02_web_controlled_robot.py` | [ ] | 0 | |
| 6 | TFLite intro | `14_AI_Introduction/02_tflite_inference.py` | [ ] | 0 | |
| 6 | Camera pipeline | `15_Computer_Vision/01_camera_opencv.py` | [ ] | 0 | |
| 7 | Face detection | `16_Face_Detection/01_face_detection_complete.py` | [ ] | 0 | |
| 7 | Object detection | `17_Object_Detection/01_mobilenet_ssd.py` | [ ] | 0 | |
| 8 | Gesture recognition | `18_Gesture_Recognition/01_hand_tracking_mediapipe.py` | [ ] | 0 | |
| 8 | Sensor fusion | `19_Intelligent_Systems/01_autonomous_navigation_ai.py` | [ ] | 0 | |
| 9 | Capstone system | `20_Capstone_Projects/01_smart_security_robot.py` | [ ] | 0 | |
| 10 | Face enroll | `21_Face_Attendance/01_enroll_face.py` | [ ] | 0 | |
| 10 | Face attendance web | `21_Face_Attendance/04_face_attendance_web.py` | [ ] | 0 | |

### Checklist per Praktik

Isi ini setelah selesai satu file:

- File dijalankan tanpa error
- Hardware yang dibutuhkan sudah terhubung
- Saya tahu input dan output program
- Saya tahu parameter mana yang aman diubah
- Saya sudah mencoba satu tuning kecil
- Saya bisa menjelaskan alur eksekusinya
- Saya menyimpan catatan hasil eksperimen

## 5. Template Catatan Eksperimen

Gunakan format ini untuk setiap sesi:

```text
Tanggal:
File:
Tujuan:
Parameter yang diubah:
Sebelum tuning:
Sesudah tuning:
Masalah yang muncul:
Solusi:
Kesimpulan:
```

## 6. Rekomendasi Urutan Belajar Singkat

1. Kuasai motor dan sensor dulu.
2. Pindah ke state machine dan avoidance.
3. Baru masuk web control dan MQTT.
4. Setelah itu, masuk camera, AI, dan face attendance.
5. Tutup dengan capstone dan integrasi penuh.

## 7. File Paling Penting Untuk Memulai

- [07_Motor/00_test_motor.py](07_Motor/00_test_motor.py)
- [07_Motor/04_motor_calibration.py](07_Motor/04_motor_calibration.py)
- [08_Navigasi/03_state_machine_robot.py](08_Navigasi/03_state_machine_robot.py)
- [09_Networking/04_gpio_web_control.py](09_Networking/04_gpio_web_control.py)
- [10_IoT/01_mqtt_iot_complete.py](10_IoT/01_mqtt_iot_complete.py)
- [11_Remote/01_web_dashboard_realtime.py](11_Remote/01_web_dashboard_realtime.py)
- [12_Mini_Projects/03_iot_monitoring_robot.py](12_Mini_Projects/03_iot_monitoring_robot.py)
- [15_Computer_Vision/01_camera_opencv.py](15_Computer_Vision/01_camera_opencv.py)
- [16_Face_Detection/01_face_detection_complete.py](16_Face_Detection/01_face_detection_complete.py)
- [21_Face_Attendance/04_face_attendance_web.py](21_Face_Attendance/04_face_attendance_web.py)

## 8. Cara Pakai Dokumen Ini

1. Jalankan program sesuai fase.
2. Tandai tracker setelah tiap sesi.
3. Kalau hasil tidak stabil, kembali ke file test pada fase yang sama.
4. Jangan tuning dua variabel besar sekaligus.
5. Simpan parameter akhir yang berhasil sebagai baseline.
