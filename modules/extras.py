from gpiozero import PWMOutputDevice, AngularServo
from gpiozero.pins.lgpio import LGPIOFactory
from gpiozero import Device
import time
import threading
from config import PIN_SERVO_PAN, PIN_SERVO_TILT, PIN_BUZZER

# =========================
# SETUP FACTORY
# =========================
try:
    factory = LGPIOFactory()
    Device.pin_factory = factory
except:
    pass 

# =========================
# DATABASE NADA
# =========================
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
}

class ExtraDrivers:
    def __init__(self):
        print(f"[EXTRAS] Init Extras. Buzzer on GPIO {PIN_BUZZER}")
        try:
            self.buzzer = PWMOutputDevice(PIN_BUZZER, initial_value=0, frequency=440)
        except Exception as e:
            self.buzzer = None

        try:
            self.servo_pan = AngularServo(PIN_SERVO_PAN, min_angle=-90, max_angle=90, min_pulse_width=0.0005, max_pulse_width=0.0025)
            self.servo_tilt = AngularServo(PIN_SERVO_TILT, min_angle=-90, max_angle=90, min_pulse_width=0.0005, max_pulse_width=0.0025)
        except:
            self.servo_pan = None
            self.servo_tilt = None

    def set_buzzer(self, state):
        if self.buzzer is None: return
        if state == "on":
            self.buzzer.frequency = 2000 
            self.buzzer.value = 0.5      
        else:
            self.buzzer.off()

    def play_melody(self, song_name):
        """
        Memainkan lagu di Thread, TAPI mengembalikan total durasi (detik)
        agar main.py tahu berapa lama harus menunggu.
        """
        if self.buzzer is None: return 0
        if song_name not in SONGS: return 0

        # Hitung total durasi lagu untuk return value
        note_list, duration_list = SONGS[song_name]
        total_duration = 0
        for d in duration_list:
            total_duration += (d + 0.05) # Ditambah jeda staccato 0.05s

        # Jalankan musik di background
        t = threading.Thread(target=self._play_melody_worker, args=(song_name,))
        t.daemon = True 
        t.start()       
        
        return total_duration

    def _play_melody_worker(self, song_name):
        # ... (Sama seperti sebelumnya) ...
        note_list, duration_list = SONGS[song_name]
        for note_char, duration in zip(note_list, duration_list):
            freq = NOTES.get(note_char, 0)
            if freq > 0:
                self.buzzer.frequency = freq
                self.buzzer.value = 0.5 
            else:
                self.buzzer.off()
            
            time.sleep(duration)
            self.buzzer.off()
            time.sleep(0.05)
        self.buzzer.off()

    def move_servo(self, type, angle):
        angle = max(-90, min(90, angle))
        if type == "pan" and self.servo_pan: self.servo_pan.angle = angle
        elif type == "tilt" and self.servo_tilt: self.servo_tilt.angle = angle