from flask import Blueprint, request, jsonify, current_app
from datetime import datetime, timezone
from bson.objectid import ObjectId
from contextlib import contextmanager

from utils.db import connect_mysql, connect_mongo, connect_Minio, redis_connection
import traceback

post_bp = Blueprint('post', __name__)


@post_bp.route("/create_post", methods=["POST"])
def create_post():
    '''Create a new post with optional media file upload'''
    token = request.headers.get("Authorization")
    title = request.form.get("title", "").strip()  # Use form data instead of JSON
    content = request.form.get("content", "").strip()
    media_file = request.files.get("media_file")  # File from multipart/form-data

    if not token:
        return jsonify({"message": "Token is required"}), 400
    if not title or not content:
        return jsonify({"message": "Title and content are required and must not be empty"}), 400

    try:
        if token:
            token = token.split(" ")[1]
            payload = current_app.config['JWT'].check_token(token)
            print(payload)
            if payload is None:
                return jsonify({"message": "Invalid token"}), 401
        
        with connect_mysql() as (cursor, connection):
            cursor.execute("SELECT user_id FROM users WHERE username = %s", (payload.get("username"),))
            result = cursor.fetchone()
            if not result:
                return jsonify({"message": "User not found"}), 404
            user_id = result[0]
        
        media_url = ""
        if media_file:
            # Upload to MinIO
            with connect_Minio() as (connect_Minio_client, bucket_name, url):
                # Ensure bucket exists
                buckets = connect_Minio_client.list_buckets()  # Returns list of Bucket objects
                bucket_names = [b.name for b in buckets]  # Access 'name' attribute
                if not buckets or bucket_name not in bucket_names:
                    connect_Minio_client.make_bucket(bucket_name)

                # Generate a unique object name
                filename = f"{user_id}_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}_{media_file.filename}"
                # Use put_object for file stream
                media_file.stream.seek(0)  # Reset stream position to the beginning
                connect_Minio_client.put_object(
                    bucket_name,
                    filename,
                    media_file.stream,
                    length=-1,  # Let MinIO determine the size (requires streaming)
                    part_size=10*1024*1024  # 10MB part size for multipart upload
                )
                # Construct the MinIO URL
                media_url = f"{url}/{filename}"

        with connect_mongo() as mongo_client:
            db = mongo_client
            collection = db["posts"]
            post = {
                "title": title,
                "media_url": media_url,  # Store MinIO URL
                "content": content,
                "user_id": user_id,
                "comments": [],
                "comment_count": 0,
                "created_at": datetime.now(timezone.utc)
            }
            result = collection.insert_one(post)
            return jsonify({"message": "Post created", "post_id": str(result.inserted_id)}), 200

    except Exception as e:
        error_details = traceback.format_exc()
        current_app.logger.error(f"Error creating post: {str(e)}\n{error_details}")
        return jsonify({"message": "An error occurred while creating the post"}), 500
    
@post_bp.route("/get_posts", methods=["GET"])
def get_posts():
    '''Get a filtered, paginated list of posts'''
    try:
        post_page = int(request.args.get("page", 1))  # Use request.args for GET query params
        post_per_page = int(request.args.get("per_page", 10))
        user_id = request.args.get("user_id")  # Filter by user
        search_term = request.args.get("search")  # Search in title or content
        
        print(post_page, post_per_page, user_id, search_term)
        if post_page < 1 or post_per_page < 1:
            return jsonify({"message": "Page and per_page must be positive integers"}), 400
            
        # Build query filters
        query = {}
        
        if user_id:
            # Try to convert to int for user_id (if stored as int)
            try:
                user_id = int(user_id)
            except ValueError:
                pass
            query["user_id"] = user_id
            
        if search_term:
            # Text search in title and content
            query["$or"] = [
                {"title": {"$regex": search_term, "$options": "i"}},  # Case-insensitive search
                {"content": {"$regex": search_term, "$options": "i"}}
            ]

        with connect_mongo() as mongo_client:
            db = mongo_client
            collection = db["posts"]
            posts = collection.find(query).sort("created_at", -1).skip((post_page - 1) * post_per_page).limit(post_per_page)
            posts_list = [dict(post, _id=str(post["_id"])) for post in posts]
            
            # Get filtered count
            total_posts = collection.count_documents(query)
            
            return jsonify({
                "posts": posts_list,
                "pagination": {
                    "total": total_posts,
                    "page": post_page,
                    "per_page": post_per_page,
                    "pages": (total_posts + post_per_page - 1) // post_per_page  # Ceiling division
                }
            }), 200
    except ValueError:
        return jsonify({"message": "Invalid page or per_page value"}), 400
    except Exception as e:
        # Log the full error with traceback
        
        error_details = traceback.format_exc()
        current_app.logger.error(f"Login error: {str(e)}\n{error_details}")
        return jsonify({"message": "An error occurred during authentication"}), 500

