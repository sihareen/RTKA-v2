from gpiozero import OutputDevice
import time

# Definisi Pin Mundur Depan (Sesuai Config Anda)
PIN_FL_BWD = 27
PIN_FR_BWD = 25

print("--- TES MUNDUR MOTOR DEPAN ---")
print(f"Menyalakan GPIO {PIN_FL_BWD} (Kiri Depan) & {PIN_FR_BWD} (Kanan Depan)...")

try:
    # Kita pakai OutputDevice biar murni High/Low tanpa PWM
    motor_kiri_mundur = OutputDevice(PIN_FL_BWD)
    motor_kanan_mundur = OutputDevice(PIN_FR_BWD)
    
    # Nyalakan!
    motor_kiri_mundur.on()
    motor_kanan_mundur.on()
    
    print("MUNDUR AKTIF! (Tahan 3 detik)")
    time.sleep(3)
    
    motor_kiri_mundur.off()
    motor_kanan_mundur.off()
    print("BERHENTI.")

except Exception as e:
    print(f"Error: {e}")