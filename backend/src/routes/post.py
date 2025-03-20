from flask import Blueprint, request, jsonify, current_app
from datetime import datetime, timezone
from bson.objectid import ObjectId
from contextlib import contextmanager
from functools import wraps
from .history import add_read_history
from utils.db import connect_mysql, connect_mongo, connect_Minio, redis_connection
import traceback

post_bp = Blueprint('post', __name__)

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
            return jsonify({"message": "Token is required"}), 400
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

@post_bp.route("/create_post", methods=["POST"])
@auth_check
def create_post(user_id, username):
    '''Create a new post with optional media file upload'''
    client_ip = request.remote_addr
    logger = current_app.logger
    logger.info(f"Create post request from IP: {client_ip}")
    
    title = request.form.get("title", "").strip()
    content = request.form.get("content", "").strip()
    media_file = request.files.get("media_file")
    
    if not title or not content:
        logger.warning(f"Missing title or content from IP: {client_ip}")
        return jsonify({"message": "Title and content are required and must not be empty"}), 400
    
    try:
        media_url = ""
        if media_file:
            with connect_Minio() as (minio_client, bucket_name, url):
                buckets = [b.name for b in minio_client.list_buckets()]
                if bucket_name not in buckets:
                    logger.debug(f"Creating new bucket: {bucket_name} from IP: {client_ip}")
                    minio_client.make_bucket(bucket_name)
                
                filename = f"{user_id}_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}_{media_file.filename}"
                logger.debug(f"Uploading file: {filename} to MinIO from IP: {client_ip}")
                media_file.stream.seek(0)
                minio_client.put_object(
                    bucket_name, filename, media_file.stream, length=-1, part_size=10*1024*1024
                )
                media_url = f"{url}/{filename}"
                logger.debug(f"Media URL created: {media_url} from IP: {client_ip}")
        
        with connect_mongo() as mongo_client:
            collection = mongo_client["posts"]
            post = {
                "title": title,
                "media_url": media_url,
                "content": content,
                "user_id": user_id,
                "comments": [],
                "comment_count": 0,
                "created_at": datetime.now(timezone.utc),
                "like_count": 0,
                "read_count": 0
            }
            result = collection.insert_one(post)
            post_id = str(result.inserted_id)
            logger.info(f"Post created with ID: {post_id} by user: {username} from IP: {client_ip}")
            return jsonify({"message": "Post created", "post_id": post_id}), 200
    except Exception as e:
        return handle_exception(e, logger, client_ip, "An error occurred while creating the post")

@post_bp.route("/get_posts", methods=["GET"])
def get_posts():
    '''Get a filtered, paginated list of posts'''
    client_ip = request.remote_addr
    logger = current_app.logger
    logger.info(f"Get posts request from IP: {client_ip}")
    
    try:
        post_page = int(request.args.get("page", 1))
        post_per_page = int(request.args.get("per_page", 10))
        user_id = request.args.get("user_id")
        search_term = request.args.get("search")
        
        if post_page < 1 or post_per_page < 1:
            logger.warning(f"Invalid pagination parameters from IP: {client_ip}")
            return jsonify({"message": "Page and per_page must be positive integers"}), 400
        
        query = {}
        if user_id:
            try:
                user_id = int(user_id)
                logger.debug(f"Filtering posts by user_id: {user_id} from IP: {client_ip}")
                query["user_id"] = user_id
            except ValueError:
                logger.warning(f"Invalid user_id format: {user_id} from IP: {client_ip}")
        
        if search_term:
            logger.debug(f"Searching posts with term: {search_term} from IP: {client_ip}")
            query["$or"] = [
                {"title": {"$regex": search_term, "$options": "i"}},
                {"content": {"$regex": search_term, "$options": "i"}}
            ]
        
        with connect_mongo() as mongo_client:
            collection = mongo_client["posts"]
            posts = collection.find(query).sort("created_at", -1).skip((post_page - 1) * post_per_page).limit(post_per_page)
            posts_list = [dict(post, _id=str(post["_id"])) for post in posts]
            total_posts = collection.count_documents(query)
            
            logger.info(f"Successfully retrieved {len(posts_list)} posts from IP: {client_ip}")
            return jsonify({
                "posts": posts_list,
                "pagination": {
                    "total": total_posts,
                    "page": post_page,
                    "per_page": post_per_page,
                    "pages": (total_posts + post_per_page - 1) // post_per_page
                }
            }), 200
    except ValueError:
        logger.warning(f"Invalid pagination parameters from IP: {client_ip}")
        return jsonify({"message": "Invalid page or per_page value"}), 400
    except Exception as e:
        return handle_exception(e, logger, client_ip, "An error occurred during post retrieval")