@post_bp.route("/get_post", methods=["GET"])
def get_post():
    '''Get a single post by post_id'''
    post_id =  request.args.get("post_id")
    if not post_id:
        return jsonify({"message": "Post ID is required"}), 400

    try:
        with connect_mongo() as mongo_client:
            db = mongo_client
            collection = db["posts"]
            post = collection.find_one({"_id": ObjectId(post_id)})
            if not post:
                return jsonify({"message": "Post not found"}), 404
            post["_id"] = str(post["_id"])  # Convert ObjectId to string
            return jsonify({"post": post}), 200
    except Exception as e:
        # Log the full error with traceback
        
        error_details = traceback.format_exc()
        current_app.logger.error(f"Login error: {str(e)}\n{error_details}")
        return jsonify({"message": "An error occurred during authentication"}), 500

@post_bp.route("/delete_post", methods=["DELETE"])
def delete_post():
    '''Delete a post by post_id'''
    post_id =  request.args.get("post_id")
    token = request.headers.get("Authorization")

    if not token:
        return jsonify({"message": "Token is required"}), 400
    if not post_id:
        return jsonify({"message": "Post ID is required"}), 400

    try:
        if token:
            token = token.split(" ")[1]
            payload = current_app.config['JWT'].check_token(token)
            print(payload)
            if payload is None:
                return jsonify({"message": "Invalid token"}), 401
        
        with connect_mysql() as (cursor, connection):
            cursor.execute("SELECT user_id FROM users WHERE username = %s", (payload["username"],))
            result = cursor.fetchone()
            if not result:
                return jsonify({"message": "User not found"}), 404
            user_id = result[0]

        with connect_mongo() as mongo_client:
            db = mongo_client
            collection = db["posts"]
            post = collection.find_one({"_id": ObjectId(post_id)})
            if not post:
                return jsonify({"message": "Post not found"}), 404
            if post["user_id"] != user_id:
                return jsonify({"message": "Unauthorized"}), 403
            collection.delete_one({"_id": ObjectId(post_id)})
            return jsonify({"message": "Post deleted"}), 200
    except Exception as e:
        # Log the full error with traceback
        
        error_details = traceback.format_exc()
        current_app.logger.error(f"Login error: {str(e)}\n{error_details}")
        return jsonify({"message": "An error occurred during authentication"}), 500

@post_bp.route("/update_post", methods=["PUT"])
def update_post():
    '''Update a post by post_id with optional media file replacement'''
    post_id =  request.args.get("post_id")
    token = request.headers.get("Authorization")
    title = request.form.get("title", "").strip()  # Use form data
    content = request.form.get("content", "").strip()
    media_file = request.files.get("media_file")  # New file to upload

    if not token:
        return jsonify({"message": "Token is required"}), 400
    if not post_id:
        return jsonify({"message": "Post ID is required"}), 400

    try:
        if token:
            token = token.split(" ")[1]
            payload = current_app.config['JWT'].check_token(token)
            print(payload)
            if payload is None:
                return jsonify({"message": "Invalid token"}), 401
        
        with connect_mysql() as (cursor, connection):
            cursor.execute("SELECT user_id FROM users WHERE username = %s", (payload["username"],))
            result = cursor.fetchone()
            if not result:
                return jsonify({"message": "User not found"}), 404
            user_id = result[0]

        with connect_mongo() as mongo_client:
            db = mongo_client
            collection = db["posts"]
            post = collection.find_one({"_id": ObjectId(post_id)})
            if not post:
                return jsonify({"message": "Post not found"}), 404
            if post["user_id"] != user_id:
                return jsonify({"message": "Unauthorized"}), 403

            update_data = {}
            if title:
                update_data["title"] = title
            if content:
                update_data["content"] = content

            # Handle media file update
            if media_file:
                media_url = ""
                # Upload to MinIO
                with connect_Minio() as (connect_Minio_client, bucket_name, url):
                    # Ensure bucket exists
                    buckets = connect_Minio_client.list_buckets()  # Returns list of Bucket objects
                    bucket_names = [b.name for b in buckets]  # Access 'name' attribute
                    if not buckets or bucket_name not in bucket_names:
                        connect_Minio_client.make_bucket(bucket_name)

                    # Generate a unique object name
                    filename = f"{user_id}_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}_{media_file.filename}"
                    # Use put_object for file stream
                    media_file.stream.seek(0)  # Reset stream position to the beginning
                    connect_Minio_client.put_object(
                        bucket_name,
                        filename,
                        media_file.stream,
                        length=-1,  # Let MinIO determine the size (requires streaming)
                        part_size=10*1024*1024  # 10MB part size for multipart upload
                    )
                    # Construct the MinIO URL
                    media_url = f"{url}/{filename}"

                    # Update media_url with new connect_Minio URL
                    update_data["media_url"] = media_url

            if update_data:
                collection.update_one({"_id": ObjectId(post_id)}, {"$set": update_data})
                return jsonify({"message": "Post updated"}), 200
            else:
                return jsonify({"message": "No changes provided"}), 400

    except Exception as e:
        error_details = traceback.format_exc()
        current_app.logger.error(f"Error updating post: {str(e)}\n{error_details}")
        return jsonify({"message": "An error occurred while updating the post"}), 500

