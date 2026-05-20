"""
Cấu hình hệ thống AI Điểm Danh
================================
"""

import os

# === Thư mục gốc của dự án ===
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# === Cấu hình MySQL ===
DB_CONFIG = {
    "host": "localhost",
    "port": 3306,
    "user": "root",
    "password": "",
    "database": "aiface_db",
}

# === Cấu hình đường dẫn ===
DATASET_DIR = os.path.join(BASE_DIR, "dataset")
ENCODINGS_DIR = os.path.join(BASE_DIR, "encodings")
ENCODINGS_FILE = os.path.join(ENCODINGS_DIR, "face_encodings.pkl")
EXPORTS_DIR = os.path.join(BASE_DIR, "exports")

# === Cấu hình nhận diện khuôn mặt ===
FACE_RECOGNITION_TOLERANCE = 0.58      # Cân bằng hoàn hảo giữa độ nhạy và chống nhận nhầm
FACE_RECOGNITION_MODEL = "hog"         # "hog" (nhanh) hoặc "cnn" (chính xác, cần GPU)
NUM_PHOTOS_PER_STUDENT = 10            # Số ảnh tối đa để nhận chính xác hơn
NUM_JITTERS = 10                       # Tăng lên 10 để trích xuất vec-tơ khuôn mặt cực kỳ ổn định và chống nhiễu
FACE_UPSCALE = 2                       # Phóng to ảnh để phát hiện mặt nhỏ

# === Cấu hình Camera ===
CAMERA_INDEX = 0
CAMERA_WIDTH = 640
CAMERA_HEIGHT = 480

# === Cấu hình điểm danh ===
LATE_THRESHOLD_MINUTES = 15

# === Cấu hình JWT ===
SECRET_KEY = "aiface-secret-key-change-this-in-production-2024"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 480

# === Cấu hình Server ===
SERVER_HOST = "0.0.0.0"
SERVER_PORT = 8000

# === Tạo các thư mục cần thiết ===
for dir_path in [DATASET_DIR, ENCODINGS_DIR, EXPORTS_DIR]:
    os.makedirs(dir_path, exist_ok=True)
