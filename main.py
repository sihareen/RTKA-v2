#!/home/pi/RTKAv2/venv/bin/python3
import os
import sys
import uvicorn
import json
import asyncio
import math
import time 
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from config import HOST, PORT
from modules.motor import MotorDriver
from modules.camera import VideoStreamer
from modules.extras import ExtraDrivers
from modules.sensors import SensorManager
from modules.config_loader import cfg_mgr

os.environ["OPENCV_LOG_LEVEL"] = "FATAL"
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

robot_motor = MotorDriver(simulation=False) 
robot_cam = VideoStreamer()
robot_extras = ExtraDrivers()
robot_sensors = SensorManager()
CURRENT_CONTROLLER = "none"

# --- HELPER: Mengatur Mode & Kirim Feedback ---
async def handle_ai_switch(websocket, payload):
    if payload.get("cmd") == "set_ai_mode":
        mode = payload.get("mode", "off")
        robot_cam.ai.set_mode(mode) # Ganti mode di ai.py
        # Feedback ke Web
        await websocket.send_text(json.dumps({"status": "active", "mode": mode}))
        return True
    return False


def reload_hardware():
    print("[SYSTEM] Reloading Hardware...")
    global robot_motor, robot_extras, robot_sensors
    
    # 1. Matikan Hardware Lama
    if 'robot_motor' in globals(): robot_motor.close()
    if 'robot_extras' in globals(): robot_extras.close()
    if 'robot_sensors' in globals(): robot_sensors.close()
    
    # 2. Hidupkan Hardware Baru (Akan otomatis baca status cfg_mgr)
    try:
        robot_motor = MotorDriver(simulation=False)
        robot_extras = ExtraDrivers()
        robot_sensors = SensorManager()
        print(f"[SYSTEM] Hardware Reloaded. User Mode: {cfg_mgr.use_user_config}")
    except Exception as e:
        print(f"[SYSTEM] Hardware Init Failed: {e}")

# WEBSOCKET CONFIG SWITCHER
@app.websocket("/ws/configSwitch")
async def ws_config_switch(websocket: WebSocket):
    await websocket.accept()
    print("[WS] Config Switcher Connected")
    
    try:
        while True:
            data = await websocket.receive_text()
            payload = json.loads(data)
            cmd = payload.get("cmd")
            
            # CASE A: SIMPAN CONFIG DARI USER
            if cmd == "save_config":
                new_config = payload.get("config")
                # Format Config harus sesuai kategori (motor, servo, dll)
                cfg_mgr.save_user_config(new_config)
                await websocket.send_text(json.dumps({"status": "saved", "msg": "Config saved to JSON"}))
                
            # CASE B: GANTI MODE (DEFAULT <-> USER)
            elif cmd == "set_mode":
                mode = payload.get("mode") # "default" atau "user"
                
                if mode == "user":
                    cfg_mgr.use_user_config = True
                    msg = "Switched to USER Config"
                else:
                    cfg_mgr.use_user_config = False
                    msg = "Switched to DEFAULT Config"
                
                # RESTART HARDWARE SEKARANG!
                reload_hardware()
                
                await websocket.send_text(json.dumps({
                    "status": "switched", 
                    "mode": mode,
                    "msg": msg
                }))
                
    except Exception as e:
        print(f"[CFG] Error: {e}")


