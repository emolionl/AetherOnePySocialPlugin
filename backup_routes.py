# plugins/AetherOnePySocial/routes.py
import os
from flask import Blueprint, jsonify, request
import requests
from services.databaseService import get_case_dao
from datetime import datetime
import json
from rich import print as rprint
from rich.pretty import pprint as rpprint
from icecream import ic

def p(obj, title="Debug Object"):
    """
    Pretty prints all attributes of an object
    """
    print(f"\n=== {title} ===")
    if obj is None:
        print("Object is None")
        return
        
    try:
        # Try to print as dictionary first
        if hasattr(obj, '__dict__'):
            print("\nAs Dictionary:")
            ic(obj.__dict__)
            
        # # Print all attributes
        # print("\nAll Attributes:")
        # for attr in dir(obj):
        #     if not attr.startswith('__'):
        #         value = getattr(obj, attr)
        #         ic(attr, value)
                
    except Exception as e:
        print(f"Error printing object: {str(e)}")

def create_blueprint():
    social_blueprint = Blueprint('social', __name__)
    
    # Get database connection using existing service
    db = get_case_dao('data/aetherone.db')
    
    @social_blueprint.route('/ping', methods=['GET'])
    def ping():
        return jsonify({
            "status": "success",
            "message": "Plugin 'AetherOnePySocial' routes loaded and registered with prefix '/aetheronepysocial'"
        })
    
    @social_blueprint.route('/share_session', methods=['POST'])
    def share_session():
        data = request.get_json()
        session_id = data.get('session_id')
        
        if not session_id:
            return jsonify({"error": "Session ID is required"}), 400
            
        # Get session using existing database service
        session = db.get_session(session_id)
        if not session:
            return jsonify({"error": "Invalid session ID"}), 404
            
        try:
            # Prepare session data for external API
            session_data = {
                "id": session.id,
                "intention": session.intention,
                "description": session.description,
                "created": session.created.isoformat(),
                "case_id": session.caseID
            }
            
            # Send to external API
            response = requests.post(
                "https://your-external-api.com/sessions",
                json=session_data
            )
            response.raise_for_status()
            
            return jsonify({
                "message": "Session shared successfully",
                "external_reference": response.json().get("id")
            })
            
        except requests.RequestException as e:
            return jsonify({"error": f"External API error: {str(e)}"}), 500
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @social_blueprint.route('/share_analysis', methods=['POST'])
    def share_analysis():
        data = request.get_json()
        
        analysis_id = data.get('analysis_id')
        if not analysis_id:
            return jsonify({"error": "Analysis ID is required"}), 400
        try:
            # Get analysis data
            analysis = db.get_analysis(analysis_id)
            if not analysis:
                return jsonify({"error": "Invalid analysis ID"}), 404
            p(analysis)
            
            # Get associated session
            session = db.get_session(analysis.sessionID)
            if not session:
                return jsonify({"error": "Associated session not found"}), 404
            p(session)
            # Get case data
            case = db.get_case(session.caseID)
            if not case:
                return jsonify({"error": "Associated case not found"}), 404
            p(case)
            
            # Get catalog data
            catalog = db.get_catalog(analysis.catalogId)
            if not catalog:
                return jsonify({"error": "Associated catalog not found"}), 404
            p(catalog)    
            # Get rates for this analysis
            rates = db.list_rates_for_analysis(analysis_id)
            p(rates)
            return jsonify({"data": "pp"})
            # Get rate analysis results
            rate_analysis = db.get_rate_analysis(analysis_id)
            if not rate_analysis:
                return jsonify({"error": "Rate analysis results not found"}), 404
            for attr in dir(rate_analysis):
                if not attr.startswith('__'):  # Skip built-in attributes
                    print(f"{attr}: {getattr(rate_analysis, attr)}") 
            return jsonify({"message": "data"})
            # Prepare complete data package
            analysis_data = {
                "case": {
                    "id": case.id,
                    "name": case.name,
                    "created": case.created.isoformat() if hasattr(case, 'created') else None
                },
                "session": {
                    "id": session.id,
                    "intention": session.intention,
                    "description": session.description,
                    "created": session.created.isoformat(),
                    "case_id": session.caseID
                },
                "analysis": {
                    "id": analysis.id,
                    "note": analysis.note,
                    "created": analysis.created.isoformat() if hasattr(analysis, 'created') else None,
                    "session_id": analysis.session_id,
                    "catalog_id": analysis.catalogId
                },
                "catalog": {
                    "id": catalog.id,
                    "name": catalog.name,
                    "description": catalog.description if hasattr(catalog, 'description') else None
                },
                "rates": [
                    {
                        "id": rate.id,
                        "name": rate.name,
                        "value": rate.value,
                        "analysis_id": rate.analysis_id
                    } for rate in rates
                ],
                "rate_analysis": {
                    "id": rate_analysis.id,
                    "analysis_id": rate_analysis.analysis_id,
                    "results": rate_analysis.results,
                    "created": rate_analysis.created.isoformat() if hasattr(rate_analysis, 'created') else None,
                    "status": rate_analysis.status if hasattr(rate_analysis, 'status') else None,
                    "metadata": rate_analysis.metadata if hasattr(rate_analysis, 'metadata') else None
                }
            }
            
            # Send to external API
            response = requests.post(
                "https://your-external-api.com/analysis",
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

    return social_blueprint