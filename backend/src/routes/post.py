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
    client_ip = request.remote_addr
    current_app.logger.info(f"Create post request from IP: {client_ip}")
    
    token = request.headers.get("Authorization")
    title = request.form.get("title", "").strip()  # Use form data instead of JSON
    content = request.form.get("content", "").strip()
    media_file = request.files.get("media_file")  # File from multipart/form-data

    if not token:
        current_app.logger.warning(f"Token missing for create_post request from IP: {client_ip}")
        return jsonify({"message": "Token is required"}), 400
    if not title or not content:
        current_app.logger.warning(f"Missing title or content in create_post request from IP: {client_ip}")
        return jsonify({"message": "Title and content are required and must not be empty"}), 400

    try:
        if token:
            token = token.split(" ")[1]
            payload = current_app.config['JWT'].check_token(token)
            username = payload.get("username", "unknown") if payload else "invalid"
            current_app.logger.debug(f"Token verification for user: {username} from IP: {client_ip}")
            if payload is None:
                current_app.logger.warning(f"Invalid token for create_post request from IP: {client_ip}")
                return jsonify({"message": "Invalid token"}), 401
        
        with connect_mysql() as (cursor, connection):
            current_app.logger.debug(f"Getting user_id for username: {payload.get('username')} from IP: {client_ip}")
            cursor.execute("SELECT user_id FROM users WHERE username = %s", (payload.get("username"),))
            result = cursor.fetchone()
            if not result:
                current_app.logger.warning(f"User {payload.get('username')} not found - create_post request from IP: {client_ip}")
                return jsonify({"message": "User not found"}), 404
            user_id = result[0]
            current_app.logger.debug(f"Found user_id: {user_id} for user: {payload.get('username')} from IP: {client_ip}")
        
        media_url = ""
        if media_file:
            # Upload to MinIO
            current_app.logger.debug(f"Uploading media file for user_id: {user_id} from IP: {client_ip}")
            with connect_Minio() as (connect_Minio_client, bucket_name, url):
                # Ensure bucket exists
                buckets = connect_Minio_client.list_buckets()  # Returns list of Bucket objects
                bucket_names = [b.name for b in buckets]  # Access 'name' attribute
                if not buckets or bucket_name not in bucket_names:
                    current_app.logger.debug(f"Creating new bucket: {bucket_name} from IP: {client_ip}")
                    connect_Minio_client.make_bucket(bucket_name)

                # Generate a unique object name
                filename = f"{user_id}_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}_{media_file.filename}"
                current_app.logger.debug(f"Uploading file: {filename} to MinIO from IP: {client_ip}")
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
                current_app.logger.debug(f"Media URL created: {media_url} from IP: {client_ip}")

        with connect_mongo() as mongo_client:
            db = mongo_client
            collection = db["posts"]
            current_app.logger.debug(f"Creating MongoDB post document for user_id: {user_id} from IP: {client_ip}")
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
            post_id = str(result.inserted_id)
            current_app.logger.info(f"Post created with ID: {post_id} by user_id: {user_id} from IP: {client_ip}")
            return jsonify({"message": "Post created", "post_id": post_id}), 200

    except Exception as e:
        error_details = traceback.format_exc()
        current_app.logger.error(f"Error creating post from IP {client_ip}: {str(e)}\n{error_details}")
        return jsonify({"message": "An error occurred while creating the post"}), 500
    
