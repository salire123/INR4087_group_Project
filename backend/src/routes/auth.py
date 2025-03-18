# routes/auth.py
from flask import Blueprint, request, jsonify, current_app
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from utils.db import connect_mysql, connect_mongo

from contextlib import contextmanager

import traceback

auth_bp = Blueprint('auth', __name__)

@auth_bp.route("/login", methods=["POST"])
# for login, we need to check if the user exists in the database
def login():
    client_ip = request.remote_addr
    current_app.logger.info(f"Login attempt received from IP: {client_ip}")

    username = request.form.get("username")
    password = request.form.get("password")
    token = request.headers.get("Authorization")

    # check if the user is already logged in
    try:
        if token:
            current_app.logger.debug(f"Token provided for user: {username} from IP: {client_ip}")
            token = token.split(" ")[1]
            payload = current_app.config['JWT'].check_token(token)
            if payload is not None and payload.get("username") == username:
                current_app.logger.info(f"User {username} already logged in from IP: {client_ip}")
                return jsonify({"message": "User already logged in"}), 200
            if payload is not None:
                current_app.logger.warning(f"Invalid token for user: {username} from IP: {client_ip}")
                return jsonify({"message": "Invalid token"}), 401

        with connect_mysql() as (cursor, connection):
            current_app.logger.debug(f"Checking credentials for user: {username} from IP: {client_ip}")
            cursor.execute("SELECT password FROM users WHERE username = %s", (username,))
            result = cursor.fetchone()
            if result is None:
                current_app.logger.info(f"User not found: {username} - login attempt from IP: {client_ip}")
                return jsonify({"message": "User not found"}), 404
            
            user_password = result[0]
            if check_password_hash(user_password, password):
                token = current_app.config['JWT'].generate_token({"username": username}, 3600)
                current_app.logger.info(f"User {username} logged in successfully from IP: {client_ip}")
                return jsonify({"token": token}), 200
            else:
                current_app.logger.warning(f"Invalid password for user: {username} from IP: {client_ip}")
                return jsonify({"message": "Invalid password"}), 400
            
    except Exception as e:
        # Log the full error with traceback
        error_details = traceback.format_exc()
        current_app.logger.error(f"Login error for IP {client_ip}: {str(e)}\n{error_details}")
        return jsonify({"message": "An error occurred during authentication"}), 500
 
@auth_bp.route("/register", methods=["POST"])
# for registration, we need to insert the user into the databased
def register():
    client_ip = request.remote_addr
    current_app.logger.info(f"Registration attempt received from IP: {client_ip}")
    
    username = request.form.get("username")
    password = request.form.get("password")
    email = request.form.get("email")

    try:
        with connect_mysql() as (cursor, connection):
            current_app.logger.debug(f"Checking if user exists: {username} - request from IP: {client_ip}")
            # check if the user already exists
            cursor.execute("SELECT username, email FROM users WHERE username = %s OR email = %s", (username, email,))
            if cursor.fetchone():
                current_app.logger.info(f"User already exists: {username} - registration attempt from IP: {client_ip}")
                return jsonify({"message": "User already exists"}), 400

            # hash the password before storing it in the database
            password = generate_password_hash(password)
            current_app.logger.debug(f"Creating new user: {username} from IP: {client_ip}")

            # insert the user into the database
            cursor.execute("INSERT INTO users (username, password, email) VALUES (%s, %s, %s)", (username, password, email))

            cursor.execute("SELECT user_id FROM users WHERE username = %s", (username,))
            user_id = cursor.fetchone()[0]
            current_app.logger.debug(f"User created with ID: {user_id} from IP: {client_ip}")

            # create a history collection for the user in MongoDB
            try:
                current_app.logger.debug(f"Creating MongoDB history collection for user ID: {user_id} from IP: {client_ip}")
                with connect_mongo() as mongo_client:
                    # create a db by userid
                    db = mongo_client
                    collection = db["users"]
                    # insert the user into the history collection
                    collection.insert_one({
                        "username": username,
                        "user_id": user_id, 
                        "history": [], 
                        "likes": [], 
                        "Subscriber_to": [],
                        "Subscribers": [],
                        "account_created": str(datetime.now()),
                        "registration_ip": client_ip,
                    })
                current_app.logger.info(f"User {username} created successfully from IP: {client_ip}")

            # if an error occurs, rollback the changes
            except Exception as e:
                current_app.logger.error(f"MongoDB error for user {user_id} from IP {client_ip}: {str(e)}")
                return jsonify({"message": f"An error occurred: {str(e)}"}), 500
            

            return jsonify({
                "message": "User created successfully",
                "user_id": user_id
                            }), 201
    
    except Exception as e:
        # Log the full error with traceback
        error_details = traceback.format_exc()
        current_app.logger.error(f"Registration error from IP {client_ip}: {str(e)}\n{error_details}")
        return jsonify({"message": "An error occurred during authentication"}), 500

@auth_bp.route("/logout", methods=["POST"])
# for logout, we need to invalidate the token
def logout():
    client_ip = request.remote_addr
    current_app.logger.info(f"Logout attempt received from IP: {client_ip}")
    
    try:
        token = request.headers.get("Authorization")
        if not token:
            current_app.logger.warning(f"Logout attempt without token from IP: {client_ip}")
            return jsonify({"message": "Token is missing"}), 401

        token = token.split(" ")[1]
        payload = current_app.config['JWT'].check_token(token)
        if not payload:
            current_app.logger.warning(f"Logout attempt with invalid token from IP: {client_ip}")
            return jsonify({"message": "Token is invalid"}), 401
            
        username = payload.get("username", "unknown")
        current_app.logger.debug(f"Blacklisting token for user: {username} from IP: {client_ip}")
        current_app.config['JWT'].blacklist_token(token)
        current_app.logger.info(f"User {username} logged out successfully from IP: {client_ip}")
        return jsonify({"message": "User logged out successfully"}), 200
    
    except Exception as e:
        # Log the full error with traceback
        error_details = traceback.format_exc()
        current_app.logger.error(f"Logout error from IP {client_ip}: {str(e)}\n{error_details}")
        return jsonify({"message": "An error occurred during authentication"}), 500

@auth_bp.route("/renew_token", methods=["POST"])
# for renewing the token, we need to check if the token is valid and renew it
def renew_token():
    client_ip = request.remote_addr
    current_app.logger.info(f"Token renewal attempt received from IP: {client_ip}")
    
    try:
        token = request.headers.get("Authorization")
        if not token:
            current_app.logger.warning(f"Token renewal attempt without token from IP: {client_ip}")
            return jsonify({"message": "Token is missing"}), 401

        token = token.split(" ")[1]
        payload = current_app.config['JWT'].check_token(token)

        if payload is None:
            current_app.logger.warning(f"Token renewal attempt with invalid token from IP: {client_ip}")
            return jsonify({"message": "Token is invalid"}), 401

        username = payload.get("username", "unknown")
        current_app.logger.debug(f"Generating new token for user: {username} from IP: {client_ip}")
        new_token = current_app.config['JWT'].generate_token(payload, 3600)
        current_app.logger.debug(f"Blacklisting old token for user: {username} from IP: {client_ip}")
        current_app.config['JWT'].blacklist_token(token)
        current_app.logger.info(f"Token renewed successfully for user: {username} from IP: {client_ip}")
        return jsonify({"token": new_token}), 200
    except Exception as e:
        # Log the full error with traceback
        error_details = traceback.format_exc()
        current_app.logger.error(f"Token renewal error from IP {client_ip}: {str(e)}\n{error_details}")
        return jsonify({"message": "An error occurred during authentication"}), 500