@post_bp.route("/create_comment", methods=["POST"])
def create_comment():
    '''Create a comment on a post'''
    token = request.headers.get("Authorization")
    post_id = request.args.get("post_id")
    comment = request.form.get("comment", "").strip()

    if not token:
        return jsonify({"message": "Token is required"}), 400
    if not post_id or not comment:
        return jsonify({"message": "Post ID and comment are required and must not be empty"}), 400

    try:
        if token:
            token = token.split(" ")[1]
            payload = current_app.config['JWT'].check_token(token)
            print(payload)
            if payload is None:
                return jsonify({"message": "Invalid token"}), 401
        
        with connect_mysql() as (cursor, connection):
            cursor.execute("SELECT user_id FROM users WHERE username = %s", (payload["username"],))
            result = cursor.fetchone()
            if not result:
                return jsonify({"message": "User not found"}), 404
            user_id = result[0]

        with connect_mongo() as mongo_client:
            db = mongo_client
            collection = db["posts"]
            post_id_obj = ObjectId(post_id)
            comment_obj = {
                "comment": comment,
                "user_id": user_id,
                "created_at": datetime.utcnow()
            }
            result = collection.update_one(
                {"_id": post_id_obj},
                {
                    "$push": {"comments": comment_obj},
                    "$inc": {"comment_count": 1}
                }
            )
            if result.matched_count == 0:
                return jsonify({"message": "Post not found"}), 404
            return jsonify({"message": "Comment created"}), 200
    except Exception as e:
        # Log the full error with traceback
        
        error_details = traceback.format_exc()
        current_app.logger.error(f"Login error: {str(e)}\n{error_details}")
        return jsonify({"message": "An error occurred during authentication"}), 500
    
@post_bp.route("/most_read_today", methods=["GET"])
def most_read_today():
    '''Get the most read posts today from Redis'''
    try:
        with redis_connection(db=1) as redis_client:
            # Get all keys matching the pattern for post reads
            post_keys = redis_client.keys("post:*:reads")
            if not post_keys:
                return jsonify({"message": "No posts read today", "top_posts": []}), 200

            # Get the read counts for all posts
            post_counts = {}
            for key in post_keys:
                post_id = key.split(":")[1]  # Extract post_id from "post:<post_id>:reads"
                count = int(redis_client.get(key))  # Get the count
                post_counts[post_id] = count

            # Sort posts by read count in descending order
            sorted_posts = sorted(post_counts.items(), key=lambda x: x[1], reverse=True)
            
            # Limit to top 10 (or adjust as needed)
            top_posts = [{"post_id": post_id, "read_count": count} for post_id, count in sorted_posts[:10]]

            return jsonify({"message": "Top posts retrieved", "top_posts": top_posts}), 200

    except Exception as e:
        error_details = traceback.format_exc()
        current_app.logger.error(f"Most read today error: {str(e)}\n{error_details}")
        return jsonify({"message": "An error occurred while retrieving most read posts"}), 500
    
