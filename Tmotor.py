# Simpan sebagai: final_test.py
from gpiozero import OutputDevice
from time import sleep

# Definisi sesuai instruksi saya barusan
motors = {
    "Kiri Depan": (17, 27),
    "Kiri Belakang": (22, 23),
    "Kanan Depan": (24, 25),
    "Kanan Belakang": (5, 6)
}

print("--- FINAL TEST ---")
try:
    for nama, (pinA, pinB) in motors.items():
        print(f"Tes {nama}...", end=" ")
        maju = OutputDevice(pinA)
        mundur = OutputDevice(pinB)
        
        maju.on()
        sleep(1)
        maju.off()
        
        maju.close()
        mundur.close()
        print("OK")
        sleep(0.5)
        
    print("Selesai. Jika ada roda terbalik (mundur), cukup tukar angka Pin di config.py")

except Exception as e:
    print(f"Error: {e}")