# 1. REMOTE CONTROL
@app.websocket("/ws/control")
async def ws_control(websocket: WebSocket):
    global CURRENT_CONTROLLER
    await websocket.accept()
    CURRENT_CONTROLLER = "manual"
    robot_cam.ai.set_mode("off")
    print("[WS] MANUAL Connected - LOGGING ACTIVE")
    
    try:
        while True:
            data = await websocket.receive_text()
            payload = json.loads(data)
            cmd = payload.get("cmd")
            
            if CURRENT_CONTROLLER == "manual":
                # --- MOTOR ---
                if cmd == "move":
                    y_val = float(payload.get("y", 0))
                    x_val = float(payload.get("x", 0))
                    speed_limit = float(payload.get("speed", 100))
                    print(f"[MANUAL] Y: {y_val:.2f} | X: {x_val:.2f} | Limit: {speed_limit}%")
                    robot_motor.move(y_val, x_val, speed_limit)
                
                # --- SERVO ---
                elif cmd == "servo": 
                    robot_extras.move_servo(payload.get("type"), payload.get("angle",0))
                
                # --- BUZZER ---
                elif cmd == "buzzer": 
                    robot_extras.set_buzzer(payload.get("state", "off"))
                
                # --- LED CONTROL (BARU) ---
                elif cmd == "led":
                    # Format Payload: {"cmd": "led", "color": "r", "state": "on"}
                    color = payload.get("color") # "r", "g", "y"
                    state = payload.get("state") # "on", "off"
                    robot_extras.set_led(color, state)
                    
                # --- STOP ---
                elif cmd == "stop": 
                    print("[MANUAL] STOP")
                    robot_motor.stop()
    except: pass
    finally: robot_motor.stop()

# 2. AUTO PILOT (DIGITAL SWITCH)
@app.websocket("/ws/autoPilot")
async def ws_autopilot(websocket: WebSocket):
    global CURRENT_CONTROLLER
    await websocket.accept()
    CURRENT_CONTROLLER = "autopilot"
    robot_cam.ai.set_mode("off") # Standby Awal
    print("[WS] AUTO PILOT Connected")

    try:
        while True:
            try:
                data = await asyncio.wait_for(websocket.receive_text(), timeout=0.05)
                payload = json.loads(data)
                
                # Logic Switch ON/OFF
                if payload.get("cmd") == "set_ai_mode":
                    mode = payload.get("mode")
                    
                    if mode == "start":
                        robot_cam.ai.set_mode("auto_pilot")
                        await websocket.send_text(json.dumps({"status": "active", "mode": "auto_pilot"}))
                    elif mode == "stop":
                        robot_cam.ai.set_mode("off")
                        robot_motor.stop()
                        await websocket.send_text(json.dumps({"status": "stopped"}))
                        
            except asyncio.TimeoutError: pass

            # Logic Drive
            if CURRENT_CONTROLLER == "autopilot" and robot_cam.ai.mode == "auto_pilot" and robot_cam.ai.object_found:
                error = robot_cam.ai.track_error_x
                throttle = 0.35 - (abs(error) * 0.15)
                steering = error * 0.8
                robot_motor.move(throttle, steering, speed_limit=50)
            else:
                robot_motor.stop()
                
            await asyncio.sleep(0.01)
    except: pass
    finally: 
        robot_motor.stop()
        robot_cam.ai.set_mode("off")


