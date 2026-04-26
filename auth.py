"""
Module Authentication - Xác thực JWT
======================================
Xử lý đăng nhập giảng viên và tạo/xác thực JWT token.
"""

from datetime import datetime, timedelta
from jose import JWTError, jwt
import bcrypt
from config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES


def verify_password(plain_password, hashed_password):
    """Kiểm tra mật khẩu có khớp với hash không"""
    return bcrypt.checkpw(
        plain_password.encode("utf-8"),
        hashed_password.encode("utf-8")
    )


def hash_password(password):
    """Mã hóa mật khẩu"""
    return bcrypt.hashpw(
        password.encode("utf-8"),
        bcrypt.gensalt()
    ).decode("utf-8")


def create_access_token(data: dict):
    """Tạo JWT access token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_token(token: str):
    """Giải mã JWT token, trả về payload hoặc None nếu token không hợp lệ"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None


if __name__ == "__main__":
    # Test tạo hash password
    hashed = hash_password("admin123")
    print(f"Hash: {hashed}")
    print(f"Verify: {verify_password('admin123', hashed)}")
