"""
Module Database - Kết nối và thao tác MySQL
=============================================
Chứa tất cả các hàm thao tác với database:
- Kết nối MySQL
- CRUD sinh viên, lớp học, điểm danh
- Quản lý giảng viên
"""

import mysql.connector
from mysql.connector import Error
from datetime import datetime, date, timedelta
from config import DB_CONFIG


def get_connection():
    """Tạo kết nối đến MySQL database"""
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        return conn
    except Error as e:
        print(f"❌ Lỗi kết nối MySQL: {e}")
        print("💡 Hãy kiểm tra:")
        print("   1. MySQL Server đã chạy chưa?")
        print("   2. Username/password trong config.py đúng chưa?")
        print("   3. Database 'aiface_db' đã tạo chưa?")
        return None


def test_connection():
    """Kiểm tra kết nối database"""
    conn = get_connection()
    if conn:
        print("✅ Kết nối MySQL thành công!")
        conn.close()
        return True
    return False


# ============================================
# GIẢNG VIÊN (Lecturers)
# ============================================

def get_lecturer_by_username(username):
    """Tìm giảng viên theo username (dùng cho đăng nhập)"""
    conn = get_connection()
    if not conn:
        return None
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM lecturers WHERE username = %s", (username,))
        return cursor.fetchone()
    except Error as e:
        print(f"❌ Lỗi truy vấn giảng viên: {e}")
        return None
    finally:
        conn.close()


def get_lecturer_by_id(lecturer_id):
    """Tìm giảng viên theo ID"""
    conn = get_connection()
    if not conn:
        return None
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id, username, full_name, email, created_at FROM lecturers WHERE id = %s", (lecturer_id,))
        return cursor.fetchone()
    except Error as e:
        print(f"❌ Lỗi truy vấn giảng viên: {e}")
        return None
    finally:
        conn.close()


def get_all_lecturers():
    """Lấy danh sách tất cả giảng viên"""
    conn = get_connection()
    if not conn:
        return []
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id, username, full_name, email, created_at FROM lecturers ORDER BY id")
        return cursor.fetchall()
    except Error as e:
        print(f"❌ Lỗi: {e}")
        return []
    finally:
        conn.close()


# ============================================
# SINH VIÊN (Students)
# ============================================

def add_student(student_code, full_name, email="", phone=""):
    """Thêm sinh viên mới"""
    conn = get_connection()
    if not conn:
        return None
    try:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO students (student_code, full_name, email, phone) VALUES (%s, %s, %s, %s)",
            (student_code, full_name, email, phone)
        )
        conn.commit()
        print(f"✅ Đã thêm sinh viên: {full_name} ({student_code})")
        return cursor.lastrowid
    except Error as e:
        print(f"❌ Lỗi thêm sinh viên: {e}")
        return None
    finally:
        conn.close()


def update_student(student_id, student_code, full_name, email="", phone=""):
    """Cập nhật thông tin sinh viên"""
    conn = get_connection()
    if not conn:
        return False
    try:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE students SET student_code=%s, full_name=%s, email=%s, phone=%s WHERE id=%s",
            (student_code, full_name, email, phone, student_id)
        )
        conn.commit()
        return cursor.rowcount > 0
    except Error as e:
        print(f"❌ Lỗi cập nhật sinh viên: {e}")
        return False
    finally:
        conn.close()


def delete_student(student_id):
    """Xóa sinh viên"""
    conn = get_connection()
    if not conn:
        return False
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM students WHERE id = %s", (student_id,))
        conn.commit()
        return cursor.rowcount > 0
    except Error as e:
        print(f"❌ Lỗi xóa sinh viên: {e}")
        return False
    finally:
        conn.close()


def get_all_students():
    """Lấy danh sách tất cả sinh viên"""
    conn = get_connection()
    if not conn:
        return []
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM students ORDER BY student_code")
        return cursor.fetchall()
    except Error as e:
        print(f"❌ Lỗi: {e}")
        return []
    finally:
        conn.close()