# 3. TARGET TRACKING (VISUALIZATON MODE)
@app.websocket("/ws/tracking")
async def ws_tracking(websocket: WebSocket):
    global CURRENT_CONTROLLER
    await websocket.accept()
    CURRENT_CONTROLLER = "tracking"
    
    robot_cam.ai.set_mode("off") 
    print("[WS] TRACKING Connected")
    
    # SETUP AWAL
    pan_pos = 0.0
    tilt_pos = 0.0
    robot_extras.move_servo("pan", 0)
    robot_extras.move_servo("tilt", 0)

    prev_error_x = 0.0
    prev_error_y = 0.0

    # --- CONFIG DEADZONE (20%) ---
    ZONA_X = 0.20
    ZONA_Y = 0.20
    
    # AKTIFKAN GAMBAR KOTAK DI KAMERA (KIRIM KE AI.PY)
    robot_cam.ai.set_deadzone(True, ZONA_X, ZONA_Y)

    await websocket.send_text(json.dumps({"status": "active", "mode": "standby"}))

    try:
        while True:
            # 1. TERIMA INPUT
            try:
                data = await asyncio.wait_for(websocket.receive_text(), timeout=0.05)
                payload = json.loads(data)
                
                if payload.get("cmd") == "set_ai_mode":
                    req = payload.get("mode") 
                    if req == "none":
                        robot_cam.ai.set_mode("off")
                        # Reset
                        pan_pos = 0.0
                        tilt_pos = 0.0
                        prev_error_x = 0.0
                        prev_error_y = 0.0
                        robot_extras.move_servo("pan", 0)
                        robot_extras.move_servo("tilt", 0)
                        await asyncio.sleep(0.5)
                        robot_extras.detach_servos()
                        
                        # Matikan Visualisasi Deadzone saat Standby
                        # (Opsional: Kalau mau tetap tampil, hapus baris ini)
                        # robot_cam.ai.set_deadzone(False) 
                        
                        await websocket.send_text(json.dumps({"status": "active", "mode": "standby"}))
                        
                    elif req == "face_track":
                        # Pastikan visualisasi nyala
                        robot_cam.ai.set_deadzone(True, ZONA_X, ZONA_Y)
                        robot_cam.ai.set_mode("face_detection")
                        await websocket.send_text(json.dumps({"status": "active", "mode": "face_track"}))
                        
                    elif req == "color_track":
                        robot_cam.ai.set_deadzone(True, ZONA_X, ZONA_Y)
                        color = payload.get("color", "red") 
                        robot_cam.ai.set_color_target(color)
                        robot_cam.ai.set_mode("color_detection")
                        await websocket.send_text(json.dumps({"status": "active", "mode": f"track_{color}"}))     
            except asyncio.TimeoutError: pass

            # 2. LOGIKA TRACKING
            if CURRENT_CONTROLLER == "tracking" and robot_cam.ai.mode != "off" and robot_cam.ai.object_found:
                
                raw_error_x = robot_cam.ai.track_error_x 
                raw_error_y = getattr(robot_cam.ai, 'track_error_y', 0.0)

                # Smoothing
                alpha = 0.2
                smooth_x = (raw_error_x * alpha) + (prev_error_x * (1.0 - alpha))
                smooth_y = (raw_error_y * alpha) + (prev_error_y * (1.0 - alpha))
                prev_error_x = smooth_x
                prev_error_y = smooth_y

                # LOGIKA DEADZONE (Visualisasi sesuai dengan yang digambar)
                if abs(smooth_x) < ZONA_X: smooth_x = 0
                if abs(smooth_y) < ZONA_Y: smooth_y = 0

                if smooth_x != 0 or smooth_y != 0:
                    gain = 0.5 
                    delta_pan = smooth_x * gain
                    delta_tilt = smooth_y * gain
                    
                    MAX_STEP = 1.0 
                    delta_pan = max(-MAX_STEP, min(MAX_STEP, delta_pan))
                    delta_tilt = max(-MAX_STEP, min(MAX_STEP, delta_tilt))

                    pan_pos -= delta_pan 
                    tilt_pos += delta_tilt

                    pan_pos = max(-90, min(90, pan_pos))
                    tilt_pos = max(-90, min(90, tilt_pos))
                    
                    robot_extras.move_servo("pan", int(pan_pos))
                    robot_extras.move_servo("tilt", int(tilt_pos))
                else:
                    # Trik Hening (Aggressive Detach)
                    robot_extras.detach_servos()

            await asyncio.sleep(0.04) 

    except Exception as e:
        print(f"[TRACK] Error: {e}")
    finally:
        # Matikan visualisasi deadzone saat disconnect
        robot_cam.ai.set_deadzone(False)
        robot_extras.detach_servos()


