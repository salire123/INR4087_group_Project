import pytest
import json
from werkzeug.security import generate_password_hash

def test_login_success(client, reset_db):
    """Test successful login with valid credentials."""
    response = client.post(
        "/auth/login",
        data=json.dumps({"username": "test", "password": "test"}),
        content_type="application/json"
    )
    assert response.status_code == 200
    assert "token" in response.json
    assert response.json["token"] == "mock_token_test"

def test_login_invalid_password(client, reset_db):
    """Test login with incorrect password."""
    response = client.post(
        "/auth/login",
        data=json.dumps({"username": "test", "password": "wrong"}),
        content_type="application/json"
    )
    assert response.status_code == 400
    assert response.json["message"] == "Invalid password"

def test_login_user_not_found(client, reset_db):
    """Test login with non-existent user."""
    response = client.post(
        "/auth/login",
        data=json.dumps({"username": "nonexistent", "password": "test"}),
        content_type="application/json"
    )
    assert response.status_code == 404
    assert response.json["message"] == "User not found"

def test_register_success(client, reset_db):
    """Test successful user registration."""
    response = client.post(
        "/auth/register",
        data=json.dumps({
            "username": "newuser",
            "email": "newuser@test.com",
            "password": "newpass"
        }),
        content_type="application/json"
    )
    assert response.status_code == 201
    assert response.json["message"] == "User created successfully"
    assert "user_id" in response.json

def test_register_user_exists(client, reset_db):
    """Test registration with an existing username."""
    response = client.post(
        "/auth/register",
        data=json.dumps({
            "username": "test",
            "email": "test2@test.com",
            "password": "test"
        }),
        content_type="application/json"
    )
    assert response.status_code == 400
    assert response.json["message"] == "User already exists"

def test_logout_success(client, reset_db):
    """Test successful logout with valid token."""
    response = client.post(
        "/auth/logout",
        headers={"Authorization": "Bearer mock_token_test"}
    )
    assert response.status_code == 200
    assert response.json["message"] == "User logged out successfully"

def test_logout_missing_token(client, reset_db):
    """Test logout without token."""
    response = client.post("/auth/logout")
    assert response.status_code == 401
    assert response.json["message"] == "Token is missing"

def test_renew_token_success(client, reset_db):
    """Test successful token renewal."""
    response = client.post(
        "/auth/renew_token",
        headers={"Authorization": "Bearer mock_token_test"}
    )
    assert response.status_code == 200
    assert "token" in response.json
    assert response.json["token"] == "mock_token_test"

def test_renew_token_invalid(client, reset_db):
    """Test token renewal with invalid token."""
    response = client.post(
        "/auth/renew_token",
        headers={"Authorization": "Bearer invalid_token"}
    )
    assert response.status_code == 401
    assert response.json["message"] == "Token is invalid"