def get_student_by_id(student_id):
    """Tìm sinh viên theo ID"""
    conn = get_connection()
    if not conn:
        return None
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM students WHERE id = %s", (student_id,))
        return cursor.fetchone()
    except Error as e:
        print(f"❌ Lỗi: {e}")
        return None
    finally:
        conn.close()


def get_student_by_code(student_code):
    """Tìm sinh viên theo mã sinh viên"""
    conn = get_connection()
    if not conn:
        return None
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM students WHERE student_code = %s", (student_code,))
        return cursor.fetchone()
    except Error as e:
        print(f"❌ Lỗi: {e}")
        return None
    finally:
        conn.close()


def update_face_registered(student_id, registered=True, photo_path=""):
    """Cập nhật trạng thái đăng ký khuôn mặt"""
    conn = get_connection()
    if not conn:
        return False
    try:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE students SET face_registered=%s, photo_path=%s WHERE id=%s",
            (registered, photo_path, student_id)
        )
        conn.commit()
        return True
    except Error as e:
        print(f"❌ Lỗi: {e}")
        return False
    finally:
        conn.close()


def get_students_by_class(class_id):
    """Lấy danh sách sinh viên của một lớp"""
    conn = get_connection()
    if not conn:
        return []
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT s.* FROM students s
            JOIN student_classes sc ON s.id = sc.student_id
            WHERE sc.class_id = %s
            ORDER BY s.student_code
        """, (class_id,))
        return cursor.fetchall()
    except Error as e:
        print(f"❌ Lỗi: {e}")
        return []
    finally:
        conn.close()


# ============================================
# LỚP HỌC (Classes)
# ============================================

def add_class(class_code, class_name, lecturer_id=None, schedule="", room=""):
    """Thêm lớp học mới"""
    conn = get_connection()
    if not conn:
        return None
    try:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO classes (class_code, class_name, lecturer_id, schedule, room) VALUES (%s, %s, %s, %s, %s)",
            (class_code, class_name, lecturer_id, schedule, room)
        )
        conn.commit()
        return cursor.lastrowid
    except Error as e:
        print(f"❌ Lỗi thêm lớp: {e}")
        return None
    finally:
        conn.close()


def update_class(class_id, class_code, class_name, lecturer_id=None, schedule="", room=""):
    """Cập nhật thông tin lớp học"""
    conn = get_connection()
    if not conn:
        return False
    try:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE classes SET class_code=%s, class_name=%s, lecturer_id=%s, schedule=%s, room=%s WHERE id=%s",
            (class_code, class_name, lecturer_id, schedule, room, class_id)
        )
        conn.commit()
        return cursor.rowcount > 0
    except Error as e:
        print(f"❌ Lỗi cập nhật lớp: {e}")
        return False
    finally:
        conn.close()


def delete_class(class_id):
    """Xóa lớp học"""
    conn = get_connection()
    if not conn:
        return False
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM classes WHERE id = %s", (class_id,))
        conn.commit()
        return cursor.rowcount > 0
    except Error as e:
        print(f"❌ Lỗi xóa lớp: {e}")
        return False
    finally:
        conn.close()


def get_all_classes():
    """Lấy danh sách tất cả lớp học (kèm tên giảng viên)"""
    conn = get_connection()
    if not conn:
        return []
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT c.*, l.full_name as lecturer_name,
                   (SELECT COUNT(*) FROM student_classes sc WHERE sc.class_id = c.id) as student_count
            FROM classes c
            LEFT JOIN lecturers l ON c.lecturer_id = l.id
            ORDER BY c.class_code
        """)
        return cursor.fetchall()
    except Error as e:
        print(f"❌ Lỗi: {e}")
        return []
    finally:
        conn.close()


