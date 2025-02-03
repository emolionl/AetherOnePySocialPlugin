from flask import Blueprint, jsonify, request
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
    social_blueprint = Blueprint('social', __name__)
    
    # Initialize databases
    db = get_case_dao('data/aetherone.db')
    social_db = SocialDatabase('data/social.db')

    # Get API configuration from environment variables
    API_BASE_URL = os.getenv('API_BASE_URL')
    API_VERSION = os.getenv('API_VERSION')
    ANALYSIS_ENDPOINT = os.getenv('ANALYSIS_ENDPOINT')
    
    # Construct full API URL
    api_url = f"{API_BASE_URL}/{API_VERSION}{ANALYSIS_ENDPOINT}"

    # CREATE
    @social_blueprint.route('/key', methods=['POST'])
    def create_analysis_key():
        try:
            data = request.get_json()
            user_id = data.get('user_id')
            analysis_id = data.get('analysis_id')
            machine_id = data.get('machine_id')
            key = data.get('key')
            
            if not user_id or not analysis_id or not machine_id or not key:
                return jsonify({
                    "status": "error",
                    "message": "user_id, analysis_id, machine_id and key are required"
                }), 400
            
            # Create metadata with timestamp
            metadata = json.dumps({
                "created_from": "key_endpoint",
                "timestamp": datetime.now().isoformat()
            })
            
            # Store the key in database
            key_id = social_db.create_analysis_key(
                key=key,
                analysis_id=analysis_id,
                user_id=user_id,
                metadata=metadata
            )
            
            # Get the created key data
            key_data = social_db.get_analysis_key(key)
            
            return jsonify({
                "status": "success",
                "message": "Analysis key created successfully",
                "data": {
                    "key_id": key_id,
                    "key": key,
                    "user_id": user_id,
                    "analysis_id": analysis_id,
                    "created_at": key_data['created_at'] if key_data else None
                }
            })

        except Exception as e:
            print(f"Error creating analysis key: {str(e)}")
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
            
            return jsonify({
                "status": "success",
                "message": f"Found {len(keys)} keys for user {user_id}",
                "data": {
                    "user_id": user_id,
                    "keys": keys
                }
            })

        except Exception as e:
            print(f"Error getting user analysis keys: {str(e)}")
            return jsonify({
                "status": "error",
                "message": str(e)
            }), 500

    @social_blueprint.route('/key/<string:key>', methods=['GET'])
    def get_analysis_key(key):
        try:
            key_data = social_db.get_analysis_key(key)

            
            if not key_data:
                return jsonify({
                    "status": "error",
                    "message": "Key not found"
                }), 404
                
            return jsonify({
                "status": "success",
                "data": key_data
            })

        except Exception as e:
            print(f"Error getting analysis key: {str(e)}")
            return jsonify({
                "status": "error",
                "message": str(e)
            }), 500

    # UPDATE
    @social_blueprint.route('/key/<string:key>', methods=['PUT'])
    def update_analysis_key(key):
        try:
            data = request.get_json()
            status = data.get('status')
            metadata = data.get('metadata')
            
            if status:
                social_db.update_analysis_key_status(key, status)
            
            if metadata:
                social_db.update_analysis_key_metadata(key, json.dumps(metadata))
            
            # Get updated key data
            key_data = social_db.get_analysis_key(key)
            
            if not key_data:
                return jsonify({
                    "status": "error",
                    "message": "Key not found"
                }), 404
                
            return jsonify({
                "status": "success",
                "message": "Key updated successfully",
                "data": key_data
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
        routes = []
        for rule in social_blueprint.url_map.iter_rules():
            routes.append({
                "endpoint": rule.endpoint,
                "methods": list(rule.methods),
                "path": str(rule)
            })
        return jsonify(routes)

    @social_blueprint.route('/ping', methods=['GET'])
    def ping():
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

    return social_blueprint