#!/usr/bin/env python3
"""
Bab 21.0: Test Camera + Face Detection
======================================
Verifikasi kamera dan deteksi wajah sebelum enroll/absensi.
"""

import time

import cv2

import attendance_utils as utils

print("=" * 60)
print("Face Attendance - Camera Test")
print("=" * 60)

utils.ensure_directories()
utils.init_database()
utils.setup_face_cascade()
detector = utils.load_face_detector()

camera = None
camera_type = None

try:
    camera, camera_type = utils.open_camera()
    print(f"Camera ready: {camera_type}")
    print("Running test for 10 seconds. Press 'q' to stop.\n")

    start_time = time.time()
    frame_count = 0

    while True:
        ret, frame = utils.read_frame(camera, camera_type)
        if not ret:
            print("Failed to read frame.")
            break

        frame_count += 1
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = detector.detectMultiScale(
            gray,
            scaleFactor=1.2,
            minNeighbors=5,
            minSize=(60, 60),
        )

        for (x, y, w, h) in faces:
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 200, 0), 2)

        elapsed = time.time() - start_time
        fps = frame_count / elapsed if elapsed > 0 else 0.0
        cv2.putText(
            frame,
            f"Faces: {len(faces)} | FPS: {fps:.1f}",
            (10, 25),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (20, 220, 20),
            2,
        )

        cv2.imshow("Face Attendance Camera Test (press Q)", frame)
        key = cv2.waitKey(1) & 0xFF
        if key == ord("q"):
            break
        if elapsed >= 10:
            break

    total_time = time.time() - start_time
    fps = frame_count / total_time if total_time > 0 else 0.0
    print("\nTest finished.")
    print(f"Frames captured: {frame_count}")
    print(f"Average FPS: {fps:.1f}")

except Exception as exc:
    print(f"Error: {exc}")

finally:
    if camera is not None:
        utils.close_camera(camera, camera_type)
    cv2.destroyAllWindows()
