from flask import Blueprint, request, jsonify, current_app
from utils.db import connect_mysql, connect_mongo
from datetime import datetime
from bson.objectid import ObjectId
from contextlib import contextmanager

history_bp = Blueprint('history', __name__)

import traceback



@history_bp.route('/get_history_like', methods=['GET'])
def get_history_like():
    '''Get the history of a user'''
    username = request.args.get("username")
    try:
        with connect_mysql() as (cursor, connection):
            cursor.execute("SELECT user_id FROM users WHERE username = %s", (username,))
            result = cursor.fetchone()
            if not result:
                return jsonify({"message": "User not found"}), 404
            user_id = result[0]
        
        with connect_mongo() as mongo_client:
            db = mongo_client
            collection = db["history_like"]

            # Get history and likes
            out = collection.find_one({"user_id": user_id})
            if not out:
                return jsonify({"message": "No history found"}), 404
            
            # Convert ObjectID to string
            out["_id"] = str(out["_id"])
            for item in out["history"]:
                item["post_id"] = str(item["post_id"])
            for item in out["likes"]:
                item["post_id"] = str(item["post_id"])
            return jsonify(out), 200
        
    except Exception as e:
        error_details = traceback.format_exc()
        current_app.logger.error(f"History error: {str(e)}\n{error_details}")
        return jsonify({"message": "An error occurred while retrieving history"}), 500

@history_bp.route('/add_read_history', methods=['POST'])    
def add_read_history():
    '''Add a post to the user's history or update timestamp if already exists'''

    post_id = request.args.get("post_id")

    # token check
    token = request.headers.get("Authorization")
    if not token:
        return jsonify({"message": "Token is required"}), 400
    
    try:
        # Token format check and verification
        if token:
            token = token.split(" ")[1]
            payload = current_app.config['JWT'].check_token(token)
            print(payload)
            if payload is None:
                return jsonify({"message": "Invalid token"}), 401

        if not post_id:
            return jsonify({"message": "Post ID is required"}), 400

        # Get user_id from username
        with connect_mysql() as (cursor, connection):
            cursor.execute("SELECT user_id FROM users WHERE username = %s", (payload["username"],))
            result = cursor.fetchone()
            if not result:
                return jsonify({"message": "User not found"}), 404
            user_id = result[0]
        
        # Connect to MongoDB and update history
        with connect_mongo() as mongo_client:
            db = mongo_client
            collection = db["history_like"]
            
            # Check if post is already in history
            existing_item = collection.find_one({
                "user_id": user_id,
                "history.post_id": post_id
            })
            
            if existing_item:
                # Update timestamp of existing item
                collection.update_one(
                    {
                        "user_id": user_id,
                        "history.post_id": post_id
                    },
                    {"$set": {"history.$.timestamp": datetime.now()}}
                )
                return jsonify({"message": "History timestamp updated"}), 200
            else:
                # Add new item to history array
                collection.update_one(
                    {"user_id": user_id},
                    {"$push": {"history": {
                        "post_id": post_id,
                        "timestamp": datetime.now()
                    }}}
                )
                return jsonify({"message": "History added"}), 200
                
    except Exception as e:
        error_details = traceback.format_exc()
        current_app.logger.error(f"Read history error: {str(e)}\n{error_details}")
        return jsonify({"message": "An error occurred while updating read history"}), 500

@history_bp.route('/add_like', methods=['POST'])
def add_like():
    '''Add a like to a post or inform user if already liked'''

    post_id = request.args.get("post_id")

    # token check
    token = request.headers.get("Authorization")
    if not token:
        return jsonify({"message": "Token is required"}), 400
    
    try:
        # Token verification
        token = token.split(" ")[1]
        payload = current_app.config['JWT'].check_token(token)
        if payload is None:
            return jsonify({"message": "Invalid token"}), 401

        if not post_id:
            return jsonify({"message": "Post ID is required"}), 400


        # Get user_id from username
        with connect_mysql() as (cursor, connection):
            cursor.execute("SELECT user_id FROM users WHERE username = %s", (payload["username"],))
            result = cursor.fetchone()
            if not result:
                return jsonify({"message": "User not found"}), 404
            user_id = result[0]
        
        # Connect to MongoDB and update likes
        with connect_mongo() as mongo_client:
            db = mongo_client
            likes_collection = db["history_like"]
            
            # Check if user already liked this post
                        # Check if post is already in history
            existing_item = likes_collection.find_one({
                "user_id": user_id,
                "likes.post_id": post_id
            })
            
            if existing_item:
                # User has already liked this post
                return jsonify({"message": "You've already liked this post", "already_liked": True}), 200
            
            else:
                likes_collection.update_one(
                        {"user_id": user_id},
                        {"$push": {"likes": {
                            "post_id": post_id,
                            "timestamp": datetime.now()
                        }}}
                    )
                
            
            return jsonify({"message": "Post liked successfully", "already_liked": False}), 200
                
    except Exception as e:
        error_details = traceback.format_exc()
        current_app.logger.error(f"Like post error: {str(e)}\n{error_details}")
        return jsonify({"message": "An error occurred while liking the post"}), 500

@history_bp.route('/remove_like', methods=['DELETE'])
def remove_like():
    '''Remove a like from a post'''
    
    post_id = request.args.get("post_id")

    # token check
    token = request.headers.get("Authorization")
    if not token:
        return jsonify({"message": "Token is required"}), 400
    
    try:
        # Token verification
        token = token.split(" ")[1]
        payload = current_app.config['JWT'].check_token(token)
        if payload is None:
            return jsonify({"message": "Invalid token"}), 401

        if not post_id:
            return jsonify({"message": "Post ID is required"}), 400

        # Get user_id from username
        with connect_mysql() as (cursor, connection):
            cursor.execute("SELECT user_id FROM users WHERE username = %s", (payload["username"],))
            result = cursor.fetchone()
            if not result:
                return jsonify({"message": "User not found"}), 404
            user_id = result[0]
        
        # Connect to MongoDB and remove like
        with connect_mongo() as mongo_client:
            db = mongo_client
            collection = db["history_like"]
            
            # Check if the post was liked by the user
            existing_item = collection.find_one({
                "user_id": user_id,
                "likes.post_id": post_id
            })
            
            if not existing_item:
                return jsonify({"message": "You haven't liked this post"}), 404
                
            # Remove the like from the user's likes array
            result = collection.update_one(
                {"user_id": user_id},
                {"$pull": {"likes": {"post_id": post_id}}}
            )
            
            if result.modified_count > 0:
                return jsonify({"message": "Like removed successfully"}), 200
            else:
                return jsonify({"message": "Failed to remove like"}), 500
                
    except Exception as e:
        error_details = traceback.format_exc()
        current_app.logger.error(f"Remove like error: {str(e)}\n{error_details}")
        return jsonify({"message": "An error occurred while removing the like"}), 500