#!/usr/bin/env python3
import os
import sys
import json
import time
import asyncio
import logging

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# =========================================================
# CONFIG INLINE (TRAINER KIT)
# =========================================================

HOST = "0.0.0.0"
PORT = 8000

# --- CAMERA ---
VIDEO_SOURCE = -1
FRAME_WIDTH = 640
FRAME_HEIGHT = 480

# --- SERVO (HW PWM) ---
PIN_SERVO_PAN  = 12
PIN_SERVO_TILT = 13

SERVO_MIN = -90
SERVO_MAX = 90

# --- TRACKING PARAM ---
SAFEZONE_X = 0.15
SAFEZONE_Y = 0.15
FOV_PAN  = 15.0
FOV_TILT = 10.0
MIN_STEP = 2.0

# --- FACE FILTER ---
MIN_FACE_RATIO = 0.02   # terlalu kecil = noise
MAX_FACE_RATIO = 0.60   # terlalu besar = bukan wajah normal
CONFIRM_FRAMES = 3      # harus muncul berturut-turut

# =========================================================
# LOGGING
# =========================================================

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("trainer-face-final")

os.environ["OPENCV_LOG_LEVEL"] = "FATAL"
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"

# =========================================================
# SERVO DRIVER
# =========================================================

from rpi_hardware_pwm import HardwarePWM

class ServoDriver:
    def __init__(self):
        self.pan = HardwarePWM(0, hz=50)
        self.tilt = HardwarePWM(1, hz=50)
        self.pan.start(0)
        self.tilt.start(0)

        self.pan_pos = 0.0
        self.tilt_pos = 0.0

    def _angle_to_duty(self, angle):
        angle = max(SERVO_MIN, min(SERVO_MAX, angle))
        return 7.5 + (angle / 90.0) * 5.0

    def move(self, axis, delta):
        if axis == "pan":
            self.pan_pos += delta
            self.pan_pos = max(SERVO_MIN, min(SERVO_MAX, self.pan_pos))
            self.pan.change_duty_cycle(self._angle_to_duty(self.pan_pos))
            time.sleep(0.12)
            self.pan.change_duty_cycle(0)

        elif axis == "tilt":
            self.tilt_pos += delta
            self.tilt_pos = max(SERVO_MIN, min(SERVO_MAX, self.tilt_pos))
            self.tilt.change_duty_cycle(self._angle_to_duty(self.tilt_pos))
            time.sleep(0.12)
            self.tilt.change_duty_cycle(0)

    def reset(self):
        self.pan_pos = 0
        self.tilt_pos = 0
        self.pan.change_duty_cycle(self._angle_to_duty(0))
        self.tilt.change_duty_cycle(self._angle_to_duty(0))
        time.sleep(0.3)
        self.pan.change_duty_cycle(0)
        self.tilt.change_duty_cycle(0)

# =========================================================
# AI PROCESSOR (ANTI FALSE POSITIVE)
# =========================================================

import cv2
import mediapipe as mp

