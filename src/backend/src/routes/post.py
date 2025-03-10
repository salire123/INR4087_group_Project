from flask import Blueprint, request, jsonify, current_app
from utils.db import create_mysql_connection, create_mongo_connection


from contextlib import contextmanager


post_bp = Blueprint('post', __name__)

@contextmanager
def connect_mysql():
    connection = None
    cursor = None
    try:
        connection = create_mysql_connection()
        if connection.is_connected():
            cursor = connection.cursor()
            yield cursor, connection
    except Exception as e:
        if connection:
            connection.rollback()
        raise e
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

@contextmanager
def connect_mongo():
    mongo_client = None
    try:
        mongo_client = create_mongo_connection()
        yield mongo_client
    except Exception as e:
        raise e
    finally:
        mongo_client.close()



@post_bp.route("/create_post", methods=["POST"])
def create_post():
    data = request.get_json()
    token = request.headers.get("Authorization")
    title = data.get("title", "").strip()
    media_url = data.get("media_url", "").strip()
    content = data.get("content", "").strip()

    if not all([title, content]):
        return jsonify({"message": "Title and content are required"}), 400

    try:
        payload = current_app.config['JWT'].check_token(token)
        if payload is None or "username" not in payload:
            return jsonify({"message": "Invalid token"}), 401
        
        with connect_mysql() as (cursor, connection):
            cursor.execute("SELECT id FROM users WHERE username = %s", (payload["username"],))
            result = cursor.fetchone()
            if result is None:
                return jsonify({"message": "User not found"}), 404
            user_id = result[0]
        
        with connect_mongo() as mongo_client:
            db = mongo_client["posts_db"]
            collection = db["posts"]
            post = {
                "title": title,
                "media_url": media_url,
                "content": content,
                "user_id": user_id,
                "comments": []
            }
            result = collection.insert_one(post)
            return jsonify({"message": "Post created", "post_id": str(result.inserted_id)}), 200
    except Exception as e:
        return jsonify({"message": str(e)}), 500

@post_bp.route("/get_posts", methods=["GET"])
def get_posts():
    post_page = request.args.get("page", 1)
    post_per_page = request.args.get("per_page", 10)
    try:
        with connect_mongo() as mongo_client:
            db = mongo_client["db"]
            collection = db["posts"]
            posts = collection.find().skip((post_page - 1) * post_per_page).limit(post_per_page)
            return jsonify({"posts": list(posts)}), 200
    except Exception as e:
        return jsonify({"message": str(e)}), 500
    
@post_bp.route("/get_post", methods=["GET"])
def get_post():
    post_id = request.args.get("post_id")
    try:
        with connect_mongo() as mongo_client:
            db = mongo_client["db"]
            collection = db["posts"]
            post = collection.find_one({"post_id": post_id})
            if post is None:
                return jsonify({"message": "Post not found"}), 404
            return jsonify({"post": post}), 200
    except Exception as e:
        return jsonify({"message": str(e)}), 500


    


    