# 4. RECOGNITION CONTROL (GESTURE & COLOR FOLLOW)
@app.websocket("/ws/recognitionControl")
async def ws_recognition(websocket: WebSocket):
    global CURRENT_CONTROLLER
    await websocket.accept()
    CURRENT_CONTROLLER = "recognition"
    robot_cam.ai.set_mode("off") 
    print("[WS] RECOGNITION Connected (Standby)")
    
    lost_counter = 0

    try:
        while True:
            try:
                data = await asyncio.wait_for(websocket.receive_text(), timeout=0.05)
                payload = json.loads(data)
                
                if payload.get("cmd") == "set_ai_mode":
                    req = payload.get("mode")
                    
                    if req == "gesture_cmd":
                        robot_cam.ai.set_mode("gesture_recognition")
                        await websocket.send_text(json.dumps({"status": "active", "mode": "gesture_control"}))
                    
                    elif req == "color_follow":
                        # --- BACA PILIHAN WARNA USER ---
                        target_color = payload.get("color", "none") # Default red jika kosong
                        robot_cam.ai.set_color_target(target_color)
                        robot_cam.ai.set_mode("color_detection")
                        if target_color == "none":
                            await websocket.send_text(json.dumps({"status": "active", "mode": "waiting_color"}))
                        else:
                            await websocket.send_text(json.dumps({"status": "active", "mode": f"follow_{target_color}"}))
            except asyncio.TimeoutError: pass
            
            if CURRENT_CONTROLLER == "recognition":
                
                # A. LOGIKA GESTURE
                if robot_cam.ai.mode == "gesture_recognition":
                    fingers = robot_cam.ai.gesture_data 
                    if fingers is not None:
                        if fingers == 1: robot_motor.move(0.3, 0.0) 
                        elif fingers == 2: robot_motor.move(-0.3, 0.0)
                        elif fingers == 3: robot_motor.move(0.0, -0.4)
                        elif fingers == 4: robot_motor.move(0.0, 0.4)
                        elif fingers >= 5: robot_motor.stop()
                    else: robot_motor.stop()

                # B. LOGIKA COLOR FOLLOW + FILTER WARNA
                elif robot_cam.ai.mode == "color_detection":
                    if robot_cam.ai.object_found:
                        lost_counter = 0 
                        robot_extras.move_servo("pan", 0)
                        
                        error_x = robot_cam.ai.track_error_x
                        area_size = robot_cam.ai.track_area
                        TARGET_SIZE = 0.15 
                        
                        throttle = 0.0
                        if area_size < TARGET_SIZE: throttle = 0.35
                        elif area_size > (TARGET_SIZE + 0.1): throttle = -0.30
                        
                        steering = error_x * 0.6
                        robot_motor.move(throttle, steering)
                    else:
                        # SEARCHING BEHAVIOR
                        lost_counter += 1
                        robot_motor.stop()
                        if lost_counter < 40:
                            scan_angle = int(math.sin(lost_counter * 0.2) * 60)
                            robot_extras.move_servo("pan", scan_angle)
                        else:
                            robot_extras.move_servo("pan", 0)
                else:
                    robot_motor.stop()

            await asyncio.sleep(0.1)

    except Exception as e:
        print(f"[RECOG] Error: {e}")
    finally:
        robot_motor.stop()
        robot_extras.move_servo("pan", 0)
        robot_cam.ai.set_mode("off")

# 5. OBJECT DETECTION (STANDBY FIRST)
@app.websocket("/ws/objectDetection")
async def ws_obj_detection(websocket: WebSocket):
    global CURRENT_CONTROLLER
    await websocket.accept()
    CURRENT_CONTROLLER = "detection"
    
    robot_cam.ai.set_mode("off") 
    print("[WS] DETECTION HUB: Connected")
    
    try:
        while True:
            data = await websocket.receive_text()
            payload = json.loads(data)
            
            cmd = payload.get("cmd")
            if cmd == "set_ai_mode":
                req_mode = payload.get("mode")
                
                # --- KHUSUS TOMBOL COLOR DI MODE INI ---
                if req_mode == "color_detection":
                    # Set target ke "ALL" (Rainbow Mode)
                    robot_cam.ai.set_color_target("all")
                    robot_cam.ai.set_mode("color_detection")
                    await websocket.send_text(json.dumps({"status": "active", "mode": "detect_all_colors"}))
                
                # Modus deteksi lainnya (Face, Object, Gesture) normal
                else:
                    robot_cam.ai.set_mode(req_mode)
                    await websocket.send_text(json.dumps({"status": "active", "mode": req_mode}))
            
    except Exception as e:
        print(f"[WS] Error: {e}")
    finally:
        robot_cam.ai.set_mode("off")

