from flask import Blueprint, request, jsonify, current_app
from utils.db import connect_mysql, connect_mongo
from datetime import datetime
from bson.objectid import ObjectId
from contextlib import contextmanager
from utils.db import redis_connection

from functools import wraps


import traceback

user_bp = Blueprint('user', __name__)

def auth_check(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = request.headers.get("Authorization")
        if not token:
            return jsonify({"message": "Missing token"}), 401
        token = token.split(" ")[1]
        payload = current_app.config['JWT'].check_token(token)
        if payload is None:
            return jsonify({"message": "Invalid token"}), 401
        return f(*args, **kwargs)
    return decorated_function


@user_bp.route('/subscribe', methods=['POST'])
@auth_check
def subscribe():
    try:
        client_ip = request.remote_addr
        current_app.logger.info(f"Subscribe request received from IP: {client_ip}")

        token = request.headers.get("Authorization")

        payload = current_app.config['JWT'].check_token(token)
        Subscribe_to = request.args.get("username")

        if not token:
            current_app.logger.warning(f"Token missing for create_post request from IP: {client_ip}")
            return jsonify({"message": "Token is required"}), 400

        if token:
            token = token.split(" ")[1]
            payload = current_app.config['JWT'].check_token(token)
            username = payload.get("username", "unknown") if payload else "invalid"
            current_app.logger.debug(f"Token verification for user: {username} from IP: {client_ip}")
            if payload is None:
                current_app.logger.warning(f"Invalid token for create_post request from IP: {client_ip}")
                return jsonify({"message": "Invalid token"}), 401
        
        if not Subscribe_to:
            return jsonify({"message": "Missing Subscribe_to"}), 400
       
        # Check both users exist
        current_app.logger.debug(f"Checking if users exist: {payload.get('username')} and {Subscribe_to}")
        with connect_mysql() as (cursor, connection):
            cursor.execute("SELECT user_id FROM users WHERE username = %s", (payload.get("username"),))
            user_id = cursor.fetchone()
            cursor.execute("SELECT user_id FROM users WHERE username = %s", (Subscribe_to,))
            subscribe_to_id = cursor.fetchone()
            if not user_id or not subscribe_to_id:
                return jsonify({"message": "User not found"}), 404
        
        if user_id == subscribe_to_id:
            return jsonify({"message": "Cannot subscribe to self"}), 400
            
        if type(user_id) == tuple:  # MySQL fetchone returns a tuple
            user_id = user_id[0]
        if type(subscribe_to_id) == tuple:
            subscribe_to_id = subscribe_to_id[0] 
        
        # Check if already subscribed
        current_app.logger.debug(f"Checking if already subscribed: {payload.get('username')} to {Subscribe_to}")
        with connect_mongo() as mongo_client:
            db = mongo_client
            collection = db["users"]
            
            # Check if the user is already subscribed
            existing_item = collection.find_one({"user_id": user_id, "Subscriber_to": subscribe_to_id})

            if existing_item:
                current_app.logger.info(f"Already subscribed: {payload.get('username')} to {Subscribe_to}")
                return jsonify({"message": "Already subscribed"}), 400
            
            # Add the subscription to both users
            current_app.logger.debug(f"Adding subscription: {payload.get('username')} to {Subscribe_to}")
 
            collection.update_one(
                {"user_id": user_id},
                {"$push": {"Subscriber_to": subscribe_to_id}}  # Push the user_id directly
            )
            collection.update_one(
                {"user_id": subscribe_to_id},
                {"$push": {"Subscribers": user_id}}  # Push the user_id directly
            )

        current_app.logger.info(f"Subscribed: {payload.get('username')} to {Subscribe_to}")
        return jsonify({"message": "Subscribed successfully"}), 200
    except Exception as e:
        error_details = traceback.format_exc()
        current_app.logger.error(f"Subscribe error for IP {client_ip}: {str(e)}\n{error_details}")
        return jsonify({"message": "An error occurred during subscription"}), 500
@user_bp.route('/unsubscribe', methods=['POST'])
@auth_check
def unsubscribe():
    try:
        client_ip = request.remote_addr
        current_app.logger.info(f"Unsubscribe request received from IP: {client_ip}")

        token = request.headers.get("Authorization")

        if not token:
            current_app.logger.warning(f"Token missing for unsubscribe request from IP: {client_ip}")
            return jsonify({"message": "Token is required"}), 400

        if token:
            token = token.split(" ")[1]
            payload = current_app.config['JWT'].check_token(token)
            username = payload.get("username", "unknown") if payload else "invalid"
            current_app.logger.debug(f"Token verification for user: {username} from IP: {client_ip}")
            if payload is None:
                current_app.logger.warning(f"Invalid token for unsubscribe request from IP: {client_ip}")
                return jsonify({"message": "Invalid token"}), 401

        unsubscribe_to = request.args.get("username")
        
        if not unsubscribe_to:
            return jsonify({"message": "Missing unsubscribe_to"}), 400
        
        # Check both users exist
        current_app.logger.debug(f"Checking if users exist: {payload.get('username')} and {unsubscribe_to}")
        with connect_mysql() as (cursor, connection):
            cursor.execute("SELECT user_id FROM users WHERE username = %s", (payload.get("username"),))
            user_id = cursor.fetchone()
            cursor.execute("SELECT user_id FROM users WHERE username = %s", (unsubscribe_to,))
            unsubscribe_to_id = cursor.fetchone()
            if not user_id or not unsubscribe_to_id:
                return jsonify({"message": "User not found"}), 404
        
        # Handle tuple from MySQL fetchone
        if type(user_id) == tuple:
            user_id = user_id[0]
        if type(unsubscribe_to_id) == tuple:
            unsubscribe_to_id = unsubscribe_to_id[0]

        if user_id == unsubscribe_to_id:
            return jsonify({"message": "Cannot unsubscribe from self"}), 400
        
        # Check if already subscribed
        current_app.logger.debug(f"Checking if already subscribed: {payload.get('username')} to {unsubscribe_to}")
        with connect_mongo() as mongo_client:
            db = mongo_client
            collection = db["users"]
            
            existing_item = collection.find_one({
                "user_id": user_id,
                "Subscriber_to": unsubscribe_to_id
            })
            if not existing_item:
                current_app.logger.info(f"Not subscribed: {payload.get('username')} to {unsubscribe_to}")
                return jsonify({"message": "Not subscribed"}), 400
            
        # Remove the subscription from both users
        current_app.logger.debug(f"Removing subscription: {payload.get('username')} to {unsubscribe_to}")
        with connect_mongo() as mongo_client:
            db = mongo_client
            collection = db["users"]

            result1 = collection.update_one(
                {"user_id": user_id},
                {"$pull": {"Subscriber_to": unsubscribe_to_id}}  # Correct field name
            )
            result2 = collection.update_one(
                {"user_id": unsubscribe_to_id},
                {"$pull": {"Subscribers": user_id}}
            )

            # Optional: Log update results for debugging
            current_app.logger.debug(f"Subscriber_to update: Matched {result1.matched_count}, Modified {result1.modified_count}")
            current_app.logger.debug(f"Subscribers update: Matched {result2.matched_count}, Modified {result2.modified_count}")

        current_app.logger.info(f"Unsubscribed: {payload.get('username')} to {unsubscribe_to}")
        return jsonify({"message": "Unsubscribed successfully"}), 200
    except Exception as e:
        error_details = traceback.format_exc()
        current_app.logger.error(f"Unsubscribe error for IP {client_ip}: {str(e)}\n{error_details}")
        return jsonify({"message": "An error occurred during unsubscription"}), 500
    
@user_bp.route('/check_user_info', methods=['GET'])
def check_user_info():
    try:
        client_ip = request.remote_addr
        current_app.logger.info(f"Check user info request received from IP: {client_ip}")

        username = request.args.get("username")
        userid = request.args.get("userid")
        if not username and not userid: # Check if either username or userid is provided
            current_app.logger.warning(f"Missing username or userid for check_user_info request from IP: {client_ip}")
            return jsonify({"message": "Missing username"}), 400

        current_app.logger.debug(f"Checking user info for: {username}")
        with connect_mongo() as mongo_client:
            db = mongo_client
            collection = db["users"]
            if userid:
                user_info = collection.find_one({"user_id": int(userid)})
            else:
                user_info = collection.find_one({"username": username})
            user_info = collection.find_one({"username": username})
            if not user_info:
                return jsonify({"message": "User not found"}), 404

            # Convert ObjectId to string
            user_info["_id"] = str(user_info["_id"])
            return jsonify(user_info), 200
    except Exception as e:
        error_details = traceback.format_exc()
        current_app.logger.error(f"Check user info error for IP {client_ip}: {str(e)}\n{error_details}")
        return jsonify({"message": "An error occurred during user info check"}), 500








