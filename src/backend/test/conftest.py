from pytest import fixture
from utils.db import create_mysql_connection, create_mongo_connection
from app import app

@fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

@fixture
def connect_mysql():
    connection = create_mysql_connection()
    yield connection
    connection.close()

@fixture
def connect_mongo():
    connection = create_mongo_connection()
    yield connection
    connection.close()