@post_bp.route("/get_post", methods=["GET"])
def get_post():
    '''Get a single post by post_id'''
    client_ip = request.remote_addr
    logger = current_app.logger
    logger.info(f"Get post request from IP: {client_ip}")
    
    post_id = request.args.get("post_id")
    if not post_id:
        logger.warning(f"Post ID missing from IP: {client_ip}")
        return jsonify({"message": "Post ID is required"}), 400
    
    try:
        with connect_mongo() as mongo_client:
            collection = mongo_client["posts"]
            post = collection.find_one({"_id": ObjectId(post_id)})
            if not post:
                logger.info(f"Post not found with ID: {post_id} from IP: {client_ip}")
                return jsonify({"message": "Post not found"}), 404
            post["_id"] = str(post["_id"])
            logger.info(f"Post retrieved successfully with ID: {post_id} from IP: {client_ip}")
            return jsonify({"post": post}), 200
    except Exception as e:
        return handle_exception(e, logger, client_ip, "An error occurred while retrieving the post")

@post_bp.route("/delete_post", methods=["DELETE"])
@auth_check
def delete_post(user_id, username):
    '''Delete a post by post_id'''
    client_ip = request.remote_addr
    logger = current_app.logger
    logger.info(f"Delete post request from IP: {client_ip}")
    
    post_id = request.args.get("post_id")
    if not post_id:
        logger.warning(f"Post ID missing from IP: {client_ip}")
        return jsonify({"message": "Post ID is required"}), 400
    
    try:
        with connect_mongo() as mongo_client:
            collection = mongo_client["posts"]
            post = collection.find_one({"_id": ObjectId(post_id)})
            if not post:
                logger.info(f"Post not found with ID: {post_id} from IP: {client_ip}")
                return jsonify({"message": "Post not found"}), 404
            if post["user_id"] != user_id:
                logger.warning(f"Unauthorized delete attempt by user_id: {user_id} for post ID: {post_id}")
                return jsonify({"message": "Unauthorized"}), 403
            collection.delete_one({"_id": ObjectId(post_id)})
            logger.info(f"Post deleted with ID: {post_id} by user: {username} from IP: {client_ip}")
            return jsonify({"message": "Post deleted"}), 200
    except Exception as e:
        return handle_exception(e, logger, client_ip, "An error occurred while deleting the post")

