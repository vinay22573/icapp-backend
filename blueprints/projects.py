from flask import Blueprint, request, jsonify
from utils.auth_utils import token_required
from utils.sponsor_utils import verify_sponsor
from datetime import datetime, timezone
from utils.anvil_executor import call_anvil_concurrent
from utils.concurrency_layer import run_project_analytics_in_process
import anvil.server
import uuid
import json
projects_bp = Blueprint('projects', __name__)


# ===== TEST ENDPOINTS WORKING =====
@projects_bp.route('/projects/health', methods=['GET'])
def health_check():
    return jsonify({
        "message": "Projects API is healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": "1.0.0"
    }), 200

@projects_bp.route('/projects/test', methods=['GET'])
@token_required
def test_projects():
    return jsonify({
        "message": "Protected route working!",
        "user": request.user
    }), 200


# ===== SPONSORSHIP WORKING =====
@projects_bp.route('/projects/<project_id>/sponsor', methods=['POST'])
@token_required
@verify_sponsor
def sponsor_project(project_id):
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Missing JSON body"}), 400

        amount = data.get("amount")
        message = data.get("message", "")

        # Validate amount
        try:
            amount = float(amount)
            if amount <= 0:
                raise ValueError("Amount must be positive")
        except (TypeError, ValueError):
            return jsonify({"error": "Amount must be a positive number"}), 400

        # Fetch project from Anvil
        project_response = anvil.server.call("get_project_by_id", project_id)
        if not project_response.get("success"):
            return jsonify({"error": project_response.get("error", "Project not found")}), 404
        project = project_response["project"]

        # if not project.get("open", False):
        #     return jsonify({"error": "Project is not open for sponsorship"}), 403

        
        spons_id = getattr(request, 'spons_id', None)
        if not spons_id:
            return jsonify({"error": "Sponsor ID not found in request"}), 400
        

        sponsors = project.get("sponsors", {})
        if not isinstance(sponsors, dict):
            sponsors = {}
        # Append sponsor entry
        sponsor_entry = {
            "amount": amount,
            "message": message
        }
        
        sponsors[spons_id] = sponsor_entry  # overwrite/update or add new entry
        
        update_result = anvil.server.call("update_project_sponsors", project_id, sponsors, spons_id)

        if not update_result.get("success"):
            return jsonify({"error": update_result.get("error", "Failed to update sponsors")}), 500

        return jsonify({
            "message": "Sponsorship added successfully",
            "sponsor_entry": sponsor_entry
        }), 200
    except ValueError as ve:
            return jsonify({'error': f'Invalid amount: {str(ve)}'}), 400
    except Exception as e:
        # Log the error for debugging
        print(f"Sponsor project error: {str(e)}")
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500


@projects_bp.route('/projects/<project_id>/sponsor', methods=['PUT'])
@token_required
@verify_sponsor
def update_project_sponsorship(project_id):
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Missing JSON body"}), 400

        # Fetch project from Anvil
        project_result = anvil.server.call("get_project_by_id", project_id)
        if not project_result.get("success"):
            return jsonify({"error": project_result.get("error", "Project not found")}), 404

        project = project_result.get("project", {})
        sponsors = project.get("sponsors", {})

        if not isinstance(sponsors, dict):
            return jsonify({"error": "Invalid sponsor format in project"}), 500

        spons_id = getattr(request, 'spons_id', None)
        if not spons_id:
            return jsonify({"error": "Sponsor ID not found in request"}), 400
        current_entry = sponsors.get(spons_id, {})

        # Preserve old amount if not provided
        amount = data.get("amount", current_entry.get("amount"))
        try:
            amount = float(amount)
            if amount <= 0:
                raise ValueError("Amount must be positive")
        except (TypeError, ValueError):
            return jsonify({"error": "Amount must be a positive number"}), 400

        # Extend message if new one is provided
        existing_message = current_entry.get("message", "")
        new_message = data.get("message")
        if new_message is not None and len(new_message.strip()) > 0:
            message =  new_message
        else:
            message = existing_message

        # Update sponsor entry
        sponsors[spons_id] = {
            "amount": amount,
            "message": message.strip()
        }

        update_result = anvil.server.call("update_project_sponsors", project_id, sponsors)

        if not update_result.get("success"):
            return jsonify({"error": update_result.get("error", "Failed to update sponsors")}), 500

        return jsonify({
            "message": "Sponsorship updated successfully",
            "sponsorship": {spons_id: sponsors[spons_id]}
        }), 200

    except Exception as e:
        print(f"Update sponsorship error: {str(e)}")
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500



