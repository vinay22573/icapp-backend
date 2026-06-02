from flask import Blueprint, request, jsonify
from utils.auth_utils import token_required
from utils.sponsor_utils import verify_sponsor

sponsors_bp = Blueprint('sponsors', __name__)

def serialize_sponsor_data(sponsor_data):
    """
    Safely serialize sponsor data, converting media objects to URLs
    """
    if not sponsor_data:
        return {}
    
    # Create a copy to avoid modifying original
    safe_data = sponsor_data.copy()
    
    # Handle logo media conversion (like in your Anvil functions)
    logo = safe_data.get('logo')
    if logo is not None:
        try:
            # Convert Anvil media to URL (same logic as serialize_media)
            safe_data['logo'] = logo.url if hasattr(logo, 'url') else None
        except Exception:
            safe_data['logo'] = None
    return safe_data

@sponsors_bp.route("/company", methods=["GET"])
@token_required
@verify_sponsor
def get_company_details():
    """Get filtered company details for logged-in sponsor"""
    
    # Get full sponsor data from verify_sponsor decorator
    full_sponsor = request.sponsor
    spons_id = getattr(request, 'spons_id', None)
    if not spons_id:
        return jsonify({'error': 'Sponsor ID not found in request'}), 400
    
    # Serialize the sponsor data to handle media types
    serialized_sponsor = serialize_sponsor_data(full_sponsor)
    
    # Filter to only safe, frontend-needed fields
    safe_company_data = {
        "id": spons_id,
        "name": serialized_sponsor.get('name', ''),
        "display_name": serialized_sponsor.get('display_name', ''),
        "website": serialized_sponsor.get('website', ''),
        "logo": serialized_sponsor.get('logo'),  # Now properly serialized URL or None
        "metrics": serialized_sponsor.get('metrics', {}),
        # DON'T expose: status, settings, admin fields
    }
    
    return jsonify({
        "spons_id": spons_id,
        "company": safe_company_data
    }), 200

@sponsors_bp.route("/company/display-name", methods=["GET"])
@token_required
@verify_sponsor
def get_company_display_name():
    """Get just the display name with fallbacks"""
    sponsor = request.sponsor
    
    # Fallback chain: display_name → name → 'Sponsor'
    display_name = (
        sponsor.get('display_name', '').strip() or 
        sponsor.get('name', '').strip() or 
        'Sponsor'
    )
    
    return jsonify({
        "display_name": display_name
    }), 200

@sponsors_bp.route("/company/logo", methods=["GET"])
@token_required
@verify_sponsor
def get_company_logo():
    """Get company logo URL/data"""
    sponsor = request.sponsor
    logo = sponsor.get('logo')
    
    # Handle Anvil media conversion
    logo_url = None
    if logo is not None:
        try:
            logo_url = logo.url if hasattr(logo, 'url') else None
        except Exception:
            logo_url = None
    
    return jsonify({
        "logo": logo_url,
        "has_logo": bool(logo_url)
    }), 200


@sponsors_bp.route("/company/website", methods=["GET"])
@token_required
@verify_sponsor
def get_company_website():
    """Get company website"""
    sponsor = request.sponsor
    website = sponsor.get('website', '').strip()
    
    return jsonify({
        "website": website,
        "has_website": bool(website)
    }), 200

@sponsors_bp.route("/company/basic-info", methods=["GET"])
@token_required
@verify_sponsor
def get_company_basic_info():
    """Get basic company info for UI display"""
    sponsor = request.sponsor
    
    # Handle logo serialization
    logo = sponsor.get('logo')
    logo_url = None
    if logo is not None:
        try:
            logo_url = logo.url if hasattr(logo, 'url') else None
        except Exception:
            logo_url = None
    
    # Safe basic info only
    basic_info = {
        "name": sponsor.get('name', '').strip(),
        "display_name": sponsor.get('display_name', '').strip(),
        "website": sponsor.get('website', '').strip(),
        "logo": logo_url,
        "has_logo": bool(logo_url)
    }
    
    return jsonify(basic_info), 200

@sponsors_bp.route("/company/name-with-fallback", methods=["GET"])
@token_required
@verify_sponsor
def get_company_name_with_fallback():
    """Get display name with proper fallback chain for UI components"""
    sponsor = request.sponsor
    
    # Smart fallback: display_name → name → 'Sponsor'
    
    name = sponsor.get('name', '').strip()
    
    final_name =  name or 'Sponsor'
    
    return jsonify({
        "name": final_name,
        "source": "name"  if name else "display_name" if sponsor.get('display_name', '').strip() else "default"
    }), 200