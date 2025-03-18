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
        token = token.split(" ")[1]
        payload = current_app.config['JWT'].check_token(token)
        subscribe_to = request.form.get("subscribe_to")
        
        if not subscribe_to:
            return jsonify({"message": "Missing subscribe_to"}), 400
        
        # Check both users exist
        current_app.logger.debug(f"Checking if users exist: {payload.get('username')} and {subscribe_to}")
        with connect_mysql() as (cursor, connection):
            cursor.execute("SELECT id FROM users WHERE username = %s", (payload.get("username"),))
            user_id = cursor.fetchone()
            cursor.execute("SELECT id FROM users WHERE username = %s", (subscribe_to,))
            subscribe_to_id = cursor.fetchone()
            if not user_id or not subscribe_to_id:
                return jsonify({"message": "User not found"}), 404
        
        # Check if already subscribed
        current_app.logger.debug(f"Checking if already subscribed: {payload.get('username')} to {subscribe_to}")
        with connect_mongo() as mongo_client:
            db = mongo_client
            collection = db["users"]
            
            existing_item = collection.find_one({
                    "user_id": user_id,
                    "history.subscribe_to": subscribe_to_id
                })
            if existing_item:
                current_app.logger.info(f"Already subscribed: {payload.get('username')} to {subscribe_to}")
                return jsonify({"message": "Already subscribed"}), 400
            
        # Add the subscription to both users
        current_app.logger.debug(f"Adding subscription: {payload.get('username')} to {subscribe_to}")
        with connect_mongo() as mongo_client:
            db = mongo_client
            collection = db["users"]

            collection.update_one(
                {"user_id": user_id},
                {"$push": {"history.subscribe_to": subscribe_to_id}}
            )

            collection.update_one(
                {"user_id": subscribe_to_id},
                {"$push": {"history.subscribers": user_id}}
            )

        current_app.logger.info(f"Subscribed: {payload.get('username')} to {subscribe_to}")
        return jsonify({"message": "Subscribed successfully"}), 200
    except Exception as e:
        # Log the full error with traceback
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
        token = token.split(" ")[1]
        payload = current_app.config['JWT'].check_token(token)
        unsubscribe_to = request.form.get("unsubscribe_to")
        
        if not unsubscribe_to:
            return jsonify({"message": "Missing unsubscribe_to"}), 400
        
        # Check both users exist
        current_app.logger.debug(f"Checking if users exist: {payload.get('username')} and {unsubscribe_to}")
        with connect_mysql() as (cursor, connection):
            cursor.execute("SELECT id FROM users WHERE username = %s", (payload.get("username"),))
            user_id = cursor.fetchone()
            cursor.execute("SELECT id FROM users WHERE username = %s", (unsubscribe_to,))
            unsubscribe_to_id = cursor.fetchone()
            if not user_id or not unsubscribe_to_id:
                return jsonify({"message": "User not found"}), 404
        
        # Check if already subscribed
        current_app.logger.debug(f"Checking if already subscribed: {payload.get('username')} to {unsubscribe_to}")
        with connect_mongo() as mongo_client:
            db = mongo_client
            collection = db["users"]
            
            existing_item = collection.find_one({
                    "user_id": user_id,
                    "history.subscribe_to": unsubscribe_to_id
                })
            if not existing_item:
                current_app.logger.info(f"Not subscribed: {payload.get('username')} to {unsubscribe_to}")
                return jsonify({"message": "Not subscribed"}), 400
            
        # Remove the subscription from both users
        current_app.logger.debug(f"Removing subscription: {payload.get('username')} to {unsubscribe_to}")
        with connect_mongo() as mongo_client:
            db = mongo_client
            collection = db["users"]

            collection.update_one(
                {"user_id": user_id},
                {"$pull": {"history.subscribe_to": unsubscribe_to_id}}
            )

            collection.update_one(
                {"user_id": unsubscribe_to_id},
                {"$pull": {"history.subscribers": user_id}}
            )

        current_app.logger.info(f"Unsubscribed: {payload.get('username')} to {unsubscribe_to}")
        return jsonify({"message": "Unsubscribed successfully"}), 200
    except Exception as e:
        # Log the full error with traceback
        error_details = traceback.format_exc()
        current_app.logger.error(f"Unsubscribe error for IP {client_ip}: {str(e)}\n{error_details}")
        return jsonify({"message": "An error occurred during unsubscription"}), 500

@user_bp.route('/check_user_info', methods=['GET'])
def check_user_info():
    try:
        client_ip = request.remote_addr
        current_app.logger.info(f"Check user info request received from IP: {client_ip}")

        username = request.args.get("username")
        if not username:
            return jsonify({"message": "Missing username"}), 400

        #get user info form mongodb
        current_app.logger.debug(f"Checking user info for: {username}")
        with connect_mongo() as mongo_client:
            db = mongo_client
            collection = db["users"]
            user_info = collection.find_one({"username": username})
            if not user_info:
                return jsonify({"message": "User not found"}), 404

            return jsonify(user_info), 200
    except Exception as e:
        # Log the full error with traceback
        error_details = traceback.format_exc()
        current_app.logger.error(f"Check user info error for IP {client_ip}: {str(e)}\n{error_details}")
        return jsonify({"message": "An error occurred during user info check"}), 500









