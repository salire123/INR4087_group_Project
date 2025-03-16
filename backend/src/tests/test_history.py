import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime
from bson.objectid import ObjectId

# Mock data
MOCK_POST_ID = "507f1f77bcf86cd799439011"
MOCK_USER_ID = 42
MOCK_USERNAME = "testuser"


def test_get_history_user_not_found(client):
    """Test getting history for non-existent user"""
    with patch('routes.history.connect_mysql') as mock_mysql:
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = None
        mock_mysql.return_value.__enter__.return_value = (mock_cursor, MagicMock())
        
        response = client.get(f'/api/history/{MOCK_USERNAME}')
        
        assert response.status_code == 404
        assert response.json['message'] == "User not found"


def test_get_history_success(client):
    """Test successful history retrieval"""
    mock_history = [
        {
            "_id": ObjectId(MOCK_POST_ID),
            "user_id": MOCK_USER_ID,
            "post_id": "507f1f77bcf86cd799439012",
            "timestamp": datetime.now()
        },
        {
            "_id": ObjectId("507f1f77bcf86cd799439013"),
            "user_id": MOCK_USER_ID,
            "post_id": "507f1f77bcf86cd799439014",
            "timestamp": datetime.now()
        }
    ]
    
    with patch('routes.history.connect_mysql') as mock_mysql, \
         patch('routes.history.connect_mongo') as mock_mongo:
        
        # Mock MySQL to return user ID
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = [MOCK_USER_ID]
        mock_mysql.return_value.__enter__.return_value = (mock_cursor, MagicMock())
        
        # Mock MongoDB to return history items
        mock_collection = MagicMock()
        mock_collection.find.return_value = mock_history
        mock_db = MagicMock()
        mock_db.__getitem__.return_value = mock_collection
        mock_mongo.return_value.__enter__.return_value = mock_db
        
        response = client.get(f'/api/history/{MOCK_USERNAME}')
        
        assert response.status_code == 200
        assert len(response.json['history']) == 2
        # Check that ObjectId was converted to string
        assert isinstance(response.json['history'][0]['_id'], str)


def test_add_read_history_missing_token(client):
    """Test adding read history without auth token"""
    response = client.post('/api/add_read_history', json={
        "post_id": MOCK_POST_ID,
        "username": MOCK_USERNAME
    })
    assert response.status_code == 400
    assert response.json['message'] == "Token is required"


def test_add_read_history_invalid_token(client, mock_jwt, auth_headers):
    """Test adding read history with invalid auth token"""
    mock_jwt.check_token.return_value = None
    response = client.post(
        '/api/add_read_history',
        headers=auth_headers('invalid_token'),
        json={
            "post_id": MOCK_POST_ID,
            "username": MOCK_USERNAME
        }
    )
    assert response.status_code == 401
    assert response.json['message'] == "Invalid token"


def test_add_read_history_missing_post_id(client, mock_jwt, auth_headers):
    """Test adding read history without post ID"""
    mock_jwt.check_token.return_value = {"username": MOCK_USERNAME}
    response = client.post(
        '/api/add_read_history',
        headers=auth_headers(),
        json={
            "username": MOCK_USERNAME
        }
    )
    assert response.status_code == 400
    assert response.json['message'] == "Post ID is required"


def test_add_read_history_missing_username(client, mock_jwt, auth_headers):
    """Test adding read history without username"""
    mock_jwt.check_token.return_value = {"username": MOCK_USERNAME}
    response = client.post(
        '/api/add_read_history',
        headers=auth_headers(),
        json={
            "post_id": MOCK_POST_ID
        }
    )
    assert response.status_code == 400
    assert response.json['message'] == "Username is required"


def test_add_read_history_user_not_found(client, mock_jwt, auth_headers):
    """Test adding read history for non-existent user"""
    mock_jwt.check_token.return_value = {"username": MOCK_USERNAME}
    
    with patch('routes.history.connect_mysql') as mock_mysql:
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = None
        mock_mysql.return_value.__enter__.return_value = (mock_cursor, MagicMock())
        
        response = client.post(
            '/api/add_read_history',
            headers=auth_headers(),
            json={
                "post_id": MOCK_POST_ID,
                "username": MOCK_USERNAME
            }
        )
        
        assert response.status_code == 404
        assert response.json['message'] == "User not found"


def test_add_read_history_success(client, mock_jwt, auth_headers):
    """Test successful read history addition"""
    mock_jwt.check_token.return_value = {"username": MOCK_USERNAME}
    
    with patch('routes.history.connect_mysql') as mock_mysql, \
         patch('routes.history.connect_mongo') as mock_mongo:
        
        # Mock MySQL to return user ID
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = [MOCK_USER_ID]
        mock_mysql.return_value.__enter__.return_value = (mock_cursor, MagicMock())
        
        # Mock MongoDB for successful insertion
        mock_collection = MagicMock()
        mock_db = MagicMock()
        mock_db.__getitem__.return_value = mock_collection
        mock_mongo.return_value.__enter__.return_value = mock_db
        
        response = client.post(
            '/api/add_read_history',
            headers=auth_headers(),
            json={
                "post_id": MOCK_POST_ID,
                "username": MOCK_USERNAME
            }
        )
        
        assert response.status_code == 200
        assert response.json['message'] == "History added"
        mock_collection.insert_one.assert_called_once()


def test_add_like_missing_token(client):
    """Test adding like without auth token"""
    response = client.post('/api/add_like', json={
        "post_id": MOCK_POST_ID,
        "username": MOCK_USERNAME
    })
    assert response.status_code == 400
    assert response.json['message'] == "Token is required"