# 6. QR SCANNER (DIGITAL SWITCH)
@app.websocket("/ws/qr")
async def ws_qr(websocket: WebSocket):
    global CURRENT_CONTROLLER
    await websocket.accept()
    CURRENT_CONTROLLER = "qr"
    
    robot_cam.ai.set_mode("off") 
    print("[WS] QR Connected")
    
    # Kita hapus last_scan_time yang statis, kita pakai logika blocking di bawah
    
    try:
        while True:
            # 1. Terima Perintah Switch ON/OFF dari UI
            try:
                data = await asyncio.wait_for(websocket.receive_text(), timeout=0.05)
                payload = json.loads(data)
                if payload.get("cmd") == "set_ai_mode":
                    mode = payload.get("mode")
                    if mode == "start":
                        robot_cam.ai.set_mode("qr_recognition")
                        await websocket.send_text(json.dumps({"status": "active", "mode": "qr_scanner"}))
                    elif mode == "stop":
                        robot_cam.ai.set_mode("off")
                        await websocket.send_text(json.dumps({"status": "stopped"}))
            except asyncio.TimeoutError: pass
            
            # 2. Logika Utama QR
            if CURRENT_CONTROLLER == "qr" and robot_cam.ai.mode == "qr_recognition":
                current_qr = robot_cam.ai.qr_data
                
                # Jika ada QR terdeteksi, kita proses lalu KITA BLOCKING (WAIT)
                if current_qr is not None:
                    
                    scan_text = current_qr.upper().strip()
                    print(f"[QR] EKSEKUSI: {scan_text}")
                    
                    # Kirim info ke UI
                    await websocket.send_text(json.dumps({"status": "active", "mode": f"CMD: {scan_text}"}))
                    
                    # Bip tanda mulai
                    robot_extras.set_buzzer("on")
                    await asyncio.sleep(0.1)
                    robot_extras.set_buzzer("off")
                    
                    # --- A. LOGIKA MUSIK (BLOCKING) ---
                    # Variable duration akan menampung lama lagu
                    duration = 0 
                    
                    if "MERRY" in scan_text:
                        duration = robot_extras.play_melody("merry_christmas")
                    elif "TWINKLE" in scan_text:
                        duration = robot_extras.play_melody("twinkle")
                    elif "MARY" in scan_text:
                        duration = robot_extras.play_melody("mary_lamb")
                    elif "BALONKU" in scan_text:
                        duration = robot_extras.play_melody("balonku")
                    elif "CICAK" in scan_text:
                        duration = robot_extras.play_melody("cicak")
                    elif "PELANGI" in scan_text:
                        duration = robot_extras.play_melody("pelangi")
                    elif "BIRTHDAY" in scan_text:
                        duration = robot_extras.play_melody("happy_birthday")

                    # Jika terdeteksi lagu, robot akan "Tidur" (ignore QR lain) selama lagu main
                    if duration > 0:
                        print(f"[QR] Lagu main selama {duration:.1f} detik. Mengabaikan QR lain...")
                        await asyncio.sleep(duration + 1.0) # Tambah 1 detik jeda
                        print("[QR] Siap menerima perintah baru.")
                        # Kosongkan data QR lama biar tidak loop instant jika kartu sudah diangkat
                        robot_cam.ai.qr_data = None 
                        continue # Lanjut ke loop berikutnya

                    # --- B. LOGIKA GERAKAN (BLOCKING) ---
                    
                    if "KOTAK" in scan_text:
                        # Gerakan Kotak
                        for _ in range(4):
                            robot_motor.move(0.5, 0.0) # Maju
                            await asyncio.sleep(1.0)
                            robot_motor.stop()
                            await asyncio.sleep(0.2)
                            robot_motor.move(0.0, 0.6) # Putar Kanan
                            await asyncio.sleep(0.6) 
                            robot_motor.stop()
                            await asyncio.sleep(0.2)
                            
                    elif "PUTAR" in scan_text:
                        # Putar 360
                        robot_motor.move(0.0, 0.7) 
                        await asyncio.sleep(2.5)   
                        robot_motor.stop()

                    elif "MAJU" in scan_text:
                        # Maju 2 Detik
                        robot_motor.move(0.5, 0.0)
                        await asyncio.sleep(2.0)
                        robot_motor.stop()
                    
                    elif "MUNDUR" in scan_text:
                        # Mundur 2 Detik
                        robot_motor.move(-0.5, 0.0)
                        await asyncio.sleep(2.0)
                        robot_motor.stop()

                    # Reset data QR setelah aksi gerakan selesai
                    # Agar tidak membaca frame yg sama berulang kali secara ultra-cepat
                    robot_cam.ai.qr_data = None
                    
                    # Beri jeda sedikit sebelum baca lagi
                    await asyncio.sleep(1.0)

            await asyncio.sleep(0.1)
            
    except Exception as e:
        print(f"[QR] Error: {e}")
    finally:
        robot_motor.stop()
        robot_extras.set_buzzer("off")
        robot_cam.ai.set_mode("off")

        