@projects_bp.route('/projects/<project_id>/sponsor', methods=['DELETE'])
@token_required
@verify_sponsor
def remove_sponsorship(project_id):
    try:
        spons_id = getattr(request, 'spons_id', None)
        if not spons_id:
            return jsonify({"error": "Sponsor ID not found in request"}), 400

        # Fetch the project to ensure it exists
        # project = anvil.server.call("get_project_by_id", project_id)
        # if not project:
        #     return jsonify({"error": "Project not found"}), 404

        # Remove sponsor entry via Anvil server
        result = anvil.server.call("remove_project_sponsor", project_id, spons_id)
        if not result.get("success"):
            return jsonify({"error": result.get("error", "Failed to remove sponsor")}), 500

        return jsonify({
            "message": "Sponsorship removed successfully",
            "removed_sponsor": result.get("removed_sponsor", {})
        }), 200

    except Exception as e:
        print(f"Remove sponsorship error: {str(e)}")
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500




# ===== CRUD Operations using Anvil Backend =====
#============= CREATE PROJECT, UPDATE PROJECT, DELETE PROJECT IS WORKING PERFECT AND IS CHECKED  =============   

@projects_bp.route('/projects', methods=['POST'])
@token_required
@verify_sponsor
def create_project():
    try:
        
        current_user = request.user
        current_user_email = current_user.get('email')
        spons_id = getattr(request, 'spons_id', None)
        if not spons_id:
            return jsonify({'error': 'Sponsor ID not found in request'}), 400
        data = request.get_json()
        if not data.get('title'):
            return jsonify({'error': 'title is required'}), 400

        # Prepare public_details
        public_details = data.get('public_details', {})
        for key in ['description', 'requirements', 'outcomes']:
            if data.get(key):
                public_details[key.capitalize() if key != 'description' else 'Description'] = data[key]

        public_details['created_at'] = datetime.now(timezone.utc).isoformat()

        project_data = {
            'uid': str(uuid.uuid4()),
            'title': data['title'],
            'owner': current_user_email,
            'org': spons_id,
            'public_details': public_details,
            'domains': json.dumps(data.get('domains', [])),  # <-- as string
            'skills': json.dumps(data.get('skills', [])),    # <-- as string
            'allotted': data.get('allotted', False),
            'instructions': data.get('instructions', ''),
            'doc': data.get('doc'),
            'questions': data.get('questions'),
            'milestones': data.get('milestones', {}),
            'browse': data.get('browse', True),
            'type': data.get('type', 'apprenticeship'),
            'open': data.get('open', True)
        }

        result = anvil.server.call('create_project', project_data, spons_id)

        if result.get('success'):
            return jsonify({
                'message': 'Project created successfully',
                'project_id': project_data['uid'],
                'project': result.get('project')
            }), 201
        else:
            return jsonify({'error': result.get('error', 'Failed to create project')}), 500

    except Exception as e:
        print(f"Create project error: {str(e)}")
        return jsonify({'error': str(e)}), 500


