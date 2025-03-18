from flask import Blueprint, request, jsonify, current_app
from utils.db import connect_mysql, connect_mongo
from datetime import datetime
from bson.objectid import ObjectId
from contextlib import contextmanager
from utils.db import redis_connection

history_bp = Blueprint('history', __name__)

import traceback



@history_bp.route('/get_history_like', methods=['GET'])
def get_history_like():
    '''Get the history of a user'''
    client_ip = request.remote_addr
    current_app.logger.info(f"History retrieval request from IP: {client_ip}")
    
    username = request.args.get("username")
    current_app.logger.debug(f"Getting history for user: {username} from IP: {client_ip}")
    
    try:
        with connect_mysql() as (cursor, connection):
            cursor.execute("SELECT user_id FROM users WHERE username = %s", (username,))
            result = cursor.fetchone()
            if not result:
                current_app.logger.info(f"User not found: {username} - request from IP: {client_ip}")
                return jsonify({"message": "User not found"}), 404
            user_id = result[0]
            current_app.logger.debug(f"Found user_id: {user_id} for username: {username} from IP: {client_ip}")
        
        with connect_mongo() as mongo_client:
            db = mongo_client
            collection = db["history_like"]

            # Get history and likes
            current_app.logger.debug(f"Querying MongoDB for history of user_id: {user_id} from IP: {client_ip}")
            out = collection.find_one({"user_id": user_id})
            if not out:
                current_app.logger.info(f"No history found for user_id: {user_id} from IP: {client_ip}")
                return jsonify({"message": "No history found"}), 404
            
            # Convert ObjectID to string
            out["_id"] = str(out["_id"])
            for item in out["history"]:
                item["post_id"] = str(item["post_id"])
            for item in out["likes"]:
                item["post_id"] = str(item["post_id"])
            
            current_app.logger.info(f"Successfully retrieved history for user: {username} from IP: {client_ip}")
            return jsonify(out), 200
        
    except Exception as e:
        error_details = traceback.format_exc()
        current_app.logger.error(f"History error for IP {client_ip}: {str(e)}\n{error_details}")
        return jsonify({"message": "An error occurred while retrieving history"}), 500

@history_bp.route('/add_read_history', methods=['POST'])    
def add_read_history():
    '''Add a post to the user's history or update timestamp if already exists'''
    client_ip = request.remote_addr
    current_app.logger.info(f"Add read history request from IP: {client_ip}")

    post_id = request.args.get("post_id")
    current_app.logger.debug(f"Adding post {post_id} to read history - request from IP: {client_ip}")

    # token check
    token = request.headers.get("Authorization")
    if not token:
        current_app.logger.warning(f"Token missing for add_read_history request from IP: {client_ip}")
        return jsonify({"message": "Token is required"}), 400
    
    try:
        # Token format check and verification
        if token:
            token = token.split(" ")[1]
            payload = current_app.config['JWT'].check_token(token)
            username = payload.get("username", "unknown") if payload else "invalid"
            current_app.logger.debug(f"Token verification for user: {username} from IP: {client_ip}")
            
            if payload is None:
                current_app.logger.warning(f"Invalid token provided from IP: {client_ip}")
                return jsonify({"message": "Invalid token"}), 401

        if not post_id:
            current_app.logger.warning(f"Post ID missing from request from IP: {client_ip}")
            return jsonify({"message": "Post ID is required"}), 400

        # Get user_id from username
        with connect_mysql() as (cursor, connection):
            current_app.logger.debug(f"Getting user_id for username: {payload['username']} from IP: {client_ip}")
            cursor.execute("SELECT user_id FROM users WHERE username = %s", (payload["username"],))
            result = cursor.fetchone()
            if not result:
                current_app.logger.warning(f"User {payload['username']} not found - request from IP: {client_ip}")
                return jsonify({"message": "User not found"}), 404
            user_id = result[0]
            current_app.logger.debug(f"Found user_id: {user_id} for user: {payload['username']} from IP: {client_ip}")
        
        # Connect to MongoDB and update history
        with connect_mongo() as mongo_client:
            db = mongo_client
            collection = db["history_like"]
            
            # Check if post is already in history
            current_app.logger.debug(f"Checking if post {post_id} exists in history for user_id: {user_id} from IP: {client_ip}")
            existing_item = collection.find_one({
                "user_id": user_id,
                "history.post_id": post_id
            })
            
            with redis_connection(db=1) as redis_client:
                read_key = f"post:{post_id}:reads"
                current_app.logger.debug(f"Incrementing read count for post {post_id} from IP: {client_ip}")
                # Increment the read count for this post
                redis_client.incr(read_key)
                # Set expiration to 24 hours if it's a new key (won't reset if already exists)
                if redis_client.ttl(read_key) == -1:  # -1 means no expiration set
                    current_app.logger.debug(f"Setting TTL for new read key: {read_key} from IP: {client_ip}")
                    redis_client.expire(read_key, 24 * 60 * 60)  # 24 hours in seconds

            if existing_item:
                # Update timestamp of existing item
                current_app.logger.debug(f"Updating timestamp for existing history item for user_id: {user_id}, post: {post_id} from IP: {client_ip}")
                collection.update_one(
                    {
                        "user_id": user_id,
                        "history.post_id": post_id
                    },
                    {"$set": {"history.$.timestamp": datetime.now()}}
                )
                current_app.logger.info(f"History timestamp updated for user: {payload['username']}, post: {post_id} from IP: {client_ip}")
                return jsonify({"message": "History timestamp updated"}), 200
            else:
                # Add new item to history array
                current_app.logger.debug(f"Adding new history item for user_id: {user_id}, post: {post_id} from IP: {client_ip}")
                collection.update_one(
                    {"user_id": user_id},
                    {"$push": {"history": {
                        "post_id": post_id,
                        "timestamp": datetime.now()
                    }}}
                )
                current_app.logger.info(f"New history item added for user: {payload['username']}, post: {post_id} from IP: {client_ip}")
                return jsonify({"message": "History added"}), 200
                
    except Exception as e:
        error_details = traceback.format_exc()
        current_app.logger.error(f"Read history error from IP {client_ip}: {str(e)}\n{error_details}")
        return jsonify({"message": "An error occurred while updating read history"}), 500

