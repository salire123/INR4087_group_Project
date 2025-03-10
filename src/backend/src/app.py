import pytest
from flask import Flask
from src.routes.auth import auth_bp
from src.utils.authtool import JWTManager
from werkzeug.security import generate_password_hash

# Fixture to set up the Flask app with the auth blueprint
@pytest.fixture
def app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'test_secret_key'
    app.config['JWT'] = JWTManager(app.config['SECRET_KEY'])
    app.register_blueprint(auth_bp, url_prefix='/auth')
    return app

# Fixture to provide a test client
@pytest.fixture
def client(app):
    return app.test_client()

# Mock the database connection context manager
@pytest.fixture
def mock_connect_mysql(mocker):
    mock_cursor = mocker.MagicMock()
    mock_connection = mocker.MagicMock()
    mock_connection.is_connected.return_value = True
    mock_context = mocker.MagicMock()
    mock_context.__enter__.return_value = (mock_cursor, mock_connection)
    mock_context.__exit__.return_value = None
    mocker.patch('routes.auth.connect_mysql', return_value=mock_context)
    return mock_cursor, mock_connection

# Test successful login
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

# Test login with invalid password
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

# Test login with non-existent user
def test_login_user_not_found(client, mock_connect_mysql):
    mock_cursor, mock_connection = mock_connect_mysql
    mock_cursor.fetchone.return_value = None

    response = client.post(
        '/auth/login',
        json={'username': 'testuser', 'password': 'password123'}
    )

    assert response.status_code == 404
    assert response.json['message'] == 'User not found'

# Test login with already logged-in user
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

# Test successful registration
def test_register_success(client, mock_connect_mysql):
    mock_cursor, mock_connection = mock_connect_mysql
    mock_cursor.fetchone.return_value = None  # User does not exist

    response = client.post(
        '/auth/register',
        json={'username': 'newuser', 'password': 'password123', 'email': 'newuser@example.com'}
    )

    assert response.status_code == 201
    assert response.json['message'] == 'User created successfully'
    mock_cursor.execute.assert_called_once()
    mock_connection.commit.assert_called_once()

# Test registration with existing user
def test_register_user_exists(client, mock_connect_mysql):
    mock_cursor, mock_connection = mock_connect_mysql
    mock_cursor.fetchone.return_value = ('newuser', 'newuser@example.com')

    response = client.post(
        '/auth/register',
        json={'username': 'newuser', 'password': 'password123', 'email': 'newuser@example.com'}
    )

    assert response.status_code == 400
    assert response.json['message'] == 'User already exists'

# Test successful logout
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

# Test logout with missing token
def test_logout_missing_token(client):
    response = client.post('/auth/logout')

    assert response.status_code == 401
    assert response.json['message'] == 'Token is missing'

# Test successful token renewal
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

# Test token renewal with invalid token
def test_renew_token_invalid(client, app, mocker):
    jwt_manager = app.config['JWT']
    mocker.patch.object(jwt_manager, 'check_token', return_value=None)

    response = client.post(
        '/auth/renew_token',
        headers={'Authorization': 'Bearer invalidtoken'}
    )

    assert response.status_code == 401
    assert response.json['message'] == 'Token is invalid'