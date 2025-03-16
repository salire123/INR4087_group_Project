from flask import Blueprint, request, jsonify, current_app
from datetime import datetime
from bson.objectid import ObjectId
from contextlib import contextmanager

from utils.db import connect_mysql, connect_mongo

post_bp = Blueprint('post', __name__)


@post_bp.route("/create_post", methods=["POST"])
def create_post():
    '''Create a new post'''
    data = request.get_json()
    token = request.headers.get("Authorization")
    title = data.get("title", "").strip()
    media_url = data.get("media_url", "").strip()
    content = data.get("content", "").strip()

    if not token:
        return jsonify({"message": "Token is required"}), 400
    if not title or not content:
        return jsonify({"message": "Title and content are required and must not be empty"}), 400

    try:
        payload = current_app.config['JWT'].check_token(token)
        if payload is None or "username" not in payload:
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
            post = {
                "title": title,
                "media_url": media_url,
                "content": content,
                "user_id": user_id,
                "comments": [],
                "comment_count": 0,  # Initialize comment count
                "created_at": datetime.utcnow()
            }
            result = collection.insert_one(post)
            return jsonify({"message": "Post created", "post_id": str(result.inserted_id)}), 200
    except Exception as e:
        return jsonify({"message": str(e)}), 500

@post_bp.route("/get_posts", methods=["GET"])
def get_posts():
    '''Get a filtered, paginated list of posts'''
    try:
        post_page = int(request.args.get("page", 1))
        post_per_page = int(request.args.get("per_page", 10))
        user_id = request.args.get("user_id")  # Filter by user
        search_term = request.args.get("search")  # Search in title or content
        
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
        return jsonify({"message": str(e)}), 500

@post_bp.route("/get_post", methods=["GET"])
def get_post():
    '''Get a single post by post_id'''
    post_id = request.args.get("post_id")
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
        return jsonify({"message": str(e)}), 500

@post_bp.route("/delete_post", methods=["DELETE"])
def delete_post():
    '''Delete a post by post_id'''
    post_id = request.args.get("post_id")
    token = request.headers.get("Authorization")

    if not token:
        return jsonify({"message": "Token is required"}), 400
    if not post_id:
        return jsonify({"message": "Post ID is required"}), 400

    try:
        payload = current_app.config['JWT'].check_token(token)
        if payload is None or "username" not in payload:
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
        return jsonify({"message": str(e)}), 500

@post_bp.route("/update_post", methods=["PUT"])
def update_post():
    '''Update a post by post_id'''
    post_id = request.args.get("post_id")
    token = request.headers.get("Authorization")
    data = request.get_json()
    title = data.get("title", "").strip()
    media_url = data.get("media_url", "").strip()
    content = data.get("content", "").strip()

    if not token:
        return jsonify({"message": "Token is required"}), 400
    if not post_id:
        return jsonify({"message": "Post ID is required"}), 400

    try:
        payload = current_app.config['JWT'].check_token(token)
        if payload is None or "username" not in payload:
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
            if media_url:
                update_data["media_url"] = media_url
            if content:
                update_data["content"] = content
            collection.update_one({"_id": ObjectId(post_id)}, {"$set": update_data})
            return jsonify({"message": "Post updated"}), 200
    except Exception as e:
        return jsonify({"message": str(e)}), 500

@post_bp.route("/create_comment", methods=["POST"])
def create_comment():
    '''Create a comment on a post'''
    data = request.get_json()
    token = request.headers.get("Authorization")
    post_id = data.get("post_id")
    comment = data.get("comment", "").strip()

    if not token:
        return jsonify({"message": "Token is required"}), 400
    if not post_id or not comment:
        return jsonify({"message": "Post ID and comment are required and must not be empty"}), 400

    try:
        payload = current_app.config['JWT'].check_token(token)
        if payload is None or "username" not in payload:
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
        return jsonify({"message": str(e)}), 500
    
@post_bp.route("/<string:post_id>/like", methods=["GET"])
def like_post(post_id):
    '''create a like on user history'''
