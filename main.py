#!/home/pi/RTKAv2/venv/bin/python3
import os
import sys
import uvicorn
import json
import asyncio
import math
import time 
import logging
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware

# --- PROJECT MODULES ---
from config import HOST, PORT
from modules.motor import MotorDriver
from modules.camera import VideoStreamer
from modules.extras import ExtraDrivers
from modules.sensors import SensorManager
from modules.config_loader import cfg_mgr

# --- SYSTEM CONFIG ---
os.environ["OPENCV_LOG_LEVEL"] = "FATAL"
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"

# --- LOGGING SETUP (GLOBAL) ---
# Ditaruh di paling atas agar terbaca oleh semua fungsi
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    handlers=[
        logging.FileHandler("crash_log.txt"), # Simpan log ke file
        logging.StreamHandler(sys.stdout)     # Tampil di terminal
    ]
)
logger = logging.getLogger("rtka")

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# --- HARDWARE PLACEHOLDERS ---
robot_motor = None
robot_cam = None
robot_extras = None
robot_sensors = None
CURRENT_CONTROLLER = "none"

# ==============================================================================
# HELPER FUNCTIONS
# ==============================================================================

def reload_hardware():
    """Merestart driver hardware saat berganti config."""
    logger.info("Reloading Hardware...")
    global robot_motor, robot_extras, robot_sensors
    
    try:
        if robot_motor: robot_motor.close()
    except Exception: pass

    try:
        if robot_extras: robot_extras.close()
    except Exception: pass

    try:
        if robot_sensors: robot_sensors.close()
    except Exception: pass

    # 2. Hidupkan Hardware Baru
    try:
        robot_motor = MotorDriver(simulation=False)
        robot_extras = ExtraDrivers()
        robot_sensors = SensorManager()
        logger.info(f"Hardware Reloaded. User Mode: {cfg_mgr.use_user_config}")
    except Exception as e:
        logger.exception(f"Hardware Init Failed: {e}")


# ---------- Async Helpers (Non-Blocking) ----------
async def async_move_servo(ser_type, angle):
    if robot_extras is None: return
    try:
        await asyncio.to_thread(robot_extras.move_servo, ser_type, angle)
    except Exception: logger.exception("Servo Error")

async def async_detach_servos():
    if robot_extras is None: return
    try:
        await asyncio.to_thread(robot_extras.detach_servos)
    except Exception: pass

async def async_set_buzzer(state):
    if robot_extras is None: return
    try:
        await asyncio.to_thread(robot_extras.set_buzzer, state)
    except Exception: pass

async def async_play_melody(name):
    if robot_extras is None: return 0
    try:
        return await asyncio.to_thread(robot_extras.play_melody, name)
    except Exception: return 0


# ---------- Startup / Shutdown ----------
@app.on_event("startup")
async def _startup():
    global robot_motor, robot_cam, robot_extras, robot_sensors
    logger.info("Starting Raspbot RTKAv2...")
    try:
        robot_motor = MotorDriver(simulation=False)
        robot_cam = VideoStreamer()
        robot_extras = ExtraDrivers()
        robot_sensors = SensorManager()
        logger.info("Hardware initialized successfully.")
    except Exception as e:
        logger.exception(f"Hardware Init Failed: {e}")

@app.on_event("shutdown")
async def _shutdown():
    logger.info("Shutting down...")
    async def _close_obj(obj):
        if obj is None: return
        fn = getattr(obj, "close", None) or getattr(obj, "stop", None)
        if callable(fn):
            try: await asyncio.to_thread(fn)
            except Exception: pass

    await _close_obj(robot_motor)
    await _close_obj(robot_extras)
    await _close_obj(robot_sensors)
    await _close_obj(robot_cam)

# ==============================================================================
# WEBSOCKET ENDPOINTS
# ==============================================================================

# 0. CONFIG SWITCHER
@app.websocket("/ws/configSwitch")
async def ws_config_switch(websocket: WebSocket):
    await websocket.accept()
    logger.info("Config Switcher Connected")
    try:
        while True:
            data = await websocket.receive_text()
            payload = json.loads(data)
            cmd = payload.get("cmd")
            
            if cmd == "save_config":
                cfg_mgr.save_user_config(payload.get("config"))
                await websocket.send_text(json.dumps({"status": "saved", "msg": "Config saved"}))
                
            elif cmd == "set_mode":
                mode = payload.get("mode")
                if mode == "user":
                    cfg_mgr.use_user_config = True
                    msg = "Switched to USER Config"
                else:
                    cfg_mgr.use_user_config = False
                    msg = "Switched to DEFAULT Config"
                reload_hardware()
                await websocket.send_text(json.dumps({"status": "switched", "mode": mode, "msg": msg}))       
    except WebSocketDisconnect: pass
    except Exception: logger.exception("Config Error")


