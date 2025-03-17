import pytest
import json
from unittest.mock import patch, MagicMock
from datetime import datetime
from bson.objectid import ObjectId
from app import app
from utils.db import connect_mysql, connect_mongo


@pytest.fixture
def client():
    """Create a test client for the app."""
    with app.test_client() as client:
        yield client


@pytest.fixture
def mock_jwt_check():
    """Mock JWT token verification"""
    # Create a mock JWT manager object
    mock_jwt = MagicMock()
    mock_jwt.check_token.return_value = {"username": "testuser"}
    
    # Save the original JWT manager
    original_jwt = app.config.get("JWT")
    
    # Replace with our mock
    app.config["JWT"] = mock_jwt
    
    yield mock_jwt
    
    # Restore original after test
    app.config["JWT"] = original_jwt


@pytest.fixture
def mock_db_connections():
    """Mock database connections"""
    mysql_cursor = MagicMock()
    mysql_connection = MagicMock()
    mongo_db = MagicMock()
    
    # Configure MySQL mock to return user_id=1 for testuser
    mysql_cursor.fetchone.return_value = (1,)
    
    with patch('routes.history.connect_mysql') as mock_mysql:
        mock_mysql.return_value.__enter__.return_value = (mysql_cursor, mysql_connection)
        with patch('routes.history.connect_mongo') as mock_mongo:
            mock_mongo.return_value.__enter__.return_value = mongo_db
            yield mysql_cursor, mysql_connection, mongo_db


