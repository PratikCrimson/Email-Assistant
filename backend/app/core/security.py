import base64
import hashlib
import hmac
import json
import os
import time

SESSION_COOKIE_NAME = "ea_session"
SESSION_TTL_SECONDS = int(os.getenv("SESSION_TTL_SECONDS", "604800"))  # 7 days

_SECRET_KEY = os.getenv("APP_SECRET_KEY", "dev-insecure-change-me")
_SECRET_KEY_BYTES = _SECRET_KEY.encode("utf-8")


def _b64url_encode(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("utf-8")


def _b64url_decode(raw: str) -> bytes:
    padding = "=" * (-len(raw) % 4)
    return base64.urlsafe_b64decode(raw + padding)


def create_session_token(user_email: str) -> str:
    payload = {
        "sub": user_email,
        "exp": int(time.time()) + SESSION_TTL_SECONDS,
    }
    payload_bytes = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
    payload_b64 = _b64url_encode(payload_bytes)
    signature = hmac.new(_SECRET_KEY_BYTES, payload_b64.encode("utf-8"), hashlib.sha256).digest()
    return f"{payload_b64}.{_b64url_encode(signature)}"


def verify_session_token(token: str) -> str | None:
    try:
        payload_b64, signature_b64 = token.split(".", 1)
    except ValueError:
        return None

    expected_signature = hmac.new(
        _SECRET_KEY_BYTES, payload_b64.encode("utf-8"), hashlib.sha256
    ).digest()
    try:
        received_signature = _b64url_decode(signature_b64)
    except Exception:
        return None
    if not hmac.compare_digest(expected_signature, received_signature):
        return None

    try:
        payload = json.loads(_b64url_decode(payload_b64))
    except Exception:
        return None

    expiry = payload.get("exp")
    user_email = payload.get("sub")
    if not isinstance(expiry, int) or not isinstance(user_email, str):
        return None
    if expiry < int(time.time()):
        return None
    return user_email