# 1. REMOTE CONTROL
@app.websocket("/ws/control")
async def ws_control(websocket: WebSocket):
    global CURRENT_CONTROLLER
    await websocket.accept()
    CURRENT_CONTROLLER = "manual"
    robot_cam.ai.set_mode("off")
    logger.info("MANUAL Connected")
    try:
        while True:
            data = await websocket.receive_text()
            payload = json.loads(data)
            cmd = payload.get("cmd")
            
            if CURRENT_CONTROLLER == "manual":
                if cmd == "move":
                    robot_motor.move(float(payload.get("y", 0)), float(payload.get("x", 0)), float(payload.get("speed", 100)))
                elif cmd == "servo": 
                    await async_move_servo(payload.get("type"), payload.get("angle", 0))
                elif cmd == "buzzer": 
                    await async_set_buzzer(payload.get("state", "off"))
                elif cmd == "led":
                    robot_extras.set_led(payload.get("color"), payload.get("state"))
                elif cmd == "stop": 
                    robot_motor.stop()
    except WebSocketDisconnect: pass
    except: pass
    finally: robot_motor.stop()


# 2. AUTO PILOT
@app.websocket("/ws/autoPilot")
async def ws_autopilot(websocket: WebSocket):
    global CURRENT_CONTROLLER
    await websocket.accept()
    CURRENT_CONTROLLER = "autopilot"
    robot_cam.ai.set_mode("off")
    logger.info("AUTO PILOT Connected")
    try:
        while True:
            try:
                data = await asyncio.wait_for(websocket.receive_text(), timeout=0.05)
                payload = json.loads(data)
                
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
            except WebSocketDisconnect: break

            if CURRENT_CONTROLLER == "autopilot" and robot_cam.ai.mode == "auto_pilot" and robot_cam.ai.object_found:
                error = robot_cam.ai.track_error_x
                robot_motor.move(0.35 - (abs(error) * 0.15), error * 0.8, 50)
            else:
                robot_motor.stop()
            await asyncio.sleep(0.01)
    except: pass
    finally: 
        robot_motor.stop()
        robot_cam.ai.set_mode("off")


