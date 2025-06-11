from flask import Blueprint, jsonify, request, current_app
import requests
from services.databaseService import get_case_dao
from datetime import datetime
import json
from rich import print as rprint
from rich.pretty import pprint as rpprint
from icecream import ic
from .database import SocialDatabase
import uuid
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..'))
db_path = os.path.join(PROJECT_ROOT, 'data', 'aetherone.db')
db = get_case_dao(db_path)

def p(obj, title="Debug Object"):
    """
    Pretty prints all attributes of an object or list of objects
    """
    print(f"\n=== {title} ===")
    if obj is None:
        print("Object is None")
        return
        
    try:
        # Handle list of objects
        if isinstance(obj, list):
            print(f"List containing {len(obj)} items:")
            for index, item in enumerate(obj):
                print(f"\nItem {index + 1}:")
                # Print all attributes of the object
                if hasattr(item, '__dict__'):
                    for attr_name, attr_value in vars(item).items():
                        print(f"{attr_name}: {attr_value}")
                else:
                    print(item)
        # Handle single object
        elif hasattr(obj, '__dict__'):
            for attr_name, attr_value in vars(obj).items():
                print(f"{attr_name}: {attr_value}")
        else:
            print(obj)
    except Exception as e:
        print(f"Error printing object: {str(e)}")
                

