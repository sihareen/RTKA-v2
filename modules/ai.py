import cv2
import numpy as np
import os
import mediapipe as mp
import time
from pyzbar.pyzbar import decode

# Cek Import TensorFlow Lite
try:
    import tflite_runtime.interpreter as tflite
except ImportError:
    try:
        import tensorflow.lite as tflite
    except ImportError:
        pass

class AIProcessor:
    def __init__(self):
        self.mode = "off"
        self.target_color = "none" 
        
        # Output Data Tracking
        self.track_error_x = 0.0    
        self.track_error_y = 0.0    
        self.track_area = 0.0 
        self.object_found = False   
        self.qr_data = None         
        self.gesture_data = None    

        # --- VISUALISASI DEADZONE ---
        self.show_deadzone = False
        self.deadzone_x_val = 0.0
        self.deadzone_y_val = 0.0
        
        # --- TAMBAHAN BARU: VISUALISASI JARAK (HUD) ---
        self.distance_val = None 

        # Setup Model SSD MobileNet (Objek)
        self.model_path = "assets/ssd_mobilenet_v2.tflite"
        self.interpreter = None
        self.labels = {
            0: "person", 1: "bicycle", 2: "car", 3: "motorcycle", 
            44: "bottle", 46: "cup", 62: "chair", 63: "couch", 
            64: "potted plant", 67: "dining table", 76: "cell phone"
        }
        self.TARGET_OBJECTS = ["person", "car", "motorcycle", "bottle", "cup", "cell phone"]
        self._init_tflite()

        # Setup MediaPipe (Wajah & Tangan)
        self.mp_face = mp.solutions.face_detection
        self.face_detector = self.mp_face.FaceDetection(min_detection_confidence=0.5)
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(max_num_hands=1, min_detection_confidence=0.5)
        self.mp_draw = mp.solutions.drawing_utils

    def _init_tflite(self):
        if os.path.exists(self.model_path):
            try:
                self.interpreter = tflite.Interpreter(model_path=self.model_path)
                self.interpreter.allocate_tensors()
                self.input_details = self.interpreter.get_input_details()
                self.output_details = self.interpreter.get_output_details()
                print("[AI] Model Loaded.")
            except: pass

    def set_mode(self, mode):
        self.mode = mode
        self.qr_data = None
        self.gesture_data = None
        self.object_found = False
        self.track_area = 0.0
        self.track_error_x = 0.0
        self.track_error_y = 0.0
        
        # Matikan deadzone visual saat ganti mode (kecuali dinyalakan lagi oleh main.py)
        if mode == "off":
            self.show_deadzone = False
            
        print(f"[AI] Mode: {self.mode}")

    def set_color_target(self, color_name):
        self.target_color = color_name.lower() 
        print(f"[AI] Target Color: {self.target_color}")

    def set_deadzone(self, active, x=0.0, y=0.0):
        """Mengaktifkan visualisasi kotak Deadzone di layar"""
        self.show_deadzone = active
        self.deadzone_x_val = x
        self.deadzone_y_val = y

    # --- FUNGSI BARU UNTUK UPDATE JARAK ---
    def update_distance(self, dist):
        """Menerima data jarak (cm) dari Main Loop untuk ditampilkan"""
        self.distance_val = dist
    # --------------------------------------

    def process_frame(self, frame):
        # Reset data per frame
        self.track_error_x = 0.0
        self.track_error_y = 0.0
        self.object_found = False
        
        # 1. Proses Utama sesuai Mode
        processed_frame = frame
        if self.mode == "off": pass
        elif self.mode == "object_detection": processed_frame = self._process_ssd_mobilenet(frame)
        elif self.mode == "face_detection": processed_frame = self._process_face(frame)
        elif self.mode == "gesture_recognition": processed_frame = self._process_gesture(frame)
        elif self.mode == "color_detection": processed_frame = self._process_color(frame)
        elif self.mode == "qr_recognition": processed_frame = self._process_qr(frame)
        elif self.mode == "auto_pilot": processed_frame = self._process_auto_pilot(frame)

        # 2. Gambar Overlay Deadzone (Jika Aktif)
        if self.show_deadzone:
            h, w, _ = processed_frame.shape
            cx, cy = w // 2, h // 2
            
            # Hitung ukuran kotak
            span_x = int(w * self.deadzone_x_val)
            span_y = int(h * self.deadzone_y_val)
            
            pt1 = (cx - span_x, cy - span_y)
            pt2 = (cx + span_x, cy + span_y)
            
            # Gambar Kotak Cyan (Biru Muda)
            cv2.rectangle(processed_frame, pt1, pt2, (255, 255, 0), 2)
            
            # Gambar Crosshair Merah Kecil di Tengah
            cv2.line(processed_frame, (cx - 10, cy), (cx + 10, cy), (0, 0, 255), 1)
            cv2.line(processed_frame, (cx, cy - 10), (cx, cy + 10), (0, 0, 255), 1)

        # 3. Overlay Distance (BARU - Pojok Kiri Atas)
        if self.distance_val is not None:
            # Tentukan Warna: Hijau jika aman (>25), Merah jika bahaya (<25)
            color = (0, 255, 0) if self.distance_val > 25 else (0, 0, 255)
            text = f"DIST: {self.distance_val:.1f} cm"
            
            # Background Hitam Transparan (Agar tulisan terbaca)
            cv2.rectangle(processed_frame, (5, 5), (220, 40), (0, 0, 0), -1) 
            # Tulisan
            cv2.putText(processed_frame, text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)

        return processed_frame

    # --- LOGIKA MODUL AI ---

    def _process_color(self, frame):
        if self.target_color == "none":
            cv2.putText(frame, "SELECT COLOR", (180, 240), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
            return frame

        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        
        color_definitions = [
            {"label": "red", "lower": np.array([0, 160, 100]), "upper": np.array([10, 255, 255]), "bgr": (0, 0, 255)},
            {"label": "red", "lower": np.array([170, 160, 100]), "upper": np.array([180, 255, 255]), "bgr": (0, 0, 255)},
            {"label": "blue", "lower": np.array([110, 180, 60]), "upper": np.array([130, 255, 255]), "bgr": (255, 0, 0)},
            {"label": "green", "lower": np.array([40, 70, 70]), "upper": np.array([80, 255, 255]), "bgr": (0, 255, 0)},
            {"label": "yellow", "lower": np.array([20, 100, 100]), "upper": np.array([35, 255, 255]), "bgr": (0, 255, 255)}
        ]

        kernel = np.ones((5,5), "uint8")
        max_area = 0
        best_contour = None
        
        for color in color_definitions:
            # Filter warna (Skip jika bukan target & target bukan "all")
            if self.target_color != "all" and color["label"] != self.target_color:
                continue 

            mask = cv2.inRange(hsv, color["lower"], color["upper"])
            mask = cv2.dilate(mask, kernel) 
            contours, _ = cv2.findContours(mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
            
            for contour in contours:
                area = cv2.contourArea(contour)
                if area > 800:
                    x, y, w, h = cv2.boundingRect(contour)
                    cv2.rectangle(frame, (x, y), (x + w, y + h), color["bgr"], 2)
                    cv2.putText(frame, color["label"].upper(), (x, y - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color["bgr"], 2)
                    
                    if area > max_area:
                        max_area = area
                        best_contour = contour
        
        # Hitung Error untuk Tracking Servo
        if best_contour is not None:
            x, y, w, h = cv2.boundingRect(best_contour)
            h_img, w_img, _ = frame.shape
            cx = x + (w // 2)
            cy = y + (h // 2)
            
            self.track_error_x = (cx - (w_img / 2)) / (w_img / 2)
            self.track_error_y = (cy - (h_img / 2)) / (h_img / 2)
            self.track_area = max_area / (w_img * h_img)
            self.object_found = True

        return frame

    def _process_face(self, frame):
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.face_detector.process(rgb)
        if results.detections:
            for detection in results.detections:
                bboxC = detection.location_data.relative_bounding_box
                h, w, c = frame.shape
                x, y = int(bboxC.xmin * w), int(bboxC.ymin * h)
                width, height = int(bboxC.width * w), int(bboxC.height * h)
                cv2.rectangle(frame, (x, y), (x + width, y + height), (0, 255, 255), 2)
                cx = x + (width // 2)
                cy = y + (height // 2)
                self.track_error_x = (cx - (w / 2)) / (w / 2)
                self.track_error_y = (cy - (h / 2)) / (h / 2)
                self.object_found = True
        return frame

    def _process_ssd_mobilenet(self, frame):
        if not self.interpreter: return frame
        h_img, w_img, _ = frame.shape
        frame_resized = cv2.resize(frame, (300, 300))
        input_data = np.expand_dims(cv2.cvtColor(frame_resized, cv2.COLOR_BGR2RGB), axis=0)
        self.interpreter.set_tensor(self.input_details[0]['index'], input_data)
        self.interpreter.invoke()
        boxes = self.interpreter.get_tensor(self.output_details[0]['index'])[0] 
        classes = self.interpreter.get_tensor(self.output_details[1]['index'])[0]
        scores = self.interpreter.get_tensor(self.output_details[2]['index'])[0]
        for i in range(len(scores)):
            if scores[i] > 0.5:
                label = self.labels.get(int(classes[i]), "unknown")
                if label in self.TARGET_OBJECTS:
                    ymin, xmin, ymax, xmax = boxes[i]
                    x, y = int(xmin * w_img), int(ymin * h_img)
                    w, h = int((xmax - xmin) * w_img), int((ymax - ymin) * h_img)
                    cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
                    cv2.putText(frame, f"{label} {int(scores[i]*100)}%", (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        return frame

    def _process_gesture(self, frame):
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        res = self.hands.process(rgb)
        self.gesture_data = None 
        if res.multi_hand_landmarks:
            for hand_landmarks, hand_info in zip(res.multi_hand_landmarks, res.multi_handedness):
                self.mp_draw.draw_landmarks(frame, hand_landmarks, self.mp_hands.HAND_CONNECTIONS)
                fingers = []
                # Jempol
                if hand_landmarks.landmark[4].x < hand_landmarks.landmark[3].x: fingers.append(1)
                else: fingers.append(0)
                # 4 Jari
                for id in [8, 12, 16, 20]:
                    if hand_landmarks.landmark[id].y < hand_landmarks.landmark[id - 2].y: fingers.append(1)
                    else: fingers.append(0)
                total = fingers.count(1)
                self.gesture_data = total
                cv2.putText(frame, f"Fingers: {total}", (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                if total == 5: 
                    cv2.putText(frame, "STOP", (200, 100), cv2.FONT_HERSHEY_SIMPLEX, 2, (0,0,255), 4)
                    self.object_found = True 
        return frame

    def _process_qr(self, frame):
        decoded = decode(frame)
        self.qr_data = None 
        for obj in decoded:
            data = obj.data.decode('utf-8')
            self.qr_data = data 
            pts = np.array([obj.polygon], np.int32).reshape((-1, 1, 2))
            cv2.polylines(frame, [pts], True, (255, 0, 255), 3)
            cv2.putText(frame, data, (obj.rect.left, obj.rect.top), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
        return frame

    def _process_auto_pilot(self, frame):
        h, w, _ = frame.shape
        roi_h = int(h / 3) 
        roi = frame[h - roi_h:h, 0:w]
        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        blur = cv2.GaussianBlur(gray, (5, 5), 0)
        _, thresh = cv2.threshold(blur, 60, 255, cv2.THRESH_BINARY_INV)
        contours, _ = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        if contours:
            largest_contour = max(contours, key=cv2.contourArea)
            if cv2.contourArea(largest_contour) > 1000:
                M = cv2.moments(largest_contour)
                if M['m00'] != 0:
                    cx = int(M['m10'] / M['m00'])
                    global_cy = int(M['m01'] / M['m00']) + (h - roi_h)
                    cv2.line(frame, (int(w/2), global_cy), (cx, global_cy), (0, 255, 255), 2)
                    self.track_error_x = (cx - (w / 2)) / (w / 2)
                    self.object_found = True
        return frame