# 3. TRACKING (SAFEZONE & MINIMUM STEP)
@app.websocket("/ws/tracking")
async def ws_tracking(websocket: WebSocket):
    global CURRENT_CONTROLLER
    await websocket.accept()
    CURRENT_CONTROLLER = "tracking"
    robot_cam.ai.show_safezone = True
    robot_cam.ai.set_mode("off") 
    logger.info("TRACKING Connected - SAFEZONE MODE")
    
    pan_pos = 0.0
    tilt_pos = 0.0
    await async_move_servo("pan", 0)
    await async_move_servo("tilt", 0)
    
    # --- KONFIGURASI TRACKING ---
    
    # 1. SAFEZONE (Area Kotak Tengah)
    # 0.15 artinya 15% dari tengah. Objek didalam area ini TIDAK DIGUBRIS.
    # Ini mencegah servo goyang-goyang saat objek sudah ditengah.
    SAFEZONE_X = 0.15
    SAFEZONE_Y = 0.15

    # 2. SENSITIVITAS (FOV FACTOR)
    # Berapa derajat servo berputar per 1.0 error.
    # Diturunkan sedikit agar tidak agresif (Overshoot prevention)
    FOV_FACTOR_X = 15.0
    FOV_FACTOR_Y = 10.0
    
    # 3. MINIMUM STEP (Rentang Nilai Minimal)
    # Servo hanya boleh bergerak jika perubahannya > 2 derajat.
    # Jangan gerak cuma 0.5 derajat (buang tenaga & bikin panas).
    MIN_STEP = 2.0 

    await websocket.send_text(json.dumps({"status": "active", "mode": "standby"}))

    try:
        while True:
            try:
                data = await asyncio.wait_for(websocket.receive_text(), timeout=0.1)
                payload = json.loads(data)
                if payload.get("cmd") == "set_ai_mode":
                    req = payload.get("mode") 
                    if req == "face_track":
                        robot_cam.ai.set_mode("face_detection")
                        await websocket.send_text(json.dumps({"status": "active", "mode": "face_track"}))
                    elif req == "color_track":
                        color = payload.get("color", "red") 
                        robot_cam.ai.set_color_target(color)
                        robot_cam.ai.set_mode("color_detection")
                        await websocket.send_text(json.dumps({"status": "active", "mode": f"track_{color}"}))
                    elif req == "none":
                        robot_cam.ai.set_mode("off")
                        await async_detach_servos()
            except asyncio.TimeoutError: pass
            except WebSocketDisconnect: break

            # LOGIKA UTAMA TRACKING
            if CURRENT_CONTROLLER == "tracking" and robot_cam.ai.mode != "off" and robot_cam.ai.object_found:
                
                # 1. Ambil Error dari AI (-1.0 s/d 1.0)
                err_x = robot_cam.ai.track_error_x 
                err_y = getattr(robot_cam.ai, 'track_error_y', 0.0)
                
                delta_pan = 0
                delta_tilt = 0

                # 2. Cek SAFEZONE X (Pan)
                # Jika error diluar batas 0.15 (diluar kotak), baru hitung gerak
                if abs(err_x) > SAFEZONE_X:
                    # Hitung derajat yang dibutuhkan
                    calc_pan = -(err_x * FOV_FACTOR_X)
                    
                    # 3. Cek MINIMUM STEP
                    # Hanya gerak jika butuh geser > 2 derajat
                    if abs(calc_pan) >= MIN_STEP:
                        delta_pan = calc_pan

                # 4. Cek SAFEZONE Y (Tilt)
                if abs(err_y) > SAFEZONE_Y:
                    calc_tilt = (err_y * FOV_FACTOR_Y)
                    if abs(calc_tilt) >= MIN_STEP:
                        delta_tilt = calc_tilt
                
                # 5. Eksekusi Gerak
                # Jika ada perubahan (salah satu tidak nol)
                if delta_pan != 0 or delta_tilt != 0:
                    
                    pan_pos += delta_pan
                    tilt_pos += delta_tilt

                    # Kunci batas fisik (-90 s/d 90)
                    pan_pos = max(-90, min(90, pan_pos))
                    tilt_pos = max(-90, min(90, tilt_pos))
                    
                    # Gerakkan Servo
                    if delta_pan != 0:
                        await async_move_servo("pan", int(pan_pos))
                    
                    if delta_tilt != 0:
                        await async_move_servo("tilt", int(tilt_pos))
                    
                    # Reset error AI agar tidak double process
                    robot_cam.ai.track_error_x = 0
                
            await asyncio.sleep(0.1)

    except Exception: logger.exception("Tracking Error")
    finally: 
        await async_detach_servos() 
        robot_cam.ai.show_safezone = False


