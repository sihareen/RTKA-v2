# config.py

# --- NETWORK SETTINGS ---
HOST = "0.0.0.0"
PORT = 8000

# --- CAMERA SETTINGS ---
# Ganti URL ini dengan path file lokal atau '0' untuk kamera fisik nanti
VIDEO_SOURCE = 0
#VIDEO_SOURCE = "assets/colour.mp4"
FRAME_WIDTH = 640
FRAME_HEIGHT = 480

# --- MOTOR SETTINGS (GPIO BCM) ---
# Pin ini belum dipakai di mode simulasi, tapi disiapkan untuk nanti
PIN_MOTOR_L_FWD = 17
PIN_MOTOR_L_BWD = 27
PIN_MOTOR_R_FWD = 22
PIN_MOTOR_R_BWD = 23
