from flask import Flask, request, jsonify, Blueprint
from flask_cors import CORS
import anvil.server
import secrets
import time
from functools import wraps
from datetime import datetime, timedelta
import bcrypt
import os
from dotenv import load_dotenv
from utils.auth_utils import token_required, generate_token, verify_password
from config import config
import threading
from utils.rate_limiter import rate_limit

# Import globals from auth_utils
from utils.auth_utils import SESSIONS, SESSIONS_LOCK

auth_bp = Blueprint('auth', __name__)

# Get SESSION_DURATION from config
SESSION_DURATION = config.SESSION_DURATION

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
        anvil_response = anvil.server.call('authenticate_user', email, password)
        
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