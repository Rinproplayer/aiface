"""
FastAPI Server - API Backend + WebSocket
==========================================
Cung cấp REST API cho Web Dashboard và WebSocket cho realtime updates.
Sử dụng: python server.py
"""

import sys
# Cấu hình encoding UTF-8 cho Windows console
if sys.platform.startswith('win'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except AttributeError:
        pass

import os
import json
import asyncio
from datetime import datetime, date
from typing import Optional, List

from fastapi import FastAPI, HTTPException, Depends, WebSocket, WebSocketDisconnect, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from pydantic import BaseModel

import pandas as pd
from config import SERVER_HOST, SERVER_PORT, EXPORTS_DIR, BASE_DIR
from database import (
    get_lecturer_by_username, get_lecturer_by_id,
    get_all_students, get_student_by_id, add_student, update_student, delete_student,
    get_students_by_class, update_face_registered,
    get_all_classes, get_class_by_id, add_class, update_class, delete_class,
    get_classes_by_lecturer,
    enroll_student, unenroll_student,
    mark_attendance, get_attendance_by_class_date, get_attendance_summary,
    get_dashboard_stats, get_recent_attendance, get_all_lecturers,
    add_lecturer, update_lecturer, change_lecturer_password, delete_lecturer
)
from auth import verify_password, hash_password, create_access_token, decode_token

# ============================================
# Khởi tạo FastAPI
# ============================================
app = FastAPI(
    title="AI Face Recognition Attendance System",
    description="Hệ thống điểm danh sinh viên bằng nhận diện khuôn mặt",
    version="1.0.0"
)

# Cho phép CORS (để web dashboard gọi API)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Tắt cache trình duyệt (dev mode) - bỏ qua WebSocket
class NoCacheMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Bỏ qua WebSocket requests (không thể thêm headers)
        if request.headers.get("upgrade", "").lower() == "websocket":
            return await call_next(request)
        response = await call_next(request)
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        return response

app.add_middleware(NoCacheMiddleware)

# Phục vụ file tĩnh (Web Dashboard)
web_dir = os.path.join(BASE_DIR, "web")
if os.path.exists(web_dir):
    app.mount("/web", StaticFiles(directory=web_dir), name="web")

if os.path.exists(EXPORTS_DIR):
    app.mount("/exports", StaticFiles(directory=EXPORTS_DIR), name="exports")


# ============================================
# Pydantic Models (Định nghĩa cấu trúc dữ liệu)
# ============================================

class LoginRequest(BaseModel):
    username: str
    password: str

class StudentCreate(BaseModel):
    student_code: str
    full_name: str
    email: str = ""
    phone: str = ""

class StudentUpdate(BaseModel):
    student_code: str
    full_name: str
    email: str = ""
    phone: str = ""

class ClassCreate(BaseModel):
    class_code: str
    class_name: str
    lecturer_id: Optional[int] = None
    schedule: str = ""
    room: str = ""

class ClassUpdate(BaseModel):
    class_code: str
    class_name: str
    lecturer_id: Optional[int] = None
    schedule: str = ""
    room: str = ""

class EnrollRequest(BaseModel):
    student_id: int
    class_id: int

class AttendanceNotify(BaseModel):
    student_code: str
    student_name: str
    class_id: int
    confidence: float
    time: str

class RegisterRequest(BaseModel):
    username: str
    password: str
    full_name: str
    email: str = ""

class ProfileUpdate(BaseModel):
    full_name: str
    email: str = ""

class PasswordChange(BaseModel):
    old_password: str
    new_password: str

class LecturerCreate(BaseModel):
    username: str
    password: str
    full_name: str
    email: str = ""
    role: str = "lecturer"

class FaceRegisterRequest(BaseModel):
    images: List[str]

class ManualAttendanceRequest(BaseModel):
    student_id: int
    class_id: int
    status: str
    date: Optional[str] = None

class RecognizeFrameRequest(BaseModel):
    image: str
    class_id: int


# ============================================
# WebSocket Manager (Quản lý kết nối realtime)
# ============================================

class ConnectionManager:
    """Quản lý các kết nối WebSocket"""

    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        """Chấp nhận kết nối WebSocket mới"""
        await websocket.accept()
        self.active_connections.append(websocket)
        print(f"[WS] WebSocket connected. Total: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        """Xóa kết nối đã đóng"""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        print(f"[WS] WebSocket disconnected. Total: {len(self.active_connections)}")

    async def broadcast(self, message: dict):
        """Gửi message đến tất cả client đang kết nối"""
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                disconnected.append(connection)
        
        # Xóa các kết nối đã mất
        for conn in disconnected:
            self.disconnect(conn)


manager = ConnectionManager()


# ============================================
# Helper Functions
# ============================================

def get_current_user(token: str):
    """Xác thực token và lấy thông tin user"""
    if not token:
        return None
    payload = decode_token(token)
    if not payload:
        return None
    user_id = payload.get("sub")
    if not user_id:
        return None
    return get_lecturer_by_id(int(user_id))


def serialize_row(row):
    """Chuyển đổi các giá trị datetime/date trong dict thành string"""
    if not row:
        return row
    result = {}
    for key, value in row.items():
        if isinstance(value, (datetime, date)):
            result[key] = value.isoformat()
        else:
            result[key] = value
    return result


def serialize_rows(rows):
    """Chuyển đổi danh sách dict"""
    return [serialize_row(row) for row in rows]


# ============================================
# API: Authentication (Đăng nhập)
# ============================================

@app.post("/api/auth/login")
async def login(request: LoginRequest):
    """Đăng nhập giảng viên"""
    user = get_lecturer_by_username(request.username)
    if not user:
        raise HTTPException(status_code=401, detail="Tên đăng nhập không tồn tại")

    if not verify_password(request.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Mật khẩu không đúng")

    # Tạo JWT token (bao gồm role)
    token = create_access_token(data={"sub": str(user["id"]), "role": user.get("role", "lecturer")})

    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user["id"],
            "username": user["username"],
            "full_name": user["full_name"],
            "email": user["email"],
            "role": user.get("role", "lecturer")
        }
    }

@app.post("/api/auth/register")
async def register(request: RegisterRequest):
    """Đăng ký tài khoản giảng viên mới"""
    # Kiểm tra username đã tồn tại
    existing = get_lecturer_by_username(request.username)
    if existing:
        raise HTTPException(status_code=400, detail="Tên đăng nhập đã tồn tại")

    if len(request.password) < 6:
        raise HTTPException(status_code=400, detail="Mật khẩu phải từ 6 ký tự trở lên")

    hashed = hash_password(request.password)
    lecturer_id = add_lecturer(request.username, hashed, request.full_name, request.email)

    if not lecturer_id:
        raise HTTPException(status_code=400, detail="Không thể tạo tài khoản")

    return {"id": lecturer_id, "message": "Đăng ký thành công"}

@app.get("/api/auth/me")
async def get_me(token: str = Query(None)):
    """Lấy thông tin user hiện tại"""
    user = get_current_user(token)
    if not user:
        raise HTTPException(status_code=401, detail="Token không hợp lệ")
    return serialize_row(user)

@app.put("/api/auth/profile")
async def update_profile(data: ProfileUpdate, token: str = Query(None)):
    """Cập nhật thông tin cá nhân"""
    user = get_current_user(token)
    if not user:
        raise HTTPException(status_code=401, detail="Token không hợp lệ")

    success = update_lecturer(user["id"], data.full_name, data.email)
    if not success:
        raise HTTPException(status_code=400, detail="Không thể cập nhật")
    return {"message": "Cập nhật thành công"}

@app.put("/api/auth/password")
async def change_password(data: PasswordChange, token: str = Query(None)):
    """Đổi mật khẩu"""
    user = get_current_user(token)
    if not user:
        raise HTTPException(status_code=401, detail="Token không hợp lệ")

    # Lấy user đầy đủ (có password_hash)
    full_user = get_lecturer_by_username(user["username"])
    if not verify_password(data.old_password, full_user["password_hash"]):
        raise HTTPException(status_code=400, detail="Mật khẩu cũ không đúng")

    if len(data.new_password) < 6:
        raise HTTPException(status_code=400, detail="Mật khẩu mới phải từ 6 ký tự")

    new_hash = hash_password(data.new_password)
    success = change_lecturer_password(user["id"], new_hash)
    if not success:
        raise HTTPException(status_code=400, detail="Không thể đổi mật khẩu")
    return {"message": "Đổi mật khẩu thành công"}


# ============================================
# API: Lecturers Management (Admin only)
# ============================================

@app.get("/api/lecturers")
async def list_lecturers():
    """Lấy danh sách giảng viên"""
    lecturers = get_all_lecturers()
    return serialize_rows(lecturers)

@app.post("/api/lecturers")
async def create_lecturer(data: LecturerCreate, token: str = Query(None)):
    """Admin: Thêm giảng viên mới"""
    user = get_current_user(token)
    if not user or user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Chỉ admin mới có quyền")

    existing = get_lecturer_by_username(data.username)
    if existing:
        raise HTTPException(status_code=400, detail="Tên đăng nhập đã tồn tại")

    hashed = hash_password(data.password)
    lid = add_lecturer(data.username, hashed, data.full_name, data.email, data.role)
    if not lid:
        raise HTTPException(status_code=400, detail="Không thể thêm giảng viên")
    return {"id": lid, "message": "Thêm giảng viên thành công"}

@app.delete("/api/lecturers/{lecturer_id}")
async def remove_lecturer(lecturer_id: int, token: str = Query(None)):
    """Admin: Xóa giảng viên"""
    user = get_current_user(token)
    if not user or user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Chỉ admin mới có quyền")

    if user["id"] == lecturer_id:
        raise HTTPException(status_code=400, detail="Không thể tự xóa chính mình")

    success = delete_lecturer(lecturer_id)
    if not success:
        raise HTTPException(status_code=400, detail="Không thể xóa")
    return {"message": "Xóa giảng viên thành công"}


# ============================================
# API: Dashboard (Tổng quan)
# ============================================

@app.get("/api/dashboard/stats")
async def dashboard_stats(token: Optional[str] = Query(None)):
    """Lấy thống kê tổng quan (phân quyền theo role)"""
    lecturer_id = None
    if token:
        user = get_current_user(token)
        if user and user.get("role") != "admin":
            lecturer_id = user.get("id")

    stats = get_dashboard_stats(lecturer_id)
    if stats.get("weekly_attendance"):
        stats["weekly_attendance"] = serialize_rows(stats["weekly_attendance"])
    return stats

@app.get("/api/dashboard/recent")
async def dashboard_recent(limit: int = 10, token: Optional[str] = Query(None)):
    """Lấy hoạt động điểm danh gần nhất (phân quyền theo role)"""
    lecturer_id = None
    if token:
        user = get_current_user(token)
        if user and user.get("role") != "admin":
            lecturer_id = user.get("id")

    data = get_recent_attendance(limit, lecturer_id)
    return serialize_rows(data)


@app.get("/api/dashboard/charts")
async def dashboard_charts(token: Optional[str] = Query(None)):
    """Lấy dữ liệu biểu đồ (phân quyền theo role)"""
    lecturer_id = None
    if token:
        user = get_current_user(token)
        if user and user.get("role") != "admin":
            lecturer_id = user.get("id")

    from database import get_dashboard_charts
    data = get_dashboard_charts(lecturer_id)
    return data


@app.get("/api/dashboard/timetable")
async def dashboard_timetable(token: Optional[str] = Query(None)):
    """Lấy dữ liệu thời khóa biểu (phân quyền theo role)"""
    lecturer_id = None
    if token:
        user = get_current_user(token)
        if user and user.get("role") != "admin":
            lecturer_id = user.get("id")

    from database import get_lecturer_timetable
    data = get_lecturer_timetable(lecturer_id)
    return serialize_rows(data)


# ============================================
# API: Students (Sinh viên)
# ============================================

@app.get("/api/students")
async def list_students():
    """Lấy danh sách tất cả sinh viên"""
    students = get_all_students()
    return serialize_rows(students)

@app.get("/api/students/{student_id}")
async def get_student(student_id: int):
    """Lấy thông tin một sinh viên"""
    student = get_student_by_id(student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Không tìm thấy sinh viên")
    return serialize_row(student)

@app.post("/api/students")
async def create_student(data: StudentCreate):
    """Thêm sinh viên mới"""
    student_id = add_student(data.student_code, data.full_name, data.email, data.phone)
    if not student_id:
        raise HTTPException(status_code=400, detail="Không thể thêm sinh viên (mã SV có thể đã tồn tại)")
    return {"id": student_id, "message": "Thêm sinh viên thành công"}

@app.put("/api/students/{student_id}")
async def edit_student(student_id: int, data: StudentUpdate):
    """Cập nhật thông tin sinh viên"""
    success = update_student(student_id, data.student_code, data.full_name, data.email, data.phone)
    if not success:
        raise HTTPException(status_code=400, detail="Không thể cập nhật sinh viên")
    return {"message": "Cập nhật thành công"}

@app.delete("/api/students/{student_id}")
async def remove_student(student_id: int):
    """Xóa sinh viên"""
    success = delete_student(student_id)
    if not success:
        raise HTTPException(status_code=400, detail="Không thể xóa sinh viên")
    return {"message": "Xóa sinh viên thành công"}


@app.post("/api/students/{student_id}/register-face")
async def register_face_api(student_id: int, data: FaceRegisterRequest):
    """Đăng ký khuôn mặt từ webcam trình duyệt"""
    import base64
    import threading
    from config import DATASET_DIR
    from face_engine import preprocess_frame, FaceEngine
    import cv2
    import numpy as np

    student = get_student_by_id(student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Không tìm thấy sinh viên")

    student_code = student["student_code"]
    full_name = student["full_name"]
    folder_name = f"{student_code}_{full_name.replace(' ', '_')}"
    student_dir = os.path.join(DATASET_DIR, folder_name)
    os.makedirs(student_dir, exist_ok=True)

    photo_count = 0
    for img_base64 in data.images:
        if "," in img_base64:
            img_base64 = img_base64.split(",")[1]
        
        try:
            img_data = base64.b64decode(img_base64)
            nparr = np.frombuffer(img_data, np.uint8)
            frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            if frame is None:
                continue
            
            photo_count += 1
            photo_path = os.path.join(student_dir, f"{photo_count}.jpg")
            cv2.imwrite(photo_path, frame)

            enhanced = preprocess_frame(frame)
            enhanced_path = os.path.join(student_dir, f"{photo_count}_enhanced.jpg")
            cv2.imwrite(enhanced_path, enhanced)
        except Exception as e:
            print(f"❌ Lỗi xử lý ảnh: {e}")
            continue

    if photo_count > 0:
        first_photo = os.path.join(student_dir, "1.jpg")
        update_face_registered(student_id, True, first_photo)
        
        def bg_train():
            print("🚀 Bắt đầu train model từ background thread...")
            try:
                engine = FaceEngine()
                engine.train_from_dataset()
                print("✅ Train model từ background thành công!")
            except Exception as ex:
                print(f"❌ Lỗi khi train model: {ex}")

        threading.Thread(target=bg_train, daemon=True).start()

        return {"message": f"Đăng ký khuôn mặt thành công! Đã lưu {photo_count} ảnh và đang huấn luyện model..."}
    else:
        raise HTTPException(status_code=400, detail="Không có ảnh hợp lệ để đăng ký")


# ============================================
# API: Classes (Lớp học)
# ============================================

@app.get("/api/classes")
async def list_classes(token: Optional[str] = Query(None)):
    """Lấy danh sách lớp học (phân quyền theo role)"""
    if token:
        user = get_current_user(token)
        if user and user.get("role") != "admin":
            classes = get_classes_by_lecturer(user.get("id"))
            return serialize_rows(classes)
    
    classes = get_all_classes()
    return serialize_rows(classes)

@app.get("/api/classes/{class_id}")
async def get_class(class_id: int):
    """Lấy thông tin một lớp học"""
    cls = get_class_by_id(class_id)
    if not cls:
        raise HTTPException(status_code=404, detail="Không tìm thấy lớp học")
    return serialize_row(cls)

@app.post("/api/classes")
async def create_class(data: ClassCreate):
    """Thêm lớp học mới"""
    class_id = add_class(data.class_code, data.class_name, data.lecturer_id, data.schedule, data.room)
    if not class_id:
        raise HTTPException(status_code=400, detail="Không thể thêm lớp (mã lớp có thể đã tồn tại)")
    return {"id": class_id, "message": "Thêm lớp học thành công"}

@app.put("/api/classes/{class_id}")
async def edit_class(class_id: int, data: ClassUpdate):
    """Cập nhật thông tin lớp học"""
    success = update_class(class_id, data.class_code, data.class_name, data.lecturer_id, data.schedule, data.room)
    if not success:
        raise HTTPException(status_code=400, detail="Không thể cập nhật lớp")
    return {"message": "Cập nhật thành công"}

@app.delete("/api/classes/{class_id}")
async def remove_class(class_id: int):
    """Xóa lớp học"""
    success = delete_class(class_id)
    if not success:
        raise HTTPException(status_code=400, detail="Không thể xóa lớp")
    return {"message": "Xóa lớp học thành công"}

@app.get("/api/classes/{class_id}/students")
async def list_class_students(class_id: int):
    """Lấy danh sách sinh viên của một lớp"""
    students = get_students_by_class(class_id)
    return serialize_rows(students)

@app.get("/api/lecturers")
async def list_lecturers():
    """Lấy danh sách giảng viên"""
    lecturers = get_all_lecturers()
    return serialize_rows(lecturers)


# ============================================
# API: Enrollment (Đăng ký lớp)
# ============================================

@app.post("/api/enrollment")
async def enroll(data: EnrollRequest):
    """Đăng ký sinh viên vào lớp"""
    success = enroll_student(data.student_id, data.class_id)
    if not success:
        raise HTTPException(status_code=400, detail="Không thể đăng ký")
    return {"message": "Đăng ký lớp thành công"}

@app.delete("/api/enrollment")
async def unenroll(student_id: int = Query(...), class_id: int = Query(...)):
    """Hủy đăng ký sinh viên khỏi lớp"""
    success = unenroll_student(student_id, class_id)
    if not success:
        raise HTTPException(status_code=400, detail="Không thể hủy đăng ký")
    return {"message": "Hủy đăng ký thành công"}


# ============================================
# API: Attendance (Điểm danh)
# ============================================

@app.get("/api/attendance")
async def list_attendance(class_id: int = Query(...), date: str = Query(None)):
    """Lấy danh sách điểm danh theo lớp và ngày"""
    from datetime import date as date_type
    target_date = None
    if date:
        try:
            target_date = date_type.fromisoformat(date)
        except ValueError:
            raise HTTPException(status_code=400, detail="Định dạng ngày không hợp lệ (YYYY-MM-DD)")

    data = get_attendance_by_class_date(class_id, target_date)
    return serialize_rows(data)

@app.get("/api/attendance/summary")
async def attendance_summary(class_id: int = Query(...)):
    """Lấy thống kê tổng hợp điểm danh theo lớp"""
    data = get_attendance_summary(class_id)
    return serialize_rows(data)

@app.get("/api/attendance/student/{student_id}")
async def list_student_attendance(student_id: int, class_id: Optional[int] = Query(None)):
    """Lấy lịch sử điểm danh của một sinh viên"""
    from database import get_attendance_by_student
    data = get_attendance_by_student(student_id, class_id)
    return serialize_rows(data)

@app.post("/api/attendance/manual")
async def manual_mark_attendance(data: ManualAttendanceRequest):
    """Điểm danh thủ công hoặc sửa trạng thái điểm danh của sinh viên"""
    from database import get_student_by_id, get_class_by_id, get_connection
    from datetime import datetime, date as date_type
    
    student = get_student_by_id(data.student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Không tìm thấy sinh viên")
        
    cls = get_class_by_id(data.class_id)
    if not cls:
        raise HTTPException(status_code=404, detail="Không tìm thấy lớp học")
        
    target_date = date_type.today()
    if data.date:
        try:
            target_date = date_type.fromisoformat(data.date)
        except ValueError:
            raise HTTPException(status_code=400, detail="Định dạng ngày không hợp lệ")

    conn = get_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Không thể kết nối cơ sở dữ liệu")
        
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT id FROM attendance WHERE student_id = %s AND class_id = %s AND date = %s",
            (data.student_id, data.class_id, target_date)
        )
        existing = cursor.fetchone()
        
        now = datetime.now()
        check_in_time = datetime.combine(target_date, now.time())
        
        if existing:
            cursor.execute(
                "UPDATE attendance SET status = %s, check_in_time = %s WHERE id = %s",
                (data.status, check_in_time, existing["id"])
            )
            conn.commit()
            message = "Cập nhật trạng thái thành công"
        else:
            cursor.execute(
                """INSERT INTO attendance (student_id, class_id, date, check_in_time, status, confidence) 
                   VALUES (%s, %s, %s, %s, %s, %s)""",
                (data.student_id, data.class_id, target_date, check_in_time, data.status, 1.0)
            )
            conn.commit()
            message = "Ghi nhận điểm danh thành công"
            
        websocket_message = {
            "type": "attendance",
            "student_code": student["student_code"],
            "student_name": student["full_name"],
            "class_id": data.class_id,
            "confidence": 1.0,
            "time": check_in_time.strftime("%H:%M:%S")
        }
        await manager.broadcast(websocket_message)
        
        return {"message": message}
    except Exception as e:
        print(f"Lỗi điểm danh thủ công: {e}")
        raise HTTPException(status_code=400, detail="Không thể lưu điểm danh")
    finally:
        conn.close()

@app.post("/api/attendance/recognize-frame")
async def recognize_frame_api(data: RecognizeFrameRequest):
    """Nhận diện khuôn mặt từ webcam trình duyệt và tự động điểm danh"""
    import base64
    import cv2
    import numpy as np
    from face_engine import FaceEngine
    from database import mark_attendance, get_student_by_code
    from datetime import datetime
    
    img_base64 = data.image
    if "," in img_base64:
        img_base64 = img_base64.split(",")[1]
        
    try:
        img_data = base64.b64decode(img_base64)
        nparr = np.frombuffer(img_data, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if frame is None:
            raise HTTPException(status_code=400, detail="Không thể giải mã ảnh")
            
        engine = FaceEngine()
        engine.load_encodings()
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        import face_recognition
        
        face_locations = face_recognition.face_locations(rgb_frame)
        face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)
        
        if not face_locations:
            return {"recognized": False, "message": "Không tìm thấy khuôn mặt"}
            
        recognized_students = []
        for face_encoding in face_encodings:
            if not engine.known_encodings:
                break
                
            from config import FACE_RECOGNITION_TOLERANCE
            matches = face_recognition.compare_faces(engine.known_encodings, face_encoding, tolerance=FACE_RECOGNITION_TOLERANCE)
            face_distances = face_recognition.face_distance(engine.known_encodings, face_encoding)
            
            if True in matches:
                best_match_index = np.argmin(face_distances)
                if matches[best_match_index]:
                    student_code = engine.known_student_codes[best_match_index]
                    student = get_student_by_code(student_code)
                    if student:
                        confidence = 1.0 - face_distances[best_match_index]
                        now = datetime.now()
                        status = "present"
                        
                        # Chuẩn bị lưu ảnh bằng chứng (Evidence Snapshot)
                        evidence_path = None
                        evidence_dir = os.path.join(EXPORTS_DIR, "evidence")
                        os.makedirs(evidence_dir, exist_ok=True)
                        evidence_filename = f"{student['student_code']}_{data.class_id}_{int(now.timestamp())}.jpg"
                        evidence_full_path = os.path.join(evidence_dir, evidence_filename)
                        
                        try:
                            # Lưu file ảnh frame camera
                            cv2.imwrite(evidence_full_path, frame)
                            evidence_path = f"/exports/evidence/{evidence_filename}"
                        except Exception as img_err:
                            print(f"❌ Lỗi ghi ảnh bằng chứng: {img_err}")
                            
                        success = mark_attendance(student["id"], data.class_id, float(confidence), status, evidence_path)
                        
                        if success:
                            websocket_message = {
                                "type": "attendance",
                                "student_code": student["student_code"],
                                "student_name": student["full_name"],
                                "class_id": data.class_id,
                                "confidence": float(confidence),
                                "time": now.strftime("%H:%M:%S"),
                                "evidence_path": evidence_path
                            }
                            await manager.broadcast(websocket_message)
                        
                        recognized_students.append({
                            "student_code": student["student_code"],
                            "full_name": student["full_name"],
                            "confidence": float(confidence),
                            "status": status,
                            "evidence_path": evidence_path,
                            "already_marked": not success
                        })
                        
        if recognized_students:
            return {
                "recognized": True, 
                "results": recognized_students, 
                "message": f"Nhận diện thành công: {', '.join([r['full_name'] for r in recognized_students])}"
            }
        else:
            return {"recognized": False, "message": "Khuôn mặt không khớp dữ liệu"}
            
    except Exception as e:
        print(f"Lỗi nhận diện qua Web: {e}")
        raise HTTPException(status_code=500, detail=f"Lỗi nhận diện: {str(e)}")

@app.post("/api/attendance/notify")
async def attendance_notify(data: AttendanceNotify):
    """Nhận thông báo điểm danh từ main.py và broadcast qua WebSocket"""
    message = {
        "type": "attendance",
        "student_code": data.student_code,
        "student_name": data.student_name,
        "class_id": data.class_id,
        "confidence": data.confidence,
        "time": data.time
    }
    await manager.broadcast(message)
    return {"message": "Notified"}


# ============================================
# API: Export (Xuất báo cáo)
# ============================================

@app.get("/api/export/attendance")
async def export_attendance(class_id: int = Query(...), date: str = Query(None)):
    """Xuất file Excel điểm danh"""
    from datetime import date as date_type
    target_date = None
    if date:
        try:
            target_date = date_type.fromisoformat(date)
        except ValueError:
            target_date = date_type.today()
    else:
        target_date = date_type.today()

    # Lấy dữ liệu
    data = get_attendance_by_class_date(class_id, target_date)
    cls = get_class_by_id(class_id)

    if not data:
        raise HTTPException(status_code=404, detail="Không có dữ liệu điểm danh")

    # Tạo DataFrame
    records = []
    for i, row in enumerate(data, 1):
        records.append({
            "STT": i,
            "Mã SV": row["student_code"],
            "Họ và tên": row["full_name"],
            "Thời gian": str(row["check_in_time"]),
            "Trạng thái": "Có mặt" if row["status"] == "present" else "Trễ",
            "Độ tin cậy": f"{row['confidence']*100:.0f}%"
        })

    df = pd.DataFrame(records)

    # Lưu file Excel
    class_code = cls["class_code"] if cls else "unknown"
    filename = f"diemdanh_{class_code}_{target_date.isoformat()}.xlsx"
    filepath = os.path.join(EXPORTS_DIR, filename)

    df.to_excel(filepath, index=False, sheet_name="Điểm danh")
    print(f"📥 Đã xuất file: {filepath}")

    return FileResponse(
        filepath,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        filename=filename
    )

@app.get("/api/export/summary")
async def export_summary(class_id: int = Query(...)):
    """Xuất file Excel tổng hợp điểm danh"""
    data = get_attendance_summary(class_id)
    cls = get_class_by_id(class_id)

    if not data:
        raise HTTPException(status_code=404, detail="Không có dữ liệu")

    records = []
    for i, row in enumerate(data, 1):
        total_sessions = row.get("total_sessions", 0)
        absent = total_sessions - row.get("total_attended", 0) if total_sessions else 0
        records.append({
            "STT": i,
            "Mã SV": row["student_code"],
            "Họ và tên": row["full_name"],
            "Số buổi có mặt": row.get("present_count", 0),
            "Số buổi trễ": row.get("late_count", 0),
            "Số buổi vắng": absent,
            "Tổng số buổi": total_sessions,
        })

    df = pd.DataFrame(records)

    class_code = cls["class_code"] if cls else "unknown"
    filename = f"tonghop_{class_code}.xlsx"
    filepath = os.path.join(EXPORTS_DIR, filename)

    df.to_excel(filepath, index=False, sheet_name="Tổng hợp")

    return FileResponse(
        filepath,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        filename=filename
    )


# ============================================
# WebSocket Endpoint
# ============================================

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint cho realtime updates"""
    await manager.connect(websocket)
    try:
        while True:
            # Nhận message từ client (keep-alive)
            data = await websocket.receive_text()
            # Echo hoặc xử lý message
            if data == "ping":
                await websocket.send_json({"type": "pong"})
    except WebSocketDisconnect:
        manager.disconnect(websocket)


# ============================================
# Serve Web Dashboard
# ============================================

@app.get("/")
async def root():
    """Redirect đến trang web dashboard"""
    return FileResponse(os.path.join(web_dir, "index.html"))

@app.get("/dashboard")
async def dashboard_page():
    return FileResponse(os.path.join(web_dir, "dashboard.html"))

@app.get("/students-page")
async def students_page():
    return FileResponse(os.path.join(web_dir, "students.html"))

@app.get("/classes-page")
async def classes_page():
    return FileResponse(os.path.join(web_dir, "classes.html"))

@app.get("/attendance-page")
async def attendance_page():
    return FileResponse(os.path.join(web_dir, "attendance.html"))

@app.get("/register-page")
async def register_page():
    return FileResponse(os.path.join(web_dir, "register.html"))

@app.get("/profile-page")
async def profile_page():
    return FileResponse(os.path.join(web_dir, "profile.html"))

@app.get("/lecturers-page")
async def lecturers_page():
    return FileResponse(os.path.join(web_dir, "lecturers.html"))


# ============================================
# Chạy Server
# ============================================

if __name__ == "__main__":
    import uvicorn
    print("=" * 50)
    print("AI FACE ATTENDANCE - API SERVER")
    print("=" * 50)
    print(f"Server: http://localhost:{SERVER_PORT}")
    print(f"API Docs: http://localhost:{SERVER_PORT}/docs")
    print(f"Dashboard: http://localhost:{SERVER_PORT}/")
    print("=" * 50)

    uvicorn.run(app, host=SERVER_HOST, port=SERVER_PORT, reload=False)
