"""
Cấu hình hệ thống AI Điểm Danh
================================
File này chứa tất cả các thiết lập cấu hình cho hệ thống.
Thay đổi các giá trị bên dưới cho phù hợp với môi trường của bạn.
"""

import os

# === Thư mục gốc của dự án ===
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# === Cấu hình MySQL ===
DB_CONFIG = {
    "host": "localhost",
    "port": 3306,
    "user": "root",           # Thay đổi nếu dùng user khác
    "password": "",            # Nhập mật khẩu MySQL của bạn
    "database": "aiface_db",
}

# === Cấu hình đường dẫn ===
DATASET_DIR = os.path.join(BASE_DIR, "dataset")          # Thư mục ảnh khuôn mặt
ENCODINGS_DIR = os.path.join(BASE_DIR, "encodings")       # Thư mục file encoding
ENCODINGS_FILE = os.path.join(ENCODINGS_DIR, "face_encodings.pkl")
EXPORTS_DIR = os.path.join(BASE_DIR, "exports")           # Thư mục xuất Excel

# === Cấu hình nhận diện khuôn mặt ===
FACE_RECOGNITION_TOLERANCE = 0.5    # Ngưỡng nhận diện (0.0 - 1.0, nhỏ hơn = chính xác hơn)
FACE_RECOGNITION_MODEL = "hog"      # "hog" (nhanh, CPU) hoặc "cnn" (chính xác, cần GPU)
NUM_PHOTOS_PER_STUDENT = 5          # Số ảnh chụp khi đăng ký khuôn mặt

# === Cấu hình Camera ===
CAMERA_INDEX = 0                    # Index webcam (0 = webcam mặc định)
CAMERA_WIDTH = 640                  # Độ rộng frame
CAMERA_HEIGHT = 480                 # Độ cao frame

# === Cấu hình điểm danh ===
LATE_THRESHOLD_MINUTES = 15         # Sau bao nhiêu phút tính là trễ

# === Cấu hình JWT (Authentication) ===
SECRET_KEY = "aiface-secret-key-change-this-in-production-2024"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 480   # Token hết hạn sau 8 giờ

# === Cấu hình Server ===
SERVER_HOST = "0.0.0.0"
SERVER_PORT = 8000

# === Tạo các thư mục cần thiết ===
for dir_path in [DATASET_DIR, ENCODINGS_DIR, EXPORTS_DIR]:
    os.makedirs(dir_path, exist_ok=True)
