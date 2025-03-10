import pytest
from flask import Flask
from routes.auth import auth_bp
from utils.authtool import JWTManager
from werkzeug.security import generate_password_hash

@pytest.fixture
def app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'test_secret_key'
    app.config['JWT'] = JWTManager(app.config['SECRET_KEY'])
    app.register_blueprint(auth_bp, url_prefix='/auth')
    return app

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def mock_connect_mysql(mocker):
    mock_cursor = mocker.MagicMock()
    mock_connection = mocker.MagicMock()
    mock_connection.is_connected.return_value = True
    # Mock the context manager directly
    mock_context = mocker.MagicMock()
    mock_context.__enter__.return_value = (mock_cursor, mock_connection)
    mock_context.__exit__.return_value = None
    # Patch the connect_mysql function in auth.py
    mocker.patch('routes.auth.connect_mysql', return_value=mock_context)
    return mock_cursor, mock_connection

@pytest.fixture
def mock_connect_mongo(mocker):
    mock_client = mocker.MagicMock()
    mock_context = mocker.MagicMock()
    mock_context.__enter__.return_value = mock_client
    mock_context.__exit__.return_value = None
    mocker.patch('routes.auth.connect_mongo', return_value=mock_context)
    return mock_client

def test_login_success(client, mock_connect_mysql, mocker):
    mock_cursor, mock_connection = mock_connect_mysql
    hashed_password = generate_password_hash('password123')
    mock_cursor.fetchone.return_value = [hashed_password]

    response = client.post(
        '/auth/login',
        json={'username': 'testuser', 'password': 'password123'}
    )

    assert response.status_code == 200
    assert 'token' in response.json

def test_login_invalid_password(client, mock_connect_mysql):
    mock_cursor, mock_connection = mock_connect_mysql
    hashed_password = generate_password_hash('password123')
    mock_cursor.fetchone.return_value = [hashed_password]

    response = client.post(
        '/auth/login',
        json={'username': 'testuser', 'password': 'wrongpassword'}
    )

    assert response.status_code == 400
    assert response.json['message'] == 'Invalid password'

def test_login_user_not_found(client, mock_connect_mysql):
    mock_cursor, mock_connection = mock_connect_mysql
    mock_cursor.fetchone.return_value = None

    response = client.post(
        '/auth/login',
        json={'username': 'testuser', 'password': 'password123'}
    )

    assert response.status_code == 404
    assert response.json['message'] == 'User not found'

def test_login_already_logged_in(client, app, mocker):
    jwt_manager = app.config['JWT']
    token = jwt_manager.generate_token({'username': 'testuser'}, 3600)
    mocker.patch.object(jwt_manager, 'check_token', return_value={'username': 'testuser'})

    response = client.post(
        '/auth/login',
        json={'username': 'testuser', 'password': 'password123'},
        headers={'Authorization': f'Bearer {token}'}
    )

    assert response.status_code == 200
    assert response.json['message'] == 'User already logged in'

# Test for successful registration (updated for MongoDB)
def test_register_success(client, mock_connect_mysql, mock_connect_mongo, mocker):
    mock_cursor, mock_connection = mock_connect_mysql
    mock_mongo_client = mock_connect_mongo

    # Mock MySQL behavior
    # First fetch: Check if user exists (returns None)
    # Second fetch: Get user_id after insertion (returns a user_id)
    mock_cursor.fetchone.side_effect = [None, (1,)]  # None for user check, 1 for user_id
    mock_mongo_collection = mock_mongo_client["history_db"]["history"]
    mock_mongo_collection.insert_one.return_value = None  # Mongo insert doesn't need a return value

    response = client.post(
        '/auth/register',
        json={'username': 'newuser', 'password': 'password123', 'email': 'newuser@example.com'}
    )

    assert response.status_code == 201
    assert response.json['message'] == 'User created successfully'

    # Verify MySQL calls
    assert mock_cursor.execute.call_count == 3  # 3 calls: check user, insert user, fetch user_id
    mock_cursor.execute.assert_any_call(
        "SELECT username, email FROM users WHERE username = %s", ('newuser',)
    )
    mock_cursor.execute.assert_any_call(
        "SELECT user_id FROM users WHERE username = %s", ('newuser',)
    )
    calls = mock_cursor.execute.call_args_list
    insert_call = calls[1]  # Second call is the INSERT
    assert insert_call[0][0] == "INSERT INTO users (username, password, email) VALUES (%s, %s, %s)"
    assert insert_call[0][1][0] == 'newuser'
    assert insert_call[0][1][2] == 'newuser@example.com'
    mock_connection.commit.assert_called_once()

    # Verify MongoDB call
    mock_mongo_collection.insert_one.assert_called_once()
    mongo_call_args = mock_mongo_collection.insert_one.call_args[0][0]
    assert mongo_call_args['user_id'] == 1
    assert mongo_call_args['history'] == []
    assert mongo_call_args['likes'] == []
    assert 'account_created' in mongo_call_args

def test_register_user_exists(client, mock_connect_mysql):
    mock_cursor, mock_connection = mock_connect_mysql
    mock_cursor.fetchone.return_value = ('newuser', 'newuser@example.com')

    response = client.post(
        '/auth/register',
        json={'username': 'newuser', 'password': 'password123', 'email': 'newuser@example.com'}
    )

    assert response.status_code == 400
    assert response.json['message'] == 'User already exists'

def test_logout_success(client, app, mocker):
    jwt_manager = app.config['JWT']
    token = jwt_manager.generate_token({'username': 'testuser'}, 3600)
    mocker.patch.object(jwt_manager, 'check_token', return_value={'username': 'testuser'})
    mocker.patch.object(jwt_manager, 'blacklist_token')

    response = client.post(
        '/auth/logout',
        headers={'Authorization': f'Bearer {token}'}
    )

    assert response.status_code == 200
    assert response.json['message'] == 'User logged out successfully'
    jwt_manager.blacklist_token.assert_called_once_with(token)

def test_logout_missing_token(client):
    response = client.post('/auth/logout')

    assert response.status_code == 401
    assert response.json['message'] == 'Token is missing'

def test_renew_token_success(client, app, mocker):
    jwt_manager = app.config['JWT']
    token = jwt_manager.generate_token({'username': 'testuser'}, 3600)
    mocker.patch.object(jwt_manager, 'check_token', return_value={'username': 'testuser'})
    mocker.patch.object(jwt_manager, 'blacklist_token')

    response = client.post(
        '/auth/renew_token',
        headers={'Authorization': f'Bearer {token}'}
    )

    assert response.status_code == 200
    assert 'token' in response.json
    jwt_manager.blacklist_token.assert_called_once_with(token)

def test_renew_token_invalid(client, app, mocker):
    jwt_manager = app.config['JWT']
    mocker.patch.object(jwt_manager, 'check_token', return_value=None)

    response = client.post(
        '/auth/renew_token',
        headers={'Authorization': 'Bearer invalidtoken'}
    )

    assert response.status_code == 401
    assert response.json['message'] == 'Token is invalid'