# 4. GESTURE RECOGNITION & COLOR FOLLOW
@app.websocket("/ws/recognitionControl")
async def ws_recognition(websocket: WebSocket):
    global CURRENT_CONTROLLER
    await websocket.accept()
    CURRENT_CONTROLLER = "recognition"

    robot_cam.ai.show_distance = True
    robot_cam.ai.set_mode("off")
    robot_cam.ai.show_safezone = True
    logger.info("RECOGNITION Connected")

    # ==================================================
    # STATE
    # ==================================================
    pan_pos = 0.0
    last_throttle = 0.0

    # ==================================================
    # MOTOR CONFIG
    # ==================================================
    SPEED_LIMIT = 25
    MAX_THROTTLE = 0.25
    STEER_GAIN = 0.6

    # ==================================================
    # SERVO CONFIG (IDENTIK /ws/tracking)
    # ==================================================
    SAFEZONE_X = 0.15
    FOV_FACTOR = 15.0
    MIN_STEP = 2.0

    # ==================================================
    # DISTANCE CONFIG (cm)
    # ==================================================
    SAFE_DISTANCE_CM = 60.0  # <100 stop, >=100 boleh maju

    # ==================================================
    # ACTIVE BRAKE
    # ==================================================
    BRAKE_FORCE = -0.35
    BRAKE_TIME = 0.10

    async def active_brake():
        nonlocal last_throttle
        if last_throttle > 0.05:
            robot_motor.move(BRAKE_FORCE, 0.0, SPEED_LIMIT)
            await asyncio.sleep(BRAKE_TIME)
        robot_motor.stop()
        last_throttle = 0.0

    # ==================================================
    # SENSOR LOOP (KHUSUS RECOGNITION)
    # ==================================================
    sensor_running = True

    async def sensor_loop():
        while sensor_running:
            try:
                if robot_sensors:
                    raw = robot_sensors.get_distance()
                    robot_cam.ai.update_distance(raw)
                await asyncio.sleep(0.05)  # 20 Hz
            except Exception:
                await asyncio.sleep(0.2)

    sensor_task = asyncio.create_task(sensor_loop())

    try:
        while True:
            # ==========================================
            # RECEIVE COMMAND
            # ==========================================
            try:
                data = await asyncio.wait_for(
                    websocket.receive_text(),
                    timeout=0.05
                )
                payload = json.loads(data)

                if payload.get("cmd") == "set_ai_mode":
                    req = payload.get("mode")

                    if req == "gesture_cmd":
                        robot_cam.ai.set_mode("gesture_recognition")
                        await websocket.send_text(json.dumps({
                            "status": "active",
                            "mode": "gesture_control"
                        }))

                    elif req == "color_follow":
                        target_color = payload.get("color", "none")
                        robot_cam.ai.set_color_target(target_color)
                        robot_cam.ai.set_mode("color_detection")

                        status_msg = (
                            "waiting_color"
                            if target_color == "none"
                            else f"follow_{target_color}"
                        )
                        await websocket.send_text(json.dumps({
                            "status": "active",
                            "mode": status_msg
                        }))

            except asyncio.TimeoutError:
                pass
            except WebSocketDisconnect:
                break

            # ==========================================
            # MAIN LOGIC
            # ==========================================
            if CURRENT_CONTROLLER == "recognition":

                # -------------------------------
                # A. GESTURE
                # -------------------------------
                if robot_cam.ai.mode == "gesture_recognition":
                    fingers = robot_cam.ai.gesture_data

                    if fingers == 1:
                        robot_motor.move(0.25, 0.0, SPEED_LIMIT)
                        last_throttle = 0.25
                    elif fingers == 2:
                        robot_motor.move(-0.25, 0.0, SPEED_LIMIT)
                        last_throttle = -0.25
                    else:
                        await active_brake()

                # -------------------------------
                # B. COLOR FOLLOW (VISION + HCSR)
                # -------------------------------
                elif robot_cam.ai.mode == "color_detection":

                    distance_cm = robot_cam.ai.distance_val

                    if robot_cam.ai.object_found:
                        err_x = robot_cam.ai.track_error_x

                        # ---- SERVO ----
                        delta_pan = 0.0
                        if abs(err_x) > SAFEZONE_X:
                            calc = -(err_x * FOV_FACTOR)
                            if abs(calc) >= MIN_STEP:
                                delta_pan = calc

                        if delta_pan != 0:
                            pan_pos += delta_pan
                            pan_pos = max(-90, min(90, pan_pos))
                            await async_move_servo("pan", int(pan_pos))

                        # ---- MOTOR ----
                        if distance_cm is not None and distance_cm >= SAFE_DISTANCE_CM:
                            robot_motor.move(
                                MAX_THROTTLE,
                                err_x * STEER_GAIN,
                                SPEED_LIMIT
                            )
                            last_throttle = MAX_THROTTLE
                        else:
                            await active_brake()

                        robot_cam.ai.track_error_x = 0.0

                    else:
                        await active_brake()

                else:
                    await active_brake()

            await asyncio.sleep(0.1)

    except Exception:
        logger.exception("Recog Error")

    finally:
        sensor_running = False
        sensor_task.cancel()
        await active_brake()
        pan_pos = 0
        await async_move_servo("pan", 0)
        robot_cam.ai.set_mode("off")
        robot_cam.ai.show_safezone = False
        robot_cam.ai.show_distance = False
        robot_cam.ai.update_distance(None)
        logger.info("RECOGNITION Disconnected")