#  AVOID & FOLLOW (SAFETY FIRST + FILTERED SENSOR + STATE MACHINE)
@app.websocket("/ws/avoid")
async def ws_avoid(websocket: WebSocket):
    global CURRENT_CONTROLLER
    await websocket.accept()
    CURRENT_CONTROLLER = "avoid"
    
    robot_cam.ai.set_mode("off")
    print("[WS] AVOID Connected - SAFETY MODE")
    
    current_mode = "standby"
    active_mask = [1, 1, 1, 1, 1]
    
    # --- SHARED DATA ---
    # Kita set nilai awal 999 biar robot gak panik pas baru nyala
    sensor_data = {"dist": 100.0} 
    
    # --- TUNING PARAMETERS ---
    # Speed diturunkan untuk safety saat testing
    SPEED_MAJU    = 0.05   # Sangat pelan (Safety First)
    SPEED_MUNDUR  = -0.50  
    SPEED_PUTAR   = 0.50   
    
    JARAK_STOP_DARURAT = 10 # cm (Haram dilewati)
    JARAK_TRIGGER      = 30 # cm (Mulai mikir untuk menghindar)
    
    DURASI_MUNDUR   = 1.0
    DURASI_PUTAR_90 = 0.7
    DURASI_STABIL   = 0.5 

    # State Machine
    state = "IDLE"
    state_ts = time.monotonic()
    
    # --- BACKGROUND TASK: SENSOR FILTERING (ANTI SPIKE) ---
    async def sensor_loop():
        # Alpha: 0.1 (Sangat Smooth/Lambat) s/d 1.0 (Tanpa Filter/Cepat)
        # 0.4 artinya: 60% data lama, 40% data baru (Cukup smooth tapi responsif)
        ALPHA = 0.4 
        
        while True:
            try:
                raw_dist = robot_sensors.get_distance()
                
                # FILTER 1: Buang Noise Ekstrim (< 2cm atau > 400cm biasanya error)
                if 2 < raw_dist < 400:
                    
                    # FILTER 2: Low-Pass Filter (Exponential Moving Average)
                    prev_dist = sensor_data["dist"]
                    filtered_dist = (prev_dist * (1 - ALPHA)) + (raw_dist * ALPHA)
                    
                    sensor_data["dist"] = filtered_dist
                    
                    # Update HUD Kamera (Biar visualnya enak dilihat, gak loncat2)
                    robot_cam.ai.update_distance(filtered_dist)
                
                await asyncio.sleep(0.04) # 25Hz Refresh Rate
            except: pass

    sensor_task = asyncio.create_task(sensor_loop())

    try:
        while True:
            # 1. INPUT HANDLING (NON-BLOCKING)
            try:
                data = await asyncio.wait_for(websocket.receive_text(), timeout=0.01)
                payload = json.loads(data)
                cmd = payload.get("cmd")
                
                if cmd == "set_ai_mode":
                    mode = payload.get("mode") 
                    current_mode = mode
                    state = "IDLE"
                    robot_motor.stop()
                    
                    msg = "MODE: SAFETY AVOID" if mode == "avoid_hcsr" else "MODE: HYBRID"
                    if mode == "standby": msg = "MODE: STANDBY"
                    
                    # Ambil config hybrid jika ada
                    if mode == "avoid_hybrid":
                        cfg = payload.get("config", {})
                        active_mask = [1 if cfg.get(k, True) else 0 for k in ["ll","l","m","r","rr"]]

                    await websocket.send_text(json.dumps({"status": "active", "mode": msg}))
            except asyncio.TimeoutError: pass

            # 2. LOGIKA UTAMA
            if CURRENT_CONTROLLER == "avoid" and current_mode != "standby":
                
                # Ambil data ter-filter
                distance = sensor_data["dist"]
                now = time.monotonic()
                elapsed = now - state_ts

                # ===============================================
                # 🔥 LAYER 1: HARD EMERGENCY STOP (ABSOLUTE PRIORITY)
                # ===============================================
                # Ini memotong semua logika State Machine di bawah.
                # Jika jarak < 10cm, MATIKAN MOTOR DETIK ITU JUGA.
                if distance < JARAK_STOP_DARURAT:
                    if state != "EMERGENCY": # Print cuma sekali biar gak spam log
                        print(f"[CRITICAL] EMERGENCY STOP! Jarak: {distance:.1f}cm")
                    
                    robot_motor.stop()
                    state = "EMERGENCY" # State khusus biar gak ngapa-ngapain
                    state_ts = now
                    
                    await asyncio.sleep(0.05) # Yield sebentar
                    continue # SKIP KODE DI BAWAHNYA, ULANG LOOP DARI ATAS
                
                # Jika sudah lolos emergency (jarak > 10cm), tapi status masih EMERGENCY
                # Kembalikan ke IDLE biar State Machine jalan lagi
                if state == "EMERGENCY" and distance > (JARAK_STOP_DARURAT + 5):
                    print("[SAFE] Jarak aman kembali. Resume IDLE.")
                    state = "IDLE"
                    state_ts = now

                # ===============================================
                # 🧠 LAYER 2: STATE MACHINE
                # ===============================================
                
                # --- STATE: IDLE (Maju Waspada) ---
                if state == "IDLE":
                    # Cek Pemicu Menghindar (Trigger)
                    if distance < JARAK_TRIGGER:
                        print(f"[SM] Halangan {distance:.1f}cm -> STOP & MUNDUR")
                        robot_motor.stop()
                        state = "PRE_BACKING"
                        state_ts = now
                    
                    else:
                        # LOGIKA MAJU (Continuous Check)
                        # Kita pastikan perintah maju hanya dikirim kalau aman
                        if current_mode == "avoid_hcsr":
                            robot_motor.move(SPEED_MAJU, 0.0)
                            
                        elif current_mode == "avoid_hybrid":
                            # Hybrid Logic
                            raw_lines = robot_sensors.get_line_status()
                            lines = [r & m for r, m in zip(raw_lines, active_mask)]
                            # ... (Logika Line Follower Copy Paste disini) ...
                            # Agar ringkas, saya pakai logika simple:
                            if sum(lines) == 0: robot_motor.stop() # Lost line
                            elif lines[2]: robot_motor.move(0.15, 0.0) # Tengah
                            elif lines[1]: robot_motor.move(0.12, -0.3) # Kiri
                            elif lines[3]: robot_motor.move(0.12, 0.3) # Kanan
                            # ... Tambahkan logika lengkap line follower Anda di sini

                # --- STATE: PRE BACKING (Jeda sebelum mundur) ---
                elif state == "PRE_BACKING":
                    robot_motor.stop()
                    if elapsed > 0.2:
                        state = "BACKING"
                        state_ts = now

                # --- STATE: BACKING (Mundur tanpa nabrak) ---
                elif state == "BACKING":
                    robot_motor.move(SPEED_MUNDUR, 0.0)
                    if elapsed > DURASI_MUNDUR:
                        robot_motor.stop()
                        state = "PRE_TURN_LEFT"
                        state_ts = now

                # --- STATE: PRE TURN LEFT ---
                elif state == "PRE_TURN_LEFT":
                    if elapsed > 0.2:
                        state = "TURN_LEFT"
                        state_ts = now

                # --- STATE: TURN LEFT ---
                elif state == "TURN_LEFT":
                    robot_motor.move(0.0, -SPEED_PUTAR)
                    if elapsed > DURASI_PUTAR_90:
                        robot_motor.stop()
                        state = "CHECK_LEFT"
                        state_ts = now

                # --- STATE: CHECK LEFT ---
                elif state == "CHECK_LEFT":
                    robot_motor.stop()
                    if elapsed > DURASI_STABIL:
                        # Logika Keputusan
                        if distance > (JARAK_TRIGGER * 1.5):
                            print("[SM] Kiri Aman -> RECOVERY")
                            state = "RECOVERY"
                        else:
                            print("[SM] Kiri Buntu -> PRE_TURN_RIGHT")
                            state = "PRE_TURN_RIGHT"
                        state_ts = now

                # --- STATE: PRE TURN RIGHT ---
                elif state == "PRE_TURN_RIGHT":
                    if elapsed > 0.2:
                        state = "TURN_RIGHT"
                        state_ts = now

                # --- STATE: TURN RIGHT (Putar Balik Kanan - Total 180 dr kiri) ---
                elif state == "TURN_RIGHT":
                    robot_motor.move(0.0, SPEED_PUTAR)
                    if elapsed > (DURASI_PUTAR_90 * 2.2):
                        robot_motor.stop()
                        state = "CHECK_RIGHT"
                        state_ts = now

                # --- STATE: CHECK RIGHT ---
                elif state == "CHECK_RIGHT":
                    robot_motor.stop()
                    if elapsed > DURASI_STABIL:
                        if distance > (JARAK_TRIGGER * 1.5):
                            print("[SM] Kanan Aman -> RECOVERY")
                            state = "RECOVERY"
                        else:
                            print("[SM] Kanan Buntu -> U_TURN")
                            state = "U_TURN"
                        state_ts = now

                # --- STATE: U_TURN (Putar 180 Derajat) ---
                elif state == "U_TURN":
                    robot_motor.move(0.0, SPEED_PUTAR)
                    if elapsed > DURASI_PUTAR_90:
                        state = "RECOVERY"
                        state_ts = now

                # --- STATE: RECOVERY ---
                elif state == "RECOVERY":
                    robot_motor.stop()
                    if elapsed > 0.5:
                        state = "IDLE"
                        state_ts = now

            else:
                robot_motor.stop()

            await asyncio.sleep(0.01)

    except Exception as e:
        print(f"[AVOID] Error: {e}")
    finally:
        sensor_task.cancel()
        robot_motor.stop()
        robot_cam.ai.update_distance(None)



@app.get("/")
def index(): return {"status": "Raspbot RTKAv2", "controller": CURRENT_CONTROLLER}

@app.get("/video_feed")
def video_feed(): return StreamingResponse(robot_cam.generate_frames(), media_type="multipart/x-mixed-replace;boundary=frame")

if __name__ == "__main__":
    uvicorn.run(app, host=HOST, port=PORT, log_level="warning")