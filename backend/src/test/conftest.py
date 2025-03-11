import pytest
import subprocess
import time
import os
from flask import Flask
from routes.auth import auth_bp
import mysql.connector
from pymongo import MongoClient

# Load environment variables from a .env file or system (assumed to exist)
from dotenv import load_dotenv

load_dotenv()

# Fixture to manage Docker Compose lifecycle
@pytest.fixture(scope="session", autouse=True)
def docker_compose():
    """Spin up Docker Compose services (MySQL and MongoDB) and tear them down after tests."""
    # Start Docker Compose
    subprocess.run(["docker-compose", "up", "-d"], check=True)

    # Wait for databases to be ready
    max_attempts = 30
    attempt = 0
    mysql_ready = False
    mongo_ready = False

    while attempt < max_attempts and not (mysql_ready and mongo_ready):
        attempt += 1
        time.sleep(2)  # Wait 2 seconds between attempts

        # Check MySQL
        try:
            conn = mysql.connector.connect(
                host="localhost",
                port=os.getenv("MYSQL_PORT", "3306"),
                user=os.getenv("MYSQL_USER"),
                password=os.getenv("MYSQL_PASSWORD"),
                database=os.getenv("MYSQL_DATABASE")
            )
            conn.close()
            mysql_ready = True
        except mysql.connector.Error:
            mysql_ready = False

        # Check MongoDB
        try:
            client = MongoClient(
                host="localhost",
                port=int(os.getenv("MONGO_PORT", "27017")),
                username=os.getenv("MONGO_USER"),
                password=os.getenv("MONGO_PASSWORD"),
                authSource=os.getenv("MONGO_DATABASE")
            )
            client.server_info()  # Test connection
            client.close()
            mongo_ready = True
        except Exception:
            mongo_ready = False

    if not (mysql_ready and mongo_ready):
        raise Exception("Failed to start databases in time")

    yield  # Run tests

    # Teardown: Stop and remove containers
    subprocess.run(["docker-compose", "down", "-v"], check=True)

# Fixture for Flask app
@pytest.fixture
def app():
    """Create and configure a Flask app instance for testing."""
    app = Flask(__name__)
    app.config['JWT'] = MockJWT()  # Mock JWT class (see below)
    app.register_blueprint(auth_bp)
    return app

# Fixture for Flask test client
@pytest.fixture
def client(app):
    """Provide a test client for the Flask app."""
    return app.test_client()

# Mock JWT class for testing
class MockJWT:
    def __init__(self):
        self.blacklist = set()

    def generate_token(self, payload, expires_in):
        return f"mock_token_{payload['username']}"

    def check_token(self, token):
        if token in self.blacklist:
            return None
        if token.startswith("mock_token_"):
            return {"username": token.split("_")[2]}
        return None

    def blacklist_token(self, token):
        self.blacklist.add(token)

# Fixture to reset database state before each test
@pytest.fixture
def reset_db():
    """Reset MySQL and MongoDB to a clean state."""
    # Reset MySQL
    conn = mysql.connector.connect(
        host="localhost",
        port=os.getenv("MYSQL_PORT", "3306"),
        user=os.getenv("MYSQL_USER"),
        password=os.getenv("MYSQL_PASSWORD"),
        database=os.getenv("MYSQL_DATABASE")
    )
    cursor = conn.cursor()
    cursor.execute("DELETE FROM users WHERE username != 'test'")
    conn.commit()
    cursor.close()
    conn.close()

    # Reset MongoDB
    client = MongoClient(
        host="localhost",
        port=int(os.getenv("MONGO_PORT", "27017")),
        username=os.getenv("MONGO_USER"),
        password=os.getenv("MONGO_PASSWORD"),
        authSource=os.getenv("MONGO_DATABASE")
    )
    db = client[os.getenv("MONGO_DATABASE")]
    db["history"].delete_many({"user_id": {"$ne": 1}})  # Keep test user's history
    client.close()
