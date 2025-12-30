from gpiozero import AngularServo, Device
from gpiozero.pins.lgpio import LGPIOFactory
import time

# ==========================================
# KONFIGURASI
# ==========================================
PIN_SERVO_TEST = 12  
THRESHOLD_GERAK = 20  # Batas minimal agar servo mau gerak normal

# ==========================================
# SETUP FACTORY
# ==========================================
try:
    factory = LGPIOFactory()
    Device.pin_factory = factory
except:
    pass

def main():
    print("=== SERVO TUNER: SMART MOVE MODE ===")
    print(f"Logic: Jika beda sudut < {THRESHOLD_GERAK}, gunakan 'Pancingan'")
    print("Range: -90 s/d 90")
    print("------------------------------------")

    servo = AngularServo(
        PIN_SERVO_TEST,
        min_angle=-90, max_angle=90,
        min_pulse_width=0.5/1000, max_pulse_width=2.5/1000
    )

    # Simpan posisi terakhir (anggap awal di 0)
    current_angle = 0
    servo.angle = 0
    time.sleep(0.5)

    try:
        while True:
            print(f"\n[Posisi Sekarang: {current_angle}]")
            raw = input("Target Sudut (-90 s/d 90): ")
            if raw.lower() == 'q': break
            
            try:
                target = float(raw)
                if not (-90 <= target <= 90):
                    print("Error: Di luar batas -90 s/d 90")
                    continue

                diff = abs(target - current_angle)

                # --- LOGIKA SMART MOVE ---
                if diff > 0 and diff < THRESHOLD_GERAK:
                    print(f" -> Jarak {diff} terlalu kecil (Rawan macet).")
                    print(" -> Melakukan manuver 'Pancingan'...")
                    
                    # Tentukan arah pancingan (Jauhi batas fisik)
                    # Jika target dekat batas atas (90), pancing ke bawah.
                    # Jika target dekat batas bawah (-90), pancing ke atas.
                    if target > 50:
                        kick_val = target - 25 # Pancing mundur
                    else:
                        kick_val = target + 25 # Pancing maju
                    
                    # 1. Gerak ke posisi pancingan
                    servo.angle = kick_val
                    time.sleep(0.15) # Jeda sangat singkat
                    
                    # 2. Masuk ke target sebenarnya (sekarang momentum sudah ada)
                    servo.angle = target
                    print(f" -> Sampai di {target} (via {kick_val})")

                else:
                    # Gerak Normal (Jarak jauh)
                    print(f" -> Gerak Normal ke {target}")
                    servo.angle = target
                
                # Update posisi
                current_angle = target
                time.sleep(0.5)
                servo.detach() # Tetap detach biar adem

            except ValueError:
                print("Input angka valid.")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        servo.close()

if __name__ == "__main__":
    main()
