from flask import Flask, request, jsonify, Blueprint
from flask_cors import CORS
import anvil.server
import secrets
import time
from functools import wraps
from datetime import datetime, timedelta
import bcrypt
import base64
import os
from dotenv import load_dotenv
from utils.auth_utils import token_required, generate_token, verify_password, hash_password
from utils.anvil_executor import call_anvil
from config import config
import threading
from utils.rate_limiter import rate_limit

# Import globals from auth_utils
from utils.auth_utils import SESSIONS, SESSIONS_LOCK

auth_bp = Blueprint('auth', __name__)

# Get SESSION_DURATION from config
SESSION_DURATION = config.SESSION_DURATION


# ─────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────

def _is_valid_email(email):
    return isinstance(email, str) and "@" in email and "." in email.rsplit("@", 1)[-1]

 
# ─────────────────────────────────────────────
# MEDIA HELPERS — comment out the next block to
# disable logo upload entirely; rest still works
# ─────────────────────────────────────────────


def _encode_logo_from_request():
    """
    Read logo file from multipart request and return (b64_string, content_type).
    Returns (None, None) if no file present or on any error.
    This function is the ONLY place that touches logo/media logic on Flask side.
    """
    try:
        logo_file = request.files.get('logo')
        if not logo_file:
            return None, None
        logo_bytes = logo_file.read()
        if not logo_bytes:
            return None, None
        logo_b64 = base64.b64encode(logo_bytes).decode('utf-8')
        return logo_b64, logo_file.content_type
    except Exception as e:
        print(f"[MEDIA] Logo encode error: {e}")
        return None, None
# ─────────────────────────────────────────────
# END MEDIA HELPERS
# ─────────────────────────────────────────────



@auth_bp.route('/signup', methods=['POST'])
def signup():
    """
    Sponsor registration endpoint.
    Accepts multipart/form-data (because of logo file upload).
    Falls back to JSON if no file is present.
 
    Flow:
        1. Validate all fields
        2. RPC1 — register_user (create user row in Anvil)
        3. [MEDIA] Try to encode logo — non-fatal if it fails
        4. RPC2 — register_sponsor (create sponsor row + update user row)
        5. If RPC2 fails → cleanup: delete user row via delete_user_by_email
        6. Return success + optional media_warning if logo upload failed
    """
 
    # Support both multipart (with file) and JSON (without file)
    is_multipart = bool(request.content_type and 'multipart/form-data' in request.content_type)
    if is_multipart:
        data = request.form
        get = lambda key, default="": data.get(key, default)
        import json
        try:
            industries = json.loads(get('industries', '[]'))
            if not isinstance(industries, list):
                industries = []
        except Exception:
            industries = []
    else:
        data = request.get_json() or {}
        get = lambda key, default="": data.get(key, default)
        industries = data.get('industries', [])
        if not isinstance(industries, list):
            industries = []
 
    # ── Extract fields ──
    email        = get('email').strip().lower()
    password     = get('password').strip()
    rep_name     = get('name').strip()
    role         = get('role', 'primary_representative').strip()
    sponsor_name = get('sponsor_name').strip()
    display_name = get('display_name').strip()
    website      = get('website').strip()
    description  = get('description', '').strip()
 
    # ── Validate ──
    if not email or not password or not rep_name:
        return jsonify({"error": "Name, email and password are required"}), 400
    if not _is_valid_email(email):
        return jsonify({"error": "Invalid email address"}), 400
    if len(password) < 8:
        return jsonify({"error": "Password must be at least 8 characters"}), 400
    if not sponsor_name or not display_name or not website:
        return jsonify({"error": "Sponsor name, display name and website are required"}), 400
 
    # ── Step 1: Register user ──
    try:
        password_hash = hash_password(password)
        rpc1 = call_anvil("register_user", email, password_hash)
        if not rpc1.get("success"):
            error_msg = rpc1.get("error", "Registration failed")
            status_code = 409 if "already" in error_msg.lower() else 400
            return jsonify({"error": error_msg}), status_code
    except Exception as e:
        print(f"[SIGNUP] RPC1 register_user failed: {e}")
        return jsonify({"error": f"User registration failed: {str(e)}"}), 500
 
    # ── [MEDIA] Step 2: Try to encode logo — non-fatal ──
    # To disable logo upload entirely: comment out the next 3 lines
    # and set logo_b64 = None, logo_content_type = None manually.
    logo_was_provided = bool(is_multipart and request.files.get('logo'))
    logo_b64, logo_content_type = _encode_logo_from_request()
    media_warning = None
    if logo_was_provided and logo_b64 is None:
        media_warning = "Logo could not be processed. Account created successfully — please upload the logo manually via the Anvil dashboard."
    # ── END MEDIA STEP ──
 
    # ── Step 3: Register sponsor (sequential — depends on user existing) ──
    try:
        sponsor_payload = {
            "name":         sponsor_name,
            "display_name": display_name,
            "website":      website,
            "description":  description,
            "industries":   industries,
            "rep_name":     rep_name,
            "role":         role,
            # ── MEDIA FIELDS — comment these two lines to disable logo in RPC ──
            "logo_b64":           logo_b64,
            "logo_content_type":  logo_content_type,
            # ── END MEDIA FIELDS ──
        }
        rpc2 = call_anvil("register_sponsor", email, sponsor_payload)
 
        if not rpc2.get("success"):
            # Atomic cleanup — user row must be removed if sponsor step failed
            try:
                call_anvil("delete_user_by_email", email)
            except Exception as cleanup_err:
                print(f"[SIGNUP] Cleanup RPC failed: {cleanup_err}")
            return jsonify({"error": rpc2.get("error", "Sponsor registration failed")}), 400
 
    except Exception as e:
        print(f"[SIGNUP] RPC2 register_sponsor failed: {e}")
        # Atomic cleanup
        try:
            call_anvil("delete_user_by_email", email)
        except Exception as cleanup_err:
            print(f"[SIGNUP] Cleanup RPC failed: {cleanup_err}")
        return jsonify({"error": f"Sponsor registration failed: {str(e)}"}), 500
 
    # ── Success ──
    response_body = {
        "success": True,
        "message": "Account created successfully. Pending admin verification before you can log in.",
    }
    if media_warning:
        response_body["media_warning"] = media_warning
 
    return jsonify(response_body), 201
 
 


