from gpiozero import PWMOutputDevice, AngularServo, LED, Device
from gpiozero.pins.lgpio import LGPIOFactory
import time
import threading
from config import *
from modules.config_loader import cfg_mgr

# --- INIT PIN FACTORY ---
try:
    factory = LGPIOFactory()
    Device.pin_factory = factory
except:
    pass 

# =========================
# DATABASE LAGU
# =========================
NOTES = { "C": 262, "D": 294, "E": 330, "F": 349, "G": 392, "A": 440, "B": 494, "C5": 523, "P": 0 }
SONGS = {
    "merry_christmas": (["G","C","C","D","C","B","A", "A","D","D","E","D","C","B","G", "G","E","C","D","C"],[0.4,0.4,0.4,0.4,0.4,0.4,0.8, 0.4,0.4,0.4,0.4,0.4,0.4,0.8, 0.4,0.4,0.4,0.4,0.8, 1.0])
}

class ExtraDrivers:
    def __init__(self):
        # 1. INIT PINS
        pin_buzzer = cfg_mgr.get_pin("buzzer", "pin", PIN_BUZZER)
        pin_pan = cfg_mgr.get_pin("servo", "pan_pin", PIN_SERVO_PAN)
        pin_tilt = cfg_mgr.get_pin("servo", "tilt_pin", PIN_SERVO_TILT)

        print(f"[EXTRAS] Init. Buzzer:{pin_buzzer}, Pan:{pin_pan}, Tilt:{pin_tilt}")
        
        try:
            self.buzzer = PWMOutputDevice(pin_buzzer, initial_value=0, frequency=440)
        except: self.buzzer = None

        try:
            # KONFIGURASI SERVO (-90 s/d 90)
            self.servo_pan = AngularServo(
                pin_pan, 
                min_angle=-90, max_angle=90, 
                min_pulse_width=0.5/1000, 
                max_pulse_width=2.5/1000
            )
            self.servo_tilt = AngularServo(
                pin_tilt, 
                min_angle=-90, max_angle=90, 
                min_pulse_width=0.5/1000, 
                max_pulse_width=2.5/1000
            )
            
            # MEMORI POSISI TERAKHIR (Penting untuk hitung selisih)
            self.last_pan_angle = 0
            self.last_tilt_angle = 0
            
            # Reset ke Tengah
            self.servo_pan.angle = 0
            self.servo_tilt.angle = 0
            time.sleep(0.4)
            self.detach_servos()
            print("[EXTRAS] Servos Ready (Kick Mode)")
            
        except Exception as e:
            print(f"[EXTRAS] Error Servo: {e}")
            self.servo_pan = None
            self.servo_tilt = None

        # 2. INIT LED
        p_r = cfg_mgr.get_pin("led", "r", PIN_LED_R)
        p_y = cfg_mgr.get_pin("led", "y", PIN_LED_Y)
        p_g = cfg_mgr.get_pin("led", "g", PIN_LED_G)

        try:
            self.led_r = LED(p_r); self.led_y = LED(p_y); self.led_g = LED(p_g)
        except:
            self.led_r = None; self.led_y = None; self.led_g = None

    def close(self):
        if self.buzzer: self.buzzer.close()
        if self.servo_pan: self.servo_pan.close()
        if self.servo_tilt: self.servo_tilt.close()
        if self.led_r: self.led_r.close()

    def detach_servos(self):
        if self.servo_pan: self.servo_pan.detach()
        if self.servo_tilt: self.servo_tilt.detach()

    # ==========================================================
    # LOGIKA KICK / BANTING (+10 / -10)
    # ==========================================================
    def move_servo(self, type, angle):
        """
        Jika perpindahan < 8 derajat, servo 'dibanting' dulu 10 derajat lebih jauh,
        baru kembali ke target asli untuk menembus gesekan (stiction).
        """
        # 1. Clamp Target agar aman (-90 s/d 90)
        angle = int(max(-90, min(90, angle)))
        
        target_servo = None
        last_angle = 0
        
        # 2. Pilih Servo & Ambil Posisi Terakhir
        if type == "pan" and self.servo_pan:
            target_servo = self.servo_pan
            last_angle = self.last_pan_angle
        elif type == "tilt" and self.servo_tilt:
            target_servo = self.servo_tilt
            last_angle = self.last_tilt_angle
            
        if target_servo:
            diff = angle - last_angle
            abs_diff = abs(diff)
            
            # Hanya proses jika ada perubahan posisi
            if abs_diff > 0:
                
                # --- LOGIKA BANTING (KICK) ---
                # Syarat: Pergerakan kecil (di bawah 8 derajat)
                if abs_diff < 9:
                    kick_angle = 0
                    
                    if diff > 0: 
                        # Gerak arah POSITIF (misal 10 ke 15)
                        # Banting dulu ke (15 + 10 = 25)
                        kick_angle = angle + 10
                    else:
                        # Gerak arah NEGATIF (misal 10 ke 5)
                        # Banting dulu ke (5 - 10 = -5)
                        kick_angle = angle - 10
                    
                    # Pastikan bantingan tidak nabrak batas fisik
                    kick_angle = int(max(-90, min(90, kick_angle)))
                    
                    # EKSEKUSI BANTINGAN
                    target_servo.angle = kick_angle
                    time.sleep(0.15) # Beri waktu sebentar untuk 'menghentak'

                # --- GERAK KE TARGET ASLI ---
                # Baik itu habis dibanting atau gerak normal, akhirnya tetap ke sini
                target_servo.angle = angle
                
                # Tunggu sampai posisi stabil
                time.sleep(0.3) 
                
                # Matikan sinyal
                target_servo.detach()
                
                # Simpan Posisi Baru ke Memori
                if type == "pan": self.last_pan_angle = angle
                else: self.last_tilt_angle = angle

    # --- LED & BUZZER ---
    def set_led(self, color, state):
        target = None
        if color == "r": target = self.led_r
        elif color == "y": target = self.led_y
        elif color == "g": target = self.led_g
        if target:
            target.on() if state == "on" else target.off()

    def set_buzzer(self, state):
        if self.buzzer is None: return
        if state == "on":
            self.buzzer.frequency = 2000; self.buzzer.value = 0.5      
        else: self.buzzer.off()

    def play_melody(self, song_name):
        return 0