def test_add_like_invalid_token(client, mock_jwt, auth_headers):
    """Test adding like with invalid auth token"""
    mock_jwt.check_token.return_value = None
    response = client.post(
        '/api/add_like',
        headers=auth_headers('invalid_token'),
        json={
            "post_id": MOCK_POST_ID,
            "username": MOCK_USERNAME
        }
    )
    assert response.status_code == 401
    assert response.json['message'] == "Invalid token"


def test_add_like_user_not_found(client, mock_jwt, auth_headers):
    """Test adding like for non-existent user"""
    mock_jwt.check_token.return_value = {"username": MOCK_USERNAME}
    
    with patch('routes.history.connect_mysql') as mock_mysql:
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = None
        mock_mysql.return_value.__enter__.return_value = (mock_cursor, MagicMock())
        
        response = client.post(
            '/api/add_like',
            headers=auth_headers(),
            json={
                "post_id": MOCK_POST_ID,
                "username": MOCK_USERNAME
            }
        )
        
        assert response.status_code == 404
        assert response.json['message'] == "User not found"


def test_add_like_success(client, mock_jwt, auth_headers):
    """Test successful like addition"""
    mock_jwt.check_token.return_value = {"username": MOCK_USERNAME}
    
    with patch('routes.history.connect_mysql') as mock_mysql, \
         patch('routes.history.connect_mongo') as mock_mongo:
        
        # Mock MySQL to return user ID
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = [MOCK_USER_ID]
        mock_mysql.return_value.__enter__.return_value = (mock_cursor, MagicMock())
        
        # Mock MongoDB for successful update
        mock_collection = MagicMock()
        mock_db = MagicMock()
        mock_db.__getitem__.return_value = mock_collection
        mock_mongo.return_value.__enter__.return_value = mock_db
        
        response = client.post(
            '/api/add_like',
            headers=auth_headers(),
            json={
                "post_id": MOCK_POST_ID,
                "username": MOCK_USERNAME
            }
        )
        
        assert response.status_code == 200
        assert response.json['message'] == "Like added"
        mock_collection.update_one.assert_called_once()


def test_remove_like_success(client, mock_jwt, auth_headers):
    """Test successful like removal"""
    mock_jwt.check_token.return_value = {"username": MOCK_USERNAME}
    
    with patch('routes.history.connect_mysql') as mock_mysql, \
         patch('routes.history.connect_mongo') as mock_mongo:
        
        # Mock MySQL to return user ID
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = [MOCK_USER_ID]
        mock_mysql.return_value.__enter__.return_value = (mock_cursor, MagicMock())
        
        # Mock MongoDB for successful update
        mock_collection = MagicMock()
        mock_db = MagicMock()
        mock_db.__getitem__.return_value = mock_collection
        mock_mongo.return_value.__enter__.return_value = mock_db
        
        response = client.post(
            '/api/remove_like',
            headers=auth_headers(),
            json={
                "post_id": MOCK_POST_ID,
                "username": MOCK_USERNAME
            }
        )
        
        assert response.status_code == 200
        assert response.json['message'] == "Like removed"
        # Check that the MongoDB update was called with the right arguments
        mock_collection.update_one.assert_called_with(
            {"user_id": MOCK_USER_ID, "post_id": MOCK_POST_ID}, 
            {"$pull": {"likes": MOCK_USER_ID}}
        )


# First, let's add a sanity check to verify the route exists
def test_route_exists(client):
    """Test if history route is properly registered"""
    # Try the add_like route which we know should exist
    response = client.post('/api/add_like', 
                          json={"post_id": MOCK_POST_ID, "username": MOCK_USERNAME})
    # It should fail with 400 (missing token) rather than 404 (route not found)
    assert response.status_code == 400, "The /api/add_like route should return 400 for missing token, not 404"


# Test just one endpoint for likes
def test_add_like_simple(client, mock_jwt, auth_headers):
    """Simple test to check if add_like route works"""
    mock_jwt.check_token.return_value = {"username": MOCK_USERNAME}
    
    # Mock both database connections
    with patch('routes.history.connect_mysql') as mock_mysql, \
         patch('routes.history.connect_mongo') as mock_mongo:
        
        # Set up MySQL mock
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = [MOCK_USER_ID]
        mock_mysql.return_value.__enter__.return_value = (mock_cursor, MagicMock())
        
        # Set up MongoDB mock
        mock_collection = MagicMock()
        mock_db = MagicMock()
        mock_db.__getitem__.return_value = mock_collection
        mock_mongo.return_value.__enter__.return_value = mock_db
        
        # Try the request
        response = client.post(
            '/api/add_like',
            headers=auth_headers(),
            json={
                "post_id": MOCK_POST_ID,
                "username": MOCK_USERNAME
            }
        )
        
        # Print response for debugging
        print(f"Response: {response.status_code} - {response.data}")
        
        # Check if the route works
        assert response.status_code != 404


def test_route_with_different_prefix(client):
    """Test if history routes have a different URL prefix"""
    # Try different prefixes
    prefixes = [
        '/api/history',   # History might be under /api/history/
        '/history',       # Or directly under /history/
        '/',              # Or at the root
    ]
    
    for prefix in prefixes:
        response = client.post(f'{prefix}/add_like', 
                              json={"post_id": MOCK_POST_ID, "username": MOCK_USERNAME})
        if response.status_code != 404:
            print(f"Found history route at prefix: {prefix}")
            return
    
    assert False, "Could not find history routes at any expected prefix"