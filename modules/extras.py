# modules/extras.py
from config import *
from gpiozero import AngularServo, Buzzer
from gpiozero.pins.lgpio import LGPIOFactory
from time import sleep

class ExtraDrivers:
    def __init__(self):
        print("[INIT] Loading Extras (Servo & Buzzer)...")
        
        try:
            # Setting Servo (Pulse width disesuaikan untuk servo standar SG90/MG90S)
            # min_pulse=0.0005 (0.5ms), max_pulse=0.0025 (2.5ms) standar umum
            self.pan = AngularServo(PIN_SERVO_PAN, min_angle=-90, max_angle=90, 
                                    min_pulse_width=0.0005, max_pulse_width=0.0025)
            
            self.tilt = AngularServo(PIN_SERVO_TILT, min_angle=-90, max_angle=90, 
                                     min_pulse_width=0.0005, max_pulse_width=0.0025)
            
            self.buzzer = Buzzer(PIN_BUZZER)
            
            # Posisi Awal (Tengah)
            self.pan.angle = 0
            self.tilt.angle = 0
            self.buzzer.off()
            
            print("[HARDWARE] Extras Ready.")
            
        except Exception as e:
            print(f"[ERROR] Extras Failed: {e}")
            self.pan = None
            self.tilt = None
            self.buzzer = None

    def move_servo(self, servo_type, angle):
        """
        servo_type: 'pan' atau 'tilt'
        angle: integer antara -90 sampai 90
        """
        # Clamp angle agar tidak merusak gigi servo
        angle = max(-90, min(90, int(angle)))
        
        if servo_type == "pan" and self.pan:
            self.pan.angle = angle
        elif servo_type == "tilt" and self.tilt:
            self.tilt.angle = angle

    def set_buzzer(self, state):
        """
        state: 'on', 'off', atau 'beep'
        """
        if not self.buzzer: return

        if state == "on":
            self.buzzer.on()
        elif state == "off":
            self.buzzer.off()
        elif state == "beep":
            self.buzzer.beep(on_time=0.1, off_time=0.1, n=2, background=True)
