from flask import Blueprint, request, jsonify, current_app
from utils.db import create_mysql_connection, create_mongo_connection
from datetime import datetime
from bson.objectid import ObjectId
from contextlib import contextmanager

history_bp = Blueprint('history', __name__)

@contextmanager
def connect_mysql():
    connection = None
    cursor = None
    try:
        connection = create_mysql_connection()
        if connection and connection.is_connected():
            cursor = connection.cursor()
            yield cursor, connection
        else:
            raise Exception("Failed to connect to MySQL")
    except Exception as e:
        if connection:
            connection.rollback()
        raise e
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

@contextmanager
def connect_mongo():
    mongo_client = None
    try:
        mongo_client = create_mongo_connection()
        if mongo_client:
            yield mongo_client
        else:
            raise Exception("Failed to connect to MongoDB")
    except Exception as e:
        raise e
    finally:
        if mongo_client:
            mongo_client.close()



@history_bp.route('/history/<string:username>', methods=['GET'])
def get_history(username):
    pass