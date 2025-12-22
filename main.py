#!/home/pi/RTKAv2/venv/bin/python3
import os
import sys
import uvicorn
import json
import asyncio
import math
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import time 
from config import HOST, PORT
from modules.motor import MotorDriver
from modules.camera import VideoStreamer
from modules.extras import ExtraDrivers
from modules.sensors import SensorManager

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

# 1. REMOTE CONTROL
@app.websocket("/ws/control")
async def ws_control(websocket: WebSocket):
    global CURRENT_CONTROLLER
    await websocket.accept()
    CURRENT_CONTROLLER = "manual"
    robot_cam.ai.set_mode("off")
    print("[WS] MANUAL Connected")
    try:
        while True:
            data = await websocket.receive_text()
            payload = json.loads(data)
            cmd = payload.get("cmd")
            if CURRENT_CONTROLLER == "manual":
                if cmd == "move": robot_motor.move(float(payload.get("y",0)), float(payload.get("x",0)), float(payload.get("speed",100)))
                elif cmd == "servo": robot_extras.move_servo(payload.get("type"), payload.get("angle",0))
                elif cmd == "buzzer": robot_extras.set_buzzer(payload.get("state", "off"))
                elif cmd == "stop": robot_motor.stop()
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

# 3. TARGET TRACKING (SERVO HEAD CENTER)
@app.websocket("/ws/tracking")
async def ws_tracking(websocket: WebSocket):
    global CURRENT_CONTROLLER
    await websocket.accept()
    CURRENT_CONTROLLER = "tracking"
    
    # --- DEFAULT: MODE NONE (STANDBY) ---
    robot_cam.ai.set_mode("off") 
    print("[WS] TRACKING Connected (Standby)")
    
    # Reset hardware ke tengah
    pan_pos = 0.0
    tilt_pos = 0.0
    robot_extras.move_servo("pan", 0)
    robot_extras.move_servo("tilt", 0)

    # Variabel untuk Smoothing (Menyimpan nilai error sebelumnya)
    prev_error_x = 0.0
    prev_error_y = 0.0

    # KIRIM STATUS KE UI
    await websocket.send_text(json.dumps({"status": "active", "mode": "standby"}))

    try:
        while True:
            try:
                data = await asyncio.wait_for(websocket.receive_text(), timeout=0.05)
                payload = json.loads(data)
                
                if payload.get("cmd") == "set_ai_mode":
                    req = payload.get("mode") 
                    
                    if req == "none":
                        robot_cam.ai.set_mode("off")
                        pan_pos = 0.0
                        tilt_pos = 0.0
                        prev_error_x = 0.0 # Reset filter
                        prev_error_y = 0.0
                        robot_extras.move_servo("pan", 0)
                        robot_extras.move_servo("tilt", 0)
                        await websocket.send_text(json.dumps({"status": "active", "mode": "standby"}))

                    elif req == "face_track":
                        robot_cam.ai.set_mode("face_detection")
                        await websocket.send_text(json.dumps({"status": "active", "mode": "face_track"}))
                        
                    elif req == "color_track":
                        color = payload.get("color", "red") 
                        robot_cam.ai.set_color_target(color)
                        robot_cam.ai.set_mode("color_detection")
                        await websocket.send_text(json.dumps({"status": "active", "mode": f"track_{color}"}))
                        
            except asyncio.TimeoutError: pass

            if CURRENT_CONTROLLER == "tracking" and robot_cam.ai.mode != "off" and robot_cam.ai.object_found:
                
                # 1. AMBIL DATA ERROR MENTAH (-1.0 s/d 1.0)
                raw_error_x = robot_cam.ai.track_error_x 
                raw_error_y = robot_cam.ai.track_error_y 

                # 2. TERAPKAN LOW PASS FILTER (SMOOTHING)
                # Rumus: (NilaiBaru * alpha) + (NilaiLama * (1-alpha))
                # Alpha kecil (0.2) = Sangat smooth tapi agak lambat (cinematic)
                # Alpha besar (0.8) = Respon cepat tapi agak kasar
                alpha = 0.3 
                
                smooth_x = (raw_error_x * alpha) + (prev_error_x * (1.0 - alpha))
                smooth_y = (raw_error_y * alpha) + (prev_error_y * (1.0 - alpha))
                
                # Simpan nilai untuk frame berikutnya
                prev_error_x = smooth_x
                prev_error_y = smooth_y

                # 3. PENGATURAN SENSITIVITAS (GAIN)
                # Turunkan sedikit dari 3.0 ke 2.0 agar tidak loncat-loncat
                pan_speed = 2.0  
                tilt_speed = 2.0 
                
                # 4. DEADZONE (Toleransi Tengah)
                # Jika error sangat kecil (di bawah 0.15), anggap 0 biar servo diam anteng
                if abs(smooth_x) < 0.15: smooth_x = 0
                if abs(smooth_y) < 0.15: smooth_y = 0

                # 5. KALKULASI POSISI BARU
                pan_pos -= (smooth_x * pan_speed)
                tilt_pos += (smooth_y * tilt_speed) 

                # 6. LIMIT (CLAMP) -90 s/d 90
                pan_pos = max(-90, min(90, pan_pos))
                tilt_pos = max(-90, min(90, tilt_pos))
                
                # 7. EKSEKUSI KE HARDWARE
                robot_extras.move_servo("pan", int(pan_pos))
                robot_extras.move_servo("tilt", int(tilt_pos))
            
            await asyncio.sleep(0.04) 

    except Exception as e:
        print(f"[TRACK] Error: {e}")
    finally:
        pass


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

        
# 7. AVOID & FOLLOW
@app.websocket("/ws/avoid")
async def ws_avoid(websocket: WebSocket):
    global CURRENT_CONTROLLER
    await websocket.accept()
    CURRENT_CONTROLLER = "avoid"
    
    robot_cam.ai.set_mode("off")
    print("[WS] AVOID Connected")
    
    current_mode = "standby"
    
    # Default: Semua sensor aktif (jika user lupa setting)
    active_mask = [1, 1, 1, 1, 1] 
    
    try:
        while True:
            # 1. TERIMA PERINTAH
            try:
                data = await asyncio.wait_for(websocket.receive_text(), timeout=0.05)
                payload = json.loads(data)
                cmd = payload.get("cmd")
                
                if cmd == "set_ai_mode":
                    mode = payload.get("mode") 
                    current_mode = mode
                    
                    if mode == "avoid_hcsr":
                        msg = "MODE: OBSTACLE AVOID"
                    elif mode == "avoid_hybrid":
                        # BACA CONFIG DARI UI
                        # config: {"ll": true, "l": false, ...}
                        cfg = payload.get("config", {})
                        
                        # Buat Masking Array [LL, L, M, R, RR]
                        # Jika True jadi 1, False jadi 0
                        active_mask = [
                            1 if cfg.get("ll", True) else 0,
                            1 if cfg.get("l",  True) else 0,
                            1 if cfg.get("m",  True) else 0,
                            1 if cfg.get("r",  True) else 0,
                            1 if cfg.get("rr", True) else 0
                        ]
                        print(f"[LINE] Sensor Mask: {active_mask}")
                        msg = f"MODE: LINE (Mask: {active_mask})"
                    else:
                        msg = "MODE: STANDBY"
                        robot_motor.stop()
                        
                    await websocket.send_text(json.dumps({"status": "active", "mode": msg}))
                    
            except asyncio.TimeoutError: pass

            # 2. LOGIKA UTAMA
            if CURRENT_CONTROLLER == "avoid" and current_mode != "standby":
                
                distance = robot_sensors.get_distance()
                
                # --- MODE A: OBSTACLE ONLY ---
                if current_mode == "avoid_hcsr":
                    if distance < 25: 
                        robot_motor.stop()
                        await asyncio.sleep(0.2)
                        robot_motor.move(-0.4, 0.0)
                        await asyncio.sleep(0.5)
                        robot_motor.move(0.0, -0.6)
                        await asyncio.sleep(0.4)
                    else:
                        robot_motor.move(0.4, 0.0)

                # --- MODE B: LINE + AVOID (WITH MASKING) ---
                elif current_mode == "avoid_hybrid":
                    if distance < 15:
                        # Safety Stop
                        robot_motor.stop()
                    else:
                        # 1. Baca Sensor Fisik [1, 0, 1, 0, 1]
                        raw_lines = robot_sensors.get_line_status()
                        
                        # 2. Terapkan Masking (Filter User)
                        # Logika AND: Hanya anggap 1 jika fisik detect (1) DAN user enable (1)
                        lines = [r & m for r, m in zip(raw_lines, active_mask)]
                        
                        # Debugging (Opsional, matikan kalau spam)
                        # print(f"Raw: {raw_lines} -> Masked: {lines}")

                        # 3. Logika Navigasi (Berdasarkan data yang sudah di-filter)
                        if lines[2] == 1: # Tengah
                            robot_motor.move(0.4, 0.0)
                            
                        elif lines[1] == 1: # Kiri
                            robot_motor.move(0.3, -0.4) 
                            
                        elif lines[3] == 1: # Kanan
                            robot_motor.move(0.3, 0.4)

                        elif lines[0] == 1: # Kiri Jauh
                            robot_motor.move(0.2, -0.6)
                            
                        elif lines[4] == 1: # Kanan Jauh
                            robot_motor.move(0.2, 0.6)
                            
                        elif sum(lines) == 0: # Tidak ada garis (sesuai filter)
                            robot_motor.stop()
                        
                        elif sum(lines) >= 3: # Perempatan
                            robot_motor.stop()
            
            await asyncio.sleep(0.05)

    except Exception as e:
        print(f"[AVOID] Error: {e}")
    finally:
        robot_motor.stop()


@app.get("/")
def index(): return {"status": "Raspbot RTKAv2", "controller": CURRENT_CONTROLLER}

@app.get("/video_feed")
def video_feed(): return StreamingResponse(robot_cam.generate_frames(), media_type="multipart/x-mixed-replace;boundary=frame")

if __name__ == "__main__":
    uvicorn.run(app, host=HOST, port=PORT, log_level="warning")