def get_class_by_id(class_id):
    """Tìm lớp học theo ID"""
    conn = get_connection()
    if not conn:
        return None
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT c.*, l.full_name as lecturer_name
            FROM classes c
            LEFT JOIN lecturers l ON c.lecturer_id = l.id
            WHERE c.id = %s
        """, (class_id,))
        return cursor.fetchone()
    except Error as e:
        print(f"❌ Lỗi: {e}")
        return None
    finally:
        conn.close()


def get_classes_by_lecturer(lecturer_id):
    """Lấy danh sách lớp của một giảng viên"""
    conn = get_connection()
    if not conn:
        return []
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT c.*,
                   (SELECT COUNT(*) FROM student_classes sc WHERE sc.class_id = c.id) as student_count
            FROM classes c
            WHERE c.lecturer_id = %s
            ORDER BY c.class_code
        """, (lecturer_id,))
        return cursor.fetchall()
    except Error as e:
        print(f"❌ Lỗi: {e}")
        return []
    finally:
        conn.close()


# ============================================
# ĐĂNG KÝ LỚP (Student-Class enrollment)
# ============================================

def enroll_student(student_id, class_id):
    """Đăng ký sinh viên vào lớp"""
    conn = get_connection()
    if not conn:
        return False
    try:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT IGNORE INTO student_classes (student_id, class_id) VALUES (%s, %s)",
            (student_id, class_id)
        )
        conn.commit()
        return True
    except Error as e:
        print(f"❌ Lỗi đăng ký lớp: {e}")
        return False
    finally:
        conn.close()


def unenroll_student(student_id, class_id):
    """Hủy đăng ký sinh viên khỏi lớp"""
    conn = get_connection()
    if not conn:
        return False
    try:
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM student_classes WHERE student_id=%s AND class_id=%s",
            (student_id, class_id)
        )
        conn.commit()
        return cursor.rowcount > 0
    except Error as e:
        print(f"❌ Lỗi: {e}")
        return False
    finally:
        conn.close()


# ============================================
# ĐIỂM DANH (Attendance)
# ============================================

def mark_attendance(student_id, class_id, confidence=0.0, status="present"):
    """Ghi nhận điểm danh cho sinh viên"""
    conn = get_connection()
    if not conn:
        return False
    try:
        cursor = conn.cursor()
        now = datetime.now()
        today = now.date()

        # Kiểm tra đã điểm danh hôm nay chưa
        cursor.execute(
            "SELECT id FROM attendance WHERE student_id=%s AND class_id=%s AND date=%s",
            (student_id, class_id, today)
        )
        if cursor.fetchone():
            return False  # Đã điểm danh rồi

        cursor.execute(
            """INSERT INTO attendance (student_id, class_id, date, check_in_time, status, confidence) 
               VALUES (%s, %s, %s, %s, %s, %s)""",
            (student_id, class_id, today, now, status, confidence)
        )
        conn.commit()
        return True
    except Error as e:
        print(f"❌ Lỗi điểm danh: {e}")
        return False
    finally:
        conn.close()


