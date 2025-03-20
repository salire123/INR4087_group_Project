from flask import Blueprint, request, jsonify, current_app
from utils.db import connect_mysql, connect_mongo, redis_connection
from datetime import datetime, timezone
from bson.objectid import ObjectId
from contextlib import contextmanager
from functools import wraps
import traceback

history_bp = Blueprint('history', __name__)

# Centralized error handling
def handle_exception(e, logger, client_ip, message="An error occurred"):
    error_details = traceback.format_exc()
    logger.error(f"Error from IP {client_ip}: {str(e)}\n{error_details}")
    return jsonify({"message": message}), 500

# Enhanced authentication decorator
def auth_check(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        client_ip = request.remote_addr
        logger = current_app.logger
        token = request.headers.get("Authorization")
        if not token:
            logger.warning(f"Missing token from IP: {client_ip}")
            return jsonify({"message": "Missing token"}), 401
        token = token.split(" ")[1]
        payload = current_app.config['JWT'].check_token(token)
        if payload is None:
            logger.warning(f"Invalid token from IP: {client_ip}")
            return jsonify({"message": "Invalid token"}), 401
        
        # Fetch user_id from MySQL
        with connect_mysql() as (cursor, connection):
            cursor.execute("SELECT user_id FROM users WHERE username = %s", (payload["username"],))
            result = cursor.fetchone()
            if not result:
                logger.warning(f"User {payload['username']} not found from IP: {client_ip}")
                return jsonify({"message": "User not found"}), 404
            user_id = result[0]
        
        kwargs["user_id"] = user_id
        kwargs["username"] = payload["username"]
        return f(*args, **kwargs)
    return decorated_function

@history_bp.route('/get_history_like', methods=['GET'])
def get_history_like():
    '''Get the history of a user'''
    client_ip = request.remote_addr
    logger = current_app.logger
    logger.info(f"History retrieval request from IP: {client_ip}")
    
    username = request.args.get("username")
    if not username:
        logger.warning(f"Username missing from IP: {client_ip}")
        return jsonify({"message": "Username is required"}), 400
    
    try:
        with connect_mysql() as (cursor, connection):
            cursor.execute("SELECT user_id FROM users WHERE username = %s", (username,))
            result = cursor.fetchone()
            if not result:
                logger.info(f"User not found: {username} from IP: {client_ip}")
                return jsonify({"message": "User not found"}), 404
            user_id = result[0]
        
        with connect_mongo() as mongo_client:
            collection = mongo_client["users"]
            logger.debug(f"Querying MongoDB for history of user_id: {user_id} from IP: {client_ip}")
            out = collection.find_one({"user_id": user_id})
            if not out:
                logger.info(f"No history found for user_id: {user_id} from IP: {client_ip}")
                return jsonify({"message": "No history found"}), 404
            
            out["_id"] = str(out["_id"])
            for item in out.get("history", []):
                item["post_id"] = str(item["post_id"])
            for item in out.get("likes", []):
                item["post_id"] = str(item["post_id"])
            
            logger.info(f"Successfully retrieved history for user: {username} from IP: {client_ip}")
            return jsonify(out), 200
    except Exception as e:
        return handle_exception(e, logger, client_ip, "An error occurred while retrieving history")

@history_bp.route('/add_read_history', methods=['POST'])    
@auth_check
def add_read_history(user_id, username):
    '''Add a post to the user's history or update timestamp if already exists'''
    client_ip = request.remote_addr
    logger = current_app.logger
    logger.info(f"Add read history request from IP: {client_ip}")
    
    post_id = request.args.get("post_id")
    if not post_id:
        logger.warning(f"Post ID missing from IP: {client_ip}")
        return jsonify({"message": "Post ID is required"}), 400
    
    try:
        with connect_mongo() as mongo_client:
            collection = mongo_client["users"]
            posts_collection = mongo_client["posts"]
            
            existing_item = collection.find_one({"user_id": user_id, "history.post_id": post_id})
            now = datetime.now(timezone.utc)
            
            with redis_connection(db=1) as redis_client:
                read_key = f"post:{post_id}:reads"
                redis_client.incr(read_key)
                if redis_client.ttl(read_key) == -1:
                    redis_client.expire(read_key, 24 * 60 * 60)
            
            if existing_item:
                logger.debug(f"Updating timestamp for post {post_id} by user_id: {user_id}")
                collection.update_one(
                    {"user_id": user_id, "history.post_id": post_id},
                    {"$set": {"history.$.timestamp": now}}
                )
                logger.info(f"History timestamp updated for user: {username}, post: {post_id}")
                return jsonify({"message": "History timestamp updated"}), 200
            else:
                logger.debug(f"Adding new history for post {post_id} by user_id: {user_id}")
                collection.update_one(
                    {"user_id": user_id},
                    {"$push": {"history": {"post_id": post_id, "timestamp": now}}},
                    upsert=True
                )
                posts_collection.update_one(
                    {"_id": ObjectId(post_id)},
                    {"$inc": {"read_count": 1}},
                    upsert=True
                )
                logger.info(f"New history item added for user: {username}, post: {post_id}")
                return jsonify({"message": "History added"}), 200
    except Exception as e:
        return handle_exception(e, logger, client_ip, "An error occurred while updating read history")

@history_bp.route('/add_like', methods=['POST'])
@auth_check
def add_like(user_id, username):
    '''Add a like to a post or inform user if already liked'''
    client_ip = request.remote_addr
    logger = current_app.logger
    logger.info(f"Add like request from IP: {client_ip}")
    
    post_id = request.args.get("post_id")
    if not post_id:
        logger.warning(f"Post ID missing from IP: {client_ip}")
        return jsonify({"message": "Post ID is required"}), 400
    
    try:
        with connect_mongo() as mongo_client:
            collection = mongo_client["users"]
            posts_collection = mongo_client["posts"]
            
            existing_item = collection.find_one({"user_id": user_id, "likes.post_id": post_id})
            if existing_item:
                logger.info(f"Post {post_id} already liked by user: {username}")
                return jsonify({"message": "You've already liked this post", "already_liked": True}), 200
            
            now = datetime.now(timezone.utc)
            collection.update_one(
                {"user_id": user_id},
                {"$push": {"likes": {"post_id": post_id, "timestamp": now}}},
                upsert=True
            )
            posts_collection.update_one(
                {"_id": ObjectId(post_id)},
                {"$inc": {"like_count": 1}},
                upsert=True
            )
            logger.info(f"Like added for post {post_id} by user: {username}")
            return jsonify({"message": "Post liked successfully", "already_liked": False}), 200
    except Exception as e:
        return handle_exception(e, logger, client_ip, "An error occurred while liking the post")

@history_bp.route('/remove_like', methods=['DELETE'])
@auth_check
def remove_like(user_id, username):
    '''Remove a like from a post'''
    client_ip = request.remote_addr
    logger = current_app.logger
    logger.info(f"Remove like request from IP: {client_ip}")
    
    post_id = request.args.get("post_id")
    if not post_id:
        logger.warning(f"Post ID missing from IP: {client_ip}")
        return jsonify({"message": "Post ID is required"}), 400
    
    try:
        with connect_mongo() as mongo_client:
            collection = mongo_client["users"]
            post_collection = mongo_client["posts"]
            
            existing_item = collection.find_one({"user_id": user_id, "likes.post_id": post_id})
            if not existing_item:
                logger.info(f"Post {post_id} not liked by user: {username}")
                return jsonify({"message": "You haven't liked this post"}), 404
            
            result = collection.update_one(
                {"user_id": user_id},
                {"$pull": {"likes": {"post_id": post_id}}}
            )
            post_collection.update_one(
                {"_id": ObjectId(post_id)},
                {"$inc": {"like_count": -1}}
            )
            
            if result.modified_count > 0:
                logger.info(f"Like removed for post {post_id} by user: {username}")
                return jsonify({"message": "Like removed successfully"}), 200
            else:
                logger.warning(f"Failed to remove like for post {post_id} by user: {username}")
                return jsonify({"message": "Failed to remove like"}), 500
    except Exception as e:
        return handle_exception(e, logger, client_ip, "An error occurred while removing the like")