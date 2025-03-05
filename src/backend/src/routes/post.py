from flask import Blueprint, request, jsonify
from utils.db import create_mysql_connection, create_mongo_connection
post_bp = Blueprint('post', __name__)

@post_bp.route("/create_post", methods=["POST"])
def create_post():
    print("api call")
    # test connection
    mysql_connection = create_mysql_connection()
    print(mysql_connection)
    mongo_connection = create_mongo_connection()
    print(mongo_connection)
    return jsonify({"message": f"Post created test, {mysql_connection} {mongo_connection}"})



    