# 5. OBJECT DETECTION
@app.websocket("/ws/objectDetection")
async def ws_obj_detection(websocket: WebSocket):
    global CURRENT_CONTROLLER
    await websocket.accept()
    CURRENT_CONTROLLER = "detection"
    robot_cam.ai.set_mode("off") 
    logger.info("DETECTION Connected")
    try:
        while True:
            data = await websocket.receive_text()
            payload = json.loads(data)
            cmd = payload.get("cmd")
            if cmd == "set_ai_mode":
                req_mode = payload.get("mode")
                if req_mode == "color_detection":
                    robot_cam.ai.set_color_target("all")
                    robot_cam.ai.set_mode("color_detection")
                    await websocket.send_text(json.dumps({"status": "active", "mode": "detect_all_colors"}))
                else:
                    robot_cam.ai.set_mode(req_mode)
                    await websocket.send_text(json.dumps({"status": "active", "mode": req_mode}))
    except WebSocketDisconnect: pass
    except Exception: logger.exception("Obj Detection Error")
    finally: robot_cam.ai.set_mode("off")


# 6. QR SCANNER
@app.websocket("/ws/qr")
async def ws_qr(websocket: WebSocket):
    global CURRENT_CONTROLLER
    await websocket.accept()
    CURRENT_CONTROLLER = "qr"
    robot_cam.ai.set_mode("off") 
    logger.info("QR Connected")
    try:
        while True:
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
            except WebSocketDisconnect: break
            
            if CURRENT_CONTROLLER == "qr" and robot_cam.ai.mode == "qr_recognition":
                current_qr = robot_cam.ai.qr_data
                if current_qr is not None:
                    scan_text = current_qr.upper().strip()
                    logger.info(f"[QR] EKSEKUSI: {scan_text}")
                    await websocket.send_text(json.dumps({"status": "active", "mode": f"CMD: {scan_text}"}))
                    
                    await async_set_buzzer("on")
                    await asyncio.sleep(0.1)
                    await async_set_buzzer("off")
                    
                    duration = 0 
                    songs = {"MERRY": "merry_christmas", "TWINKLE": "twinkle", "MARY": "mary_lamb", "BALONKU": "balonku", "CICAK": "cicak", "PELANGI": "pelangi", "BIRTHDAY": "happy_birthday"}
                    for key, song in songs.items():
                        if key in scan_text:
                            duration = await async_play_melody(song)
                            break

                    if duration > 0:
                        await asyncio.sleep(duration + 1.0)
                        robot_cam.ai.qr_data = None 
                        continue 

                    if "KOTAK" in scan_text:
                        for _ in range(4):
                            robot_motor.move(0.5, 0.0); await asyncio.sleep(1.0)
                            robot_motor.stop(); await asyncio.sleep(0.2)
                            robot_motor.move(0.0, 0.6); await asyncio.sleep(0.6) 
                            robot_motor.stop(); await asyncio.sleep(0.2)
                    elif "PUTAR" in scan_text:
                        robot_motor.move(0.0, 0.7); await asyncio.sleep(2.5)   
                        robot_motor.stop()
                    elif "MAJU" in scan_text:
                        robot_motor.move(0.5, 0.0); await asyncio.sleep(2.0)
                        robot_motor.stop()
                    elif "MUNDUR" in scan_text:
                        robot_motor.move(-0.5, 0.0); await asyncio.sleep(2.0)
                        robot_motor.stop()

                    robot_cam.ai.qr_data = None
                    await asyncio.sleep(1.0)
            await asyncio.sleep(0.1)
    except Exception: logger.exception("QR Error")
    finally:
        robot_motor.stop()
        await async_set_buzzer("off")
        robot_cam.ai.set_mode("off")