@projects_bp.route('/projects/<project_id>', methods=['GET'])
@token_required
@verify_sponsor
def get_project(project_id):
    """Get a single project by ID for editing"""
    try:
        spons_id = getattr(request, 'spons_id', None)
        if not spons_id:
            return jsonify({'error': 'Sponsor ID not found in request'}), 400

        # Fetch project from Anvil
        project = anvil.server.call('get_project_by_uid', project_id)
        if not project:
            return jsonify({'error': 'Project not found'}), 404

        # Authorization check: only project creator can edit
        if project.get('org') != spons_id:
            return jsonify({'error': 'Unauthorized: Project not owned by your organization'}), 403

        return jsonify({
            'message': 'Project fetched successfully',
            'project': project
        }), 200

    except Exception as e:
        print(f"Get project error: {str(e)}")
        return jsonify({'error': str(e)}), 500




@projects_bp.route('/projects/<project_id>', methods=['PUT'])
@token_required
@verify_sponsor
def update_project(project_id):
    try:
        current_user = request.user
        spons_id = getattr(request, 'spons_id', None)
        data = request.get_json()

        # Input Validation
        if not isinstance(data, dict):
            return jsonify({'error': 'Invalid input data format'}), 400

        existing = anvil.server.call('get_project_by_uid', project_id)
        if not existing:
            return jsonify({'error': 'Project not found'}), 404

        if existing.get('org') != spons_id:
            return jsonify({'error': 'Unauthorized: Project not owned by your organization'}), 403

        updated_data = {}

        # AFTER (fix data types):
        # String fields
        string_fields = ['title', 'instructions', 'type']
        for field in string_fields:
            updated_data[field] = data.get(field, existing.get(field) or '')

        # Boolean fields - preserve their boolean nature
        boolean_fields = ['allotted', 'browse', 'open']
        for field in boolean_fields:
            if field in data:
                # Ensure it's a boolean
                updated_data[field] = bool(data[field])
            else:
                # Keep existing value (already boolean)
                updated_data[field] = existing.get(field, False)

        # Public details
        public_details = existing.get('public_details', {})
        for key in ['description', 'requirements', 'outcomes']:
            if key in data:
                pd_key = key.capitalize() if key != 'description' else 'Description'
                public_details[pd_key] = data[key]
        updated_data['public_details'] = public_details

        # Domains & Skills: ensure JSON safety
        for field in ['domains', 'skills']:
            if field in data:
                if isinstance(data[field], list):
                    updated_data[field] = json.dumps(data[field])
                else:
                    return jsonify({'error': f'{field} must be a list'}), 400
            else:
                updated_data[field] = existing.get(field)

        # Milestones: default to {}
        updated_data['milestones'] = data.get('milestones', existing.get('milestones', {}))

        # Business logic (optional): auto-close if allotted
        if updated_data.get('allotted') is True:
            updated_data['open'] = False

        # Ensure safe fields
        updated_data['uid'] = project_id
        updated_data['org'] = spons_id
        # updated_data['owner'] = current_user.get('email')  # commented out as per requirements

        result = anvil.server.call('update_project', project_id, updated_data)

        if result.get('success'):
            return jsonify({
                'message': 'Project updated successfully',
                'updated_fields': result.get('updated_fields'),
                'project': result.get('project')
            }), 200
        else:
            return jsonify({'error': result.get('error', 'Update failed')}), 500

    except Exception as e:
        print(f"Update project error at Flask Level: {str(e)}")
        return jsonify({'error': str(e)}), 500


@projects_bp.route('/projects/<project_id>', methods=['DELETE'])
@token_required
@verify_sponsor
def delete_project(project_id):
    try:
        spons_id = getattr(request, 'spons_id', None)
        if not spons_id:
            return jsonify({'error': 'Sponsor ID not found in request'}), 400
        # Check if project exists
        existing = anvil.server.call('get_project_by_uid', project_id)
        if not existing:
            return jsonify({'error': 'Project not found'}), 404

        # Check ownership
        if existing.get('org') != spons_id:
            return jsonify({'error': 'Unauthorized: Project not owned by your organization'}), 403

        # Call Anvil server function to delete
        result = anvil.server.call('delete_project', project_id,spons_id)

        if result.get('success'):
            return jsonify({'message': 'Project deleted successfully'}), 200
        else:
            return jsonify({'error': result.get('error', 'Deletion failed')}), 500

    except Exception as e:
        print(f"Delete project error at Flask Level: {str(e)}")
        return jsonify({'error': str(e)}), 500






