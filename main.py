"""
Main - Điểm danh bằng nhận diện khuôn mặt
============================================
Mở webcam, nhận diện khuôn mặt realtime, tự động điểm danh.
Sử dụng: python main.py
"""

import cv2
import json
import time
import asyncio
import threading
import requests
from datetime import datetime

from config import CAMERA_INDEX, CAMERA_WIDTH, CAMERA_HEIGHT
from face_engine import FaceEngine
from database import (
    get_student_by_code, mark_attendance, get_all_classes,
    get_students_by_class
)

# Biến toàn cục để giao tiếp với WebSocket
attendance_events = []
attendance_lock = threading.Lock()


def send_websocket_notification(student_code, student_name, class_id, confidence):
    """Gửi thông báo điểm danh qua API (để WebSocket broadcast)"""
    try:
        data = {
            "student_code": student_code,
            "student_name": student_name,
            "class_id": class_id,
            "confidence": confidence,
            "time": datetime.now().strftime("%H:%M:%S")
        }
        requests.post("http://localhost:8000/api/attendance/notify", json=data, timeout=2)
    except Exception:
        pass  # Server có thể chưa chạy


def run_attendance(class_id=None):
    """
    Chạy điểm danh bằng webcam.
    
    Args:
        class_id: ID lớp học (None = chọn từ menu)
    """
    print("=" * 50)
    print("📷 ĐIỂM DANH BẰNG NHẬN DIỆN KHUÔN MẶT")
    print("=" * 50)

    # Chọn lớp học
    if class_id is None:
        classes = get_all_classes()
        if not classes:
            print("❌ Chưa có lớp học nào! Hãy tạo lớp trên Web Dashboard.")
            return

        print("\n📚 Danh sách lớp học:")
        for c in classes:
            print(f"  [{c['id']}] {c['class_code']} - {c['class_name']}")

        try:
            class_id = int(input("\n📝 Nhập ID lớp cần điểm danh: "))
        except ValueError:
            print("❌ ID không hợp lệ!")
            return

    # Tải model nhận diện
    print("\n🔄 Đang tải model nhận diện...")
    engine = FaceEngine()
    if not engine.load_encodings():
        print("❌ Chưa train model! Hãy chạy: python train_model.py")
        return

    # Mở webcam
    print(f"\n📷 Mở webcam...")
    cap = cv2.VideoCapture(CAMERA_INDEX)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, CAMERA_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CAMERA_HEIGHT)

    if not cap.isOpened():
        print("❌ Không thể mở webcam!")
        return

    print("✅ Webcam đã sẵn sàng!")
    print("   Nhấn Q để thoát | Nhấn R để reload model")
    print("-" * 50)

    # Danh sách SV đã điểm danh trong phiên này
    checked_in = set()
    frame_count = 0
    process_every_n = 3  # Xử lý mỗi 3 frame để tăng tốc

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame_count += 1
        display = frame.copy()

        # Chỉ xử lý nhận diện mỗi N frame
        if frame_count % process_every_n == 0:
            results = engine.recognize(frame)

            for result in results:
                student_code = result["student_code"]
                name = result["name"]
                confidence = result["confidence"]
                top, right, bottom, left = result["location"]

                if student_code != "Unknown" and student_code not in checked_in:
                    # Tìm sinh viên trong database
                    student = get_student_by_code(student_code)
                    if student:
                        # Ghi nhận điểm danh
                        status = "present"
                        success = mark_attendance(student["id"], class_id, confidence, status)

                        if success:
                            checked_in.add(student_code)
                            timestamp = datetime.now().strftime("%H:%M:%S")
                            print(f"  ✅ [{timestamp}] {name} ({student_code}) - Độ tin cậy: {confidence*100:.0f}%")

                            # Gửi thông báo WebSocket
                            send_websocket_notification(student_code, name, class_id, confidence)

            # Vẽ kết quả lên frame
            display = engine.draw_results(display, results)

        # Hiển thị thông tin
        cv2.putText(display, f"Da diem danh: {len(checked_in)} SV | Q: Thoat",
                    (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        cv2.putText(display, datetime.now().strftime("%H:%M:%S"),
                    (CAMERA_WIDTH - 120, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)

        cv2.imshow("AI Diem Danh - Nhan PHIM Q de thoat", display)

        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        elif key == ord('r'):
            print("🔄 Reload model...")
            engine.load_encodings()

    cap.release()
    cv2.destroyAllWindows()

    print(f"\n📊 Kết quả: Đã điểm danh {len(checked_in)} sinh viên")
    print("=" * 50)


if __name__ == "__main__":
    run_attendance()
