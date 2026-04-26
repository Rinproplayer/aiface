# 🎓 AI Face Recognition Attendance System
## Hệ thống điểm danh sinh viên bằng nhận diện khuôn mặt

### 📋 Mô tả
Hệ thống sử dụng AI nhận diện khuôn mặt để tự động điểm danh sinh viên khi vào lớp. Giảng viên có thể quản lý sinh viên, lớp học và xem báo cáo điểm danh qua web dashboard.

### ⚙️ Công nghệ sử dụng
- **AI/CV**: face_recognition, OpenCV, dlib
- **Backend**: FastAPI, WebSocket
- **Frontend**: HTML, CSS, JavaScript
- **Database**: MySQL
- **Auth**: JWT Token

---

## 🚀 Hướng dẫn cài đặt

### Bước 1: Cài đặt thư viện Python
```bash
cd d:\AIFace
pip install -r requirements.txt
```

> ⚠️ Nếu lỗi khi cài `dlib`, cần cài trước:
> - Visual Studio Build Tools (Desktop C++)
> - CMake

### Bước 2: Tạo Database MySQL
```bash
mysql -u root -p < setup_database.sql
```
Hoặc mở MySQL Workbench → chạy nội dung file `setup_database.sql`

### Bước 3: Cấu hình
Mở file `config.py`, sửa password MySQL:
```python
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "your_password_here",  # ← Sửa ở đây
    "database": "aiface_db",
}
```

---

## 📖 Hướng dẫn sử dụng

### 1. Chạy Web Dashboard
```bash
python server.py
```
Mở trình duyệt: http://localhost:8000
- **Tài khoản**: admin / admin123

### 2. Đăng ký khuôn mặt sinh viên
```bash
python register_face.py
```

### 3. Train model nhận diện
```bash
python train_model.py
```

### 4. Bắt đầu điểm danh
```bash
python main.py
```

---

## 📁 Cấu trúc dự án
```
AIFace/
├── main.py              # Điểm danh qua webcam
├── register_face.py     # Đăng ký khuôn mặt
├── train_model.py       # Train model
├── server.py            # API server + WebSocket
├── config.py            # Cấu hình
├── database.py          # Thao tác MySQL
├── auth.py              # JWT authentication
├── face_engine.py       # Engine nhận diện
├── web/                 # Web Dashboard
├── dataset/             # Ảnh khuôn mặt
├── encodings/           # Model đã train
└── exports/             # File Excel xuất ra
```
