import uvicorn
import subprocess
import os
import signal
import sys
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

# --- KONFIGURASI ---
# Path ke Python di virtual environment Anda
VENV_PYTHON = "/home/pi/RTKAv2/venv/bin/python3"
# Path ke script main.py Anda
MAIN_SCRIPT = "/home/pi/RTKAv2/main.py"
# Port untuk Manager (BEDA dengan Port Robot)
MANAGER_PORT = 5000 

app = FastAPI()

# Variabel untuk menyimpan proses main.py
robot_process = None

# Model Data sesuai Request Anda
class CommandRequest(BaseModel):
    cmd: str
    mode: str

@app.post("/")
def handle_command(req: CommandRequest):
    global robot_process

    # Validasi cmd
    if req.cmd != "command":
        raise HTTPException(status_code=400, detail="Command tidak dikenal")

    # --- LOGIKA START ---
    if req.mode == "start":
        if robot_process is None or robot_process.poll() is not None:
            # Jalankan main.py sebagai subprocess
            # cwd="/home/pi/RTKAv2" penting agar aset tflite terbaca
            robot_process = subprocess.Popen(
                [VENV_PYTHON, MAIN_SCRIPT], 
                cwd="/home/pi/RTKAv2" 
            )
            return {"status": "success", "message": "Raspbot Started (PID: {})".format(robot_process.pid)}
        else:
            return {"status": "warning", "message": "Raspbot is already running"}

    # --- LOGIKA STOP (Force Close) ---
    elif req.mode == "stop":
        if robot_process and robot_process.poll() is None:
            # Kirim sinyal terminate
            robot_process.terminate()
            try:
                # Tunggu max 5 detik, kalau bandel kill paksa
                robot_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                robot_process.kill()
            
            robot_process = None
            return {"status": "success", "message": "Raspbot Stopped"}
        else:
            return {"status": "warning", "message": "Raspbot is not running"}

    # --- LOGIKA RESET (Reboot Pi) ---
    elif req.mode == "reset":
        # Perintah reboot sistem
        os.system("sudo reboot")
        return {"status": "success", "message": "Rebooting System..."}

    else:
        raise HTTPException(status_code=400, detail="Mode tidak dikenal")

if __name__ == "__main__":
    print(f"Manager Service running at Port {MANAGER_PORT}")
    uvicorn.run(app, host="0.0.0.0", port=MANAGER_PORT)
