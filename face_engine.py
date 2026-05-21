"""
Module Nhận Diện Khuôn Mặt - PHIÊN BẢN NÂNG CẤP
====================================================
Cải thiện:
- Tiền xử lý ảnh (cân bằng sáng, tăng tương phản)
- Dùng cả HOG + Haar Cascade để phát hiện mặt
- Tăng số lần jitter khi encode
- Xử lý ảnh ở độ phân giải cao hơn
"""

import os
import sys
# Cấu hình encoding UTF-8 cho Windows console
if sys.platform.startswith('win'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except AttributeError:
        pass

import pickle
import cv2
import numpy as np

try:
    import face_recognition
    FACE_LIB_AVAILABLE = True
except ImportError:
    FACE_LIB_AVAILABLE = False
    print("Chua cai face_recognition. Chay: pip install face-recognition --no-deps")

from config import (
    DATASET_DIR, ENCODINGS_FILE, ENCODINGS_DIR,
    FACE_RECOGNITION_TOLERANCE, FACE_RECOGNITION_MODEL,
    NUM_JITTERS, FACE_UPSCALE
)

# Tải Haar Cascade cho phát hiện khuôn mặt dự phòng
HAAR_CASCADE = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")


def safe_print(message, end="\n"):
    """In log an toàn, tự động loại bỏ ký tự unicode nếu console không hỗ trợ"""
    try:
        print(message, end=end)
    except UnicodeEncodeError:
        try:
            import unicodedata
            normalized = unicodedata.normalize('NFKD', message)
            ascii_msg = "".join([c for c in normalized if not unicodedata.combining(c)])
            print(ascii_msg.encode('ascii', 'ignore').decode('ascii'), end=end)
        except Exception:
            try:
                print(message.encode('ascii', 'ignore').decode('ascii'), end=end)
            except Exception:
                pass


def preprocess_frame(frame):
    """
    Tiền xử lý ảnh để cải thiện nhận diện:
    - Cân bằng histogram (tăng tương phản)
    - Điều chỉnh sáng cho ảnh ngược sáng
    """
    # Chuyển sang LAB color space
    lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)

    # CLAHE - Cân bằng histogram thích ứng (xử lý ngược sáng rất tốt)
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
    l = clahe.apply(l)

    # Ghép lại và chuyển về BGR
    lab = cv2.merge([l, a, b])
    enhanced = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)

    return enhanced


def detect_faces_haar(frame):
    """
    Phát hiện khuôn mặt bằng Haar Cascade (nhanh, ổn định).
    Dùng làm phương pháp dự phòng khi face_recognition không tìm thấy.
    
    Returns:
        List of (top, right, bottom, left) giống format face_recognition
    """
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    gray = cv2.equalizeHist(gray)

    faces = HAAR_CASCADE.detectMultiScale(
        gray,
        scaleFactor=1.1,
        minNeighbors=5,
        minSize=(60, 60),
        flags=cv2.CASCADE_SCALE_IMAGE
    )

    # Chuyển format (x, y, w, h) → (top, right, bottom, left)
    locations = []
    for (x, y, w, h) in faces:
        locations.append((y, x + w, y + h, x))

    return locations


