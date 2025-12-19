#!/home/pi/RTKAv2/venv/bin/python3
import os
import sys
import uvicorn
import json
import asyncio
import math # <--- PENTING: Untuk gerakan gelombang servo
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware

from config import HOST, PORT
from modules.motor import MotorDriver
from modules.camera import VideoStreamer
from modules.extras import ExtraDrivers

os.environ["OPENCV_LOG_LEVEL"] = "FATAL"
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

robot_motor = MotorDriver(simulation=False) 
robot_cam = VideoStreamer()
robot_extras = ExtraDrivers()
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

    # KIRIM STATUS KE UI AGAR TAHU KITA SEDANG STANDBY
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
                # ... (Logika Servo PID sama seperti sebelumnya) ...
                error_x = robot_cam.ai.track_error_x 
                error_y = robot_cam.ai.track_error_y 
                
                pan_speed = 3.0  
                tilt_speed = 3.0 
                
                if abs(error_x) > 0.1: pan_pos -= (error_x * pan_speed)
                if abs(error_y) > 0.1: tilt_pos += (error_y * tilt_speed) 

                pan_pos = max(-90, min(90, pan_pos))
                tilt_pos = max(-90, min(90, tilt_pos))
                
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
    print("[WS] DETECTION HUB: Connected (Standby)")
    try:
        while True:
            data = await websocket.receive_text()
            payload = json.loads(data)
            await handle_ai_switch(websocket, payload)
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
            await asyncio.sleep(0.1)
    except: pass

# 7. AVOID & FOLLOW
@app.websocket("/ws/avoid")
async def ws_avoid(websocket: WebSocket):
    global CURRENT_CONTROLLER
    await websocket.accept()
    CURRENT_CONTROLLER = "avoid"
    robot_cam.ai.set_mode("off")
    print("[WS] AVOID Connected (Standby)")
    try:
        while True:
            try:
                data = await asyncio.wait_for(websocket.receive_text(), timeout=0.05)
                payload = json.loads(data)
                if payload.get("cmd") == "set_ai_mode":
                    mode = payload.get("mode")
                    await websocket.send_text(json.dumps({"status": "active", "mode": mode}))
            except asyncio.TimeoutError: pass
            await asyncio.sleep(0.1)
    except: pass

@app.get("/")
def index(): return {"status": "Raspbot RTKAv2", "controller": CURRENT_CONTROLLER}

@app.get("/video_feed")
def video_feed(): return StreamingResponse(robot_cam.generate_frames(), media_type="multipart/x-mixed-replace;boundary=frame")

if __name__ == "__main__":
    uvicorn.run(app, host=HOST, port=PORT, log_level="warning")