# main.py
import os
import sys

# --- SUPPRESS LOGS (HAPUS WARNING SAMPAH) ---
# Lakukan ini SEBELUM import cv2 / mediapipe / tensorflow
os.environ["OPENCV_LOG_LEVEL"] = "FATAL"    # Hapus [WARN:0] dari OpenCV
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"    # Hapus log TensorFlow
os.environ["GLOG_minloglevel"] = "3"        # Hapus W0000 dari MediaPipe (0=INFO, 1=WARN, 2=ERROR, 3=FATAL)

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

# Inisialisasi App
app = FastAPI()

app.add_middleware(
    CORSMiddleware, 
    allow_origins=["*"], 
    allow_methods=["*"], 
    allow_headers=["*"]
)

# --- HARDWARE INIT ---
robot_motor = MotorDriver(simulation=False) #true untuk mode simulasi tanpa hardware
robot_cam = VideoStreamer()

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
                data = await asyncio.wait_for(websocket.receive_text(), timeout=0.1)
                payload = json.loads(data)
                cmd = payload.get("cmd")

                if cmd == "move":
                    robot_motor.move(
                        float(payload.get("y", 0)), 
                        float(payload.get("x", 0)), 
                        float(payload.get("speed", 100))
                    )
                
                elif cmd == "ai_mode":
                    mode = payload.get("mode", "off")
                    robot_cam.ai.set_mode(mode)
                    robot_motor.stop()

                elif cmd == "stop":
                    robot_motor.stop()

            except asyncio.TimeoutError:
                pass
            
            except WebSocketDisconnect:
                print("[WS] Client Disconnected (Normal)")
                break 
            
            except Exception as e:
                # Kita filter error kecil agar log tidak penuh
                if "disconnect message" not in str(e):
                    print(f"[WS] Socket Error: {e}")
                break

            # LOGIC AUTO-PILOT
            ai_mode = robot_cam.ai.mode
            if ai_mode in ["face_detection", "color_detection"] and robot_cam.ai.object_found:
                error_x = robot_cam.ai.track_error_x 
                Kp = 0.6 
                steering_adjust = error_x * Kp
                robot_motor.move(0.0, steering_adjust, speed_limit=40)
            
            elif ai_mode == "gesture_recognition" and robot_cam.ai.track_error_x == 0 and robot_cam.ai.object_found:
                 robot_motor.stop()

            await asyncio.sleep(0.01)

    except Exception as e:
        print(f"[WS] Critical Loop Error: {e}")
    
    finally:
        print("[WS] Cleaning up connection...")
        robot_motor.stop()

if __name__ == "__main__":
    print(f"Server starting at http://{HOST}:{PORT}")
    # Matikan log akses server (GET /video_feed...) agar tidak spamming
    uvicorn.run(app, host=HOST, port=PORT, log_level="warning")