# config.py

# --- NETWORK SETTINGS ---
HOST = "0.0.0.0"
PORT = 8000

# --- CAMERA SETTINGS ---
# Ganti URL ini dengan path file lokal atau '0' untuk kamera fisik nanti
VIDEO_SOURCE = -1
#VIDEO_SOURCE = "assets/colour.mp4"
FRAME_WIDTH = 640
FRAME_HEIGHT = 480

# --- MOTOR SETTINGS (FINAL CONFIGURATION) ---

# SISI KIRI (Driver 1) - GPIO 17, 27, 22, 23
PIN_FL_FWD = 17 
PIN_FL_BWD = 27
PIN_RL_FWD = 22
PIN_RL_BWD = 23

# SISI KANAN (Driver 2) - GPIO 24, 25, 5, 6
PIN_FR_FWD = 24
PIN_FR_BWD = 25
PIN_RR_FWD = 5
PIN_RR_BWD = 6
