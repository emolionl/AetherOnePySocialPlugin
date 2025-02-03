from flask import Blueprint
from .routes import create_blueprint
import os
from .install import install_requirements

def register_plugin():
    """Register the AetherOnePySocial plugin"""
    # Check if requirements are installed
    try:
        import dotenv
        import requests
    except ImportError:
        print("Installing required dependencies for AetherOnePySocial plugin...")
        if not install_requirements():
            raise Exception("Failed to install plugin dependencies")
    
    return create_blueprint() 