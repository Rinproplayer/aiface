"""
Module Nhận Diện Khuôn Mặt
=============================
Sử dụng thư viện face_recognition (dựa trên dlib) để:
- Phát hiện khuôn mặt trong ảnh/video
- Mã hóa (encode) khuôn mặt thành vector 128 chiều
- So khớp khuôn mặt với database đã đăng ký
"""

import os
import pickle
import cv2
import numpy as np

try:
    import face_recognition
    FACE_LIB_AVAILABLE = True
except ImportError:
    FACE_LIB_AVAILABLE = False
    print("⚠️ Thư viện face_recognition chưa được cài đặt.")
    print("   Chạy: pip install face-recognition")

from config import (
    DATASET_DIR, ENCODINGS_FILE, ENCODINGS_DIR,
    FACE_RECOGNITION_TOLERANCE, FACE_RECOGNITION_MODEL
)


class FaceEngine:
    """
    Engine nhận diện khuôn mặt.
    
    Cách sử dụng:
        engine = FaceEngine()
        engine.load_encodings()         # Tải dữ liệu đã train
        name, conf = engine.recognize(frame)  # Nhận diện từ frame camera
    """

    def __init__(self):
        self.known_encodings = []       # Danh sách encoding đã biết
        self.known_student_codes = []   # Danh sách mã SV tương ứng
        self.known_names = []           # Danh sách tên SV tương ứng
        self.is_loaded = False

    def load_encodings(self):
        """Tải file encoding đã train trước đó"""
        if not os.path.exists(ENCODINGS_FILE):
            print("⚠️ Chưa có file encoding. Hãy chạy train_model.py trước!")
            return False

        try:
            with open(ENCODINGS_FILE, "rb") as f:
                data = pickle.load(f)

            self.known_encodings = data["encodings"]
            self.known_student_codes = data["student_codes"]
            self.known_names = data["names"]
            self.is_loaded = True

            print(f"✅ Đã tải {len(self.known_encodings)} khuôn mặt đã đăng ký")
            return True
        except Exception as e:
            print(f"❌ Lỗi tải encoding: {e}")
            return False

    def train_from_dataset(self):
        """
        Train model từ thư mục dataset.
        Cấu trúc thư mục:
            dataset/
                SV001_NguyenVanA/
                    1.jpg
                    2.jpg
                SV002_TranThiB/
                    1.jpg
        """
        if not FACE_LIB_AVAILABLE:
            print("❌ Cần cài đặt face_recognition!")
            return False

        encodings = []
        student_codes = []
        names = []

        if not os.path.exists(DATASET_DIR):
            print(f"❌ Thư mục dataset không tồn tại: {DATASET_DIR}")
            return False

        # Duyệt qua từng thư mục sinh viên
        student_dirs = [d for d in os.listdir(DATASET_DIR)
                        if os.path.isdir(os.path.join(DATASET_DIR, d))]

        if not student_dirs:
            print("❌ Không có dữ liệu sinh viên trong dataset/")
            return False

        print(f"🔄 Bắt đầu train {len(student_dirs)} sinh viên...")

        for student_dir in student_dirs:
            # Tên thư mục: SV001_NguyenVanA
            parts = student_dir.split("_", 1)
            student_code = parts[0]
            student_name = parts[1].replace("_", " ") if len(parts) > 1 else student_code

            student_path = os.path.join(DATASET_DIR, student_dir)
            image_files = [f for f in os.listdir(student_path)
                           if f.lower().endswith(('.jpg', '.jpeg', '.png'))]

            print(f"  📸 {student_name} ({student_code}): {len(image_files)} ảnh", end="")

            face_count = 0
            for img_file in image_files:
                img_path = os.path.join(student_path, img_file)
                image = face_recognition.load_image_file(img_path)

                # Tìm và encode khuôn mặt
                face_encs = face_recognition.face_encodings(image, model=FACE_RECOGNITION_MODEL)

                if face_encs:
                    encodings.append(face_encs[0])
                    student_codes.append(student_code)
                    names.append(student_name)
                    face_count += 1

            print(f" → {face_count} khuôn mặt ✅" if face_count > 0 else " → Không tìm thấy khuôn mặt ❌")

        if not encodings:
            print("❌ Không encode được khuôn mặt nào!")
            return False

        # Lưu file encoding
        os.makedirs(ENCODINGS_DIR, exist_ok=True)
        data = {
            "encodings": encodings,
            "student_codes": student_codes,
            "names": names
        }
        with open(ENCODINGS_FILE, "wb") as f:
            pickle.dump(data, f)

        self.known_encodings = encodings
        self.known_student_codes = student_codes
        self.known_names = names
        self.is_loaded = True

        print(f"\n🎉 Train hoàn tất! Đã lưu {len(encodings)} encoding vào {ENCODINGS_FILE}")
        return True

    def detect_faces(self, frame):
        """
        Phát hiện khuôn mặt trong frame.
        
        Args:
            frame: Frame từ camera (BGR format)
            
        Returns:
            List of (top, right, bottom, left) - vị trí khuôn mặt
        """
        if not FACE_LIB_AVAILABLE:
            return []

        # Chuyển BGR → RGB (face_recognition dùng RGB)
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # Thu nhỏ frame để xử lý nhanh hơn
        small_frame = cv2.resize(rgb_frame, (0, 0), fx=0.5, fy=0.5)

        # Phát hiện khuôn mặt
        face_locations = face_recognition.face_locations(small_frame, model=FACE_RECOGNITION_MODEL)

        # Scale lại vị trí cho frame gốc
        face_locations = [(t*2, r*2, b*2, l*2) for (t, r, b, l) in face_locations]

        return face_locations

    def recognize(self, frame):
        """
        Nhận diện khuôn mặt trong frame camera.
        
        Args:
            frame: Frame từ camera (BGR format)
            
        Returns:
            List of dict: [{
                "student_code": "SV001",
                "name": "Nguyễn Văn A",
                "confidence": 0.85,
                "location": (top, right, bottom, left)
            }]
        """
        if not FACE_LIB_AVAILABLE or not self.is_loaded:
            return []

        # Chuyển BGR → RGB
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # Thu nhỏ để xử lý nhanh
        small_frame = cv2.resize(rgb_frame, (0, 0), fx=0.5, fy=0.5)

        # Phát hiện và encode khuôn mặt
        face_locations = face_recognition.face_locations(small_frame, model=FACE_RECOGNITION_MODEL)
        face_encodings = face_recognition.face_encodings(small_frame, face_locations)

        results = []
        for encoding, location in zip(face_encodings, face_locations):
            # So khớp với tất cả khuôn mặt đã đăng ký
            matches = face_recognition.compare_faces(
                self.known_encodings, encoding,
                tolerance=FACE_RECOGNITION_TOLERANCE
            )

            # Tính khoảng cách (distance nhỏ = giống hơn)
            distances = face_recognition.face_distance(self.known_encodings, encoding)

            student_code = "Unknown"
            name = "Không xác định"
            confidence = 0.0

            if True in matches:
                # Tìm khuôn mặt giống nhất
                best_match_idx = np.argmin(distances)
                if matches[best_match_idx]:
                    student_code = self.known_student_codes[best_match_idx]
                    name = self.known_names[best_match_idx]
                    confidence = round(1 - distances[best_match_idx], 2)

            # Scale lại vị trí cho frame gốc
            top, right, bottom, left = [v * 2 for v in location]

            results.append({
                "student_code": student_code,
                "name": name,
                "confidence": confidence,
                "location": (top, right, bottom, left)
            })

        return results

    def draw_results(self, frame, results):
        """Vẽ khung và tên lên frame camera"""
        for result in results:
            top, right, bottom, left = result["location"]
            name = result["name"]
            confidence = result["confidence"]
            is_known = result["student_code"] != "Unknown"

            # Màu: xanh lá = đã biết, đỏ = không biết
            color = (0, 200, 0) if is_known else (0, 0, 255)

            # Vẽ khung khuôn mặt
            cv2.rectangle(frame, (left, top), (right, bottom), color, 2)

            # Vẽ nền cho text
            label = f"{name} ({confidence*100:.0f}%)" if is_known else "Khong xac dinh"
            cv2.rectangle(frame, (left, bottom - 35), (right, bottom), color, cv2.FILLED)
            cv2.putText(frame, label, (left + 6, bottom - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

        return frame


# Instance toàn cục để sử dụng trong toàn bộ ứng dụng
face_engine = FaceEngine()
