# LEVEL 1 - BEGINNER

Dasar physical computing dengan Raspberry Pi untuk Bab 1-6.

Dokumen ini menjelaskan fungsi masing-masing script secara rinci agar alur praktik jelas dari test dasar sampai mini project.

Struktur folder:

- 01_GPIO: konsep input/output, HIGH/LOW, BCM vs BOARD
- 02_Output: eksperimen LED dasar sampai running LED
- 03_Input: push button, pull-up/pull-down, polling, event-driven
- 04_Buzzer: beep, alarm, feedback audio
- 05_Sensor: ultrasonik, pengukuran jarak, filtering, integrasi LED/Buzzer
- 06_Mini_Project_Beginner: proyek alarm jarak dan auto light

## Detail Fungsi Script per Bab

### Bab 1 - GPIO Dasar (Folder 01_GPIO)

- 00_test_gpio_setup.py
	- Fungsi utama: memastikan akses GPIO berjalan dan LED dapat ON/OFF.
	- Tujuan belajar: validasi environment sebelum masuk eksperimen lain.
	- Output saat run: LED menyala 1 detik lalu mati, status setup.

- 01_io_concept_demo.py
	- Fungsi utama: demo konsep input-output real-time.
	- Cara kerja: tombol sebagai input, LED sebagai output.
	- Output saat run: LED otomatis ON saat tombol ditekan dan OFF saat dilepas.

- 02_logic_high_low.py
	- Fungsi utama: menunjukkan pergantian logika digital HIGH dan LOW.
	- Tujuan belajar: memahami hubungan status pin dengan tegangan digital.
	- Output saat run: status HIGH/LOW berganti periodik setiap 1 detik.

- 03_bcm_vs_board.py
	- Fungsi utama: referensi mapping pin BOARD dan BCM.
	- Tujuan belajar: mencegah salah wiring akibat salah mode penomoran.
	- Output saat run: tabel mapping pin umum yang sering dipakai di eksperimen.

### Bab 2 - Output Dasar (Folder 02_Output)

- 00_test_output.py
	- Fungsi utama: test awal output multi-LED secara berurutan.
	- Tujuan belajar: cek koneksi beberapa LED sebelum eksperimen detail.
	- Output saat run: LED menyala satu per satu lalu mati.

- 01_single_led.py
	- Fungsi utama: menyalakan satu LED selama 5 detik.
	- Tujuan belajar: output digital paling dasar.
	- Output saat run: LED ON stabil lalu OFF.

- 02_led_blink_delay.py
	- Fungsi utama: membuat LED berkedip dengan delay tetap.
	- Tujuan belajar: loop dan timing control sederhana.
	- Output saat run: LED berkedip ON/OFF periodik sampai dihentikan.

- 03_led_functions.py
	- Fungsi utama: mengelola LED dengan pendekatan fungsi modular.
	- Tujuan belajar: struktur kode rapi, reusable, dan mudah dikembangkan.
	- Output saat run: LED ON beberapa detik, lalu blink sesuai parameter fungsi.

- 04_running_led.py
	- Fungsi utama: pola running LED pada beberapa pin.
	- Tujuan belajar: koordinasi multi-output dan sequencing.
	- Output saat run: LED menyala bergantian membentuk efek berjalan.

### Bab 3 - Input Dasar (Folder 03_Input)

- 00_test_input.py
	- Fungsi utama: test pembacaan tombol cepat.
	- Tujuan belajar: validasi input digital sebelum masuk polling/event.
	- Output saat run: terminal menampilkan status DITEKAN atau LEPAS.

- 01_push_button_basic.py
	- Fungsi utama: membaca status tombol dengan is_pressed.
	- Tujuan belajar: memahami boolean input pada gpiozero.
	- Output saat run: True atau False secara berkala.

- 02_pullup_pulldown_demo.py
	- Fungsi utama: membandingkan konfigurasi pull-up dan pull-down.
	- Tujuan belajar: memahami kondisi default pin dan mencegah floating.
	- Output saat run: dua status tombol ditampilkan bersamaan.

- 03_button_polling.py
	- Fungsi utama: pembacaan tombol dengan polling loop.
	- Tujuan belajar: metode sampling input periodik.
	- Output saat run: pesan Tombol ditekan atau tidak ditekan tiap interval.

