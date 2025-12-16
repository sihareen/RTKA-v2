import cv2
import numpy as np
import os
from ultralytics import YOLO
import mediapipe as mp
from pyzbar.pyzbar import decode

class AIProcessor:
    def __init__(self):
        self.mode = "off"
        self.track_error_x = 0.0 
        self.object_found = False
        
        # --- INIT DUAL MODELS ---
        print("[AI] Loading General Model (COCO)...")
        self.model_general = YOLO('assets/yolov8n.pt') 
        
        # Cek apakah model face ada
        self.face_model_path = 'assets/yolov8n-face.pt'
        if os.path.exists(self.face_model_path):
            print("[AI] Loading Face Model (Custom)...")
            self.model_face = YOLO(self.face_model_path)
            self.has_face_model = True
        else:
            print("[AI] WARNING: yolov8n-face.pt not found. Fallback to general model.")
            self.has_face_model = False
            self.model_face = self.model_general # Fallback

        # --- Init MediaPipe ---
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(max_num_hands=1, min_detection_confidence=0.5)
        self.mp_draw = mp.solutions.drawing_utils

    def set_mode(self, mode):
        self.mode = mode
        print(f"[AI] Mode changed to: {self.mode}")

    def process_frame(self, frame):
        self.object_found = False
        self.track_error_x = 0.0
        
        if self.mode == "off":
            return frame
        elif self.mode in ["object_detection", "face_detection", "target_tracking"]:
            return self._process_yolo(frame)
        elif self.mode == "color_detection":
            return self._process_color(frame)
        elif self.mode == "qr_recognition":
            return self._process_qr(frame)
        elif self.mode == "gesture_recognition":
            return self._process_gesture(frame)
        return frame

    def _process_yolo(self, frame):
        # --- PEMILIHAN MODEL & KELAS ---
        
        if self.mode == "face_detection" and self.has_face_model:
            # Gunakan Model Khusus Wajah
            active_model = self.model_face
            # Di model yolov8n-face, Class 0 biasanya adalah "Face"
            target_classes = [0] 
        else:
            # Gunakan Model Umum (COCO)
            active_model = self.model_general
            target_classes = [0,2, 3, 39, 41, 67, 73] 

        # --- INFERENCE ---
        results = active_model.track(
            frame, 
            persist=True, 
            classes=target_classes, 
            verbose=False,
            conf=0.40,  #makin besar makin ga sensitif (batas bawah klasifikasi)
            imgsz=320, 
            tracker="bytetrack.yaml"
        )
        
        annotated_frame = results[0].plot()
        
        # --- TRACKING LOGIC ---
        if len(results[0].boxes) > 0:
            box = results[0].boxes[0].xywh[0]
            h, w, _ = frame.shape
            cx = float(box[0])
            self.track_error_x = (cx - (w / 2)) / (w / 2)
            self.object_found = True
            
        return annotated_frame

    # ... (Sisa fungsi _process_color, _process_qr, _process_gesture SAMA seperti sebelumnya) ...
    # Agar hemat tempat, copy-paste fungsi-fungsi tersebut dari kode sebelumnya ke sini.
    # Jangan lupa menyertakan method _process_color, _process_qr, dan _process_gesture di sini.
    
    def _process_color(self, frame):
        # (Paste kode _process_color versi bersih terakhir Anda di sini)
        # ...
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        color_definitions = [
            {"label": "Red", "lower": np.array([0, 100, 100]), "upper": np.array([10, 255, 255]), "bgr": (0, 0, 255)},
            {"label": "Red", "lower": np.array([170, 100, 100]), "upper": np.array([180, 255, 255]), "bgr": (0, 0, 255)},
            {"label": "Blue", "lower": np.array([100, 150, 0]), "upper": np.array([140, 255, 255]), "bgr": (255, 0, 0)},
            {"label": "Green", "lower": np.array([36, 100, 100]), "upper": np.array([86, 255, 255]), "bgr": (0, 255, 0)},
            {"label": "Yellow", "lower": np.array([20, 100, 100]), "upper": np.array([35, 255, 255]), "bgr": (0, 255, 255)},
            {"label": "Orange", "lower": np.array([10, 100, 100]), "upper": np.array([20, 255, 255]), "bgr": (0, 165, 255)}
        ]
        kernel = np.ones((5,5), "uint8")
        max_area = 0 
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
                    if area > max_area:
                        max_area = area
                        h_img, w_img, _ = frame.shape
                        cx = x + (w // 2)
                        self.track_error_x = (cx - (w_img / 2)) / (w_img / 2)
                        self.object_found = True
        return frame

    def _process_qr(self, frame):
        decoded = decode(frame)
        for obj in decoded:
            data = obj.data.decode('utf-8')
            pts = np.array([obj.polygon], np.int32).reshape((-1, 1, 2))
            cv2.polylines(frame, [pts], True, (255, 0, 255), 3)
            cv2.putText(frame, data, (obj.rect.left, obj.rect.top), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
            print(f"[QR]: {data}")
        return frame

    def _process_gesture(self, frame):
            # MediaPipe butuh RGB
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            res = self.hands.process(rgb)
            
            if res.multi_hand_landmarks:
                # Loop untuk setiap tangan yang terdeteksi (Support Handedness Check)
                # Kita pakai 'zip' untuk mengambil data koordinat DAN label (Kiri/Kanan) sekaligus
                for hand_landmarks, hand_info in zip(res.multi_hand_landmarks, res.multi_handedness):
                    
                    # 1. Gambar Skeleton Tangan
                    self.mp_draw.draw_landmarks(frame, hand_landmarks, self.mp_hands.HAND_CONNECTIONS)
                    
                    # 2. Cek Apakah Tangan Kiri atau Kanan
                    # Note: Kamera selfie seringkali Mirroring, jadi label bisa terbalik.
                    # Sesuaikan logika ini jika nanti jempol terbalik bacanya.
                    hand_label = hand_info.classification[0].label # "Left" atau "Right"
                    
                    fingers = []

                    # --- A. LOGIKA JEMPOL (THUMB - ID 4) ---
                    # Jempol tidak cek Y, tapi cek X (Menyamping)
                    # Bandingkan Ujung Jempol (4) dengan Ruas Jempol (3)
                    
                    if hand_label == "Right":
                        # Tangan Kanan: Jempol terbuka jika ada di sebelah KIRI ruasnya (Nilai X Lebih Kecil)
                        if hand_landmarks.landmark[4].x < hand_landmarks.landmark[3].x:
                            fingers.append(1)
                        else:
                            fingers.append(0)
                    else: # "Left"
                        # Tangan Kiri: Jempol terbuka jika ada di sebelah KANAN ruasnya (Nilai X Lebih Besar)
                        if hand_landmarks.landmark[4].x > hand_landmarks.landmark[3].x:
                            fingers.append(1)
                        else:
                            fingers.append(0)

                    # --- B. LOGIKA 4 JARI LAINNYA (Index - Pinky) ---
                    # Menggunakan Sumbu Y (Vertikal)
                    # Ujung Jari: 8, 12, 16, 20
                    # Ruas Bawah: 6, 10, 14, 18 (PIP Joint)
                    tip_ids = [8, 12, 16, 20]
                    
                    for id in tip_ids:
                        # Jika Ujung (id) lebih TINGGI dari Ruas (id-2)
                        # Ingat: Di layar, Y=0 itu di ATAS. Jadi makin ke atas, nilai Y makin KECIL.
                        if hand_landmarks.landmark[id].y < hand_landmarks.landmark[id - 2].y:
                            fingers.append(1)
                        else:
                            fingers.append(0)

                    # --- C. HASIL ---
                    total_fingers = fingers.count(1)
                    
                    # Tampilkan Teks
                    cv2.putText(frame, f"Hand: {hand_label}", (10, 50), 
                                cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)
                    cv2.putText(frame, f"Count: {total_fingers}", (10, 100), 
                                cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 255, 0), 3)
                    
                    # --- COMMAND LOGIC (Opsional) ---
                    if total_fingers == 5:
                        cv2.putText(frame, "STOP", (200, 100), cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 0, 255), 4)
                        self.track_error_x = 0 # Robot diam
                    elif total_fingers == 1:
                        cv2.putText(frame, "MAJU", (200, 100), cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 255, 255), 4)

            return frame
