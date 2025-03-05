from flask import Blueprint, request, jsonify, current_app
from utils.db import create_mysql_connection
from werkzeug.security import generate_password_hash, check_password_hash

from contextlib import contextmanager



auth_bp = Blueprint('auth', __name__)

@contextmanager
def connect_mysql():
    connection = None
    cursor = None
    try:
        connection = create_mysql_connection()
        if connection.is_connected():
            cursor = connection.cursor()
            yield cursor, connection
    except Exception as e:
        if connection:
            connection.rollback()
        raise e
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

@auth_bp.route("/login", methods=["POST"])
# for login, we need to check if the user exists in the database
def login():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")
    token = request.headers.get("Authorization")

    # check if the user is already logged in
    if token:
        token = token.split(" ")[1]
        payload = current_app.config['JWT'].check_token(token)
        if payload is not None and payload.get("username") == username:
            return jsonify({"message": "User already logged in"}), 200
        if payload is not None:
            return jsonify({"message": "Invalid token"}), 401

    
    try:
        with connect_mysql() as (cursor, connection):
            cursor.execute("SELECT password FROM users WHERE username = %s", (username,))
            result = cursor.fetchone()
            if result is None:
                return jsonify({"message": "User not found"}), 404
            
            user_password = result[0]
            if check_password_hash(user_password, password):
                token = current_app.config['JWT'].generate_token({"username": username}, 3600)
                return jsonify({"token": token}), 200
            else:
                return jsonify({"message": "Invalid password"}), 400
            
    except Exception as e:
        return jsonify({"message": f"An error occurred: {str(e)}"}), 500
        
 

@auth_bp.route("/register", methods=["POST"])
# for registration, we need to insert the user into the database
def register():
    data        = request.get_json()  
    email       = data.get("email")
    username    = data.get("username")
    password    = data.get("password")

    try:
        with connect_mysql() as (cursor, connection):

            # check if the user already exists
            cursor.execute("SELECT username, email FROM users WHERE username = %s", (username, email,))
            if cursor.fetchone():
                return jsonify({"message": "User already exists"}), 400

            # hash the password before storing it in the database
            password = generate_password_hash(password)

            # insert the user into the database
            cursor.execute("INSERT INTO users (username, password, email) VALUES (%s, %s, %s)", (username, password, email))
            
            if connection.is_connected():
                connection.commit()

            return jsonify({"message": "User created successfully"}), 201
    
    except Exception as e:
        return jsonify({"message": f"An error occurred: {str(e)}"}), 500


@auth_bp.route("/logout", methods=["POST"])
# for logout, we need to invalidate the token
def logout():
    try:
        token = request.headers.get("Authorization")
        if not token:
            return jsonify({"message": "Token is missing"}), 401

        token = token.split(" ")[1]
        if not current_app.config['JWT'].check_token(token):
            return jsonify({"message": "Token is invalid"}), 401
        current_app.config['JWT'].blacklist_token(token)
        return jsonify({"message": "User logged out successfully"}), 200
    
    except Exception as e:
        return jsonify({"message": f"An error occurred: {str(e)}"}), 500


@auth_bp.route("/renew_token", methods=["POST"])
# for renewing the token, we need to check if the token is valid and renew it
def renew_token():
    try:
        token = request.headers.get("Authorization")
        if not token:
            return jsonify({"message": "Token is missing"}), 401

        token = token.split(" ")[1]
        payload = current_app.config['JWT'].check_token(token)

        if payload is None:
            return jsonify({"message": "Token is invalid"}), 401

        new_token = current_app.config['JWT'].generate_token(payload, 3600)
        current_app.config['JWT'].blacklist_token(token)
        return jsonify({"token": new_token}), 200
    except Exception as e:
        return jsonify({"message": f"An error occurred: {str(e)}"}), 500