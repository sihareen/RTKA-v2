import lgpio
import time
import csv
from datetime import datetime

# ======================
# CONFIG
# ======================
GPIO_CHIP = 0
SERVO_PIN = 12
FREQ = 50              # 50Hz servo
PERIOD_US = 20000
US_START = 500
US_END = 2500
US_STEP = 100
DELAY = 0.09
LOG_FILE = "servo_lgpio_log.csv"

# ======================
# INIT
# ======================
h = lgpio.gpiochip_open(GPIO_CHIP)
lgpio.gpio_claim_output(h, SERVO_PIN)

def writeMicroseconds(us):
    duty_cycle = (us / PERIOD_US) * 100.0
    lgpio.tx_pwm(h, SERVO_PIN, FREQ, duty_cycle)

# ======================
# LOG FILE
# ======================
with open(LOG_FILE, "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["timestamp", "pulse_us", "delta_us"])

print("[INFO] LGPIO Servo Test START")

# ======================
# MAIN LOOP
# ======================
for us in range(US_START, US_END + 1, US_STEP):
    writeMicroseconds(us)

    ts = datetime.now().isoformat(timespec="milliseconds")
    delta = us - 1500

    print(f"{ts} | {us} us | Δ {delta:+}")

    with open(LOG_FILE, "a", newline="") as f:
        csv.writer(f).writerow([ts, us, delta])

    time.sleep(DELAY)

# ======================
# STOP
# ======================
lgpio.tx_pwm(h, SERVO_PIN, 0, 0)
lgpio.gpiochip_close(h)

print("[INFO] FINISHED")
print(f"[INFO] Log saved: {LOG_FILE}")
