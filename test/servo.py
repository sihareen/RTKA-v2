import time
from gpiozero import Servo
from time import sleep

servo_angguk_pin = 13
servo_geleng_pin = 12

TITIK_NOL_ANGGUK = 0.95

rentang_angguk = 0.3
rentang_geleng = 1.0 # Nilai ini membuat gerakan menggeleng menjadi lebih luas

servo_angguk = Servo(servo_angguk_pin, min_pulse_width=0.5/1000, max_pulse_width=2.5/1000)
servo_geleng = Servo(servo_geleng_pin, min_pulse_width=0.5/1000, max_pulse_width=2.5/1000)

def gerak_halus(servo, posisi_mulai, posisi_akhir, durasi):

    langkah_halus = 200
    selisih_posisi = posisi_akhir - posisi_mulai
    jeda_waktu = durasi / langkah_halus
    
    for i in range(langkah_halus + 1):
        posisi_saat_ini = posisi_mulai + (i / langkah_halus) * selisih_posisi
        posisi_saat_ini = max(-1.0, min(1.0, posisi_saat_ini))
        servo.value = posisi_saat_ini
        sleep(jeda_waktu)

try:
    print("Mengatur kedua servo ke posisi awal...")
    servo_angguk.value = TITIK_NOL_ANGGUK
    servo_geleng.value = 0.0
    sleep(1) 

    print("Memulai gerakan mengangguk dan menggeleng...")
    
    while True:
        posisi_depan = TITIK_NOL_ANGGUK - rentang_angguk
        gerak_halus(servo_angguk, TITIK_NOL_ANGGUK, posisi_depan, 2.0)
        gerak_halus(servo_angguk, posisi_depan, TITIK_NOL_ANGGUK, 2.0)
        
        posisi_kanan = rentang_geleng # Menggunakan nilai 1.0
        posisi_kiri = -rentang_geleng # Menggunakan nilai -1.0
        
        gerak_halus(servo_geleng, 0.0, posisi_kanan, 1.5) 
        gerak_halus(servo_geleng, posisi_kanan, posisi_kiri, 3.0) 
        gerak_halus(servo_geleng, posisi_kiri, 0.0, 1.5) 
        
except KeyboardInterrupt:
    print("Program dihentikan.")
    servo_angguk.close()
    servo_geleng.close()