@post_bp.route("/get_posts", methods=["GET"])
def get_posts():
    '''Get a filtered, paginated list of posts'''
    client_ip = request.remote_addr
    current_app.logger.info(f"Get posts request from IP: {client_ip}")
    
    try:
        post_page = int(request.args.get("page", 1))  # Use request.args for GET query params
        post_per_page = int(request.args.get("per_page", 10))
        user_id = request.args.get("user_id")  # Filter by user
        search_term = request.args.get("search")  # Search in title or content
        
        current_app.logger.debug(f"Get posts parameters - page: {post_page}, per_page: {post_per_page}, user_id: {user_id}, search: {search_term} from IP: {client_ip}")
        
        if post_page < 1 or post_per_page < 1:
            current_app.logger.warning(f"Invalid pagination parameters from IP: {client_ip}")
            return jsonify({"message": "Page and per_page must be positive integers"}), 400
            
        # Build query filters
        query = {}
        
        if user_id:
            # Try to convert to int for user_id (if stored as int)
            try:
                user_id = int(user_id)
                current_app.logger.debug(f"Filtering posts by user_id: {user_id} from IP: {client_ip}")
            except ValueError:
                current_app.logger.warning(f"Invalid user_id format: {user_id} from IP: {client_ip}")
                pass
            query["user_id"] = user_id
            
        if search_term:
            # Text search in title and content
            current_app.logger.debug(f"Searching posts with term: {search_term} from IP: {client_ip}")
            query["$or"] = [
                {"title": {"$regex": search_term, "$options": "i"}},  # Case-insensitive search
                {"content": {"$regex": search_term, "$options": "i"}}
            ]

        with connect_mongo() as mongo_client:
            db = mongo_client
            collection = db["posts"]
            current_app.logger.debug(f"Querying MongoDB posts with pagination - page: {post_page}, per_page: {post_per_page} from IP: {client_ip}")
            posts = collection.find(query).sort("created_at", -1).skip((post_page - 1) * post_per_page).limit(post_per_page)
            posts_list = [dict(post, _id=str(post["_id"])) for post in posts]
            
            # Get filtered count
            total_posts = collection.count_documents(query)
            current_app.logger.debug(f"Found {total_posts} total posts matching query from IP: {client_ip}")
            
            current_app.logger.info(f"Successfully retrieved {len(posts_list)} posts from IP: {client_ip}")
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
        current_app.logger.warning(f"Invalid pagination parameters from IP: {client_ip}")
        return jsonify({"message": "Invalid page or per_page value"}), 400
    except Exception as e:
        # Log the full error with traceback
        error_details = traceback.format_exc()
        current_app.logger.error(f"Error retrieving posts from IP {client_ip}: {str(e)}\n{error_details}")
        return jsonify({"message": "An error occurred during post retrieval"}), 500

@post_bp.route("/get_post", methods=["GET"])
def get_post():
    '''Get a single post by post_id'''
    client_ip = request.remote_addr
    current_app.logger.info(f"Get post request from IP: {client_ip}")
    
    post_id = request.args.get("post_id")
    if not post_id:
        current_app.logger.warning(f"Post ID missing from get_post request from IP: {client_ip}")
        return jsonify({"message": "Post ID is required"}), 400

    try:
        current_app.logger.debug(f"Getting post with ID: {post_id} from IP: {client_ip}")
        with connect_mongo() as mongo_client:
            db = mongo_client
            collection = db["posts"]
            post = collection.find_one({"_id": ObjectId(post_id)})
            if not post:
                current_app.logger.info(f"Post not found with ID: {post_id} - request from IP: {client_ip}")
                return jsonify({"message": "Post not found"}), 404
            post["_id"] = str(post["_id"])  # Convert ObjectId to string
            current_app.logger.info(f"Post retrieved successfully with ID: {post_id} from IP: {client_ip}")
            return jsonify({"post": post}), 200
    except Exception as e:
        # Log the full error with traceback
        error_details = traceback.format_exc()
        current_app.logger.error(f"Error retrieving post from IP {client_ip}: {str(e)}\n{error_details}")
        return jsonify({"message": "An error occurred while retrieving the post"}), 500

@post_bp.route("/delete_post", methods=["DELETE"])
def delete_post():
    '''Delete a post by post_id'''
    client_ip = request.remote_addr
    current_app.logger.info(f"Delete post request from IP: {client_ip}")
    
    post_id = request.args.get("post_id")
    token = request.headers.get("Authorization")

    if not token:
        current_app.logger.warning(f"Token missing for delete_post request from IP: {client_ip}")
        return jsonify({"message": "Token is required"}), 400
    if not post_id:
        current_app.logger.warning(f"Post ID missing from delete_post request from IP: {client_ip}")
        return jsonify({"message": "Post ID is required"}), 400

    try:
        if token:
            token = token.split(" ")[1]
            payload = current_app.config['JWT'].check_token(token)
            username = payload.get("username", "unknown") if payload else "invalid"
            current_app.logger.debug(f"Token verification for user: {username} from IP: {client_ip}")
            if payload is None:
                current_app.logger.warning(f"Invalid token for delete_post request from IP: {client_ip}")
                return jsonify({"message": "Invalid token"}), 401
        
        with connect_mysql() as (cursor, connection):
            current_app.logger.debug(f"Getting user_id for username: {payload['username']} from IP: {client_ip}")
            cursor.execute("SELECT user_id FROM users WHERE username = %s", (payload["username"],))
            result = cursor.fetchone()
            if not result:
                current_app.logger.warning(f"User {payload['username']} not found - delete_post request from IP: {client_ip}")
                return jsonify({"message": "User not found"}), 404
            user_id = result[0]
            current_app.logger.debug(f"Found user_id: {user_id} for user: {payload['username']} from IP: {client_ip}")

        with connect_mongo() as mongo_client:
            db = mongo_client
            collection = db["posts"]
            current_app.logger.debug(f"Checking post ownership for ID: {post_id} and user_id: {user_id} from IP: {client_ip}")
            post = collection.find_one({"_id": ObjectId(post_id)})
            if not post:
                current_app.logger.info(f"Post not found with ID: {post_id} - delete request from IP: {client_ip}")
                return jsonify({"message": "Post not found"}), 404
            if post["user_id"] != user_id:
                current_app.logger.warning(f"Unauthorized delete attempt by user_id: {user_id} for post ID: {post_id} from IP: {client_ip}")
                return jsonify({"message": "Unauthorized"}), 403
            collection.delete_one({"_id": ObjectId(post_id)})
            current_app.logger.info(f"Post deleted with ID: {post_id} by user: {payload['username']} from IP: {client_ip}")
            return jsonify({"message": "Post deleted"}), 200
    except Exception as e:
        # Log the full error with traceback
        error_details = traceback.format_exc()
        current_app.logger.error(f"Error deleting post from IP {client_ip}: {str(e)}\n{error_details}")
        return jsonify({"message": "An error occurred while deleting the post"}), 500

