import cv2
import time
from gpiozero import AngularServo, Device
from gpiozero.pins.lgpio import LGPIOFactory

# --- SETUP SERVO ---
PIN_PAN = 12 
try:
    factory = LGPIOFactory()
    Device.pin_factory = factory
except:
    pass

# Init Servo (-90 to 90)
servo = AngularServo(PIN_PAN, min_angle=-90, max_angle=90, 
                     min_pulse_width=0.5/1000, max_pulse_width=2.5/1000)

def draw_grid(frame):
    h, w = frame.shape[:2]
    color = (0, 255, 0) # Hijau
    
    cv2.line(frame, (w//2, 0), (w//2, h), (0, 0, 255), 2)
    
    steps = 10
    step_px = w // steps
    
    for i in range(1, steps):
        x = i * step_px
        cv2.line(frame, (x, 0), (x, h), color, 1)
        norm_x = (x - (w/2)) / (w/2)
        cv2.putText(frame, f"{norm_x:.1f}", (x+2, 30), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.4, color, 1)

    return frame

def main():
    print("=== KALIBRASI SEDANG (STEP 5 DERAJAT) ===")
    print("1. Taruh benda di TENGAH (Garis Merah).")
    print("2. Tekan 'r' untuk Reset ke 0.")
    print("3. Tekan 'd' SATU KALI (Gerak 5 derajat).")
    print("4. Lihat posisi grid benda.")
    print("Tekan 'q' untuk keluar.")
    
    cap = cv2.VideoCapture(0)
    cap.set(3, 640)
    cap.set(4, 480)
    
    current_angle = 0
    servo.angle = 0
    time.sleep(1)
    servo.detach()

    while True:
        ret, frame = cap.read()
        if not ret: break
        
        frame = cv2.flip(frame, 1)
        h, w = frame.shape[:2]
        frame = draw_grid(frame)
        
        cv2.putText(frame, f"Angle: {current_angle} deg", (10, h-20), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
        
        cv2.imshow("Calibration Grid", frame)
        
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
            
        elif key == ord('d'): # STEP 5 DERAJAT
            if current_angle + 5 <= 90:
                current_angle += 5
                servo.angle = current_angle
                time.sleep(0.5)
                servo.detach()
            else: print("Mentok!")
                
        elif key == ord('a'): # STEP 5 DERAJAT
            if current_angle - 5 >= -90:
                current_angle -= 5
                servo.angle = current_angle
                time.sleep(0.5)
                servo.detach()
            else: print("Mentok!")
                
        elif key == ord('r'): 
            current_angle = 0
            servo.angle = 0
            time.sleep(0.5)
            servo.detach()

    cap.release()
    cv2.destroyAllWindows()
    servo.close()

if __name__ == "__main__":
    main()
