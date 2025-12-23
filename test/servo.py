from sshkeyboard import listen_keyboard
import time
from adafruit_servokit import ServoKit

kit = ServoKit(channels=12)

pan_angle = 90
tilt_angle = 90

release_a = False
release_d = False
release_w = False
release_s = False

kit.servo[0].angle = pan_angle
kit.servo[1].angle = tilt_angle

def press(key):
    global pan_angle, tilt_angle, release_a, release_d, release_w, release_s

    if key == "w":
        release_w = False
        while(tilt_angle > 0 and not release_w):
            tilt_angle -= 1
            kit.servo[1].angle = tilt_angle
            time.sleep(0.01)

    elif key == "s":
        release_s = False
        while(tilt_angle < 180 and not release_s):
            tilt_angle += 1
            kit.servo[1].angle = tilt_angle
            time.sleep(0.01)

    elif key == "a":
        release_a = False
        while(pan_angle < 180 and not release_a):
            pan_angle += 1
            kit.servo[0].angle = pan_angle
            time.sleep(0.01)

    elif key == "d":
        release_d = False
        while(pan_angle > 0 and not release_d):
            pan_angle -= 1
            kit.servo[0].angle = pan_angle
            time.sleep(0.01)

def release(key):
    global release_a, release_d, release_w, release_s

    if key == "w":
        release_w = True

    elif key == "s":
        release_s = True

    elif key == "a":
        release_a = True

    elif key == "d":
        release_d = True

listen_keyboard(
    on_press=press,
    on_release=release,
    delay_second_char = 0.001
)