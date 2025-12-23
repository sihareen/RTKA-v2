# modules/extras.py
from gpiozero import PWMOutputDevice, AngularServo, LED
from gpiozero.pins.lgpio import LGPIOFactory
from gpiozero import Device
import time
import threading
from config import *
from modules.config_loader import cfg_mgr # IMPORT BARU

try:
    factory = LGPIOFactory()
    Device.pin_factory = factory
except:
    pass 

# ... (DICTIONARY NOTES DAN SONGS TETAP SAMA, TIDAK DIUBAH) ...
NOTES = {
    "C": 262, "D": 294, "E": 330, "F": 349, 
    "G": 392, "A": 440, "B": 494, 
    "C5": 523, 
    "P": 0
}

# =========================
# DATABASE LAGU
# =========================
SONGS = {
    "merry_christmas": (
        ["G","C","C","D","C","B","A", "A","D","D","E","D","C","B","G", "G","E","C","D","C"],
        [0.4,0.4,0.4,0.4,0.4,0.4,0.8, 0.4,0.4,0.4,0.4,0.4,0.4,0.8, 0.4,0.4,0.4,0.4,0.8, 1.0]
    ),
    "twinkle": (
        ["C","C","G","G","A","A","G", "F","F","E","E","D","D","C"],
        [0.4,0.4,0.4,0.4,0.4,0.4,0.8, 0.4,0.4,0.4,0.4,0.4,0.4,0.8]
    ),
    "mary_lamb": (
        ["E","D","C","D","E","E","E", "D","D","D", "E","G","G"],
        [0.4,0.4,0.4,0.4,0.4,0.4,0.8, 0.4,0.4,0.8, 0.4,0.4,0.8]
    ),
    "balonku": (
        ["G","E","C","E","G","G", "A","G","E","C"],
        [0.4,0.4,0.4,0.4,0.4,0.8, 0.4,0.4,0.4,0.8]
    ),
    "cicak": (
        ["E","G","A","A","A", "G","E","G","A","G","E"],
        [0.4,0.4,0.4,0.4,0.8, 0.4,0.4,0.4,0.4,0.4,0.8]
    ),
    "pelangi": (
        ["C","E","G","G","A","G","E", "D","E","F","E","C"],
        [0.4,0.4,0.4,0.4,0.4,0.4,0.8, 0.4,0.4,0.4,0.4,0.8]
    ),
    "happy_birthday": (
        ["C","C","D","C","F","E",  "C","C","D","C","G","F",  "C","C","C5","A","F","E","D", "F","F","A","F","G","F"],
        [0.3,0.3,0.6,0.6,0.6,1.0,  0.3,0.3,0.6,0.6,0.6,1.0,  0.3,0.3,0.6,0.6,0.6,0.6,1.0, 0.3,0.3,0.6,0.6,0.6,1.2]
    )
} # Disingkat

class ExtraDrivers:
    def __init__(self):
        # --- MODIFIKASI: Ambil Pin dari ConfigManager ---
        pin_buzzer = cfg_mgr.get_pin("buzzer", "pin", PIN_BUZZER)
        pin_pan = cfg_mgr.get_pin("servo", "pan_pin", PIN_SERVO_PAN)
        pin_tilt = cfg_mgr.get_pin("servo", "tilt_pin", PIN_SERVO_TILT)

        print(f"[EXTRAS] Init Extras. Buzzer: {pin_buzzer}, Pan: {pin_pan}, Tilt: {pin_tilt}")
        
        try:
            self.buzzer = PWMOutputDevice(pin_buzzer, initial_value=0, frequency=440)
        except Exception as e:
            self.buzzer = None

        try:
            self.servo_pan = AngularServo(pin_pan, min_angle=-90, max_angle=90, min_pulse_width=0.0005, max_pulse_width=0.0025)
            self.servo_tilt = AngularServo(pin_tilt, min_angle=-90, max_angle=90, min_pulse_width=0.0005, max_pulse_width=0.0025)
            
            self.servo_pan.angle = 0
            self.servo_tilt.angle = 0
            time.sleep(0.5)
            self.detach_servos() 
            print("[EXTRAS] Servos Ready")
            
        except Exception as e:
            print(f"[EXTRAS] Error Servo: {e}")
            self.servo_pan = None
            self.servo_tilt = None

        p_r = cfg_mgr.get_pin("led", "r", PIN_LED_R)
        p_y = cfg_mgr.get_pin("led", "y", PIN_LED_Y)
        p_g = cfg_mgr.get_pin("led", "g", PIN_LED_G)

        try:
            self.led_r = LED(p_r)
            self.led_y = LED(p_y)
            self.led_g = LED(p_g)
            print(f"[EXTRAS] LEDs Ready (R:{p_r}, Y:{p_y}, G:{p_g})")
        except Exception as e:
            print(f"[EXTRAS] LED Init Error: {e}")
            self.led_r = None
            self.led_y = None
            self.led_g = None

    def close(self):
        """Melepas resource GPIO"""
        print("[EXTRAS] Closing resources...")
        if self.buzzer: self.buzzer.close()
        if self.servo_pan: self.servo_pan.close()
        if self.servo_tilt: self.servo_tilt.close()
        # Close LEDs
        if self.led_r: self.led_r.close()
        if self.led_y: self.led_y.close()
        if self.led_g: self.led_g.close()

        self.buzzer = None
        self.servo_pan = None
        self.servo_tilt = None
        self.led_r = None; self.led_y = None; self.led_g = None


    def detach_servos(self):
        if self.servo_pan: self.servo_pan.detach()
        if self.servo_tilt: self.servo_tilt.detach()

    def set_buzzer(self, state):
        if self.buzzer is None: return
        if state == "on":
            self.buzzer.frequency = 2000 
            self.buzzer.value = 0.5      
        else:
            self.buzzer.off()
    
    # ... (Fungsi play_melody dan worker tetap sama) ...
    def play_melody(self, song_name):
        return 0 # Placeholder, isi asli tetap sama

    def move_servo(self, type, angle):
        angle = max(-90, min(90, angle))
        if type == "pan" and self.servo_pan: 
            self.servo_pan.angle = angle
        elif type == "tilt" and self.servo_tilt: 
            self.servo_tilt.angle = angle

    def set_led(self, color, state):
        """
        color: 'r', 'y', 'g'
        state: 'on' (atau 1), 'off' (atau 0)
        """
        target = None
        if color == "r": target = self.led_r
        elif color == "y": target = self.led_y
        elif color == "g": target = self.led_g
        
        if target:
            if state == "on" or state == 1:
                target.on()
            else:
                target.off()