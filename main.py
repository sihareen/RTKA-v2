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

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# --- HARDWARE INITIALIZATION ---
robot_motor = MotorDriver(simulation=False) 
robot_cam = VideoStreamer()
robot_extras = ExtraDrivers()
robot_sensors = SensorManager()
CURRENT_CONTROLLER = "none"

# ==============================================================================
# HELPER FUNCTIONS
# ==============================================================================

def reload_hardware():
    """Merestart driver hardware saat berganti config (Default <-> User)."""
    print("[SYSTEM] Reloading Hardware...")
    global robot_motor, robot_extras, robot_sensors
    
    # 1. Matikan Hardware Lama
    if 'robot_motor' in globals(): robot_motor.close()
    if 'robot_extras' in globals(): robot_extras.close()
    if 'robot_sensors' in globals(): robot_sensors.close()
    
    # 2. Hidupkan Hardware Baru (Otomatis baca cfg_mgr)
    try:
        robot_motor = MotorDriver(simulation=False)
        robot_extras = ExtraDrivers()
        robot_sensors = SensorManager()
        print(f"[SYSTEM] Hardware Reloaded. User Mode: {cfg_mgr.use_user_config}")
    except Exception as e:
        print(f"[SYSTEM] Hardware Init Failed: {e}")

# ==============================================================================
# WEBSOCKET ENDPOINTS
# ==============================================================================

# 0. CONFIG SWITCHER
@app.websocket("/ws/configSwitch")
async def ws_config_switch(websocket: WebSocket):
    await websocket.accept()
    print("[WS] Config Switcher Connected")
    
    try:
        while True:
            data = await websocket.receive_text()
            payload = json.loads(data)
            cmd = payload.get("cmd")
            
            # CASE A: SIMPAN CONFIG
            if cmd == "save_config":
                new_config = payload.get("config")
                cfg_mgr.save_user_config(new_config)
                await websocket.send_text(json.dumps({"status": "saved", "msg": "Config saved to JSON"}))
                
            # CASE B: GANTI MODE
            elif cmd == "set_mode":
                mode = payload.get("mode") # "default" / "user"
                
                if mode == "user":
                    cfg_mgr.use_user_config = True
                    msg = "Switched to USER Config"
                else:
                    cfg_mgr.use_user_config = False
                    msg = "Switched to DEFAULT Config"
                
                reload_hardware()
                
                await websocket.send_text(json.dumps({
                    "status": "switched", 
                    "mode": mode,
                    "msg": msg
                }))       
    except Exception as e:
        print(f"[CFG] Error: {e}")


# 1. REMOTE CONTROL (MANUAL)
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
                if cmd == "move":
                    y = float(payload.get("y", 0))
                    x = float(payload.get("x", 0))
                    limit = float(payload.get("speed", 100))
                    robot_motor.move(y, x, limit)
                
                elif cmd == "servo": 
                    robot_extras.move_servo(payload.get("type"), payload.get("angle",0))
                
                elif cmd == "buzzer": 
                    robot_extras.set_buzzer(payload.get("state", "off"))
                
                elif cmd == "led":
                    robot_extras.set_led(payload.get("color"), payload.get("state"))
                    
                elif cmd == "stop": 
                    robot_motor.stop()
    except: pass
    finally: robot_motor.stop()


# 2. AUTO PILOT (SIMPLE LANE)
@app.websocket("/ws/autoPilot")
async def ws_autopilot(websocket: WebSocket):
    global CURRENT_CONTROLLER
    await websocket.accept()
    CURRENT_CONTROLLER = "autopilot"
    robot_cam.ai.set_mode("off")
    print("[WS] AUTO PILOT Connected")

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


