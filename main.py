#!/home/pi/RTKAv2/venv/bin/python3
import os
import sys

# --- SUPPRESS LOGS (HAPUS WARNING SAMPAH) ---
os.environ["OPENCV_LOG_LEVEL"] = "FATAL"    # Hapus [WARN:0] dari OpenCV
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"    # Hapus log TensorFlow
os.environ["GLOG_minloglevel"] = "3"        # Hapus log MediaPipe

# Import Library Standar
import uvicorn
import json
import asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware

# Import Config & Modules
from config import HOST, PORT
from modules.motor import MotorDriver
from modules.camera import VideoStreamer
from modules.extras import ExtraDrivers  # <--- [BARU] Import Module Extras

# Inisialisasi App
app = FastAPI()

app.add_middleware(
    CORSMiddleware, 
    allow_origins=["*"], 
    allow_methods=["*"], 
    allow_headers=["*"]
)

# --- HARDWARE INIT ---
robot_motor = MotorDriver(simulation=False) 
robot_cam = VideoStreamer()
robot_extras = ExtraDrivers()  # <--- [BARU] Inisialisasi Servo & Buzzer

@app.get("/")
def index():
    return {"status": "Raspbot Online", "mode": robot_cam.ai.mode}

@app.get("/video_feed")
def video_feed():
    return StreamingResponse(robot_cam.generate_frames(), 
                             media_type="multipart/x-mixed-replace;boundary=frame")

@app.websocket("/ws/control")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    print("[WS] Client Connected")
    
    try:
        while True:
            try:
                # Tunggu data masuk (Timeout 0.1s agar loop tracking tetap jalan)
                data = await asyncio.wait_for(websocket.receive_text(), timeout=0.1)
                payload = json.loads(data)
                cmd = payload.get("cmd")

                # --- 1. KONTROL MOTOR ---
                if cmd == "move":
                    robot_motor.move(
                        float(payload.get("y", 0)), 
                        float(payload.get("x", 0)), 
                        float(payload.get("speed", 100))
                    )
                
                # --- 2. KONTROL SERVO [BARU] ---
                elif cmd == "servo":
                    # type: "pan" (geleng) atau "tilt" (angguk)
                    # angle: -90 s/d 90
                    s_type = payload.get("type")
                    s_angle = payload.get("angle", 0)
                    robot_extras.move_servo(s_type, s_angle)

                # --- 3. KONTROL BUZZER [BARU] ---
                elif cmd == "buzzer":
                    # state: "on", "off", atau "beep"
                    state = payload.get("state", "off")
                    robot_extras.set_buzzer(state)

                # --- 4. GANTI MODE AI ---
                elif cmd == "ai_mode":
                    mode = payload.get("mode", "off")
                    robot_cam.ai.set_mode(mode)
                    robot_motor.stop() # Safety stop saat ganti mode

                # --- 5. STOP ---
                elif cmd == "stop":
                    robot_motor.stop()
                    robot_extras.set_buzzer("off") # Matikan buzzer juga biar ga berisik

            except asyncio.TimeoutError:
                pass
            
            except WebSocketDisconnect:
                print("[WS] Client Disconnected (Normal)")
                break 
            
            except Exception as e:
                if "disconnect message" not in str(e):
                    print(f"[WS] Socket Error: {e}")
                break

            # --- LOGIC AUTO-PILOT (AI TRACKING) ---
            ai_mode = robot_cam.ai.mode
            
            # Tracking Wajah / Warna
            if ai_mode in ["face_detection", "color_detection"] and robot_cam.ai.object_found:
                error_x = robot_cam.ai.track_error_x 
                Kp = 0.6 
                steering_adjust = error_x * Kp
                robot_motor.move(0.0, steering_adjust, speed_limit=40)
            
            # Gesture Stop
            elif ai_mode == "gesture_recognition" and robot_cam.ai.track_error_x == 0 and robot_cam.ai.object_found:
                 robot_motor.stop()
                 # Opsional: Bunyi beep sekali saat gesture STOP terdeteksi
                 # robot_extras.set_buzzer("beep") 

            await asyncio.sleep(0.01)

    except Exception as e:
        print(f"[WS] Critical Loop Error: {e}")
    
    finally:
        print("[WS] Cleaning up connection...")
        robot_motor.stop()
        robot_extras.set_buzzer("off") # Pastikan buzzer mati saat koneksi putus

if __name__ == "__main__":
    print(f"Server starting at http://{HOST}:{PORT}")
    uvicorn.run(app, host=HOST, port=PORT, log_level="warning")