# ===== SPONSOR ENDPOINTS ==============================================================================

@projects_bp.route('/projects/browse', methods=['GET'])
@token_required
@verify_sponsor  # Add sponsor verification
def get_browseable_projects():
    """Get all projects where browse=True (public browsing, no auth required)"""
    try:
        # Get filter parameters
        search_term = request.args.get('search')
        project_type = request.args.get('type')
        
        result = anvil.server.call('get_browseable_projects')
        
        if result.get('success'):
            projects = result.get('projects', [])
            
            # Apply additional filters if provided
            if search_term:
                search_lower = search_term.lower()
                projects = [p for p in projects 
                          if search_lower in p.get('title', '').lower() 
                          or search_lower in p.get('public_details', {}).get('Description', '').lower()]
            
            if project_type:
                projects = [p for p in projects 
                          if p.get('type', '').lower() == project_type.lower()]
            
            return jsonify({
                'message': 'Browseable projects fetched successfully',
                'projects': projects,
                'count': len(projects),
                'total_browseable': result.get('count', 0),
                'filters_applied': {
                    'search': search_term,
                    'type': project_type
                }
            }), 200
        else:
            return jsonify({

                'error': result.get('error', 'Failed to fetch browseable projects'),
                'projects': [],
                'count': 0
            }), 500
        
    except Exception as e:
        print(f"Get browseable projects error: {str(e)}")
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500




@projects_bp.route('/projects/<project_id>/sponsorship/<spons_id>', methods=['GET'])
@token_required
@verify_sponsor
def get_sponsorship_details(project_id, spons_id):
    """
    Fetch sponsorship details for a specific sponsor ID from the project's public_details.
    """
    try:
        # Verify the requesting sponsor matches the spons_id in URL (security check)
        requesting_spons_id = getattr(request, 'spons_id', None)
        if requesting_spons_id != spons_id:
            return jsonify({"error": "Unauthorized: Cannot access other sponsor's data"}), 403

        # Fetch the project
        project = anvil.server.call('get_project_by_uid', project_id)
        if not project:
            return jsonify({"error": f"Project with ID '{project_id}' not found."}), 404

        # Extract sponsorship details from public_details.sponsors (FIXED LOCATION)
        public_details = project.get('public_details', {})
        sponsors = public_details.get('sponsors', {})

        if spons_id not in sponsors:
            return jsonify({"error": f"Sponsorship for sponsor ID '{spons_id}' not found."}), 404

        sponsorship_details = sponsors[spons_id]

        return jsonify({
            "success": True,
            "sponsorship": sponsorship_details
        }), 200

    except Exception as e:
        print(f"Error fetching sponsorship details: {str(e)}")
        return jsonify({"error": f"Server error: {str(e)}"}), 500


# ===== SPONSOR-SPECIFIC ENDPOINTS =====

@projects_bp.route('/projects/my', methods=['GET'])
@token_required
@verify_sponsor
def get_my_created_projects():
    """Get projects created by the current sponsor organization"""
    try:
        spons_id = getattr(request, 'spons_id', None)
        if not spons_id:
            return jsonify({'error': 'Sponsor ID not found in request'}), 400
        
        result = anvil.server.call('get_my_created_projects_by_sponsor', spons_id)
        
        if result.get('success'):
            return jsonify({
                'message': 'Projects fetched successfully',
                'projects': result.get('projects', []),
                'count': result.get('count', 0),
                'sponsor_id': spons_id
            }), 200
        else:
            return jsonify({
                'error': result.get('error', 'Failed to fetch created projects'),
                'projects': [],
                'count': 0
            }), 500
        
    except Exception as e:
        print(f"Get my created projects error: {str(e)}")
        return jsonify({'error': str(e)}), 500