# 3. TRACKING (FACE/COLOR PAN-TILT)
@app.websocket("/ws/tracking")
async def ws_tracking(websocket: WebSocket):
    global CURRENT_CONTROLLER
    await websocket.accept()
    CURRENT_CONTROLLER = "tracking"
    
    robot_cam.ai.set_mode("off") 
    print("[WS] TRACKING Connected")
    
    pan_pos = 0.0
    tilt_pos = 0.0
    robot_extras.move_servo("pan", 0)
    robot_extras.move_servo("tilt", 0)

    prev_error_x = 0.0
    prev_error_y = 0.0
    ZONA_X = 0.20
    ZONA_Y = 0.20
    robot_cam.ai.set_deadzone(True, ZONA_X, ZONA_Y)

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
                        pan_pos, tilt_pos = 0.0, 0.0
                        prev_error_x, prev_error_y = 0.0, 0.0
                        robot_extras.move_servo("pan", 0)
                        robot_extras.move_servo("tilt", 0)
                        await asyncio.sleep(0.5)
                        robot_extras.detach_servos()
                        await websocket.send_text(json.dumps({"status": "active", "mode": "standby"}))
                        
                    elif req == "face_track":
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

            if CURRENT_CONTROLLER == "tracking" and robot_cam.ai.mode != "off" and robot_cam.ai.object_found:
                raw_x = robot_cam.ai.track_error_x 
                raw_y = getattr(robot_cam.ai, 'track_error_y', 0.0)

                # Smoothing
                alpha = 0.2
                smooth_x = (raw_x * alpha) + (prev_error_x * (1.0 - alpha))
                smooth_y = (raw_y * alpha) + (prev_error_y * (1.0 - alpha))
                prev_error_x, prev_error_y = smooth_x, smooth_y

                if abs(smooth_x) < ZONA_X: smooth_x = 0
                if abs(smooth_y) < ZONA_Y: smooth_y = 0

                if smooth_x != 0 or smooth_y != 0:
                    gain = 0.5 
                    delta_pan = max(-1.0, min(1.0, smooth_x * gain))
                    delta_tilt = max(-1.0, min(1.0, smooth_y * gain))

                    pan_pos = max(-90, min(90, pan_pos - delta_pan))
                    tilt_pos = max(-90, min(90, tilt_pos + delta_tilt))
                    
                    robot_extras.move_servo("pan", int(pan_pos))
                    robot_extras.move_servo("tilt", int(tilt_pos))
                else:
                    robot_extras.detach_servos()

            await asyncio.sleep(0.04) 

    except Exception as e:
        print(f"[TRACK] Error: {e}")
    finally:
        robot_cam.ai.set_deadzone(False)
        robot_extras.detach_servos()


# 4. RECOGNITION (GESTURE & COLOR FOLLOW)
@app.websocket("/ws/recognitionControl")
async def ws_recognition(websocket: WebSocket):
    global CURRENT_CONTROLLER
    await websocket.accept()
    CURRENT_CONTROLLER = "recognition"
    robot_cam.ai.set_mode("off") 
    print("[WS] RECOGNITION Connected")
    
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
                        target_color = payload.get("color", "none")
                        robot_cam.ai.set_color_target(target_color)
                        robot_cam.ai.set_mode("color_detection")
                        status_msg = "waiting_color" if target_color == "none" else f"follow_{target_color}"
                        await websocket.send_text(json.dumps({"status": "active", "mode": status_msg}))
            except asyncio.TimeoutError: pass
            
            if CURRENT_CONTROLLER == "recognition":
                # A. GESTURE
                if robot_cam.ai.mode == "gesture_recognition":
                    fingers = robot_cam.ai.gesture_data 
                    if fingers == 1: robot_motor.move(0.3, 0.0) 
                    elif fingers == 2: robot_motor.move(-0.3, 0.0)
                    elif fingers == 3: robot_motor.move(0.0, -0.4)
                    elif fingers == 4: robot_motor.move(0.0, 0.4)
                    elif fingers is not None and fingers >= 5: robot_motor.stop()
                    else: robot_motor.stop()

                # B. COLOR FOLLOW
                elif robot_cam.ai.mode == "color_detection":
                    if robot_cam.ai.object_found:
                        lost_counter = 0 
                        robot_extras.move_servo("pan", 0)
                        area = robot_cam.ai.track_area
                        TARGET_SIZE = 0.15 
                        
                        throttle = 0.0
                        if area < TARGET_SIZE: throttle = 0.35
                        elif area > (TARGET_SIZE + 0.1): throttle = -0.30
                        
                        steering = robot_cam.ai.track_error_x * 0.6
                        robot_motor.move(throttle, steering)
                    else:
                        # Search Mode
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


