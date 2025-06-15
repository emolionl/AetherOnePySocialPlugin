from flask import Blueprint, jsonify, request, current_app, send_from_directory
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
from flasgger import Swagger, swag_from
import traceback

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
    analysis_connected_key_url = f"{API_BASE_URL}/api/analysis/key"
    cleanup_data = f"{API_BASE_URL}/api/utils/clear-data"

    # Serve frontend static files
    FRONTEND_DIST_DIR = os.path.join(os.path.dirname(__file__), 'frontend', 'dist')
    FRONTEND_PUBLIC_DIR = os.path.join(os.path.dirname(__file__), 'frontend', 'public')

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

    @social_blueprint.route('/key', methods=['POST'])
    def create_analysis_key():
        """
        Create a new analysis key for a session and user. Requires login.
        ---
        parameters:
          - name: body
            in: body
            required: true
            schema:
              type: object
              properties:
                local_session_id:
                  type: integer
                  description: Local session ID
        responses:
          200:
            description: Key created successfully
            schema:
              type: object
              properties:
                status:
                  type: string
                server:
                  type: object
                local:
                  type: object
          401:
            description: Unauthorized
          400:
            description: Missing required fields
        """
        try:
            data = request.get_json()
            user = social_db.get_only_user()
            if not user or not user.get('token'):
                return jsonify({
                    "status": "error",
                    "message": "No user or token found. Please login."
                }), 401
            server_user_id = user.get('server_user_id')
            local_session_id = data.get('local_session_id')
            token = user.get('token')
            if not all([server_user_id, local_session_id, token]):
                return jsonify({
                    "status": "error",
                    "message": "server_user_id, local_session_id, and token are required"
                }), 400
            # Check if a key already exists for this session and user
            existing_keys = social_db.get_analysis_keys_by_user(server_user_id)
            for k in existing_keys:
                if k['session_id'] == local_session_id:
                    return jsonify({
                        "status": "exists",
                        "message": "Key already exists for this session.",
                        "local": k
                    })
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

    @social_blueprint.route('/key/<int:user_id>', methods=['GET'])
    def get_user_analysis_keys(user_id):
        """
        Get all analysis keys for a user (local and server).
        ---
        parameters:
          - name: user_id
            in: path
            type: integer
            required: true
            description: User ID
        responses:
          200:
            description: List of keys
            schema:
              type: object
              properties:
                status:
                  type: string
                message:
                  type: string
                data:
                  type: object
          401:
            description: Unauthorized
        """
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
                    resp = requests.get(f"{key_url}/{user_id}", headers=headers)
                    resp.raise_for_status()
                    server_keys = resp.json()
                    # print(f"[DEBUG]get_key_by_string token: {token}")
                    # print(f"[DEBUG]get_key_by_string key_url: {key_url}")
                    # print(f"[DEBUG]get_key_by_string server_key: {server_keys}")
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
        """
        Get a specific analysis key by key string (local and server).
        ---
        parameters:
          - name: key
            in: path
            type: string
            required: true
            description: The key string
        responses:
          200:
            description: Key details
            schema:
              type: object
              properties:
                status:
                  type: string
                data:
                  type: object
          401:
            description: Unauthorized
        """
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

    @social_blueprint.route('/key/<string:key>', methods=['PUT'])
    def update_analysis_key(key):
        """
        Update the status and metadata of an analysis key (local and server).
        ---
        parameters:
          - name: key
            in: path
            type: string
            required: true
            description: The key string
          - name: body
            in: body
            required: true
            schema:
              type: object
              properties:
                status:
                  type: string
                  description: New status (e.g., 'used')
        responses:
          200:
            description: Key updated
            schema:
              type: object
              properties:
                status:
                  type: string
                local:
                  type: object
                server:
                  type: object
          404:
            description: Key not found
          401:
            description: Unauthorized
        """
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

    @social_blueprint.route('/key/<string:key>', methods=['DELETE'])
    def delete_analysis_key(key):
        """
        Delete an analysis key locally.
        ---
        parameters:
          - name: key
            in: path
            type: string
            required: true
            description: The key string
        responses:
          200:
            description: Key deleted
            schema:
              type: object
              properties:
                status:
                  type: string
                message:
                  type: string
          404:
            description: Key not found
        """
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

    @social_blueprint.route('/sessions', methods=['GET'])
    def get_sessions():
        """
        Get all sessions (across all cases).
        ---
        responses:
          200:
            description: List of sessions
            schema:
              type: array
              items:
                type: object
        """
        try:
            sessions = db.list_all_sessions()  # New method to be implemented in DAO
            return jsonify({'sessions': [s.__dict__ for s in sessions]})
        except Exception as e:
            return jsonify({'status': 'error', 'message': str(e)}), 500
        
    @social_blueprint.route('/session/<int:session_id>', methods=['GET'])
    def get_session(session_id):
        session = db.get_session(session_id)
        return jsonify(session)
    
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
        """
        Share analysis data with the external server.
        ---
        parameters:
          - name: body
            in: body
            required: true
            schema:
              type: object
              properties:
                session_id:
                  type: integer
                  description: Local session ID
                key:
                  type: string
                  description: Analysis key
        responses:
          200:
            description: Analysis shared successfully
            schema:
              type: object
              properties:
                message:
                  type: string
                external_reference:
                  type: string
          401:
            description: Unauthorized
          400:
            description: Missing required fields
        """
        data = request.get_json()
        session_id = data.get('session_id')
        user = social_db.get_only_user()
        if not user or not user.get('token'):
            return jsonify({
                "status": "error",
                "message": "No user or token found. Please login."
            }), 401
        user_id = user.get('server_user_id')
        token = user.get('token')
        headers = {"Authorization": f"Bearer {token}"}
        key = data.get('key')
        machine_id = str(uuid.getnode())

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
                return jsonify({"error": "Associated analyses not found, your session is empty, no rates, you only have session"}), 404
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
                        "user_id": user_id,
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

            
            data_to_send = {
                "status": "success",
                "message": f"Found {len(session_data)} analyses with their related data",
                "data": {
                    "session_id": session_id,
                    "user_id": user_id,
                    "machine_id": machine_id,
                    "key": key,
                    "analyses": session_data
                }
            }
            data_to_send = convert_datetimes(data_to_send)
            # Send to external API
            response = requests.post(
                analysis_url,
                json=data_to_send,
                headers=headers
            )
            response.raise_for_status()
            
            # Update key status
            social_db.update_analysis_key_status(key, 'used')
            
            return jsonify({
                "status": "success",
                "status_code": 200,
                "message": "Analysis data shared successfully",
                "external_reference": response.json().get("id")
            })
            
        except requests.RequestException as e:
            return jsonify({"error": f"External API error: {str(e)}"}), 500
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @social_blueprint.route('/debug_routes', methods=['GET'])
    def debug_routes():
        """
        List all registered routes for the AetherOnePySocial plugin.
        ---
        responses:
          200:
            description: List of registered routes
            schema:
              type: array
              items:
                type: object
                properties:
                  endpoint:
                    type: string
                  methods:
                    type: array
                    items:
                      type: string
                  path:
                    type: string
        """
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
        """
        Health check endpoint for the AetherOnePySocial plugin.
        ---
        responses:
          200:
            description: Pong response with plugin info and timestamp
            schema:
              type: object
              properties:
                status:
                  type: string
                message:
                  type: string
                plugin:
                  type: string
                timestamp:
                  type: string
        """
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
            traceback.print_exc()
            return jsonify({
                "status": "error",
                "message": str(e)
            }), 500

    @social_blueprint.route('/send_key/<string:key>', methods=['GET'])
    def send_key(key):
        """
        Get key details from the external server
        ---
        parameters:
          - name: key
            in: path
            type: string
            required: true
            description: The key string to fetch
        responses:
          200:
            description: Key details
            schema:
              type: object
              properties:
                status:
                  type: string
                result:
                  type: object
          401:
            description: Unauthorized
          400:
            description: Missing key
        """
        if not key:
            return jsonify({
                "status": "error",
                "message": "Missing required 'key' parameter"
            }), 400

        user = social_db.get_only_user()
        if not user or not user.get('token'):
            return jsonify({
                "status": "error",
                "message": "No user or token found. Please login."
            }), 401

        token = user.get('token')
        try:
            headers = {"Authorization": f"Bearer {token}"}
            resp = requests.get(f"{key_url}/{key}", headers=headers)
            resp.raise_for_status()
            result = resp.json()
            print(f"[DEBUG]send_key result: {result}")
            return jsonify({
                "status": "success",
                "result": result
            })
        except Exception as e:
            return jsonify({
                "status": "error",
                "message": str(e)
            }), 500

    @social_blueprint.route('/analysis_for_key/<string:key>', methods=['GET'])
    def analysis_for_key(key):
        """
        Get all analysis connected to a key from the external server
        ---
        parameters:
          - name: key
            in: path
            type: string
            required: true
            description: The key string to fetch analysis for
        responses:
          200:
            description: Analysis list
            schema:
              type: object
              properties:
                status:
                  type: string
                result:
                  type: object
          401:
            description: Unauthorized
          400:
            description: Missing key
        """
        if not key:
            return jsonify({
                "status": "error",
                "message": "Missing required 'key' parameter"
            }), 400

        user = social_db.get_only_user()
        if not user or not user.get('token'):
            return jsonify({
                "status": "error",
                "message": "No user or token found. Please login."
            }), 401

        token = user.get('token')
        try:
            headers = {"Authorization": f"Bearer {token}"}
            resp = requests.get(f"{analysis_connected_key_url}/{key}", headers=headers)
            try:
                resp.raise_for_status()
            except requests.HTTPError as http_err:
                # If the response has JSON, forward it
                try:
                    error_json = resp.json()
                    return jsonify({
                        "status": "error",
                        "error": error_json
                    }), resp.status_code
                except Exception:
                    # If not JSON, just forward the text
                    return jsonify({
                        "status": "error",
                        "message": str(http_err),
                        "raw_response": resp.text
                    }), resp.status_code

            result = resp.json()
            print(f"[DEBUG]analysis_for_key result: {result}")
            return jsonify({
                "status": "success",
                "result": result
            })
        except Exception as e:
            return jsonify({
                "status": "error",
                "message": str(e)
            }), 500
    
    @social_blueprint.route('/check_key_exists/<string:key>', methods=['GET'])
    def check_key_exists(key):
        """
        Check if a key exists and has associated sessions on the external server.
        Forwards the response from /api/analysis/public/key/<key>.
        """
        if not key:
            return jsonify({
                "status": "error",
                "message": "Missing required 'key' parameter"
            }), 400

        user = social_db.get_only_user()
        if not user or not user.get('token'):
            return jsonify({
                "status": "error",
                "message": "No user or token found. Please login."
            }), 401

        token = user.get('token')
        public_key_url = f"{API_BASE_URL}/api/analysis/public/key/{key}"
        try:
            headers = {"Authorization": f"Bearer {token}"}
            resp = requests.get(public_key_url, headers=headers)
            try:
                resp.raise_for_status()
            except requests.HTTPError as http_err:
                try:
                    error_json = resp.json()
                    return jsonify(error_json), resp.status_code
                except Exception:
                    return jsonify({
                        "status": "error",
                        "message": str(http_err),
                        "raw_response": resp.text
                    }), resp.status_code
            result = resp.json()
            return jsonify(result)
        except Exception as e:
            return jsonify({
                "status": "error",
                "message": str(e)
            }), 500
    
    @social_blueprint.route('/local/login', methods=['POST', 'OPTIONS'])
    def login():
        """
        Login to the external server and store the token locally.
        ---
        parameters:
          - name: body
            in: body
            required: true
            schema:
              type: object
              properties:
                email:
                  type: string
                  description: User email
                password:
                  type: string
                  description: User password
        responses:
          200:
            description: Login successful
            schema:
              type: object
              properties:
                status:
                  type: string
                access_token:
                  type: string
          400:
            description: Missing required fields
          401:
            description: Unauthorized
        """
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
    
    @social_blueprint.route('/local/register', methods=['POST'])
    def register():
        """
        Register a new user on the external server and store the token locally.
        ---
        parameters:
          - name: body
            in: body
            required: true
            schema:
              type: object
              properties:
                email:
                  type: string
                  description: User email
                password:
                  type: string
                  description: User password
                username:
                  type: string
                  description: Optional username
        responses:
          200:
            description: Registration successful
            schema:
              type: object
              properties:
                status:
                  type: string
                external_response:
                  type: object
          400:
            description: Missing required fields
        """
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

    def convert_datetimes(obj):
        if isinstance(obj, dict):
            return {k: convert_datetimes(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [convert_datetimes(i) for i in obj]
        elif isinstance(obj, datetime):
            return obj.isoformat()
        else:
            return obj

    # Swagger config for blueprint
    swagger_template = {
        "swagger": "2.0",
        "info": {
            "title": "AetherOnePySocial API",
            "description": "API documentation for the AetherOnePySocial plugin.",
            "version": "1.0.0"
        },
        "basePath": "/aetheronepysocial"
    }
    @social_blueprint.route('/', methods=['GET'])
    def index():
        # Serve the frontend index.html from dist if it exists, else from public
        if os.path.exists(os.path.join(FRONTEND_DIST_DIR, 'index.html')):
            return send_from_directory(FRONTEND_DIST_DIR, 'index.html')
        else:
            return send_from_directory(FRONTEND_PUBLIC_DIR, 'index.html')

    @social_blueprint.route('/frontend/<path:filename>', methods=['GET'])
    def frontend_static(filename):
        # Serve static files for the frontend from dist if built, else from public
        dist_path = os.path.join(FRONTEND_DIST_DIR, filename)
        public_path = os.path.join(FRONTEND_PUBLIC_DIR, filename)
        if os.path.exists(dist_path):
            return send_from_directory(FRONTEND_DIST_DIR, filename)
        elif os.path.exists(public_path):
            return send_from_directory(FRONTEND_PUBLIC_DIR, filename)
        else:
            return jsonify({"error": "File not found"}), 404

    @social_blueprint.route('/docs', methods=['GET'])
    def docs():
        # Redirect to the main Swagger UI (Flasgger serves at /apidocs by default)
        return '''<script>window.location.href='/apidocs';</script>'''

    @social_blueprint.route('/base_url', methods=['GET'])
    def base_url():
        """
        Returns the base URL (mount point) for the plugin, so the frontend can use it for dynamic asset loading or API calls.
        """
        # This is hardcoded for now, but could be made dynamic if needed
        return jsonify({"base_url": "/aetheronepysocial/"})

    @social_blueprint.route('/server', methods=['POST'])
    def add_server():
        """
        Add a new server URL and description to the servers table.
        Expects JSON: {"url": "...", "description": "..."}
        """
        data = request.get_json()
        url = data.get('url')
        description = data.get('description')
        if not url:
            return jsonify({"status": "error", "message": "Missing 'url' field"}), 400
        try:
            server_id = social_db.add_server(url, description)
            return jsonify({"status": "success", "server_id": server_id})
        except Exception as e:
            return jsonify({"status": "error", "message": str(e)}), 500

    @social_blueprint.route('/server', methods=['GET'])
    def list_servers():
        """
        List all servers from the servers table.
        """
        try:
            servers = social_db.get_servers()
            return jsonify({"status": "success", "servers": servers})
        except Exception as e:
            return jsonify({"status": "error", "message": str(e)}), 500
    
    @social_blueprint.route('/user', methods=['GET'])
    def get_user_info():
        """Return the only user from social.db, including server_user_id."""
        user = social_db.get_only_user()
        if user:
            return jsonify(user)
        else:
            return jsonify({'status': 'error', 'message': 'No user found'}), 404
        
    @social_blueprint.route('/<path:filename>', methods=['GET'])
    def serve_vue_static(filename):
        # Serve static files for the frontend from dist if built, else from public
        dist_path = os.path.join(FRONTEND_DIST_DIR, filename)
        public_path = os.path.join(FRONTEND_PUBLIC_DIR, filename)
        if os.path.exists(dist_path):
            return send_from_directory(FRONTEND_DIST_DIR, filename)
        elif os.path.exists(public_path):
            return send_from_directory(FRONTEND_PUBLIC_DIR, filename)
        else:
            return jsonify({"error": "File not found"}), 404

    @social_blueprint.route('/plugins', methods=['GET'])
    def list_plugins():
        """
        List all available plugins in the plugins directory.
        """
        plugins_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        try:
            plugins = [
                name for name in os.listdir(plugins_dir)
                if os.path.isdir(os.path.join(plugins_dir, name)) and not name.startswith('__')
            ]
            return jsonify({"status": "success", "plugins": plugins})
        except Exception as e:
            return jsonify({"status": "error", "message": str(e)}), 500

    

    return social_blueprint