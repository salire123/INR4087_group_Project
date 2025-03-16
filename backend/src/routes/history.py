from flask import Blueprint, request, jsonify, current_app
from utils.db import connect_mysql, connect_mongo
from datetime import datetime
from bson.objectid import ObjectId
from contextlib import contextmanager

history_bp = Blueprint('history', __name__)

import traceback



@history_bp.route('/history/<string:username>', methods=['GET'])
def get_history(username):
    '''Get the history of a user'''
    try:
        with connect_mysql() as (cursor, connection):
            cursor.execute("SELECT user_id FROM users WHERE username = %s", (username,))
            result = cursor.fetchone()
            if not result:
                return jsonify({"message": "User not found"}), 404
            user_id = result[0]
        
        with connect_mongo() as mongo_client:
            db = mongo_client
            collection = db["history"]
            posts = collection.find({"user_id": user_id})
            response = []
            for post in posts:
                post["_id"] = str(post["_id"])
                response.append(post)
            return jsonify({"history": response}), 200
    except Exception as e:
        error_details = traceback.format_exc()
        current_app.logger.error(f"Login error: {str(e)}\n{error_details}")
        return jsonify({"message": "An error occurred during authentication"}), 500
    
@history_bp.route('/add_read_history', methods=['POST'])
def add_read_history():
    '''Add a post to the user's history'''


    post_id = request.form.get("post_id")
    username  = request.form.get("username")


    #token check
    token = request.headers.get("Authorization")
    if not token:
        return jsonify({"message": "Token is required"}), 400
    try:
        payload = current_app.config['JWT'].check_token(token)
        if payload is None or "username" not in payload:
            return jsonify({"message": "Invalid token"}), 401


        if not post_id:
            return jsonify({"message": "Post ID is required"}), 400
        if not username:
            return jsonify({"message": "Username is required"}), 400

        with connect_mysql() as (cursor, connection):
            cursor.execute("SELECT user_id FROM users WHERE username = %s", (username,))
            result = cursor.fetchone()
            if not result:
                return jsonify({"message": "User not found"}), 404
            user_id = result[0]
        
        with connect_mongo() as mongo_client:
            db = mongo_client
            collection = db["history"]
            collection.insert_one({"user_id": user_id, "post_id": post_id, "timestamp": datetime.now()})
            return jsonify({"message": "History added"}), 200
    except Exception as e:
        error_details = traceback.format_exc()
        current_app.logger.error(f"Login error: {str(e)}\n{error_details}")
        return jsonify({"message": "An error occurred during authentication"}), 500
    

@history_bp.route('/add_like', methods=['POST'])
def add_like():
    '''Add a like to a post'''
    post_id = request.form.get("post_id")
    username  = request.form.get("username")


    #token check
    token = request.headers.get("Authorization")
    if not token:
        return jsonify({"message": "Token is required"}), 400
    try:
        payload = current_app.config['JWT'].check_token(token)
        if payload is None or "username" not in payload:
            return jsonify({"message": "Invalid token"}), 401

        if not post_id:
            return jsonify({"message": "Post ID is required"}), 400
        if not username:
            return jsonify({"message": "Username is required"}), 400
    
        with connect_mysql() as (cursor, connection):
            cursor.execute("SELECT user_id FROM users WHERE username = %s", (username,))
            result = cursor.fetchone()
            if not result:
                return jsonify({"message": "User not found"}), 404
            user_id = result[0]
        
        with connect_mongo() as mongo_client:
            db = mongo_client
            collection = db["history"]
            collection.update_one({"user_id": user_id, "post_id": post_id}, {"$addToSet": {"likes": user_id}})
            return jsonify({"message": "Like added"}), 200
    except Exception as e:
        error_details = traceback.format_exc()
        current_app.logger.error(f"Login error: {str(e)}\n{error_details}")
        return jsonify({"message": "An error occurred during authentication"}), 500
    

@history_bp.route('/remove_like', methods=['POST'])
def remove_like():
    '''Remove a like from a post'''
    
    post_id = request.form.get("post_id")
    username  = request.form.get("username")


    #token check
    token = request.headers.get("Authorization")
    if not token:
        return jsonify({"message": "Token is required"}), 400
    try:
        payload = current_app.config['JWT'].check_token(token)
        if payload is None or "username" not in payload:
            return jsonify({"message": "Invalid token"}), 401

        if not post_id:
            return jsonify({"message": "Post ID is required"}), 400
        if not username:
            return jsonify({"message": "Username is required"}), 400

        with connect_mysql() as (cursor, connection):
            cursor.execute("SELECT user_id FROM users WHERE username = %s", (username,))
            result = cursor.fetchone()
            if not result:
                return jsonify({"message": "User not found"}), 404
            user_id = result[0]
        
        with connect_mongo() as mongo_client:
            db = mongo_client
            collection = db["history"]
            collection.update_one({"user_id": user_id, "post_id": post_id}, {"$pull": {"likes": user_id}})
            return jsonify({"message": "Like removed"}), 200
    except Exception as e:
        error_details = traceback.format_exc()
        current_app.logger.error(f"Login error: {str(e)}\n{error_details}")
        return jsonify({"message": "An error occurred during authentication"}), 500