# 5. OBJECT DETECTION
@app.websocket("/ws/objectDetection")
async def ws_obj_detection(websocket: WebSocket):
    global CURRENT_CONTROLLER
    await websocket.accept()
    CURRENT_CONTROLLER = "detection"
    robot_cam.ai.set_mode("off") 
    print("[WS] DETECTION Connected")
    
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
    except Exception as e:
        print(f"[WS] Error: {e}")
    finally:
        robot_cam.ai.set_mode("off")


# 6. QR SCANNER (BLOCKING ACTIONS)
@app.websocket("/ws/qr")
async def ws_qr(websocket: WebSocket):
    global CURRENT_CONTROLLER
    await websocket.accept()
    CURRENT_CONTROLLER = "qr"
    robot_cam.ai.set_mode("off") 
    print("[WS] QR Connected")
    
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
            
            if CURRENT_CONTROLLER == "qr" and robot_cam.ai.mode == "qr_recognition":
                current_qr = robot_cam.ai.qr_data
                
                if current_qr is not None:
                    scan_text = current_qr.upper().strip()
                    print(f"[QR] EKSEKUSI: {scan_text}")
                    await websocket.send_text(json.dumps({"status": "active", "mode": f"CMD: {scan_text}"}))
                    
                    robot_extras.set_buzzer("on")
                    await asyncio.sleep(0.1)
                    robot_extras.set_buzzer("off")
                    
                    # --- MUSIC ACTIONS ---
                    duration = 0 
                    songs = {
                        "MERRY": "merry_christmas", "TWINKLE": "twinkle", "MARY": "mary_lamb",
                        "BALONKU": "balonku", "CICAK": "cicak", "PELANGI": "pelangi", "BIRTHDAY": "happy_birthday"
                    }
                    
                    for key, song in songs.items():
                        if key in scan_text:
                            duration = robot_extras.play_melody(song)
                            break

                    if duration > 0:
                        print(f"[QR] Playing song for {duration:.1f}s")
                        await asyncio.sleep(duration + 1.0)
                        robot_cam.ai.qr_data = None 
                        continue 

                    # --- MOVEMENT ACTIONS ---
                    if "KOTAK" in scan_text:
                        for _ in range(4):
                            robot_motor.move(0.5, 0.0) 
                            await asyncio.sleep(1.0)
                            robot_motor.stop()
                            await asyncio.sleep(0.2)
                            robot_motor.move(0.0, 0.6) 
                            await asyncio.sleep(0.6) 
                            robot_motor.stop()
                            await asyncio.sleep(0.2)
                            
                    elif "PUTAR" in scan_text:
                        robot_motor.move(0.0, 0.7) 
                        await asyncio.sleep(2.5)   
                        robot_motor.stop()

                    elif "MAJU" in scan_text:
                        robot_motor.move(0.5, 0.0)
                        await asyncio.sleep(2.0)
                        robot_motor.stop()
                    
                    elif "MUNDUR" in scan_text:
                        robot_motor.move(-0.5, 0.0)
                        await asyncio.sleep(2.0)
                        robot_motor.stop()

                    robot_cam.ai.qr_data = None
                    await asyncio.sleep(1.0)

            await asyncio.sleep(0.1)
            
    except Exception as e:
        print(f"[QR] Error: {e}")
    finally:
        robot_motor.stop()
        robot_extras.set_buzzer("off")
        robot_cam.ai.set_mode("off")


