# config.py

# --- NETWORK SETTINGS ---
HOST = "0.0.0.0"
PORT = 8000

# --- CAMERA SETTINGS ---
VIDEO_SOURCE = -1
#VIDEO_SOURCE = "assets/colour.mp4"
FRAME_WIDTH = 640
FRAME_HEIGHT = 480

# config.py - FINAL SAFE MAPPING (Avoiding GPIO 2, 3, 5, 6, 9)

# --- MOTOR SETTINGS ---
# SISI KIRI (Driver 1) - Status: OK
PIN_FL_FWD = 17 
PIN_FL_BWD = 27
PIN_RL_FWD = 22
PIN_RL_BWD = 23

# SISI KANAN (Driver 2) - Menggunakan pin yang terbukti 'lo' di log pinctrl
PIN_FR_FWD = 10
PIN_FR_BWD = 25
PIN_RR_FWD = 16
PIN_RR_BWD = 26   # PINDAH KE 26 (Menghindari GPIO 5 & 9)

# --- EXTRAS (SERVO & BUZZER) ---
PIN_SERVO_PAN = 12   # Tetap (Wajib)
PIN_SERVO_TILT = 13  # Tetap (Wajib)
PIN_BUZZER = 21      # PINDAH KE 21 (Sebelumnya bentrok dengan GPIO 16)

# --- ULTRASONIC (HC-SR04) ---
PIN_HCSR_TRIG = 24   
PIN_HCSR_ECHO = 20   

# --- (BFD-1000 / 5 Channel IR) ---
PIN_LINE_LL = 4
PIN_LINE_L = 14
PIN_LINE_M = 15
PIN_LINE_R = 18
PIN_LINE_RR = 11     

# --- PIN EMERGENCY / OBSTACLE ---
PIN_BFD_NEAR = 19    
PIN_BFD_CLAP = 0     # Gunakan GPIO 0 (ID_SDA)

# --- LED INDIKATOR ---
PIN_LED_R = 7   
PIN_LED_Y = 8   
PIN_LED_G = 1        # Gunakan GPIO 1 (ID_SCL)
