# main.py
import uvicorn
import json
import asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware

from config import HOST, PORT
from modules.motor import MotorDriver
from modules.camera import VideoStreamer

app = FastAPI()

app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"]
)

# Set simulation=True jika belum colok driver motor
robot_motor = MotorDriver(simulation=True) 
robot_cam = VideoStreamer()

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
            # 1. Handle Command dari Android
            try:
                data = await asyncio.wait_for(websocket.receive_text(), timeout=0.1)
                payload = json.loads(data)
                cmd = payload.get("cmd")

                if cmd == "move":
                    # Manual Control
                    robot_motor.move(
                        float(payload.get("y", 0)), 
                        float(payload.get("x", 0)), 
                        float(payload.get("speed", 100))
                    )
                
                elif cmd == "ai_mode":
                    # Ganti Mode AI
                    mode = payload.get("mode", "off")
                    robot_cam.ai.set_mode(mode)

                elif cmd == "stop":
                    robot_motor.stop()
                    
            except asyncio.TimeoutError:
                # Tidak ada data baru, lanjut ke logic tracking
                pass
            except Exception as e:
                # print(f"Error: {e}") 
                pass

            # 2. Logic AUTO-PILOT (Tracking)
            # Jika mode Tracking aktif & Objek ditemukan, override manual control
            if robot_cam.ai.mode in ["target_tracking", "face_detection"] and robot_cam.ai.object_found:
                
                error_x = robot_cam.ai.track_error_x # -1.0 (Kiri) ... 1.0 (Kanan)
                
                # Proportional Controller (P-Control)
                Kp = 0.6 # Konstanta sensitivitas
                steering_adjust = error_x * Kp
                
                # Robot berputar mengikuti wajah/objek
                # Speed dibatasi 40% saat tracking agar tidak overshoot
                robot_motor.move(0.0, steering_adjust, speed_limit=40)

            # Heartbeat loop
            await asyncio.sleep(0.01)

    except WebSocketDisconnect:
        print("[WS] Disconnected")
        robot_motor.stop()

if __name__ == "__main__":
    uvicorn.run(app, host=HOST, port=PORT)
