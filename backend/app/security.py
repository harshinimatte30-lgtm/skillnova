import base64, hashlib, hmac, json, os, time
from fastapi import HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from .db import settings
from .models import User

bearer = HTTPBearer(auto_error=False)

def hash_password(password: str) -> str:
    salt = os.urandom(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 120_000)
    return base64.urlsafe_b64encode(salt + digest).decode()

def verify_password(password: str, stored: str) -> bool:
    try:
        raw = base64.urlsafe_b64decode(stored.encode())
        salt, expected = raw[:16], raw[16:]
        actual = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 120_000)
        return hmac.compare_digest(actual, expected)
    except Exception:
        return False

def _b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode().rstrip("=")

def create_token(user: User) -> str:
    header = _b64(b'{"alg":"HS256","typ":"SKILLNOVA"}')
    payload = _b64(json.dumps({"sub": user.id, "role": user.role, "exp": int(time.time()) + 86400}).encode())
    sig = _b64(hmac.new(settings.secret_key.encode(), f"{header}.{payload}".encode(), hashlib.sha256).digest())
    return f"{header}.{payload}.{sig}"

def current_user(credentials: HTTPAuthorizationCredentials | None, db: Session) -> User:
    if not credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
    try:
        header, payload, sig = credentials.credentials.split(".")
        expected = _b64(hmac.new(settings.secret_key.encode(), f"{header}.{payload}".encode(), hashlib.sha256).digest())
        if not hmac.compare_digest(sig, expected):
            raise ValueError()
        data = json.loads(base64.urlsafe_b64decode(payload + "=" * (-len(payload) % 4)))
        if data["exp"] < time.time():
            raise ValueError()
        user = db.get(User, int(data["sub"]))
        if not user:
            raise ValueError()
        return user
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")


def decode_token(token: str) -> dict:
    try:
        header, payload, sig = token.split(".")

        expected = _b64(
            hmac.new(
                settings.secret_key.encode(),
                f"{header}.{payload}".encode(),
                hashlib.sha256
            ).digest()
        )

        if not hmac.compare_digest(sig, expected):
            raise ValueError("Invalid signature")

        data = json.loads(
            base64.urlsafe_b64decode(
                payload + "=" * (-len(payload) % 4)
            )
        )

        if data.get("exp", 0) < time.time():
            raise ValueError("Token expired")

        return data

    except Exception as e:
        raise ValueError("Invalid or expired token") from e