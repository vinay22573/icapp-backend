from flask import request, jsonify
from functools import wraps
import time
import secrets
import bcrypt
import threading
from config import config


# This will be imported from app.py
SESSIONS = None
SESSIONS_LOCK = threading.Lock()
SESSION_DURATION = config.SESSION_DURATION

def init_auth(sessions_store):
    """Initialize the auth module with the sessions store"""
    global SESSIONS
    SESSIONS = sessions_store

def generate_token():
    return secrets.token_hex(32)

def verify_password(plain_password, hashed_password):
    """Verify password using bcrypt"""
    try:
        password_bytes = plain_password.encode('utf-8')
        hash_bytes = hashed_password.encode('utf-8')
        return bcrypt.checkpw(password_bytes, hash_bytes)
    except Exception as e:
        print(f"Flask bcrypt error: {e}")
        return False

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return jsonify({"error": "Unauthorized - Missing token"}), 401

        token = auth_header.split(" ")[1]
        with SESSIONS_LOCK:
            session = SESSIONS.get(token)

            if not session:
                return jsonify({"error": "Invalid or expired token"}), 401

            if session["expires_at"] < time.time():
                del SESSIONS[token]
                return jsonify({"error": "Session expired"}), 401

            session["request_count"] = session.get("request_count", 0) + 1
            session["last_accessed"] = time.time()
            request.user = session["user"]
        return f(*args, **kwargs)
    return decorated