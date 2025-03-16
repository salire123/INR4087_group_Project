import sys
import os
# Add the src directory to the path so imports work correctly
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from flask import Flask
from unittest.mock import MagicMock
from routes.auth import auth_bp
from routes.post import post_bp
from routes.history import history_bp  # Import the history blueprint


@pytest.fixture
def app():
    """Create and configure a Flask app for testing"""
    app = Flask(__name__)
    app.config['TESTING'] = True
    app.config['SECRET_KEY'] = 'test_secret_key'
    app.config['JWT'] = MagicMock()
    
    # Register blueprints with proper URL prefixes
    app.register_blueprint(auth_bp, url_prefix='/api')
    app.register_blueprint(post_bp, url_prefix='/api')
    app.register_blueprint(history_bp, url_prefix='/api')  # Register history blueprint
    
    return app


@pytest.fixture
def client(app):
    """Test client for the Flask app"""
    return app.test_client()


@pytest.fixture
def mock_jwt(app):
    """Access to the JWT mock for setting return values"""
    return app.config['JWT']


@pytest.fixture
def auth_headers():
    """Helper fixture to create Authorization headers"""
    def _auth_headers(token='valid_token'):
        # Based on authtool.py, the token is used directly without 'Bearer' prefix
        return {'Authorization': token}
    return _auth_headers