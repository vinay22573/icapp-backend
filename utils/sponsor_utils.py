# sponsor_utils.py
from functools import wraps
import anvil.server
import threading
import time
from flask import request, jsonify


_SPONSOR_CACHE = {}
_SPONSOR_CACHE_LOCK = threading.Lock()
_SPONSOR_CACHE_TTL_SECONDS = 60


def _cache_get(key):
    with _SPONSOR_CACHE_LOCK:
        entry = _SPONSOR_CACHE.get(key)
        if not entry:
            return None
        if time.time() >= entry["expires_at"]:
            _SPONSOR_CACHE.pop(key, None)
            return None
        return entry["value"]


def _cache_set(key, value, ttl_seconds=_SPONSOR_CACHE_TTL_SECONDS):
    with _SPONSOR_CACHE_LOCK:
        _SPONSOR_CACHE[key] = {
            "value": value,
            "expires_at": time.time() + ttl_seconds,
        }


def verify_sponsor(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user = request.user
        email = user.get("email")

        cache_key = f"sponsor_verification:{email}"
        cached_result = _cache_get(cache_key)
        if cached_result:
            request.sponsor = cached_result["sponsor"]
            request.spons_id = cached_result["spons_id"]
            return f(*args, **kwargs)

        try:
            response = anvil.server.call('get_user_details', email)
        except Exception as e:
            return jsonify({"error": f"Anvil error while getting user: {str(e)}"}), 500

        if not response.get("success"):
            return jsonify({"error": "User details fetch failed: " + response.get("error", "Unknown error")}), 500

        user_details = response["user_data"].get("details", {})
        company_data = user_details.get("company_relationship", {})

        spons_id = company_data.get("spons_id")
        if not spons_id:
            return jsonify({"error": "You are not associated with any sponsor company"}), 403

        try:
            sponsor_response = anvil.server.call('get_sponsor_by_id', spons_id)
        except Exception as e:
            return jsonify({"error": f"Anvil error while getting sponsor info: {str(e)}"}), 500

        if not sponsor_response.get("success"):
            return jsonify({"error": sponsor_response.get("error", "Failed to retrieve sponsor info")}), 403

        sponsor = sponsor_response.get("sponsor", {})
        status = sponsor.get("status", "unknown")

        if not sponsor or status.lower() not in ["active", "verified"]:
            return jsonify({
                "error": f"Your company is not allowed due to status: {sponsor.get('status', 'unknown')}. Contact admin."
            }), 403

        request.sponsor = sponsor
        request.spons_id = spons_id

        _cache_set(cache_key, {
            "sponsor": sponsor,
            "spons_id": spons_id,
        })

        return f(*args, **kwargs)
    return decorated_function
