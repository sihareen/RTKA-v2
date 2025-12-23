from gpiozero import DistanceSensor, DigitalInputDevice
from gpiozero.pins.lgpio import LGPIOFactory
from gpiozero import Device
# --- BAGIAN INI YANG KEMARIN HILANG ---
from gpiozero.exc import DistanceSensorNoEcho 
import warnings
# --------------------------------------
import config

# Setup Factory untuk Pi 5
try:
    Device.pin_factory = LGPIOFactory()
except:
    pass

class SensorManager:
    def __init__(self):
        print("[SENSORS] Initializing Sensors...")
        
        # 1. SETUP ULTRASONIC (HC-SR04)
        try:
            self.ultrasonic = DistanceSensor(
                echo=config.PIN_HCSR_ECHO, 
                trigger=config.PIN_HCSR_TRIG,
                max_distance=1.0 
            )
        except Exception as e:
            print(f"[SENSORS] Error Ultrasonic: {e}")
            self.ultrasonic = None

        # 2. SETUP LINE SENSORS (BFD-1000)
        try:
            self.line_ll = DigitalInputDevice(config.PIN_LINE_LL)
            self.line_l  = DigitalInputDevice(config.PIN_LINE_L)
            self.line_m  = DigitalInputDevice(config.PIN_LINE_M)
            self.line_r  = DigitalInputDevice(config.PIN_LINE_R)
            self.line_rr = DigitalInputDevice(config.PIN_LINE_RR)
        except Exception as e:
            print(f"[SENSORS] Error Line Sensors: {e}")

    def get_distance(self):
        """Mengembalikan jarak dalam CM dengan Error Handling"""
        if self.ultrasonic:
            try:
                # Bungkam warning 'no echo' agar tidak spam di console
                with warnings.catch_warnings():
                    warnings.simplefilter("error", category=DistanceSensorNoEcho)
                    
                    dist_cm = self.ultrasonic.distance * 100
                    return round(dist_cm, 1)
            except (DistanceSensorNoEcho, Exception):
                # Jika sensor error/no echo/timeout, anggap jalan kosong (999 cm)
                return 999 
        return 999

    def get_line_status(self):
        """
        Return List: [LL, L, M, R, RR]
        Logika: 1 = Garis Hitam, 0 = Lantai Putih
        """
        try:
            return [
                1 if not self.line_ll.value else 0,
                1 if not self.line_l.value else 0,
                1 if not self.line_m.value else 0,
                1 if not self.line_r.value else 0,
                1 if not self.line_rr.value else 0
            ]
        except:
            return [0,0,0,0,0]