@post_bp.route("/update_post", methods=["PUT"])
@auth_check
def update_post(user_id, username):
    '''Update a post by post_id with optional media file replacement'''
    client_ip = request.remote_addr
    logger = current_app.logger
    logger.info(f"Update post request from IP: {client_ip}")
    
    post_id = request.args.get("post_id")
    title = request.form.get("title", "").strip()
    content = request.form.get("content", "").strip()
    media_file = request.files.get("media_file")
    
    if not post_id:
        logger.warning(f"Post ID missing from IP: {client_ip}")
        return jsonify({"message": "Post ID is required"}), 400
    
    try:
        with connect_mongo() as mongo_client:
            collection = mongo_client["posts"]
            post = collection.find_one({"_id": ObjectId(post_id)})
            if not post:
                logger.info(f"Post not found with ID: {post_id} from IP: {client_ip}")
                return jsonify({"message": "Post not found"}), 404
            if post["user_id"] != user_id:
                logger.warning(f"Unauthorized update attempt by user_id: {user_id} for post ID: {post_id}")
                return jsonify({"message": "Unauthorized"}), 403
            
            update_data = {}
            if title:
                update_data["title"] = title
            if content:
                update_data["content"] = content
            
            if media_file:
                with connect_Minio() as (minio_client, bucket_name, url):
                    buckets = [b.name for b in minio_client.list_buckets()]
                    if bucket_name not in buckets:
                        logger.debug(f"Creating new bucket: {bucket_name} from IP: {client_ip}")
                        minio_client.make_bucket(bucket_name)
                    
                    filename = f"{user_id}_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}_{media_file.filename}"
                    logger.debug(f"Uploading new media file: {filename} to MinIO from IP: {client_ip}")
                    media_file.stream.seek(0)
                    minio_client.put_object(
                        bucket_name, filename, media_file.stream, length=-1, part_size=10*1024*1024
                    )
                    update_data["media_url"] = f"{url}/{filename}"
                    logger.debug(f"New media URL created: {update_data['media_url']} from IP: {client_ip}")
            
            if update_data:
                collection.update_one({"_id": ObjectId(post_id)}, {"$set": update_data})
                logger.info(f"Post updated with ID: {post_id} by user: {username} from IP: {client_ip}")
                return jsonify({"message": "Post updated"}), 200
            else:
                logger.info(f"No changes provided for post ID: {post_id} from IP: {client_ip}")
                return jsonify({"message": "No changes provided"}), 400
    except Exception as e:
        return handle_exception(e, logger, client_ip, "An error occurred while updating the post")

@post_bp.route("/create_comment", methods=["POST"])
@auth_check
def create_comment(user_id, username):
    '''Create a comment on a post'''
    client_ip = request.remote_addr
    logger = current_app.logger
    logger.info(f"Create comment request from IP: {client_ip}")
    
    post_id = request.args.get("post_id")
    comment = request.form.get("comment", "").strip()
    
    if not post_id or not comment:
        logger.warning(f"Post ID or comment missing from IP: {client_ip}")
        return jsonify({"message": "Post ID and comment are required and must not be empty"}), 400
    
    try:
        with connect_mongo() as mongo_client:
            collection = mongo_client["posts"]
            comment_obj = {
                "comment": comment,
                "user_id": user_id,
                "created_at": datetime.now(timezone.utc)
            }
            result = collection.update_one(
                {"_id": ObjectId(post_id)},
                {"$push": {"comments": comment_obj}, "$inc": {"comment_count": 1}}
            )
            if result.matched_count == 0:
                logger.info(f"Post not found with ID: {post_id} from IP: {client_ip}")
                return jsonify({"message": "Post not found"}), 404
            logger.info(f"Comment created for post ID: {post_id} by user: {username} from IP: {client_ip}")
            return jsonify({"message": "Comment created"}), 200
    except Exception as e:
        return handle_exception(e, logger, client_ip, "An error occurred while creating the comment")

@post_bp.route("/most_read_today", methods=["GET"])
def most_read_today():
    '''Get the most read posts today from Redis'''
    client_ip = request.remote_addr
    logger = current_app.logger
    logger.info(f"Most read posts request from IP: {client_ip}")
    
    try:
        with redis_connection(db=1) as redis_client:
            post_keys = redis_client.keys("post:*:reads")
            if not post_keys:
                logger.info(f"No posts read today from IP: {client_ip}")
                return jsonify({"message": "No posts read today", "top_posts": []}), 200
            
            post_counts = {key.split(":")[1]: int(redis_client.get(key)) for key in post_keys}
            sorted_posts = sorted(post_counts.items(), key=lambda x: x[1], reverse=True)
            top_posts = [{"post_id": post_id, "read_count": count} for post_id, count in sorted_posts[:10]]
            
            logger.info(f"Top posts retrieved from IP: {client_ip}")
            return jsonify({"message": "Top posts retrieved", "top_posts": top_posts}), 200
    except Exception as e:
        return handle_exception(e, logger, client_ip, "An error occurred while retrieving most read posts")