@history_bp.route('/add_like', methods=['POST'])
def add_like():
    '''Add a like to a post or inform user if already liked'''
    client_ip = request.remote_addr
    current_app.logger.info(f"Add like request from IP: {client_ip}")

    post_id = request.args.get("post_id")
    current_app.logger.debug(f"Adding like for post {post_id} - request from IP: {client_ip}")

    # token check
    token = request.headers.get("Authorization")
    if not token:
        current_app.logger.warning(f"Token missing for add_like request from IP: {client_ip}")
        return jsonify({"message": "Token is required"}), 400
    
    try:
        # Token verification
        token = token.split(" ")[1]
        payload = current_app.config['JWT'].check_token(token)
        username = payload.get("username", "unknown") if payload else "invalid"
        current_app.logger.debug(f"Token verification for user: {username} from IP: {client_ip}")
        
        if payload is None:
            current_app.logger.warning(f"Invalid token provided from IP: {client_ip}")
            return jsonify({"message": "Invalid token"}), 401

        if not post_id:
            current_app.logger.warning(f"Post ID missing from like request from IP: {client_ip}")
            return jsonify({"message": "Post ID is required"}), 400

        # Get user_id from username
        with connect_mysql() as (cursor, connection):
            current_app.logger.debug(f"Getting user_id for username: {payload['username']} from IP: {client_ip}")
            cursor.execute("SELECT user_id FROM users WHERE username = %s", (payload["username"],))
            result = cursor.fetchone()
            if not result:
                current_app.logger.warning(f"User {payload['username']} not found - like request from IP: {client_ip}")
                return jsonify({"message": "User not found"}), 404
            user_id = result[0]
            current_app.logger.debug(f"Found user_id: {user_id} for user: {payload['username']} from IP: {client_ip}")
        
        # Connect to MongoDB and update likes
        with connect_mongo() as mongo_client:
            db = mongo_client
            likes_collection = db["history_like"]
            
            # Check if user already liked this post
            current_app.logger.debug(f"Checking if post {post_id} already liked by user_id: {user_id} from IP: {client_ip}")
            existing_item = likes_collection.find_one({
                "user_id": user_id,
                "likes.post_id": post_id
            })
            
            if existing_item:
                # User has already liked this post
                current_app.logger.info(f"Post {post_id} already liked by user: {payload['username']} - request from IP: {client_ip}")
                return jsonify({"message": "You've already liked this post", "already_liked": True}), 200
            
            else:
                current_app.logger.debug(f"Adding like for post {post_id} by user_id: {user_id} from IP: {client_ip}")
                likes_collection.update_one(
                        {"user_id": user_id},
                        {"$push": {"likes": {
                            "post_id": post_id,
                            "timestamp": datetime.now()
                        }}}
                    )
                current_app.logger.info(f"Like added for post {post_id} by user: {payload['username']} from IP: {client_ip}")
            return jsonify({"message": "Post liked successfully", "already_liked": False}), 200
                
    except Exception as e:
        error_details = traceback.format_exc()
        current_app.logger.error(f"Like post error from IP {client_ip}: {str(e)}\n{error_details}")
        return jsonify({"message": "An error occurred while liking the post"}), 500