@projects_bp.route('/projects/sponsored', methods=['GET'])
@token_required
@verify_sponsor
def get_my_sponsored_projects():
    """Get projects sponsored by the current sponsor organization (lightweight version)"""
    try:
        spons_id = getattr(request, 'spons_id', None)
        if not spons_id:
            return jsonify({'error': 'Sponsor ID not found in request'}), 400
        
        result = anvil.server.call('get_my_sponsored_projects_by_sponsor', spons_id)
        
        if result.get('success'):
            return jsonify({
                'message': 'Sponsored projects fetched successfully',
                'sponsored_projects': result.get('sponsored_projects', []),
                'count': result.get('count', 0),
                'sponsor_id': spons_id
            }), 200
        else:
            return jsonify({
                'error': result.get('error', 'Failed to fetch sponsored projects'),
                'sponsored_projects': [],
                'count': 0
            }), 500
        
    except Exception as e:
        print(f"Get my sponsored projects error: {str(e)}")
        return jsonify({'error': str(e)}), 500
    







@projects_bp.route('/sponsors/dashboard', methods=['GET'])
@token_required
@verify_sponsor
def sponsor_dashboard():
    """Get both created and sponsored projects for the current sponsor organization.
        This Endpoint is just created to showcase the use of ThreadPoolExecutor & Concurrent calls to Anvil server functions to optimize performance by fetching created and sponsored projects in parallel. The individual endpoints for created and sponsored projects are still available and can be used independently if needed.
     """
    spons_id = getattr(request, 'spons_id', None)
    if not spons_id:
        return jsonify({"error": "Sponsor ID not found in request"}), 400

    created_result, sponsored_result = call_anvil_concurrent([
        ("get_my_created_projects_by_sponsor", spons_id),
        ("get_my_sponsored_projects_by_sponsor", spons_id),
    ])

    if not created_result.get("success"):
        return jsonify({"error": created_result.get("error", "Failed to fetch created projects")}), 500

    if not sponsored_result.get("success"):
        return jsonify({"error": sponsored_result.get("error", "Failed to fetch sponsored projects")}), 500

    return jsonify({
        "created_projects": created_result.get("projects", []),
        "sponsored_projects": sponsored_result.get("projects", [])
    }), 200










@projects_bp.route('/projects/analytics-demo', methods=['GET'])
@token_required
@verify_sponsor
def analytics_demo():
    """
    Demo endpoint for ProcessPoolExecutor.

    Technical reason:
    - Fetching projects is I/O-bound and stays in the normal request flow.
    - Counting, grouping, and aggregating over a large project list is CPU-bound.
    - Offloading that work to a process pool bypasses the GIL for true parallelism.
    """
    try:
        spons_id = getattr(request, 'spons_id', None)
        if not spons_id:
            return jsonify({"error": "Sponsor ID not found in request"}), 400

        # Step 1: get data using normal I/O
        result = anvil.server.call('get_my_created_projects_by_sponsor', spons_id)
        if not result.get("success"):
            return jsonify({"error": result.get("error", "Failed to fetch projects")}), 500

        projects = result.get("projects", [])
        if not isinstance(projects, list):
            return jsonify({"error": "Invalid projects payload"}), 500

        # Step 2: CPU-bound analytics in a separate process
        future = run_project_analytics_in_process(projects)
        analytics = future.result(timeout=10)

        return jsonify({
            "message": "Project analytics computed successfully",
            "analytics": analytics
        }), 200

    except Exception as e:
        print(f"Analytics demo error: {str(e)}")
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500