class TestHistoryRoutes:
    
    def test_get_history_like_success(self, client, mock_db_connections):
        """Test successful retrieval of history and likes."""
        _, _, mongo_db = mock_db_connections
        
        # Mock MongoDB find_one response
        history_data = {
            "_id": ObjectId("6075b792d51c5b5e6c3a1234"),
            "user_id": 1,
            "history": [
                {"post_id": ObjectId("6075b7a2d51c5b5e6c3a5678"), "timestamp": datetime.now()}
            ],
            "likes": [
                {"post_id": ObjectId("6075b7b2d51c5b5e6c3a9abc"), "timestamp": datetime.now()}
            ]
        }
        mongo_db["history_like"].find_one.return_value = history_data
        
        response = client.get('/history/get_history_like?username=testuser')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert isinstance(data["_id"], str)  # ObjectId converted to string
        assert isinstance(data["history"][0]["post_id"], str)
        assert isinstance(data["likes"][0]["post_id"], str)

    def test_get_history_like_user_not_found(self, client, mock_db_connections):
        """Test history retrieval for non-existent user."""
        mysql_cursor, _, _ = mock_db_connections
        mysql_cursor.fetchone.return_value = None
        
        response = client.get('/history/get_history_like?username=nonexistent')
        
        assert response.status_code == 404
        assert json.loads(response.data)["message"] == "User not found"

    def test_get_history_like_no_history(self, client, mock_db_connections):
        """Test case when user has no history."""
        _, _, mongo_db = mock_db_connections
        mongo_db["history_like"].find_one.return_value = None
        
        response = client.get('/history/get_history_like?username=testuser')
        
        assert response.status_code == 404
        assert json.loads(response.data)["message"] == "No history found"

    def test_add_read_history_new_entry(self, client, mock_jwt_check, mock_db_connections):
        """Test adding a new item to read history."""
        _, _, mongo_db = mock_db_connections
        post_id = "6075b7b2d51c5b5e6c3a9abc"
        
        # Mock: Post not already in history
        mongo_db["history_like"].find_one.return_value = None
        
        response = client.post(
            f'/history/add_read_history?post_id={post_id}',
            headers={"Authorization": "Bearer valid_token"}
        )
        
        assert response.status_code == 200
        assert json.loads(response.data)["message"] == "History added"
        
        # Verify the update_one call with $push
        mongo_db["history_like"].update_one.assert_called_once()
        call_args = mongo_db["history_like"].update_one.call_args[0]
        assert call_args[0] == {"user_id": 1}
        assert "$push" in call_args[1]

    def test_add_read_history_update_existing(self, client, mock_jwt_check, mock_db_connections):
        """Test updating timestamp of existing history item."""
        _, _, mongo_db = mock_db_connections
        post_id = "6075b7b2d51c5b5e6c3a9abc"
        
        # Mock: Post already in history
        mongo_db["history_like"].find_one.return_value = {
            "user_id": 1,
            "history": [{"post_id": post_id, "timestamp": datetime.now()}]
        }
        
        response = client.post(
            f'/history/add_read_history?post_id={post_id}',
            headers={"Authorization": "Bearer valid_token"}
        )
        
        assert response.status_code == 200
        assert json.loads(response.data)["message"] == "History timestamp updated"
        
        # Verify the update_one call with $set
        mongo_db["history_like"].update_one.assert_called_once()
        call_args = mongo_db["history_like"].update_one.call_args[0]
        assert "$set" in call_args[1]

    def test_add_like_new(self, client, mock_jwt_check, mock_db_connections):
        """Test adding a new like."""
        _, _, mongo_db = mock_db_connections
        post_id = "6075b7b2d51c5b5e6c3a9abc"
        
        # Mock: Post not already liked
        mongo_db["history_like"].find_one.return_value = None
        
        response = client.post(
            f'/history/add_like?post_id={post_id}',
            headers={"Authorization": "Bearer valid_token"}
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["message"] == "Post liked successfully"
        assert data["already_liked"] is False

    def test_add_like_already_liked(self, client, mock_jwt_check, mock_db_connections):
        """Test attempting to like an already liked post."""
        _, _, mongo_db = mock_db_connections
        post_id = "6075b7b2d51c5b5e6c3a9abc"
        
        # Mock: Post already liked
        mongo_db["history_like"].find_one.return_value = {
            "user_id": 1,
            "likes": [{"post_id": post_id, "timestamp": datetime.now()}]
        }
        
        response = client.post(
            f'/history/add_like?post_id={post_id}',
            headers={"Authorization": "Bearer valid_token"}
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["message"] == "You've already liked this post"
        assert data["already_liked"] is True

    def test_remove_like_success(self, client, mock_jwt_check, mock_db_connections):
        """Test successfully removing a like."""
        _, _, mongo_db = mock_db_connections
        post_id = "6075b7b2d51c5b5e6c3a9abc"
        
        # Mock: Post is liked
        mongo_db["history_like"].find_one.return_value = {
            "user_id": 1,
            "likes": [{"post_id": post_id, "timestamp": datetime.now()}]
        }
        
        # Mock successful update
        update_result = MagicMock()
        update_result.modified_count = 1
        mongo_db["history_like"].update_one.return_value = update_result
        
        response = client.delete(
            f'/history/remove_like?post_id={post_id}',
            headers={"Authorization": "Bearer valid_token"}
        )
        
        assert response.status_code == 200
        assert json.loads(response.data)["message"] == "Like removed successfully"
        
        # Verify the update_one call with $pull
        mongo_db["history_like"].update_one.assert_called_once()
        call_args = mongo_db["history_like"].update_one.call_args[0]
        assert "$pull" in call_args[1]

    def test_remove_like_not_found(self, client, mock_jwt_check, mock_db_connections):
        """Test removing a like that doesn't exist."""
        _, _, mongo_db = mock_db_connections
        post_id = "6075b7b2d51c5b5e6c3a9abc"
        
        # Mock: Post not liked
        mongo_db["history_like"].find_one.return_value = None
        
        response = client.delete(
            f'/history/remove_like?post_id={post_id}',
            headers={"Authorization": "Bearer valid_token"}
        )
        
        assert response.status_code == 404
        assert json.loads(response.data)["message"] == "You haven't liked this post"

    def test_missing_token(self, client):
        """Test endpoints with missing authentication token."""
        post_id = "6075b7b2d51c5b5e6c3a9abc"
        
        # Test each endpoint that requires authentication
        endpoints = [
            (f'/history/add_read_history?post_id={post_id}', 'POST'),
            (f'/history/add_like?post_id={post_id}', 'POST'),
            (f'/history/remove_like?post_id={post_id}', 'DELETE')
        ]
        
        for endpoint, method in endpoints:
            if method == 'POST':
                response = client.post(endpoint)
            else:
                response = client.delete(endpoint)
                
            assert response.status_code == 400
            assert json.loads(response.data)["message"] == "Token is required"

    def test_invalid_token(self, client, mock_jwt_check):
        """Test endpoints with invalid token."""
        # Set the mock to return None for invalid tokens
        mock_jwt_check.check_token.return_value = None
        post_id = "6075b7b2d51c5b5e6c3a9abc"
        
        # Test each endpoint that requires authentication
        endpoints = [
            (f'/history/add_read_history?post_id={post_id}', 'POST'),
            (f'/history/add_like?post_id={post_id}', 'POST'),
            (f'/history/remove_like?post_id={post_id}', 'DELETE')
        ]
        
        for endpoint, method in endpoints:
            if method == 'POST':
                response = client.post(endpoint, headers={"Authorization": "Bearer invalid_token"})
            else:
                response = client.delete(endpoint, headers={"Authorization": "Bearer invalid_token"})
                
            assert response.status_code == 401
            assert json.loads(response.data)["message"] == "Invalid token"