- 04_button_event_interrupt.py
	- Fungsi utama: input berbasis event (interrupt sederhana).
	- Tujuan belajar: model event-driven yang lebih efisien dari polling.
	- Output saat run: event ditekan atau dilepas muncul saat perubahan terjadi.

### Bab 4 - Buzzer dan Indikator Audio (Folder 04_Buzzer)

- 00_test_buzzer.py
	- Fungsi utama: test buzzer dan pengantar active vs passive buzzer.
	- Tujuan belajar: memahami konsep active-low pada board.
	- Output saat run: bunyi beep dua kali sebagai validasi.

- 01_beep_basic.py
	- Fungsi utama: menghasilkan beep pendek berulang.
	- Tujuan belajar: pola audio sederhana untuk indikator sistem.
	- Output saat run: 5 beep pendek.

- 02_simple_alarm.py
	- Fungsi utama: membuat pola alarm sederhana (beep cepat per siklus).
	- Tujuan belajar: membangun alarm berbasis pola waktu.
	- Output saat run: beberapa siklus alarm dengan jeda antar siklus.

- 03_audio_feedback_embedded.py
	- Fungsi utama: pola suara berbeda untuk status OK, WARNING, ERROR.
	- Tujuan belajar: audio feedback sebagai UI sistem embedded.
	- Output saat run: tiga pola bunyi berbeda untuk tiap status.

### Bab 5 - Sensor Dasar (Folder 05_Sensor)

- 00_test_ultrasonic.py
	- Fungsi utama: test pembacaan sensor HC-SR04.
	- Tujuan belajar: memastikan sensor dan wiring TRIG-ECHO valid.
	- Output saat run: nilai jarak cm dalam beberapa sampel.

- 01_measure_distance.py
	- Fungsi utama: monitoring jarak real-time.
	- Tujuan belajar: membaca data sensor kontinu.
	- Output saat run: nilai jarak terus ter-update.

- 02_distance_filtering.py
	- Fungsi utama: filtering data jarak dengan moving average.
	- Tujuan belajar: meredam noise agar pembacaan lebih stabil.
	- Output saat run: perbandingan nilai raw dan filtered.

- 03_distance_led_buzzer_app.py
	- Fungsi utama: aplikasi sensor jarak terintegrasi LED dan buzzer.
	- Tujuan belajar: aksi output otomatis berdasarkan threshold sensor.
	- Output saat run: status AMAN atau DEKAT, LED/buzzer aktif saat dekat.

### Bab 6 - Mini Project Beginner (Folder 06_Mini_Project_Beginner)

- 01_distance_alarm_system.py
	- Fungsi utama: sistem alarm jarak bertingkat (safe, mid, near).
	- Tujuan belajar: integrasi sensor + filtering + pola alarm + indikator LED.
	- Output saat run: mode alarm berubah sesuai jarak objek.

- 02_auto_light_sensor.py
	- Fungsi utama: lampu otomatis berbasis deteksi objek (presence).
	- Tujuan belajar: otomasi ON/OFF dengan mekanisme delay padam.
	- Output saat run: state lampu ON, ON_DELAY, atau OFF.

- 03_challenge_mandiri.py
	- Fungsi utama: template eksplorasi untuk eksperimen lanjutan mandiri.
	- Tujuan belajar: mendorong modifikasi logika dan kreativitas implementasi.
	- Output saat run: pola random LED+buzzer sebagai baseline challenge.

## Urutan Run yang Direkomendasikan

1. Jalankan file 00_test pada setiap bab terlebih dahulu.
2. Lanjut ke file eksperimen berurutan 01, 02, 03, dst.
3. Setelah Bab 5 selesai, lanjut ke mini project Bab 6.

Urutan ini membantu meminimalkan error wiring karena validasi dilakukan bertahap.

## Cara Menjalankan

Contoh:

```bash
cd Experiments/02_Output
python3 01_single_led.py
```

## Catatan Pin Default

- LED utama: GPIO 17
- Tombol: GPIO 24
- Buzzer (active low): GPIO 23
- Ultrasonik TRIG: GPIO 5
- Ultrasonik ECHO: GPIO 6

Sesuaikan pin jika wiring board Anda berbeda.