@post_bp.route("/update_post", methods=["PUT"])
def update_post():
    '''Update a post by post_id with optional media file replacement'''
    client_ip = request.remote_addr
    current_app.logger.info(f"Update post request from IP: {client_ip}")
    
    post_id = request.args.get("post_id")
    token = request.headers.get("Authorization")
    title = request.form.get("title", "").strip()  # Use form data
    content = request.form.get("content", "").strip()
    media_file = request.files.get("media_file")  # New file to upload

    if not token:
        current_app.logger.warning(f"Token missing for update_post request from IP: {client_ip}")
        return jsonify({"message": "Token is required"}), 400
    if not post_id:
        current_app.logger.warning(f"Post ID missing from update_post request from IP: {client_ip}")
        return jsonify({"message": "Post ID is required"}), 400

    try:
        if token:
            token = token.split(" ")[1]
            payload = current_app.config['JWT'].check_token(token)
            username = payload.get("username", "unknown") if payload else "invalid"
            current_app.logger.debug(f"Token verification for user: {username} from IP: {client_ip}")
            if payload is None:
                current_app.logger.warning(f"Invalid token for update_post request from IP: {client_ip}")
                return jsonify({"message": "Invalid token"}), 401
        
        with connect_mysql() as (cursor, connection):
            current_app.logger.debug(f"Getting user_id for username: {payload['username']} from IP: {client_ip}")
            cursor.execute("SELECT user_id FROM users WHERE username = %s", (payload["username"],))
            result = cursor.fetchone()
            if not result:
                current_app.logger.warning(f"User {payload['username']} not found - update_post request from IP: {client_ip}")
                return jsonify({"message": "User not found"}), 404
            user_id = result[0]
            current_app.logger.debug(f"Found user_id: {user_id} for user: {payload['username']} from IP: {client_ip}")

        with connect_mongo() as mongo_client:
            db = mongo_client
            collection = db["posts"]
            current_app.logger.debug(f"Checking post ownership for ID: {post_id} and user_id: {user_id} from IP: {client_ip}")
            post = collection.find_one({"_id": ObjectId(post_id)})
            if not post:
                current_app.logger.info(f"Post not found with ID: {post_id} - update request from IP: {client_ip}")
                return jsonify({"message": "Post not found"}), 404
            if post["user_id"] != user_id:
                current_app.logger.warning(f"Unauthorized update attempt by user_id: {user_id} for post ID: {post_id} from IP: {client_ip}")
                return jsonify({"message": "Unauthorized"}), 403

            update_data = {}
            if title:
                update_data["title"] = title
            if content:
                update_data["content"] = content

            # Handle media file update
            if media_file:
                current_app.logger.debug(f"Updating media file for post ID: {post_id} by user_id: {user_id} from IP: {client_ip}")
                media_url = ""
                # Upload to MinIO
                with connect_Minio() as (connect_Minio_client, bucket_name, url):
                    # Ensure bucket exists
                    buckets = connect_Minio_client.list_buckets()  # Returns list of Bucket objects
                    bucket_names = [b.name for b in buckets]  # Access 'name' attribute
                    if not buckets or bucket_name not in bucket_names:
                        current_app.logger.debug(f"Creating new bucket: {bucket_name} from IP: {client_ip}")
                        connect_Minio_client.make_bucket(bucket_name)

                    # Generate a unique object name
                    filename = f"{user_id}_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}_{media_file.filename}"
                    current_app.logger.debug(f"Uploading new media file: {filename} to MinIO from IP: {client_ip}")
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
                    current_app.logger.debug(f"New media URL created: {media_url} from IP: {client_ip}")

                    # Update media_url with new connect_Minio URL
                    update_data["media_url"] = media_url

            if update_data:
                current_app.logger.debug(f"Updating post ID: {post_id} with data: {update_data.keys()} from IP: {client_ip}")
                collection.update_one({"_id": ObjectId(post_id)}, {"$set": update_data})
                current_app.logger.info(f"Post updated with ID: {post_id} by user: {payload['username']} from IP: {client_ip}")
                return jsonify({"message": "Post updated"}), 200
            else:
                current_app.logger.info(f"No changes provided for post ID: {post_id} from IP: {client_ip}")
                return jsonify({"message": "No changes provided"}), 400

    except Exception as e:
        error_details = traceback.format_exc()
        current_app.logger.error(f"Error updating post from IP {client_ip}: {str(e)}\n{error_details}")
        return jsonify({"message": "An error occurred while updating the post"}), 500

