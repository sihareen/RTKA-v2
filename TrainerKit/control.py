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

# --- MOTOR PIN ---
PIN_FL_FWD = 17
PIN_FL_BWD = 27
PIN_RL_FWD = 22
PIN_RL_BWD = 23

PIN_FR_FWD = 24
PIN_FR_BWD = 25
PIN_RR_FWD = 5
PIN_RR_BWD = 6

MIN_PWM = 0.40

# --- SERVO / BUZZER / LED ---
PIN_SERVO_PAN = 12
PIN_SERVO_TILT = 13
PIN_BUZZER = 16

PIN_LED_R = 7
PIN_LED_Y = 8
PIN_LED_G = 9

# =========================================================
# LOGGING
# =========================================================

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("trainer-control")

os.environ["OPENCV_LOG_LEVEL"] = "FATAL"
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"

# =========================================================
# HARDWARE DRIVER (INLINE)
# =========================================================

from gpiozero import Motor, LED, PWMOutputDevice
from rpi_hardware_pwm import HardwarePWM

class MotorDriver:
    def __init__(self):
        self.motor_FL = Motor(PIN_FL_FWD, PIN_FL_BWD)
        self.motor_RL = Motor(PIN_RL_FWD, PIN_RL_BWD)
        self.motor_FR = Motor(PIN_FR_FWD, PIN_FR_BWD)
        self.motor_RR = Motor(PIN_RR_FWD, PIN_RR_BWD)

    def _map(self, v):
        if abs(v) < 0.05:
            return 0.0
        sign = 1 if v > 0 else -1
        v = abs(v)
        return sign * (MIN_PWM + v * (1.0 - MIN_PWM))

    def move(self, throttle, steering, speed=100):
        l = throttle + steering
        r = throttle - steering

        l = max(-1, min(1, l)) * (speed / 100)
        r = max(-1, min(1, r)) * (speed / 100)

        self.motor_FL.value = self._map(l)
        self.motor_RL.value = self._map(l)
        self.motor_FR.value = self._map(r)
        self.motor_RR.value = self._map(r)

    def stop(self):
        for m in (self.motor_FL, self.motor_RL, self.motor_FR, self.motor_RR):
            m.stop()


class Extras:
    def __init__(self):
        self.buzzer = PWMOutputDevice(PIN_BUZZER, frequency=2000)

        self.led_r = LED(PIN_LED_R)
        self.led_y = LED(PIN_LED_Y)
        self.led_g = LED(PIN_LED_G)

        self.pwm_pan = HardwarePWM(0, hz=50)
        self.pwm_tilt = HardwarePWM(1, hz=50)
        self.pwm_pan.start(0)
        self.pwm_tilt.start(0)

    def servo(self, typ, angle):
        angle = max(-90, min(90, int(angle)))
        duty = 7.5 + (angle / 90.0) * 5.0
        pwm = self.pwm_pan if typ == "pan" else self.pwm_tilt
        pwm.change_duty_cycle(duty)
        time.sleep(0.15)
        pwm.change_duty_cycle(0)

    def buzzer_set(self, state):
        if state == "on":
            self.buzzer.value = 0.5
        else:
            self.buzzer.off()

    def led(self, color, state):
        target = {"r": self.led_r, "y": self.led_y, "g": self.led_g}.get(color)
        if target:
            target.on() if state == "on" else target.off()


# =========================================================
# CAMERA + AI (WAJIB ADA)
# =========================================================


import cv2
import numpy as np

class AIProcessor:
    """
    AI MINIMAL – TRAINER KIT
    - Tidak melakukan detection
    - Hanya display crosshair + safezone
    """

    def __init__(self):
        self.mode = "off"

    def set_mode(self, mode):
        self.mode = mode

    def process_frame(self, frame):
        h, w, _ = frame.shape
        cx, cy = w // 2, h // 2


        # --- MODE TEXT ---
        cv2.putText(
            frame,
            f"AI MODE: {self.mode.upper()}",
            (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 255, 0),
            2
        )

        return frame

class VideoStreamer:
    def __init__(self):
        self.cap = cv2.VideoCapture(VIDEO_SOURCE, cv2.CAP_V4L2)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_WIDTH)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)
        self.cap.set(cv2.CAP_PROP_FPS, 30)

        self.ai = AIProcessor()
        self.ai.set_mode("off")  # CONTROL MODE = AI OFF

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

motor = MotorDriver()
extras = Extras()
camera = VideoStreamer()

# =========================================================
# VIDEO FEED (WAJIB ADA)
# =========================================================

@app.get("/video_feed")
def video_feed():
    return StreamingResponse(
        camera.generate_frames(),
        media_type="multipart/x-mixed-replace;boundary=frame"
    )

# =========================================================
# WEBSOCKET: /ws/control
# =========================================================

@app.websocket("/ws/control")
async def ws_control(ws: WebSocket):
    await ws.accept()
    logger.info("CONTROL CONNECTED")

    try:
        while True:
            msg = await ws.receive_text()
            data = json.loads(msg)
            cmd = data.get("cmd")

            if cmd == "move":
                motor.move(
                    float(data.get("y", 0)),
                    float(data.get("x", 0)),
                    int(data.get("speed", 100))
                )

            elif cmd == "stop":
                motor.stop()

            elif cmd == "servo":
                await asyncio.to_thread(
                    extras.servo,
                    data.get("type"),
                    data.get("angle", 0)
                )

            elif cmd == "buzzer":
                extras.buzzer_set(data.get("state"))

            elif cmd == "led":
                extras.led(data.get("color"), data.get("state"))

    except WebSocketDisconnect:
        pass
    finally:
        motor.stop()
        extras.buzzer_set("off")
        logger.info("CONTROL DISCONNECTED")


# =========================================================
# MAIN
# =========================================================

if __name__ == "__main__":
    uvicorn.run(app, host=HOST, port=PORT, log_level="warning")