@auth_bp.route('/login', methods=['POST'])
@rate_limit(limit=5, period=3600, key_func=lambda: ((request.get_json(silent=True) or {}).get('email') or request.remote_addr or "unknown").lower())
def login():
    data = request.get_json()
    if not data or 'email' not in data or 'password' not in data:
        return jsonify({"error": "Email and password are required"}), 400
    email = data.get('email')
    password = data.get('password')
    try:        # Call the Anvil server function for authentication
        # Instead of using anvil.users.check_password directly
        # print("FLASK: before authenticate_user", flush=True)
        # anvil_response = anvil.server.call('authenticate_user', email, password)
        anvil_response = call_anvil("authenticate_user", email, password)
        # print("FLASK: after authenticate_user", anvil_response, flush=True)
        
        # Check if Anvil call was successful
        if not anvil_response.get('success'):
            error_msg = anvil_response.get('error', 'Authentication failed')
            return jsonify({"error": error_msg}), 401
        # Extract user data and password hash
        user_data = anvil_response.get('user_data')
        hash_password = user_data.get('password_hash')
        # print(f'Hash password from Anvil: {hash_password}')
          # Verify password using bcrypt
        password_correct = verify_password(password, hash_password)
        
        # print("DEBUG: Password verification result:", password_correct)
        
        if password_correct:
            # Generate a token on successful authentication
            token = generate_token()
            
            clean_user_data = {
                "email": user_data["email"]
                # ,"verification_status": user_data.get("verification_status", "pending"), # Look this needs more work because for logging in a user needs not to be verified just getting password authentication is fine but if a company bieng a representative of the company if the company is restricted/suspended, banned , or anything of that sort then we can not allow the user/company to add/remove/create projects or add/remove/create sponsorships
            }
            # Store in session dictionary (in-memory for now)
            with SESSIONS_LOCK:
                SESSIONS[token] = {
                    'user': clean_user_data,
                    'expires_at': time.time() + SESSION_DURATION,
                    'request_count': 0,
                    'last_accessed': time.time()
                }
            
            return jsonify({
                'token': token,
                'user': clean_user_data,
                'message': 'Login successful'
            })
        else:
            return jsonify({"error": "Invalid password"}), 401
    except Exception as e:
        print(f"Login error: {str(e)}")
        return jsonify({"error": f"Authentication Failed: {str(e)}"}), 500


@auth_bp.route('/logout', methods=['POST'])
@token_required
def logout():
    token = request.headers.get("Authorization").split(" ")[1]
    with SESSIONS_LOCK:
        SESSIONS.pop(token, None)
    return jsonify({"message": "Logged out successfully"}), 200





@auth_bp.route("/me", methods=["GET"])
@token_required
def me():
    return jsonify({"user": request.user}), 200

@auth_bp.route("/profile", methods=["GET"])
@token_required
def profile():
    user_email = request.user.get("email")
    # Fetch full user details from Anvil
    anvil_response = anvil.server.call('get_user_details', user_email)
    if not anvil_response.get('success'):
        return jsonify({"error": "Could not fetch user details"}), 500

    user_data = anvil_response.get('user_data', {})
    # permissions = {
    #     "can_sponsor": _can_user_sponsor(user_data),
    #     "can_create_projects": _can_user_create_projects(user_data),
    #     "is_company_rep": _is_company_representative(user_data)
    # }
    return jsonify({
        "email": user_email,
        "details": user_data.get("details", {}),
        "user_type": user_data.get("user_type", "")
        # ,"permissions": permissions
    }), 200





@auth_bp.route("/internal/runtime-info", methods=["GET"])
@token_required
def runtime_info():
    return jsonify({
        "pid": os.getpid(),
        "tid": threading.get_ident(),
        "thread_name": threading.current_thread().name,
        "active_threads": threading.active_count()
    }), 200





@auth_bp.route('/refresh', methods=['POST'])
@token_required
def refresh_token():
    # Future: Token refresh logic
    # pass
    return jsonify({"message": "This page is still under development. \n Dummy: Token refreshed successfully"}), 200