@post_bp.route("/create_comment", methods=["POST"])
def create_comment():
    '''Create a comment on a post'''
    client_ip = request.remote_addr
    current_app.logger.info(f"Create comment request from IP: {client_ip}")
    
    token = request.headers.get("Authorization")
    post_id = request.args.get("post_id")
    comment = request.form.get("comment", "").strip()

    if not token:
        current_app.logger.warning(f"Token missing for create_comment request from IP: {client_ip}")
        return jsonify({"message": "Token is required"}), 400
    if not post_id or not comment:
        current_app.logger.warning(f"Post ID or comment missing from request from IP: {client_ip}")
        return jsonify({"message": "Post ID and comment are required and must not be empty"}), 400

    try:
        if token:
            token = token.split(" ")[1]
            payload = current_app.config['JWT'].check_token(token)
            username = payload.get("username", "unknown") if payload else "invalid"
            current_app.logger.debug(f"Token verification for user: {username} from IP: {client_ip}")
            if payload is None:
                current_app.logger.warning(f"Invalid token for create_comment request from IP: {client_ip}")
                return jsonify({"message": "Invalid token"}), 401
        
        with connect_mysql() as (cursor, connection):
            current_app.logger.debug(f"Getting user_id for username: {payload['username']} from IP: {client_ip}")
            cursor.execute("SELECT user_id FROM users WHERE username = %s", (payload["username"],))
            result = cursor.fetchone()
            if not result:
                current_app.logger.warning(f"User {payload['username']} not found - create_comment request from IP: {client_ip}")
                return jsonify({"message": "User not found"}), 404
            user_id = result[0]
            current_app.logger.debug(f"Found user_id: {user_id} for user: {payload['username']} from IP: {client_ip}")

        with connect_mongo() as mongo_client:
            db = mongo_client
            collection = db["posts"]
            post_id_obj = ObjectId(post_id)
            current_app.logger.debug(f"Creating comment for post ID: {post_id} by user_id: {user_id} from IP: {client_ip}")
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
                current_app.logger.info(f"Post not found with ID: {post_id} - comment request from IP: {client_ip}")
                return jsonify({"message": "Post not found"}), 404
            current_app.logger.info(f"Comment created for post ID: {post_id} by user: {payload['username']} from IP: {client_ip}")
            return jsonify({"message": "Comment created"}), 200
    except Exception as e:
        # Log the full error with traceback
        error_details = traceback.format_exc()
        current_app.logger.error(f"Error creating comment from IP {client_ip}: {str(e)}\n{error_details}")
        return jsonify({"message": "An error occurred while creating the comment"}), 500
    
@post_bp.route("/most_read_today", methods=["GET"])
def most_read_today():
    '''Get the most read posts today from Redis'''
    client_ip = request.remote_addr
    current_app.logger.info(f"Most read posts request from IP: {client_ip}")
    
    try:
        with redis_connection(db=1) as redis_client:
            current_app.logger.debug(f"Querying Redis for most read posts from IP: {client_ip}")
            # Get all keys matching the pattern for post reads
            post_keys = redis_client.keys("post:*:reads")
            if not post_keys:
                current_app.logger.info(f"No posts read today - request from IP: {client_ip}")
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

