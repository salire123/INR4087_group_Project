import pytest
import subprocess
import time
import os
import sys
from flask import Flask
from pathlib import Path

# Add backend/src to sys.path explicitly
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from routes.auth import auth_bp  
import mysql.connector
from pymongo import MongoClient

from dotenv import load_dotenv
load_dotenv()

DOCKER_COMPOSE_PATH = Path(__file__).parent.parent.parent.parent / "docker" / "docker-compose.yml"

@pytest.fixture(scope="session", autouse=True)
def docker_compose():
    max_attempts = 30
    attempt = 0
    mysql_ready = False
    mongo_ready = False

    while attempt < max_attempts and not (mysql_ready and mongo_ready):
        attempt += 1
        time.sleep(2)
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

        try:
            client = MongoClient(
                host="localhost",
                port=int(os.getenv("MONGO_PORT", "27017")),
                username=os.getenv("MONGO_USER"),
                password=os.getenv("MONGO_PASSWORD"),
                authSource=os.getenv("MONGO_DATABASE")
            )
            client.server_info()
            client.close()
            mongo_ready = True
        except Exception:
            mongo_ready = False

    if not (mysql_ready and mongo_ready):
        raise Exception("Failed to start databases in time")

    yield

    subprocess.run(
        ["docker-compose", "-f", str(DOCKER_COMPOSE_PATH), "down", "-v"],
        check=True
    )

@pytest.fixture
def app():
    app = Flask(__name__)
    app.config['JWT'] = MockJWT()
    app.register_blueprint(auth_bp)
    return app

@pytest.fixture
def client(app):
    return app.test_client()

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

@pytest.fixture
def reset_db():
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

    client = MongoClient(
        host="localhost",
        port=int(os.getenv("MONGO_PORT", "27017")),
        username=os.getenv("MONGO_USER"),
        password=os.getenv("MONGO_PASSWORD"),
        authSource=os.getenv("MONGO_DATABASE")
    )
    db = client[os.getenv("MONGO_DATABASE")]
    db["history"].delete_many({"user_id": {"$ne": 1}})
    client.close()