def get_attendance_by_class_date(class_id, target_date=None):
    """Lấy danh sách điểm danh của một lớp theo ngày"""
    if target_date is None:
        target_date = date.today()

    conn = get_connection()
    if not conn:
        return []
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT a.*, s.student_code, s.full_name
            FROM attendance a
            JOIN students s ON a.student_id = s.id
            WHERE a.class_id = %s AND a.date = %s
            ORDER BY a.check_in_time
        """, (class_id, target_date))
        return cursor.fetchall()
    except Error as e:
        print(f"❌ Lỗi: {e}")
        return []
    finally:
        conn.close()


def get_attendance_by_student(student_id, class_id=None):
    """Lấy lịch sử điểm danh của một sinh viên"""
    conn = get_connection()
    if not conn:
        return []
    try:
        cursor = conn.cursor(dictionary=True)
        if class_id:
            cursor.execute("""
                SELECT a.*, c.class_code, c.class_name
                FROM attendance a
                JOIN classes c ON a.class_id = c.id
                WHERE a.student_id = %s AND a.class_id = %s
                ORDER BY a.date DESC
            """, (student_id, class_id))
        else:
            cursor.execute("""
                SELECT a.*, c.class_code, c.class_name
                FROM attendance a
                JOIN classes c ON a.class_id = c.id
                WHERE a.student_id = %s
                ORDER BY a.date DESC
            """, (student_id,))
        return cursor.fetchall()
    except Error as e:
        print(f"❌ Lỗi: {e}")
        return []
    finally:
        conn.close()


def get_attendance_summary(class_id):
    """Lấy thống kê điểm danh tổng hợp của một lớp"""
    conn = get_connection()
    if not conn:
        return []
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT 
                s.id, s.student_code, s.full_name,
                COUNT(CASE WHEN a.status = 'present' THEN 1 END) as present_count,
                COUNT(CASE WHEN a.status = 'late' THEN 1 END) as late_count,
                COUNT(a.id) as total_attended,
                (SELECT COUNT(DISTINCT date) FROM attendance WHERE class_id = %s) as total_sessions
            FROM students s
            JOIN student_classes sc ON s.id = sc.student_id
            LEFT JOIN attendance a ON s.id = a.student_id AND a.class_id = %s
            WHERE sc.class_id = %s
            GROUP BY s.id, s.student_code, s.full_name
            ORDER BY s.student_code
        """, (class_id, class_id, class_id))
        return cursor.fetchall()
    except Error as e:
        print(f"❌ Lỗi: {e}")
        return []
    finally:
        conn.close()


# ============================================
# THỐNG KÊ (Dashboard Stats)
# ============================================

def get_dashboard_stats():
    """Lấy thống kê tổng quan cho dashboard"""
    conn = get_connection()
    if not conn:
        return {}
    try:
        cursor = conn.cursor(dictionary=True)

        # Tổng số sinh viên
        cursor.execute("SELECT COUNT(*) as count FROM students")
        total_students = cursor.fetchone()["count"]

        # Tổng số lớp
        cursor.execute("SELECT COUNT(*) as count FROM classes")
        total_classes = cursor.fetchone()["count"]

        # Điểm danh hôm nay
        today = date.today()
        cursor.execute("SELECT COUNT(*) as count FROM attendance WHERE date = %s", (today,))
        today_attendance = cursor.fetchone()["count"]

        # Số SV đã đăng ký khuôn mặt
        cursor.execute("SELECT COUNT(*) as count FROM students WHERE face_registered = TRUE")
        face_registered = cursor.fetchone()["count"]

        # Điểm danh 7 ngày gần nhất
        cursor.execute("""
            SELECT date, COUNT(*) as count 
            FROM attendance 
            WHERE date >= %s
            GROUP BY date 
            ORDER BY date
        """, (today - timedelta(days=6),))
        weekly_data = cursor.fetchall()

        return {
            "total_students": total_students,
            "total_classes": total_classes,
            "today_attendance": today_attendance,
            "face_registered": face_registered,
            "weekly_attendance": weekly_data
        }
    except Error as e:
        print(f"❌ Lỗi: {e}")
        return {}
    finally:
        conn.close()


def get_recent_attendance(limit=10):
    """Lấy danh sách điểm danh gần nhất"""
    conn = get_connection()
    if not conn:
        return []
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT a.*, s.student_code, s.full_name, c.class_code, c.class_name
            FROM attendance a
            JOIN students s ON a.student_id = s.id
            JOIN classes c ON a.class_id = c.id
            ORDER BY a.check_in_time DESC
            LIMIT %s
        """, (limit,))
        return cursor.fetchall()
    except Error as e:
        print(f"❌ Lỗi: {e}")
        return []
    finally:
        conn.close()


if __name__ == "__main__":
    # Test kết nối
    test_connection()