class FaceEngine:
    """
    Engine nhận diện khuôn mặt - Phiên bản nâng cấp.
    
    Cải thiện:
    - Tiền xử lý ảnh (CLAHE) cho điều kiện ánh sáng khó
    - Dual detection: face_recognition + Haar Cascade fallback  
    - Xử lý ở độ phân giải 75% thay vì 50%
    - Tăng jitter khi encode để chính xác hơn
    - Voting system: chọn kết quả phổ biến nhất
    """

    def __init__(self):
        self.known_encodings = []
        self.known_student_codes = []
        self.known_names = []
        self.is_loaded = False
        # Cache kết quả gần nhất (dùng để ổn định nhận dạng)
        self._last_results = {}
        self._recognition_history = {}  # {student_code: count}

    def load_encodings(self):
        """Tải file encoding đã train"""
        if not os.path.exists(ENCODINGS_FILE):
            print("Chua co file encoding. Hay chay train_model.py truoc!")
            return False

        try:
            with open(ENCODINGS_FILE, "rb") as f:
                data = pickle.load(f)

            self.known_encodings = data["encodings"]
            self.known_student_codes = data["student_codes"]
            self.known_names = data["names"]
            self.is_loaded = True

            unique_students = len(set(self.known_student_codes))
            print(f"Da tai {len(self.known_encodings)} encoding cua {unique_students} sinh vien")
            return True
        except Exception as e:
            print(f"Loi tai encoding: {e}")
            return False

    def train_from_dataset(self):
        """
        Train model từ thư mục dataset.
        Sử dụng num_jitters để tăng độ chính xác encoding.
        """
        if not FACE_LIB_AVAILABLE:
            print("Can cai dat face_recognition!")
            return False

        encodings = []
        student_codes = []
        names = []

        if not os.path.exists(DATASET_DIR):
            print(f"Thu muc dataset khong ton tai: {DATASET_DIR}")
            return False

        student_dirs = [d for d in os.listdir(DATASET_DIR)
                        if os.path.isdir(os.path.join(DATASET_DIR, d))]

        if not student_dirs:
            print("Khong co du lieu sinh vien trong dataset/")
            return False

        safe_print(f"Bat dau train {len(student_dirs)} sinh vien...")

        for student_dir in student_dirs:
            parts = student_dir.split("_", 1)
            student_code = parts[0]
            student_name = parts[1].replace("_", " ") if len(parts) > 1 else student_code

            student_path = os.path.join(DATASET_DIR, student_dir)
            image_files = [f for f in os.listdir(student_path)
                           if f.lower().endswith(('.jpg', '.jpeg', '.png'))]

            safe_print(f"  {student_name} ({student_code}): {len(image_files)} anh", end="")

            face_count = 0
            for img_file in image_files:
                img_path = os.path.join(student_path, img_file)

                # Đọc ảnh bằng OpenCV để tiền xử lý
                img_bgr = cv2.imread(img_path)
                if img_bgr is None:
                    continue

                # Tiền xử lý: cân bằng sáng
                img_enhanced = preprocess_frame(img_bgr)

                # Chuyển BGR → RGB cho face_recognition
                img_rgb = cv2.cvtColor(img_enhanced, cv2.COLOR_BGR2RGB)

                # Phát hiện khuôn mặt
                face_locs = face_recognition.face_locations(img_rgb, model=FACE_RECOGNITION_MODEL,
                                                            number_of_times_to_upsample=FACE_UPSCALE)

                if not face_locs:
                    # Thử với ảnh gốc (không enhance)
                    img_rgb_orig = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
                    face_locs = face_recognition.face_locations(img_rgb_orig, model=FACE_RECOGNITION_MODEL,
                                                                number_of_times_to_upsample=FACE_UPSCALE)

                if face_locs:
                    # Encode với num_jitters cao hơn = chính xác hơn (nhưng chậm hơn)
                    face_encs = face_recognition.face_encodings(
                        img_rgb, face_locs, num_jitters=NUM_JITTERS
                    )

                    for enc in face_encs:
                        encodings.append(enc)
                        student_codes.append(student_code)
                        names.append(student_name)
                        face_count += 1

            status = f" -> {face_count} khuon mat OK" if face_count > 0 else " -> KHONG TIM THAY khuon mat"
            safe_print(status)

        if not encodings:
            safe_print("Khong encode duoc khuon mat nao!")
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

        unique = len(set(student_codes))
        safe_print(f"\nTrain hoan tat! {len(encodings)} encoding cua {unique} sinh vien")
        return True

    def detect_faces(self, frame):
        """
        Phát hiện khuôn mặt - kết hợp 2 phương pháp:
        1. face_recognition (chính xác hơn)
        2. Haar Cascade (fallback, nhanh hơn)
        """
        if not FACE_LIB_AVAILABLE:
            return detect_faces_haar(frame)

        # Tiền xử lý
        enhanced = preprocess_frame(frame)
        rgb_frame = cv2.cvtColor(enhanced, cv2.COLOR_BGR2RGB)

        # Thử face_recognition trước
        face_locations = face_recognition.face_locations(
            rgb_frame, model=FACE_RECOGNITION_MODEL,
            number_of_times_to_upsample=1
        )

        # Nếu không tìm thấy, thử Haar Cascade
        if not face_locations:
            face_locations = detect_faces_haar(frame)

        # Nếu vẫn không, thử face_recognition với upsample=2
        if not face_locations:
            face_locations = face_recognition.face_locations(
                rgb_frame, model=FACE_RECOGNITION_MODEL,
                number_of_times_to_upsample=2
            )

        return face_locations

    def recognize(self, frame):
        """
        Nhận diện khuôn mặt - phiên bản nâng cấp.
        
        Cải thiện:
        - Tiền xử lý ảnh (CLAHE) trước khi nhận diện
        - Xử lý ở 75% resolution (thay vì 50%)
        - Dual detection fallback
        - Tính confidence chính xác hơn
        """
        if not FACE_LIB_AVAILABLE or not self.is_loaded:
            return []

        # Tiền xử lý: cân bằng sáng
        enhanced = preprocess_frame(frame)

        # Chuyển BGR → RGB
        rgb_frame = cv2.cvtColor(enhanced, cv2.COLOR_BGR2RGB)

        # Tự động tính toán tỉ lệ scale phù hợp: Chỉ scale nếu ảnh quá to (ví dụ > 800px)
        # Giúp bảo toàn độ sắc nét tối đa cho các webcam chuẩn 640x480
        h, w = rgb_frame.shape[:2]
        if w > 800:
            scale = 800.0 / w
            small_frame = cv2.resize(rgb_frame, (0, 0), fx=scale, fy=scale)
        else:
            scale = 1.0
            small_frame = rgb_frame

        # Phát hiện khuôn mặt
        face_locations = face_recognition.face_locations(
            small_frame, model=FACE_RECOGNITION_MODEL,
            number_of_times_to_upsample=1
        )

        # Fallback: Haar Cascade nếu không tìm thấy
        if not face_locations:
            if scale != 1.0:
                small_bgr = cv2.resize(enhanced, (0, 0), fx=scale, fy=scale)
            else:
                small_bgr = enhanced
            haar_locs = detect_faces_haar(small_bgr)
            if haar_locs:
                face_locations = haar_locs

        # Fallback 2: thử upsample=2
        if not face_locations:
            face_locations = face_recognition.face_locations(
                small_frame, model=FACE_RECOGNITION_MODEL,
                number_of_times_to_upsample=2
            )

        if not face_locations:
            return []

        # Encode khuôn mặt đã tìm thấy
        face_encodings = face_recognition.face_recognition.face_encodings(small_frame, face_locations, num_jitters=1) if hasattr(face_recognition, 'face_recognition') else face_recognition.face_encodings(small_frame, face_locations, num_jitters=1)

        results = []
        inv_scale = 1.0 / scale

        for encoding, location in zip(face_encodings, face_locations):
            # So khớp với tất cả khuôn mặt đã đăng ký
            distances = face_recognition.face_distance(self.known_encodings, encoding)

            student_code = "Unknown"
            name = "Khong xac dinh"
            confidence = 0.0

            if len(distances) > 0:
                best_match_idx = np.argmin(distances)
                best_distance = distances[best_match_idx]

                # Kiểm tra với tolerance
                if best_distance <= FACE_RECOGNITION_TOLERANCE:
                    student_code = self.known_student_codes[best_match_idx]
                    name = self.known_names[best_match_idx]
                    confidence = round(1 - best_distance, 2)

                    # Cập nhật lịch sử nhận diện (ổn định kết quả)
                    self._recognition_history[student_code] = \
                        self._recognition_history.get(student_code, 0) + 1

            # Scale lại vị trí cho frame gốc
            top, right, bottom, left = [int(v * inv_scale) for v in location]

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
            color = (0, 220, 0) if is_known else (0, 0, 255)

            # Vẽ khung khuôn mặt (dày hơn)
            cv2.rectangle(frame, (left, top), (right, bottom), color, 2)

            # Vẽ nền cho text
            if is_known:
                label = f"{name} ({confidence*100:.0f}%)"
            else:
                label = "Unknown"

            # Tính kích thước text
            (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
            cv2.rectangle(frame, (left, bottom), (left + tw + 10, bottom + th + 16), color, cv2.FILLED)
            cv2.putText(frame, label, (left + 5, bottom + th + 8),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

        return frame


# Instance toàn cục
face_engine = FaceEngine()
