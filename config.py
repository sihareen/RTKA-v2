# config.py 

# --- MOTOR SETTINGS ---
# Berjejer rapi di header Pi sisi KIRI ATAS (Fisik Pin 7, 11, 13, 15)
PIN_FL_FWD = 4
PIN_FL_BWD = 17
PIN_RL_FWD = 27
PIN_RL_BWD = 22

# Berjejer rapi di header Pi sisi KANAN ATAS (Fisik Pin 8, 10, 12, 16)
PIN_FR_FWD = 14
PIN_FR_BWD = 15
PIN_RR_FWD = 18
PIN_RR_BWD = 23

# --- EXTRAS (SERVO & BUZZER) ---
PIN_SERVO_PAN = 12   # Tetap (Pin Fisik 32 - Hardware PWM)
PIN_SERVO_TILT = 13  # Tetap (Pin Fisik 33 - Hardware PWM)
PIN_BUZZER = 8       # Berada di Kanan Tengah (Pin Fisik 24)

# --- ULTRASONIC (HC-SR04) ---
# Berada di Kanan Tengah (Pin Fisik 18 dan 22) - Mudah dirutekan dengan GND di Pin 20
PIN_HCSR_TRIG = 24   
PIN_HCSR_ECHO = 25   

# --- (BFD-1000 / 5 Channel IR) ---
# Berjejer rapi di header Pi sisi KIRI TENGAH-BAWAH (Fisik Pin 19, 21, 23, 29, 31)
PIN_LINE_LL = 10
PIN_LINE_L = 9
PIN_LINE_M = 11
PIN_LINE_R = 5
PIN_LINE_RR = 6      

# --- PIN EMERGENCY / OBSTACLE ---
# Berjejer di Kanan Bawah (Fisik Pin 26 dan 36)
PIN_BFD_NEAR = 7    
PIN_BFD_CLAP = 16    

# --- LED INDIKATOR ---
# Terkumpul di area Bawah (Fisik Pin 35, 37, 38)
PIN_LED_R = 19   
PIN_LED_Y = 26   
PIN_LED_G = 20# config.py - OPTIMIZED FOR KICAD PCB ROUTING

# --- MOTOR SETTINGS ---
# Berjejer rapi di header Pi sisi KIRI ATAS (Fisik Pin 7, 11, 13, 15)
PIN_FL_FWD = 17
PIN_FL_BWD = 4
PIN_RL_FWD = 27
PIN_RL_BWD = 22

# Berjejer rapi di header Pi sisi KANAN ATAS (Fisik Pin 8, 10, 12, 16)
PIN_FR_FWD = 15
PIN_FR_BWD = 14
PIN_RR_FWD = 18
PIN_RR_BWD = 23

# --- EXTRAS (SERVO & BUZZER) ---
PIN_SERVO_PAN = 12   # Tetap (Pin Fisik 32 - Hardware PWM)
PIN_SERVO_TILT = 13  # Tetap (Pin Fisik 33 - Hardware PWM)
PIN_BUZZER = 8       # Berada di Kanan Tengah (Pin Fisik 24)

# --- ULTRASONIC (HC-SR04) ---
# Berada di Kanan Tengah (Pin Fisik 18 dan 22) - Mudah dirutekan dengan GND di Pin 20
PIN_HCSR_TRIG = 24   
PIN_HCSR_ECHO = 25   

# --- (BFD-1000 / 5 Channel IR) ---
# Berjejer rapi di header Pi sisi KIRI TENGAH-BAWAH (Fisik Pin 19, 21, 23, 29, 31)
PIN_LINE_LL = 10
PIN_LINE_L = 9
PIN_LINE_M = 11
PIN_LINE_R = 5
PIN_LINE_RR = 6      

# --- PIN EMERGENCY / OBSTACLE ---
# Berjejer di Kanan Bawah (Fisik Pin 26 dan 36)
PIN_BFD_NEAR = 7    
PIN_BFD_CLAP = 16    

# --- LED INDIKATOR ---
# Terkumpul di area Bawah (Fisik Pin 35, 37, 38)
PIN_LED_R = 19   
PIN_LED_Y = 26   
PIN_LED_G = 20