class AIProcessor:
    def __init__(self):
        self.mode = "face_tracking"

        self.face = mp.solutions.face_detection.FaceDetection(
            model_selection=1,
            min_detection_confidence=0.75
        )

        self.error_x = 0.0
        self.error_y = 0.0
        self.found = False

        self.confirm_count = 0

    def process_frame(self, frame):
        self.error_x = 0.0
        self.error_y = 0.0
        self.found = False

        h, w, _ = frame.shape
        cx, cy = w // 2, h // 2

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        res = self.face.process(rgb)

        if res.detections:
            det = res.detections[0]
            box = det.location_data.relative_bounding_box

            x = int(box.xmin * w)
            y = int(box.ymin * h)
            bw = int(box.width * w)
            bh = int(box.height * h)

            face_area = bw * bh
            frame_area = w * h
            ratio = face_area / frame_area

            # FILTER AREA
            if MIN_FACE_RATIO <= ratio <= MAX_FACE_RATIO:
                self.confirm_count += 1
            else:
                self.confirm_count = 0

            # CONFIRM FACE
            if self.confirm_count >= CONFIRM_FRAMES:
                fx = x + bw // 2
                fy = y + bh // 2

                self.error_x = (fx - cx) / cx
                self.error_y = (fy - cy) / cy
                self.found = True

                cv2.rectangle(frame, (x,y), (x+bw,y+bh), (0,255,255), 2)
        else:
            self.confirm_count = 0

        # SAFEZONE
        zx = int(w * SAFEZONE_X)
        zy = int(h * SAFEZONE_Y)
        cv2.rectangle(frame, (cx-zx, cy-zy), (cx+zx, cy+zy), (255,255,0), 1)

        # CROSSHAIR
        cv2.line(frame, (cx-10,cy),(cx+10,cy),(0,0,255),1)
        cv2.line(frame, (cx,cy-10),(cx,cy+10),(0,0,255),1)

        # HUD
        cv2.rectangle(frame, (5,5), (300,90), (0,0,0), -1)
        cv2.putText(frame, "AI MODE: FACE TRACK (STABLE)",
                    (10,30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,255,0), 2)
        cv2.putText(frame,
                    f"ERR X:{self.error_x:+.2f} Y:{self.error_y:+.2f}",
                    (10,65),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,255,255), 2)

        return frame

# =========================================================
# CAMERA
# =========================================================

class VideoStreamer:
    def __init__(self):
        self.cap = cv2.VideoCapture(VIDEO_SOURCE, cv2.CAP_V4L2)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_WIDTH)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)
        self.cap.set(cv2.CAP_PROP_FPS, 30)
        self.ai = AIProcessor()

    def generate_frames(self):
        while True:
            ret, frame = self.cap.read()
            if not ret:
                continue

            frame = cv2.resize(frame, (FRAME_WIDTH, FRAME_HEIGHT))
            frame = self.ai.process_frame(frame)

            ok, buf = cv2.imencode(".jpg", frame, [int(cv2.IMWRITE_JPEG_QUALITY), 60])
            if not ok:
                continue

            yield (
                b"--frame\r\n"
                b"Content-Type: image/jpeg\r\n\r\n"
                + buf.tobytes()
                + b"\r\n"
            )

# =========================================================
# FASTAPI
# =========================================================

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

servo = ServoDriver()
camera = VideoStreamer()

TRACKING = False

# =========================================================
# VIDEO FEED
# =========================================================

@app.get("/video_feed")
def video_feed():
    return StreamingResponse(
        camera.generate_frames(),
        media_type="multipart/x-mixed-replace;boundary=frame"
    )

# =========================================================
# WEBSOCKET /ws/tracking
# =========================================================

@app.websocket("/ws/tracking")
async def ws_tracking(ws: WebSocket):
    global TRACKING
    await ws.accept()
    logger.info("FACE TRACKING CONNECTED")

    try:
        while True:
            try:
                msg = await asyncio.wait_for(ws.receive_text(), timeout=0.05)
                data = json.loads(msg)
                if data.get("cmd") == "set_ai_mode":
                    if data.get("mode") == "face_track":
                        TRACKING = True
                    elif data.get("mode") == "none":
                        TRACKING = False
                        servo.reset()
            except asyncio.TimeoutError:
                pass

            if TRACKING and camera.ai.found:
                ex = camera.ai.error_x
                ey = camera.ai.error_y

                if abs(ex) > SAFEZONE_X:
                    dp = -ex * FOV_PAN
                    if abs(dp) >= MIN_STEP:
                        await asyncio.to_thread(servo.move, "pan", dp)

                if abs(ey) > SAFEZONE_Y:
                    dt = ey * FOV_TILT
                    if abs(dt) >= MIN_STEP:
                        await asyncio.to_thread(servo.move, "tilt", dt)

            await asyncio.sleep(0.05)

    except WebSocketDisconnect:
        pass
    finally:
        TRACKING = False
        servo.reset()
        logger.info("FACE TRACKING DISCONNECTED")

# =========================================================
# MAIN
# =========================================================

if __name__ == "__main__":
    uvicorn.run(app, host=HOST, port=PORT, log_level="warning")