def create_blueprint():
    print("[DEBUG] Creating AetherOnePySocial blueprint...")
    social_blueprint = Blueprint('social', __name__)
    
    # Initialize databases
    social_db_path = os.path.join(os.path.dirname(__file__), 'social.db')
    social_db = SocialDatabase(social_db_path)

    # Get API configuration from environment variables
    API_BASE_URL = os.getenv('API_BASE_URL')
    API_VERSION = os.getenv('API_VERSION')
    ANALYSIS_ENDPOINT = os.getenv('ANALYSIS_ENDPOINT')
    
    # Construct full API URL
    api_url = f"{API_BASE_URL}/"
    login_url = f"{API_BASE_URL}/api/auth/login"
    register_url = f"{API_BASE_URL}/api/auth/register"
    logout_url = f"{API_BASE_URL}/api/auth/logout" # needs to be made on serverside logout endpoint
    key_url = f"{API_BASE_URL}/api/keys"
    analysis_url = f"{API_BASE_URL}/api/analysis/share"
    cleanup_data = f"{API_BASE_URL}/api/utils/clear-data"

    # --- Auth helper functions ---
    def login_to_server(email, password, login_url):
        response = requests.post(login_url, data={
            "username": email,
            "password": password
        })
        response.raise_for_status()
        social_db.upsert_user_token(
            response.json().get("username"),
            response.json().get("email"), 
            response.json().get("access_token"),
            response.json().get("user_id"),
        )
        return response.json().get("access_token")

    def send_key_to_server(key_data, api_url, token):
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.post(api_url, json=key_data, headers=headers)
        response.raise_for_status()
        return response.json()

    # CREATE
    @social_blueprint.route('/key', methods=['POST'])
    def create_analysis_key():
        try:
            data = request.get_json()
            user = social_db.get_only_user()
            if not user:
                return jsonify({
                    "status": "error",
                    "message": "No user found. Please login."
                }), 401
            server_user_id = user.get('server_user_id')
            local_session_id = data.get('local_session_id')
            token = user.get('token')
            if not all([server_user_id, local_session_id, token]):
                return jsonify({
                    "status": "error",
                    "message": "server_user_id, local_session_id, and token are required"
                }), 400
            key_data = {
                "user_id": server_user_id,
                "local_session_id": local_session_id
            }
            # Forward to external server
            result = send_key_to_server(key_data, key_url, token)
            key = result.get('key')
            key_id = result.get('key_id')
            session_id = result.get('local_session_id') #local session_id from aetherone sessions
            user_id = result.get('user_id')

            # Create metadata with timestamp
            metadata = json.dumps({
                "created_from": "key_endpoint",
                "timestamp": datetime.now().isoformat()
            })
            
            # Store the key in database
            social_db.create_analysis_key(
                key_id=key_id,
                key=key,
                session_id=session_id,
                user_id=user_id,
                metadata=metadata
            )
            
            # Get the created key data
            key_data_local = social_db.get_analysis_key(key)

            return jsonify({
                "status": "success",
                "server": result,
                "local": key_data_local
            })
        except Exception as e:
            print(f"Error forwarding key to server: {str(e)}")
            return jsonify({
                "status": "error",
                "message": str(e)
            }), 500

    # READ
    @social_blueprint.route('/key/<int:user_id>', methods=['GET'])
    def get_user_analysis_keys(user_id):
        try:
            # Get all keys for the user
            keys = social_db.get_analysis_keys_by_user(user_id)
            # Fetch server keys as well
            server_keys = None
            try:
                user = social_db.get_only_user()
                token = user.get('token') if user else None
                if token:
                    headers = {"Authorization": f"Bearer {token}"}
                    resp = requests.get(key_url, headers=headers)
                    resp.raise_for_status()
                    server_keys = resp.json()
            except Exception as e:
                print(f"[DEBUG] Failed to fetch server keys: {e}")
                server_keys = {"error": str(e)}
            return jsonify({
                "status": "success",
                "message": f"Found {len(keys)} keys for user_id server side use_id  {user_id}",
                "data": {
                    "user_id": user_id,
                    "local": keys,
                    "server": server_keys
                }
            })

        except Exception as e:
            print(f"Error getting user analysis keys: {str(e)}")
            return jsonify({
                "status": "error",
                "message": str(e)
            }), 500

    @social_blueprint.route('/key/<string:key>', methods=['GET'])
    def get_key_by_string(key):
        # Fetch local key
        local_key = social_db.get_analysis_key(key)
        # Fetch server key
        server_key = None
        try:
            user = social_db.get_only_user()
            token = user.get('token') if user else None
            if token:
                headers = {"Authorization": f"Bearer {token}"}
                resp = requests.get(f"{key_url}/{key}", headers=headers)
                resp.raise_for_status()
                server_key = resp.json()
        except Exception as e:
            print(f"[DEBUG] Failed to fetch server key: {e}")
            server_key = {"error": str(e)}
        return jsonify({
            "status": "success",
            "data": {
                "local": local_key,
                "server": server_key
            }
        })

    # UPDATE
    @social_blueprint.route('/key/<string:key>', methods=['PUT'])
    def update_analysis_key(key):
        try:
            data = request.get_json()
            status = data.get('status') # used or not used
            # Always set metadata to updated_from and current timestamp
            from datetime import datetime, timezone
            metadata = json.dumps({
                "updated_from": "key_update_endpoint",
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
            # Update local key
            if status:
                social_db.update_analysis_key_status(key, status)
            social_db.update_analysis_key_metadata(key, metadata)
            # Get updated key data
            key_data = social_db.get_analysis_key(key)
            if not key_data:
                return jsonify({
                    "status": "error",
                    "message": "Key not found"
                }), 404
            # Also update on server
            server_response = None
            try:
                user = social_db.get_only_user()
                token = user.get('token') if user else None
                if token:
                    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
                    patch_url = f"{key_url}/use/{key}"
                    now_iso = datetime.now(timezone.utc).isoformat()
                    patch_data = {"used": True, "used_at": now_iso}
                    resp = requests.patch(patch_url, headers=headers, json=patch_data)
                    resp.raise_for_status()
                    server_response = resp.json()
            except Exception as e:
                print(f"[DEBUG] Failed to update key on server: {e}")
                server_response = {"error": str(e)}
            return jsonify({
                "status": "success",
                "local": key_data,
                "server": server_response
            })
        except Exception as e:
            print(f"Error updating analysis key: {str(e)}")
            return jsonify({
                "status": "error",
                "message": str(e)
            }), 500

    # DELETE
    @social_blueprint.route('/key/<string:key>', methods=['DELETE'])
    def delete_analysis_key(key):
        try:
            if social_db.delete_analysis_key(key):
                return jsonify({
                    "status": "success",
                    "message": "Key deleted successfully"
                })
            else:
                return jsonify({
                    "status": "error",
                    "message": "Key not found"
                }), 404

        except Exception as e:
            print(f"Error deleting analysis key: {str(e)}")
            return jsonify({
                "status": "error",
                "message": str(e)
            }), 500

    # Additional utility endpoints
    @social_blueprint.route('/keys/cleanup', methods=['POST'])
    def cleanup_keys():
        try:
            count = social_db.cleanup_expired_keys()
            return jsonify({
                "status": "success",
                "message": f"Cleaned up {count} expired keys"
            })

        except Exception as e:
            print(f"Error cleaning up keys: {str(e)}")
            return jsonify({
                "status": "error",
                "message": str(e)
            }), 500

    @social_blueprint.route('/analysis', methods=['POST'])
    def share_analysis():
        data = request.get_json()
        session_id = data.get('session_id')
        user_id = data.get('user_id')
        key = data.get('key')
        machine_id = data.get('machine_id')

        if not all([session_id, user_id, key, machine_id]):
            return jsonify({
                "status": "error",
                "message": "session_id, user_id, key and machine_id are required"
            }), 400
       
        try:
            #p(session_id, "session_id")
            # Get session data
            session = db.get_session(session_id)
            if not session:
                return jsonify({"error": "Invalid session ID"}), 404
            #p(session, "session")
            
            # Get associated analysis
            analyses = db.list_analysis(session.id)
            if not analyses:
                return jsonify({"error": "Associated analysss not found"}), 404
            #p(analysis, "analysis")
            # Get case data
            case = db.get_case(session.caseID)
            if not case:
                return jsonify({"error": "Associated case not found"}), 404
            #p(case, "case")

            # Build complete data structure
            session_data = {
                "session": {
                    "id": session.id,
                    "intention": session.intention if hasattr(session, 'intention') else None,
                    "description": session.description if hasattr(session, 'description') else None,
                    "created": session.created.isoformat() if hasattr(session, 'created') else None,
                    "case_id": session.caseID if hasattr(session, 'caseID') else None,
                },
                "case": {
                    "id": case.id,
                    "name": case.name if hasattr(case, 'name') else None,
                    "email": case.email if hasattr(case, 'email') else None,
                    "color": case.color if hasattr(case, 'color') else None,
                    "description": case.description if hasattr(case, 'description') else None,
                    "created": case.created.isoformat() if hasattr(case, 'created') else None,
                    "last_change": case.last_change if hasattr(case, 'last_change') else None
                },
                "analyses": []
            }
            for analysis in analyses:
                # Get catalog data
                catalog = db.get_catalog(analysis.catalogId)
                if not catalog:
                    return jsonify({"error": "Associated catalog not found"}), 404
                #p(catalog, "catalog")    

                # Get rates for this catalog
                rates = db.list_rates_from_catalog(catalog.id)
                if not rates:
                    return jsonify({"error": "Rates not found"}), 404
                #p(rates, "rates")
                #p(analysis.id, "analysis.id")
                # Get rate analysis results
                rate_analysis = db.list_rates_for_analysis(analysis.id)
                if not rate_analysis:
                    return jsonify({"error": "Rate analysis results not found"}), 404
                #p(rate_analysis, "rate_analysis")

                # Debug print for each analysis
                #p(analysis, f"Analysis {analysis.id}")
                #p(rates, f"Rates for analysis {analysis.id}")
                #p(rate_analysis, f"Rate Analysis for analysis {analysis.id}")
                #p(catalog, f"Catalog for analysis {analysis.id}")
            
                analysis_data = {
                    "analysis": {
                        "id": analysis.id,
                        "name": analysis.name if hasattr(analysis, 'name') else None,
                        "target_gv": analysis.target_gv if hasattr(analysis, 'target_gv') else None,
                        "session_id": session_id,
                        "catalog_id": analysis.catalogId if hasattr(analysis, 'catalogId') else None,
                        "created": analysis.created.isoformat() if hasattr(analysis, 'created') else None
                    },
                    "catalog": {
                        "id": catalog.id if catalog else None,
                        "name": catalog.name if catalog else None,
                        "description": catalog.description if catalog and hasattr(catalog, 'description') else None
                    } if catalog else None,
                    "rates": [
                        {
                            "id": rate.id,
                            "signature": rate.signature if hasattr(rate, 'signature') else None,
                            "description": rate.description if hasattr(rate, 'description') else None,
                            "catalog_id": catalog.id,
                        }
                        for rate in rates
                    ] if rates else [],
                    "rate_analysis": [
                        {
                            "id": ra.id,
                            "signature": ra.signature if hasattr(ra, 'signature') else None,
                            "description": ra.description if hasattr(ra, 'description') else None,
                            "catalog_id": ra.catalog_id if hasattr(ra, 'catalog_id') else None,
                            "analysis_id": ra.analysis_id if hasattr(ra, 'analysis_id') else None,
                            "energetic_value": ra.energetic_value if hasattr(ra, 'energetic_value') else None,
                            "gv": ra.gv if hasattr(ra, 'gv') else None,
                            "level": ra.level if hasattr(ra, 'level') else None,
                            "potencyType": ra.potency_type if hasattr(ra, 'potency_type') else None,
                            "potency": ra.potency if hasattr(ra, 'potency') else None,
                            "note": ra.note if hasattr(ra, 'note') else None
                        }
                        for ra in rate_analysis
                    ] if rate_analysis else []
                }
                session_data["analyses"].append(analysis_data)

            # Update key status
            social_db.update_analysis_key_status(key, 'used')
            
            return jsonify({
                "status": "success",
                "message": f"Found {len(session_data)} analyses with their related data",
                "data": {
                    "session_id": session_id,
                    "user_id": user_id,
                    "machine_id": machine_id,
                    "key": key,
                    "analyses": session_data
                }
            })
            # Send to external API
            response = requests.post(
                api_url,
                json=analysis_data
            )
            response.raise_for_status()
            
            return jsonify({
                "message": "Analysis data shared successfully",
                "external_reference": response.json().get("id")
            })
            
        except requests.RequestException as e:
            return jsonify({"error": f"External API error: {str(e)}"}), 500
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @social_blueprint.route('/debug_routes', methods=['GET'])
    def debug_routes():
        prefix = '/aetheronepysocial'  # Change this if your prefix is different
        routes = []
        for rule in current_app.url_map.iter_rules():
            if str(rule).startswith(prefix):
                routes.append({
                    "endpoint": rule.endpoint,
                    "methods": list(rule.methods),
                    "path": str(rule)
                })
        return jsonify(routes)

    @social_blueprint.route('/ping', methods=['GET'])
    def ping():
        print("[DEBUG] /ping endpoint was called!")
        try:
            return jsonify({
                "status": "success",
                "message": "pong",
                "plugin": "AetherOnePySocial",
                "timestamp": datetime.now().isoformat()
            })
        except Exception as e:
            print(f"Error in ping: {str(e)}")
            return jsonify({
                "status": "error",
                "message": str(e)
            }), 500

    # SEND KEY ENDPOINT
    # POST /aetheronepysocial/send_key
    # Payload: {"key_data": {...}, "api_url": "https://external-server.com/api/keys", "token": "..."}
    @social_blueprint.route('/send_key', methods=['POST'])
    def send_key():
        data = request.get_json()
        key_data = data.get('key_data')
        api_url = data.get('api_url')
        token = data.get('token')
        if not all([key_data, api_url, token]):
            return jsonify({
                "status": "error",
                "message": "key_data, api_url, and token are required"
            }), 400
        try:
            result = send_key_to_server(key_data, api_url, token)
            return jsonify({
                "status": "success",
                "result": result
            })
        except Exception as e:
            return jsonify({
                "status": "error",
                "message": str(e)
            }), 500

    # LOGIN ENDPOINT
    # POST /aetheronepysocial/login
    # Payload: {"email": "user@example.com", "password": "secret", "login_url": "https://external-server.com/api/login"}
    @social_blueprint.route('/local/login', methods=['POST'])
    def login():
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')
        if not all([email, password, login_url]):
            return jsonify({
                "status": "error",
                "message": "email, password, and login_url are required"
            }), 400
        try:
            token = login_to_server(email, password, login_url)
            #social_db.update_user_token(email, token)
            return jsonify({
                "status": "success",
                "access_token": token
            })
        except Exception as e:
            return jsonify({
                "status": "error",
                "message": str(e)
            }), 500
    
    # REGISTER ENDPOINT
    # POST /aetheronepysocial/register
    # Payload: {"email": "user@example.com", "password": "secret", "username": "optional", "register_url": "https://external-server.com/api/register"}
    @social_blueprint.route('/local/register', methods=['POST'])
    def register():
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')
        username = data.get('username', email)  # fallback to email if username not provided
        if not all([email, password, register_url]):
            return jsonify({
                "status": "error",
                "message": "email, password are required"
            }), 400
        try:
            # Forward registration to external server
            payload = {
                "email": email,
                "password": password,
                "username": username
            }
            response = requests.post(register_url, json=payload)
            response.raise_for_status()

            response.raise_for_status()
            #print(f"register response: {response.json()}")
            # On success, store user locally
            social_db.save_user(username, 
                                email, 
                                response.json().get("access_token"),
                                response.json().get("user_id"))
            return jsonify({
                "status": "success",
                "external_response": response.json()
            })
        except Exception as e:
            return jsonify({
                "status": "error",
                "message": str(e)
            }), 500

    return social_blueprint