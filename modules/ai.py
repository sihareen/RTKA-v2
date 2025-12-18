import cv2
import numpy as np
import os
import time
import mediapipe as mp
from pyzbar.pyzbar import decode

# Import TFLite
try:
    import tflite_runtime.interpreter as tflite
except ImportError:
    try:
        import tensorflow.lite as tflite
    except ImportError:
        print("[AI] CRITICAL: Install tflite-runtime with 'pip install tflite-runtime'")

class AIProcessor:
    def __init__(self):
        self.mode = "off"
        # Variable tracking tetap di-init, tapi tidak akan pernah diupdate
        self.track_error_x = 0.0
        self.object_found = False

        # =========================================
        # 1. SETUP SSD MOBILENET (TFLite)
        # =========================================
        self.model_path = "assets/ssd_mobilenet_v2.tflite"
        self.interpreter = None
        
        # --- LABEL MAP ---
        self.labels = {
            0: "person", 1: "???", 2: "car", 3: "motorcycle", 4: "bicycle",
            5: "airplane", 6: "bus", 7: "train", 8: "truck", 9: "boat",
            10: "traffic light", 11: "fire hydrant", 12: "???", 13: "stop sign", 14: "parking meter", 15: "bench", 
            16: "bird", 17: "cat", 18: "dog", 19: "horse", 20: "sheep", 21: "cow", 22: "elephant", 23: "bear", 24: "zebra", 25: "giraffe", 
            26: "???", 27: "backpack", 28: "umbrella", 29: "???", 30: "???", 31: "handbag", 32: "tie", 33: "suitcase", 
            34: "frisbee", 35: "skis", 36: "snowboard", 37: "sports ball", 38: "kite", 39: "baseball bat", 40: "baseball glove", 
            41: "skateboard", 42: "surfboard", 43: "bottle", 44: "tennis racket", 45: "???", 46: "cup", 47: "wine glass", 
            48: "fork", 49: "knife", 50: "spoon", 51: "bowl", 52: "banana", 53: "apple", 54: "sandwich", 55: "orange", 
            56: "broccoli", 57: "carrot", 58: "hot dog", 59: "pizza", 60: "donut", 61: "cake", 62: "chair", 63: "couch", 
            64: "potted plant", 65: "bed", 66: "???", 67: "dining table", 68: "???", 69: "???", 70: "toilet", 71: "???", 
            72: "laptop", 73: "tv", 74: "mouse", 75: "remote", 76: "cell phone", 77: "keyboard", 
            78: "microwave", 79: "oven", 80: "toaster", 81: "sink", 82: "refrigerator", 83: "???", 
            84: "book", 85: "clock", 86: "vase", 87: "scissors", 88: "teddy bear", 89: "hair drier", 90: "toothbrush"
        }

        # Filter Target
        self.TARGET_OBJECTS = [
            "person", "car", "motorcycle", 
            "cell phone", "laptop", "book", "bottle", "cup"
        ]

        # Init TFLite
        self._init_tflite()

        # =========================================
        # 2. SETUP MEDIAPIPE
        # =========================================
        self.mp_face = mp.solutions.face_detection
        self.face_detector = self.mp_face.FaceDetection(min_detection_confidence=0.5, model_selection=0)
        
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(max_num_hands=1, min_detection_confidence=0.5)
        self.mp_draw = mp.solutions.drawing_utils

    def _init_tflite(self):
        if os.path.exists(self.model_path):
            print(f"[AI] Loading Model: {self.model_path}")
            try:
                self.interpreter = tflite.Interpreter(model_path=self.model_path)
                self.interpreter.allocate_tensors()
                self.input_details = self.interpreter.get_input_details()
                self.output_details = self.interpreter.get_output_details()
                print("[AI] Model Loaded (Detection Only).")
            except Exception as e:
                print(f"[AI] Error TFLite: {e}")
        else:
            print(f"[AI] ERROR: File missing {self.model_path}")

    def set_mode(self, mode):
        self.mode = mode
        print(f"[AI] Mode: {self.mode}")

    def process_frame(self, frame):
        # RESET TRACKING VARIABLES TIAP FRAME
        self.track_error_x = 0.0
        self.object_found = False # Selalu False agar motor tidak jalan otomatis

        if self.mode == "off": return frame
        
        if self.mode == "object_detection":
            return self._process_ssd_mobilenet(frame)
        elif self.mode == "face_detection":
            return self._process_face(frame)
        elif self.mode == "gesture_recognition":
            return self._process_gesture(frame)
        elif self.mode == "color_detection":
            return self._process_color(frame)
        elif self.mode == "qr_recognition":
            return self._process_qr(frame)
        
        return frame

    # =========================================
    # 1. OBJECT DETECTION (VISUAL ONLY)
    # =========================================
    def _process_ssd_mobilenet(self, frame):
        if not self.interpreter: return frame

        h_img, w_img, _ = frame.shape
        
        input_size = 300 
        frame_resized = cv2.resize(frame, (input_size, input_size))
        frame_rgb = cv2.cvtColor(frame_resized, cv2.COLOR_BGR2RGB)
        input_data = np.expand_dims(frame_rgb, axis=0)

        self.interpreter.set_tensor(self.input_details[0]['index'], input_data)
        self.interpreter.invoke()

        boxes = self.interpreter.get_tensor(self.output_details[0]['index'])[0] 
        classes = self.interpreter.get_tensor(self.output_details[1]['index'])[0]
        scores = self.interpreter.get_tensor(self.output_details[2]['index'])[0]

        for i in range(len(scores)):
            score = scores[i]
            if score > 0.5: 
                class_id = int(classes[i])
                label_name = self.labels.get(class_id, "unknown")
                
                if label_name in self.TARGET_OBJECTS:
                    ymin, xmin, ymax, xmax = boxes[i]
                    x = int(xmin * w_img)
                    y = int(ymin * h_img)
                    w = int((xmax - xmin) * w_img)
                    h = int((ymax - ymin) * h_img)
                    x = max(0, x); y = max(0, y)
                    
                    # HANYA MENGGAMBAR (Tidak ada hitungan tracking)
                    color = (0, 255, 0) 
                    cv2.rectangle(frame, (x, y), (x+w, y+h), color, 2)
                    label_text = f"{label_name} {int(score*100)}%"
                    cv2.putText(frame, label_text, (x, y-10), 
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
        return frame

    # =========================================
    # 2. FACE DETECTION (VISUAL ONLY)
    # =========================================
    def _process_face(self, frame):
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.face_detector.process(rgb)
        if results.detections:
            for detection in results.detections:
                bboxC = detection.location_data.relative_bounding_box
                h, w, c = frame.shape
                x = int(bboxC.xmin * w)
                y = int(bboxC.ymin * h)
                width = int(bboxC.width * w)
                height = int(bboxC.height * h)
                
                # Visualisasi Saja
                cv2.rectangle(frame, (x, y), (x + width, y + height), (0, 255, 255), 2)
                cv2.putText(frame, "Face", (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
                
                # TRACKING LOGIC DIHAPUS
                # cx = x + (width // 2)
                # self.track_error_x = (cx - (w / 2)) / (w / 2)
                # self.object_found = True <-- Dihapus
        return frame

    # =========================================
    # 3. GESTURE (VISUAL ONLY)
    # =========================================
    def _process_gesture(self, frame):
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        res = self.hands.process(rgb)
        if res.multi_hand_landmarks:
            for hand_landmarks, hand_info in zip(res.multi_hand_landmarks, res.multi_handedness):
                self.mp_draw.draw_landmarks(frame, hand_landmarks, self.mp_hands.HAND_CONNECTIONS)
                hand_label = hand_info.classification[0].label
                fingers = []
                if hand_label == "Right":
                    fingers.append(1 if hand_landmarks.landmark[4].x < hand_landmarks.landmark[3].x else 0)
                else:
                    fingers.append(1 if hand_landmarks.landmark[4].x > hand_landmarks.landmark[3].x else 0)
                for id in [8, 12, 16, 20]:
                    fingers.append(1 if hand_landmarks.landmark[id].y < hand_landmarks.landmark[id - 2].y else 0)
                
                total = fingers.count(1)
                cv2.putText(frame, f"{hand_label}: {total}", (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                
                if total == 5: 
                    cv2.putText(frame, "STOP", (200, 100), cv2.FONT_HERSHEY_SIMPLEX, 2, (0,0,255), 4)
                    # TRACKING STOP DIHAPUS
                    # self.track_error_x = 0 
        return frame

    # =========================================
    # 4. COLOR DETECTION (VISUAL ONLY)
    # =========================================
    def _process_color(self, frame):
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        color_definitions = [
            {"label": "Red", "lower": np.array([0, 160, 100]), "upper": np.array([10, 255, 255]), "bgr": (0, 0, 255)},
            {"label": "Red", "lower": np.array([170, 160, 100]), "upper": np.array([180, 255, 255]), "bgr": (0, 0, 255)},
            {"label": "Blue", "lower": np.array([110, 180, 60]), "upper": np.array([130, 255, 255]), "bgr": (255, 0, 0)},
            {"label": "Yellow", "lower": np.array([20, 100, 100]), "upper": np.array([35, 255, 255]), "bgr": (0, 255, 255)}
        ]
        kernel = np.ones((5,5), "uint8")
        # max_area = 0 <-- Tidak dipakai
        for color in color_definitions:
            mask = cv2.inRange(hsv, color["lower"], color["upper"])
            mask = cv2.dilate(mask, kernel)
            contours, _ = cv2.findContours(mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
            for contour in contours:
                area = cv2.contourArea(contour)
                if area > 800:
                    x, y, w, h = cv2.boundingRect(contour)
                    cv2.rectangle(frame, (x, y), (x + w, y + h), color["bgr"], 2)
                    cv2.putText(frame, color["label"], (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color["bgr"], 2)
                    
                    # LOGIKA TRACKING DIHAPUS
                    # if area > max_area:
                    #     max_area = area
                    #     h_img, w_img, _ = frame.shape
                    #     cx = x + (w // 2)
                    #     self.track_error_x = (cx - (w_img / 2)) / (w_img / 2)
                    #     self.object_found = True
        return frame

    # =========================================
    # 5. QR RECOGNITION (VISUAL ONLY)
    # =========================================
    def _process_qr(self, frame):
        decoded = decode(frame)
        for obj in decoded:
            data = obj.data.decode('utf-8')
            pts = np.array([obj.polygon], np.int32).reshape((-1, 1, 2))
            cv2.polylines(frame, [pts], True, (255, 0, 255), 3)
            cv2.putText(frame, data, (obj.rect.left, obj.rect.top), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
            print(f"[QR]: {data}")
        return frame