# 7. OBSTACLE AVOIDANCE (AGRESSIVE: BRAKE -> SCAN)
@app.websocket("/ws/avoid")
async def ws_avoid(websocket: WebSocket):
    global CURRENT_CONTROLLER
    await websocket.accept()
    CURRENT_CONTROLLER = "avoid"
    
    robot_cam.ai.set_mode("off")
    robot_cam.ai.show_distance = True
    logger.info("AVOID Connected - AGRESSIVE MODE")
    
    # --- SHARED DATA ---
    sensor_data = {"dist": 100.0, "panic": False}
    
    # --- CONFIG PHYSICS ---
    ZONA_LIMIT    = 15    # Jarak Pengereman (sesuai request)
    
    SPEED_MAJU    = 0.06  # Kecepatan Jalan
    SPEED_MUNDUR  = -0.40 # Kecepatan Mundur (Hanya dipakai jika nabrak fisik)
    SPEED_PUTAR   = 0.50  # Putar agak cepat biar sat-set
    
    # Active Brake Config
    BRAKE_FORCE   = -0.80 # Hentakan Rem
    BRAKE_TIME    = 0.15  # Durasi Rem

    TIME_SCAN_TURN = 0.6  # Waktu putar saat scan (sedikit dipercepat)
    TIME_STABIL    = 0.3  # Waktu diam sebelum baca sensor

    state = "IDLE"
    current_mode = "standby"
    retreat_locked = False
    
    state_ts = time.monotonic()
    dist_left = 0
    dist_right = 0
    active_mask = [1, 1, 1, 1, 1]
    
    # --- ASYNC SENSOR LOOP ---
    async def sensor_loop():
        ALPHA = 1.0 # Data Mentah (Responsif)
        while True:
            try:
                if robot_sensors:
                    raw = None
                    try:
                        raw = await asyncio.wait_for(
                            asyncio.to_thread(robot_sensors.get_distance), 
                            timeout=0.1 
                        )
                    except: raw = None

                    robot_cam.ai.update_distance(raw)

                    if raw is None:
                        sensor_data["dist"] = -1.0 
                    else:
                        if sensor_data["dist"] == -1.0: sensor_data["dist"] = raw
                        else: sensor_data["dist"] = (sensor_data["dist"] * (1-ALPHA)) + (raw * ALPHA)
                    
                    sensor_data["panic"] = robot_sensors.check_panic()
                
                await asyncio.sleep(0.01) 
            except: await asyncio.sleep(1)

    sensor_task = asyncio.create_task(sensor_loop())

    try:
        while True:
            try:
                data = await asyncio.wait_for(websocket.receive_text(), timeout=0.01)
                payload = json.loads(data)
                cmd = payload.get("cmd")
                if cmd == "set_ai_mode":
                    mode = payload.get("mode")
                    current_mode = mode
                    if mode == "standby":
                        state = "IDLE"; robot_motor.stop(); msg = "MODE: STANDBY"
                    else:
                        state = "FORWARD"; retreat_locked = False
                        if mode == "avoid_hybrid":
                            cfg = payload.get("config", {})
                            active_mask = [1 if cfg.get(k, True) else 0 for k in ["ll","l","m","r","rr"]]
                            msg = "MODE: HYBRID START"
                        else: msg = "MODE: AVOID START"
                    await websocket.send_text(json.dumps({"status": "active", "mode": msg}))
            except asyncio.TimeoutError: pass
            except WebSocketDisconnect: break

            if CURRENT_CONTROLLER == "avoid" and current_mode != "standby":
                distance = sensor_data["dist"]
                is_panic = sensor_data["panic"]
                now = time.monotonic()
                elapsed = now - state_ts

                # 1. SAFETY CHECK
                if distance == -1.0:
                    robot_motor.stop()
                    state = "IDLE"
                    await asyncio.sleep(0.1)
                    continue 

                # 2. EMERGENCY (TABRAKAN FISIK)
                # Jika sensor BFD kena, robot tetap WAJIB mundur dulu biar lepas
                if is_panic and not retreat_locked:
                    robot_motor.move(BRAKE_FORCE, 0.0)
                    await asyncio.sleep(BRAKE_TIME)
                    robot_motor.stop()
                    state = "RETREAT" # Khusus panic, tetap mundur
                    retreat_locked = True
                    state_ts = now
                    continue

                # ---------------------------------------------------------
                # STATE MACHINE
                # ---------------------------------------------------------
                
                if state == "IDLE": 
                    robot_motor.stop()

                elif state == "FORWARD":
                    # --- LOGIKA BARU: BRAKE -> SCAN ---
                    if distance <= ZONA_LIMIT:
                        logger.info(f"[OBSTACLE] Jarak {distance}cm. STOP & SCAN!")
                        
                        # 1. Active Brake (Agar tidak menabrak sisa inersia)
                        robot_motor.move(BRAKE_FORCE, 0.0) 
                        await asyncio.sleep(BRAKE_TIME)   
                        
                        # 2. Stop Total
                        robot_motor.stop()
                        await asyncio.sleep(0.2) # Jeda sesaat agar stabil
                        
                        # 3. LANGSUNG SCAN (Tidak ada mundur)
                        state = "SCAN_INIT"
                        state_ts = now
                    else:
                        # Jalan Maju
                        if current_mode == "avoid_hcsr": 
                            robot_motor.move(SPEED_MAJU, 0.0)
                        elif current_mode == "avoid_hybrid":
                            raw_lines = [0]*5
                            if robot_sensors: raw_lines = robot_sensors.get_line_status()
                            lines = [r & m for r, m in zip(raw_lines, active_mask)]
                            if sum(lines) == 0: robot_motor.stop()
                            elif lines[2]: robot_motor.move(0.15, 0.0)
                            elif lines[1]: robot_motor.move(0.12, -0.3)
                            elif lines[3]: robot_motor.move(0.12, 0.3)
                            elif lines[0]: robot_motor.move(0.10, -0.5)
                            elif lines[4]: robot_motor.move(0.10, 0.5)

                elif state == "RETREAT":
                    # State ini HANYA dipakai jika Panic Sensor (Tabrakan) aktif
                    # Jika sensor ultrasonic, state ini dilewati.
                    if distance >= (ZONA_LIMIT + 5):
                        robot_motor.stop()
                        state = "SCAN_INIT"
                    elif elapsed > 1.5: 
                        robot_motor.stop()
                        state = "SCAN_INIT"
                    else:
                        robot_motor.move(SPEED_MUNDUR, 0.0)

                # --- LOGIKA SCANNING ---
                elif state == "SCAN_INIT": 
                    state = "SCAN_LEFT_MOVE"; state_ts = now
                
                elif state == "SCAN_LEFT_MOVE":
                    robot_motor.move(0.0, -SPEED_PUTAR)
                    if elapsed > TIME_SCAN_TURN: robot_motor.stop(); state = "SCAN_LEFT_READ"; state_ts = now
                
                elif state == "SCAN_LEFT_READ":
                    if elapsed > TIME_STABIL: dist_left = distance; state = "SCAN_RIGHT_MOVE"; state_ts = now
                
                elif state == "SCAN_RIGHT_MOVE":
                    robot_motor.move(0.0, SPEED_PUTAR)
                    if elapsed > (TIME_SCAN_TURN * 2.2): robot_motor.stop(); state = "SCAN_RIGHT_READ"; state_ts = now
                
                elif state == "SCAN_RIGHT_READ":
                    if elapsed > TIME_STABIL:
                        dist_right = distance
                        logger.info(f"Scan -> Kiri: {dist_left}, Kanan: {dist_right}")
                        
                        target_dir = "NONE"
                        # Syarat jalan: minimal ada ruang sedikit lebih besar dari limit
                        SYARAT_RUANG = ZONA_LIMIT + 5 
                        
                        if dist_left >= SYARAT_RUANG and dist_right >= SYARAT_RUANG: 
                            target_dir = "LEFT" if dist_left > dist_right else "RIGHT"
                        elif dist_left >= SYARAT_RUANG: target_dir = "LEFT"
                        elif dist_right >= SYARAT_RUANG: target_dir = "RIGHT"
                        
                        if target_dir != "NONE": 
                            state = "TURN_TO_LEFT" if target_dir == "LEFT" else "TURN_TO_RIGHT"
                        else: 
                            state = "DEAD_END"
                        state_ts = now

                elif state == "TURN_TO_LEFT":
                    robot_motor.move(0.0, -SPEED_PUTAR)
                    if elapsed > (TIME_SCAN_TURN * 2.2): robot_motor.stop(); state = "RESET_AND_GO"
                
                elif state == "TURN_TO_RIGHT":
                    robot_motor.move(0.0, SPEED_PUTAR) 
                    if elapsed > (TIME_SCAN_TURN * 2.2): robot_motor.stop(); state = "RESET_AND_GO"

                elif state == "RESET_AND_GO":
                    retreat_locked = False; state = "FORWARD"
                
                elif state == "DEAD_END":
                    await async_set_buzzer("on")
                    if elapsed > 2.0: await async_set_buzzer("off"); state = "SCAN_INIT"; state_ts = now
            else: robot_motor.stop()
            
            await asyncio.sleep(0.01)
    except Exception: logger.exception("[AVOID] Error")
    finally:
        sensor_task.cancel(); robot_motor.stop(); robot_cam.ai.show_distance = False; robot_cam.ai.update_distance(None)


# ==============================================================================
@app.get("/")
def index(): return {"status": "Raspbot RTKAv2", "controller": CURRENT_CONTROLLER}

@app.get("/video_feed")
def video_feed(): return StreamingResponse(robot_cam.generate_frames(), media_type="multipart/x-mixed-replace;boundary=frame")

if __name__ == "__main__":
    uvicorn.run(app, host=HOST, port=PORT, log_level="warning")