@history_bp.route('/remove_like', methods=['DELETE'])
def remove_like():
    '''Remove a like from a post'''
    client_ip = request.remote_addr
    current_app.logger.info(f"Remove like request from IP: {client_ip}")
    
    post_id = request.args.get("post_id")
    current_app.logger.debug(f"Removing like for post {post_id} - request from IP: {client_ip}")

    # token check
    token = request.headers.get("Authorization")
    if not token:
        current_app.logger.warning(f"Token missing for remove_like request from IP: {client_ip}")
        return jsonify({"message": "Token is required"}), 400
    
    try:
        # Token verification
        token = token.split(" ")[1]
        payload = current_app.config['JWT'].check_token(token)
        username = payload.get("username", "unknown") if payload else "invalid"
        current_app.logger.debug(f"Token verification for user: {username} from IP: {client_ip}")
        
        if payload is None:
            current_app.logger.warning(f"Invalid token provided from IP: {client_ip}")
            return jsonify({"message": "Invalid token"}), 401

        if not post_id:
            current_app.logger.warning(f"Post ID missing from remove_like request from IP: {client_ip}")
            return jsonify({"message": "Post ID is required"}), 400

        # Get user_id from username
        with connect_mysql() as (cursor, connection):
            current_app.logger.debug(f"Getting user_id for username: {payload['username']} from IP: {client_ip}")
            cursor.execute("SELECT user_id FROM users WHERE username = %s", (payload["username"],))
            result = cursor.fetchone()
            if not result:
                current_app.logger.warning(f"User {payload['username']} not found - remove_like request from IP: {client_ip}")
                return jsonify({"message": "User not found"}), 404
            user_id = result[0]
            current_app.logger.debug(f"Found user_id: {user_id} for user: {payload['username']} from IP: {client_ip}")
        
        # Connect to MongoDB and remove like
        with connect_mongo() as mongo_client:
            db = mongo_client
            collection = db["history_like"]
            
            # Check if the post was liked by the user
            current_app.logger.debug(f"Checking if post {post_id} was liked by user_id: {user_id} from IP: {client_ip}")
            existing_item = collection.find_one({
                "user_id": user_id,
                "likes.post_id": post_id
            })
            
            if not existing_item:
                current_app.logger.info(f"Post {post_id} not liked by user: {payload['username']} - request from IP: {client_ip}")
                return jsonify({"message": "You haven't liked this post"}), 404
                
            # Remove the like from the user's likes array
            current_app.logger.debug(f"Removing like for post {post_id} by user_id: {user_id} from IP: {client_ip}")
            result = collection.update_one(
                {"user_id": user_id},
                {"$pull": {"likes": {"post_id": post_id}}}
            )
            
            if result.modified_count > 0:
                current_app.logger.info(f"Like removed for post {post_id} by user: {payload['username']} from IP: {client_ip}")
                return jsonify({"message": "Like removed successfully"}), 200
            else:
                current_app.logger.warning(f"Failed to remove like for post {post_id} by user: {payload['username']} from IP: {client_ip}")
                return jsonify({"message": "Failed to remove like"}), 500
                
    except Exception as e:
        error_details = traceback.format_exc()
        current_app.logger.error(f"Remove like error from IP {client_ip}: {str(e)}\n{error_details}")
        return jsonify({"message": "An error occurred while removing the like"}), 500