# 7. OBSTACLE AVOIDANCE (FIX: START IN STANDBY)
@app.websocket("/ws/avoid")
async def ws_avoid(websocket: WebSocket):
    global CURRENT_CONTROLLER
    await websocket.accept()
    CURRENT_CONTROLLER = "avoid"
    
    robot_cam.ai.set_mode("off")
    print("[WS] AVOID Connected - STANDBY FIRST")
    
    # --- SHARED DATA ---
    sensor_data = {"dist": 100.0, "panic": False}
    
    # --- CONFIG ---
    SPEED_MAJU    = 0.05
    SPEED_MUNDUR  = -0.60 
    SPEED_PUTAR   = 0.40
    
    ZONA_KRITIS   = 10  
    ZONA_BREAK    = 15  
    SYARAT_JALAN  = 30  
    
    MAX_RETREAT_TIME = 0.5  
    TIME_SCAN_TURN   = 0.8 
    TIME_STABIL      = 0.5

    # [PERBAIKAN 1] State awal adalah IDLE (Diam), bukan FORWARD
    state = "IDLE"
    current_mode = "standby" # Melacak pilihan user (standby/avoid_hcsr/avoid_hybrid)
    retreat_locked = False
    
    state_ts = time.monotonic()
    dist_left = 0
    dist_right = 0
    active_mask = [1, 1, 1, 1, 1] # Untuk mode hybrid
    
    # --- SENSOR TASK ---
    async def sensor_loop():
        ALPHA = 0.6 
        while True:
            try:
                raw = robot_sensors.get_distance()
                if 0 <= raw < 400: 
                    sensor_data["dist"] = (sensor_data["dist"] * (1-ALPHA)) + (raw * ALPHA)
                    robot_cam.ai.update_distance(sensor_data["dist"])
                
                sensor_data["panic"] = robot_sensors.check_panic()
                await asyncio.sleep(0.04)
            except: pass

    sensor_task = asyncio.create_task(sensor_loop())

    try:
        while True:
            # 1. INPUT HANDLING
            try:
                data = await asyncio.wait_for(websocket.receive_text(), timeout=0.01)
                payload = json.loads(data)
                cmd = payload.get("cmd")
                
                if cmd == "set_ai_mode":
                    mode = payload.get("mode") # "standby", "avoid_hcsr", "avoid_hybrid"
                    current_mode = mode
                    
                    if mode == "standby":
                        state = "IDLE"
                        robot_motor.stop()
                        msg = "MODE: STANDBY"
                    else:
                        # [PERBAIKAN 2] Baru mulai jalan (FORWARD) jika mode dipilih
                        state = "FORWARD"
                        retreat_locked = False
                        
                        if mode == "avoid_hybrid":
                            cfg = payload.get("config", {})
                            active_mask = [1 if cfg.get(k, True) else 0 for k in ["ll","l","m","r","rr"]]
                            msg = "MODE: HYBRID START"
                        else:
                            msg = "MODE: AVOID START"
                            
                    await websocket.send_text(json.dumps({"status": "active", "mode": msg}))
                    
            except asyncio.TimeoutError: pass

            # 2. LOGIKA UTAMA (Hanya jalan jika BUKAN STANDBY)
            if CURRENT_CONTROLLER == "avoid" and current_mode != "standby":
                
                distance = sensor_data["dist"]
                is_panic = sensor_data["panic"]
                now = time.monotonic()
                elapsed = now - state_ts

                # ====================================================
                # PRIORITAS 1: SENSOR BFD (LOCKING)
                # ====================================================
                if is_panic and not retreat_locked:
                    print("[PRIORITY] BFD TRIGGERED! Locking Retreat.")
                    robot_motor.stop()
                    await asyncio.sleep(0.1)
                    retreat_locked = True
                    state = "RETREAT"
                    state_ts = now 
                    continue 

                # ====================================================
                # STATE MACHINE
                # ====================================================

                # 0. IDLE (Safety State)
                if state == "IDLE":
                    robot_motor.stop()

                # 1. FORWARD
                elif state == "FORWARD":
                    if distance < ZONA_KRITIS:
                        if not retreat_locked:
                            robot_motor.stop()
                            state = "RETREAT"
                            state_ts = now 
                    elif distance <= ZONA_BREAK:
                        print(f"[FWD] Break Zone {distance:.1f}cm. Stop & Scan.")
                        robot_motor.stop()
                        state = "SCAN_INIT" 
                    else:
                        # LOGIKA GERAK MAJU (Beda antara Pure Avoid & Hybrid)
                        if current_mode == "avoid_hcsr":
                            robot_motor.move(SPEED_MAJU, 0.0)
                        elif current_mode == "avoid_hybrid":
                            # Simple Line Follower Logic
                            raw_lines = robot_sensors.get_line_status()
                            lines = [r & m for r, m in zip(raw_lines, active_mask)]
                            if sum(lines) == 0: robot_motor.stop()
                            elif lines[2]: robot_motor.move(0.15, 0.0)
                            elif lines[1]: robot_motor.move(0.12, -0.3)
                            elif lines[3]: robot_motor.move(0.12, 0.3)
                            elif lines[0]: robot_motor.move(0.10, -0.5)
                            elif lines[4]: robot_motor.move(0.10, 0.5)

                # 2. RETREAT (FAILSAFE)
                elif state == "RETREAT":
                    succes_condition = distance >= ZONA_BREAK
                    timeout_condition = elapsed > MAX_RETREAT_TIME 
                    
                    if succes_condition:
                        print(f"[RETREAT] Target Tercapai ({distance:.1f}cm). Stop.")
                        robot_motor.stop()
                        state = "SCAN_INIT"
                    elif timeout_condition:
                        print(f"[RETREAT] TIMEOUT 0.5s. Force Stop.")
                        robot_motor.stop()
                        state = "SCAN_INIT" 
                    else:
                        robot_motor.move(SPEED_MUNDUR, 0.0)

                # 3. SCANNING SEQUENCE
                elif state == "SCAN_INIT":
                    state = "SCAN_LEFT_MOVE"
                    state_ts = now
                
                elif state == "SCAN_LEFT_MOVE":
                    robot_motor.move(0.0, -SPEED_PUTAR)
                    if elapsed > TIME_SCAN_TURN:
                        robot_motor.stop()
                        state = "SCAN_LEFT_READ"
                        state_ts = now
                
                elif state == "SCAN_LEFT_READ":
                    if elapsed > TIME_STABIL:
                        dist_left = distance
                        print(f"[SCAN] Kiri: {dist_left:.1f} cm")
                        state = "SCAN_RIGHT_MOVE"
                        state_ts = now

                elif state == "SCAN_RIGHT_MOVE":
                    robot_motor.move(0.0, SPEED_PUTAR)
                    if elapsed > (TIME_SCAN_TURN * 2.2):
                        robot_motor.stop()
                        state = "SCAN_RIGHT_READ"
                        state_ts = now

                elif state == "SCAN_RIGHT_READ":
                    if elapsed > TIME_STABIL:
                        dist_right = distance
                        print(f"[SCAN] Kanan: {dist_right:.1f} cm")
                        
                        target_dir = "NONE"
                        if dist_left >= SYARAT_JALAN and dist_right >= SYARAT_JALAN:
                            target_dir = "LEFT" if dist_left > dist_right else "RIGHT"
                        elif dist_left >= SYARAT_JALAN:
                            target_dir = "LEFT"
                        elif dist_right >= SYARAT_JALAN:
                            target_dir = "RIGHT"
                        
                        if target_dir != "NONE":
                            print(f"[DECIDE] {target_dir}")
                            state = "TURN_TO_LEFT" if target_dir == "LEFT" else "TURN_TO_RIGHT"
                        else:
                            print("[DECIDE] Buntu.")
                            state = "DEAD_END"
                        state_ts = now

                # 4. TURN & EXECUTE
                elif state == "TURN_TO_LEFT":
                    robot_motor.move(0.0, -SPEED_PUTAR)
                    if elapsed > (TIME_SCAN_TURN * 2.2): 
                        robot_motor.stop()
                        state = "RESET_AND_GO"
                
                elif state == "TURN_TO_RIGHT":
                    robot_motor.stop()
                    state = "RESET_AND_GO"

                # 5. RESET LOCK
                elif state == "RESET_AND_GO":
                    retreat_locked = False 
                    state = "FORWARD"

                # 6. DEAD END
                elif state == "DEAD_END":
                    robot_extras.set_buzzer("on")
                    if elapsed > 3.0:
                        robot_extras.set_buzzer("off")
                        state = "SCAN_INIT" 
                        state_ts = now

            else:
                # [PERBAIKAN 3] Jika mode == standby, pastikan motor mati
                robot_motor.stop()
            
            await asyncio.sleep(0.01)

    except Exception as e:
        print(f"[AVOID] Error: {e}")
    finally:
        sensor_task.cancel()
        robot_motor.stop()
        robot_cam.ai.update_distance(None)

# ==============================================================================
# HTTP ENDPOINTS & RUNNER
# ==============================================================================

@app.get("/")
def index(): 
    return {"status": "Raspbot RTKAv2", "controller": CURRENT_CONTROLLER}

@app.get("/video_feed")
def video_feed(): 
    return StreamingResponse(robot_cam.generate_frames(), media_type="multipart/x-mixed-replace;boundary=frame")

if __name__ == "__main__":
    uvicorn.run(app, host=HOST, port=PORT, log_level="warning")