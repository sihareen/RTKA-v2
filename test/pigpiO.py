import os
import time
import sys
from rpi_hardware_pwm import HardwarePWM

# ================= AUTO-FIX =================
print("Mengatur Pin 12 ke mode PWM (Alt0)...")
os.system("pinctrl set 12 a0")
# ============================================

# KONFIGURASI
PWM_CHANNEL = 0   # GPIO 12
MIN_DC = 0.0      # Posisi 0 derajat
MAX_DC = 15.0     # Posisi 180 derajat
STEP = 0.05       # Resolusi gerakan
DELAY = 0.01      # Kecepatan swipe

# Inisialisasi PWM
pwm = HardwarePWM(pwm_channel=PWM_CHANNEL, hz=50)

def hitung_derajat(duty_cycle):
    """
    Mengubah Duty Cycle menjadi perkiraan Sudut Derajat.
    Rumus: (DutySekarang - MinDuty) * (180 / RentangDuty)
    """
    rentang_duty = MAX_DC - MIN_DC
    sudut = (duty_cycle - MIN_DC) * (180 / rentang_duty)
    return round(sudut, 1)

def main():
    pwm.start(MIN_DC)
    print(f"Mulai Swipe... (Range: {MIN_DC}% - {MAX_DC}%)")
    print("Tekan Ctrl+C untuk stop")
    time.sleep(1)

    try:
        while True:
            # --- SWIPE KE KANAN (0 -> 180) ---
            print("\n>>> Gerak KANAN >>>")
            duty = MIN_DC
            while duty <= MAX_DC:
                # Update posisi servo
                pwm.change_duty_cycle(duty)
                
                # Hitung dan Log ke terminal
                sudut = hitung_derajat(duty)
                print(f"Duty: {duty:.2f}%  |  Sudut: {sudut:>5.1f}°")
                
                duty += STEP
                duty = round(duty, 3) # Menghindari error koma floating point
                time.sleep(DELAY)
            
            time.sleep(0.5) 

            # --- SWIPE KE KIRI (180 -> 0) ---
            print("\n<<< Gerak KIRI <<<")
            duty = MAX_DC
            while duty >= MIN_DC:
                # Update posisi servo
                pwm.change_duty_cycle(duty)
                
                # Hitung dan Log ke terminal
                sudut = hitung_derajat(duty)
                print(f"Duty: {duty:.2f}%  |  Sudut: {sudut:>5.1f}°")
                
                duty -= STEP
                duty = round(duty, 3) # Menghindari error koma floating point
                time.sleep(DELAY)
            
            time.sleep(0.5)

    except KeyboardInterrupt:
        print("\nBerhenti.")
        pwm.stop()
        sys.exit()

if __name__ == "__main__":
    main()