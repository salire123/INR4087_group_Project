import pytest
from flask import Flask
from routes.post import post_bp  # Adjust import based on your structure
from bson.objectid import ObjectId
from datetime import datetime, timezone

# Create a Flask app for testing
@pytest.fixture
def app():
    app = Flask(__name__)
    app.register_blueprint(post_bp)
    
    # Mock JWT configuration
    class MockJWT:
        def check_token(self, token):
            if token == "valid_token":
                return {"username": "testuser"}
            return None
    
    app.config['JWT'] = MockJWT()
    return app

@pytest.fixture
def client(app):
    return app.test_client()

# Mock MySQL connection with context manager
@pytest.fixture
def mock_connect_mysql(mocker):
    mock_cursor = mocker.MagicMock()
    mock_connection = mocker.MagicMock()
    mock_connection.is_connected.return_value = True
    mock_cursor.fetchone.return_value = (1,)  # Mock user_id
    mock_context = mocker.MagicMock()
    mock_context.__enter__.return_value = (mock_cursor, mock_connection)
    mock_context.__exit__.return_value = None
    mocker.patch('routes.post.connect_mysql', return_value=mock_context)
    return mock_cursor, mock_connection

# Mock MongoDB connection with context manager
@pytest.fixture
def mock_connect_mongo(mocker):
    mock_client = mocker.MagicMock()
    mock_db = mock_client["posts_db"]
    mock_collection = mock_db["posts"]
    mock_context = mocker.MagicMock()
    mock_context.__enter__.return_value = mock_client
    mock_context.__exit__.return_value = None
    mocker.patch('routes.post.connect_mongo', return_value=mock_context)
    return mock_collection

# Test create_post endpoint
def test_create_post_success(client, mock_connect_mysql, mock_connect_mongo):
    mock_cursor, _ = mock_connect_mysql
    mock_collection = mock_connect_mongo
    mock_collection.insert_one.return_value.inserted_id = ObjectId()

    response = client.post(
        "/create_post",
        json={"title": "Test Post", "content": "This is a test", "media_url": "http://example.com"},
        headers={"Authorization": "valid_token"}
    )
    
    assert response.status_code == 200
    assert response.json["message"] == "Post created"
    assert "post_id" in response.json

def test_create_post_missing_token(client):
    response = client.post(
        "/create_post",
        json={"title": "Test Post", "content": "This is a test"}
    )
    
    assert response.status_code == 400
    assert response.json["message"] == "Token is required"

def test_create_post_invalid_token(client, mock_connect_mysql):
    response = client.post(
        "/create_post",
        json={"title": "Test Post", "content": "This is a test"},
        headers={"Authorization": "invalid_token"}
    )
    
    assert response.status_code == 401
    assert response.json["message"] == "Invalid token"

# Test get_posts endpoint
def test_get_posts_success(client, mock_connect_mongo):
    mock_collection = mock_connect_mongo
    posts = [{"_id": ObjectId(), "title": "Post 1", "content": "Content 1", "created_at": datetime.now(timezone.utc)}]
    mock_collection.find.return_value.skip.return_value.limit.return_value = posts
    
    response = client.get("/get_posts?page=1&per_page=10")
    
    assert response.status_code == 200
    assert "posts" in response.json
    assert len(response.json["posts"]) == 1

def test_get_posts_invalid_page(client):
    response = client.get("/get_posts?page=0&per_page=10")
    
    assert response.status_code == 400
    assert response.json["message"] == "Page and per_page must be positive integers"

# Test get_post endpoint
def test_get_post_success(client, mock_connect_mongo):
    mock_collection = mock_connect_mongo
    post_id = str(ObjectId())
    mock_collection.find_one.return_value = {"_id": ObjectId(post_id), "title": "Test Post"}
    
    response = client.get(f"/get_post?post_id={post_id}")
    
    assert response.status_code == 200
    assert response.json["post"]["_id"] == post_id

def test_get_post_missing_id(client):
    response = client.get("/get_post")
    
    assert response.status_code == 400
    assert response.json["message"] == "Post ID is required"

# Test delete_post endpoint
def test_delete_post_success(client, mock_connect_mysql, mock_connect_mongo):
    mock_cursor, _ = mock_connect_mysql
    mock_collection = mock_connect_mongo
    post_id = str(ObjectId())
    mock_collection.find_one.return_value = {"_id": ObjectId(post_id), "user_id": 1}
    mock_collection.delete_one.return_value.deleted_count = 1
    
    response = client.delete(
        f"/delete_post?post_id={post_id}",
        headers={"Authorization": "valid_token"}
    )
    
    assert response.status_code == 200
    assert response.json["message"] == "Post deleted"

def test_delete_post_unauthorized(client, mock_connect_mysql, mock_connect_mongo):
    mock_cursor, _ = mock_connect_mysql
    mock_collection = mock_connect_mongo
    post_id = str(ObjectId())
    mock_collection.find_one.return_value = {"_id": ObjectId(post_id), "user_id": 2}  # Different user_id
    
    response = client.delete(
        f"/delete_post?post_id={post_id}",
        headers={"Authorization": "valid_token"}
    )
    
    assert response.status_code == 403
    assert response.json["message"] == "Unauthorized"

# Test update_post endpoint
def test_update_post_success(client, mock_connect_mysql, mock_connect_mongo):
    mock_cursor, _ = mock_connect_mysql
    mock_collection = mock_connect_mongo
    post_id = str(ObjectId())
    mock_collection.find_one.return_value = {"_id": ObjectId(post_id), "user_id": 1}
    mock_collection.update_one.return_value.matched_count = 1
    
    response = client.put(
        f"/update_post?post_id={post_id}",
        json={"title": "Updated Title"},
        headers={"Authorization": "valid_token"}
    )
    
    assert response.status_code == 200
    assert response.json["message"] == "Post updated"

# Test create_comment endpoint
def test_create_comment_success(client, mock_connect_mysql, mock_connect_mongo):
    mock_cursor, _ = mock_connect_mysql
    mock_collection = mock_connect_mongo
    post_id = str(ObjectId())
    mock_collection.update_one.return_value.matched_count = 1
    
    response = client.post(
        "/create_comment",
        json={"post_id": post_id, "comment": "Nice post!"},
        headers={"Authorization": "valid_token"}
    )
    
    assert response.status_code == 200
    assert response.json["message"] == "Comment created"