"""JWT kimlik doğrulama yardımcı fonksiyonları."""

from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

import yaml
import bcrypt
from jose import jwt, JWTError
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

SECRET_KEY = "sta_jwt_secret_2024_sanal_ogretmen"
ALGORITHM = "HS256"
TOKEN_EXPIRE_HOURS = 24

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

_CONFIG_PATH = Path(__file__).parent.parent / "config" / "users.yaml"


def _load_users() -> dict:
    with open(_CONFIG_PATH, encoding="utf-8") as f:
        return yaml.safe_load(f)["credentials"]["usernames"]


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    except Exception:
        return False


def authenticate_user(username: str, password: str) -> Optional[dict]:
    users = _load_users()
    if username not in users:
        return None
    user = users[username]
    if not verify_password(password, user["password"]):
        return None
    return {
        "username": username,
        "name": user["name"],
        "role": user.get("role", "student"),
    }


def create_access_token(data: dict) -> str:
    payload = data.copy()
    payload["exp"] = datetime.utcnow() + timedelta(hours=TOKEN_EXPIRE_HOURS)
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token geçersiz veya süresi dolmuş",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if not username:
            raise credentials_exception
        return {
            "username": username,
            "name": payload.get("name", username),
            "role": payload.get("role", "student"),
        }
    except JWTError:
        raise credentials_exception


def require_teacher(user: dict = Depends(get_current_user)) -> dict:
    if user["role"] != "teacher":
        raise HTTPException(status_code=403, detail="Bu işlem için öğretmen yetkisi gerekli")
    return user
