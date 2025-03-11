
from pytest import fixture
from flask import current_app
from app import app


def test_login_success(client):
    response = client.post('/auth/login', json={  #
        "username": "test",
        "password": "test"
    })

    # It should return 200 with token
    assert response.status_code == 200
    token = response.json.get("token")
    assert token is not None
    payload = current_app.config['JWT'].check_token(token)
    assert payload[0].get("username") == "test"  

def test_register_success(client):
    response = client.post('/auth/register', json={ 
        "username": "test1",
        "password": "test1",
        "email": "test1@test.com"
    })

    # It should return 200
    print(response.json)
    assert response.status_code == 200

