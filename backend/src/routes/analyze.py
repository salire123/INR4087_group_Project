from flask import Blueprint, request, jsonify, current_app, send_file
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from utils import *  # Assuming this includes connect_mongo
from contextlib import contextmanager
import traceback

# Import Matplotlib and related libraries
import matplotlib.pyplot as plt
from io import BytesIO

analyze_bp = Blueprint('analyze', __name__)

@analyze_bp.route("/analyze_eachday_post", methods=["GET"])
def analyze_eachday_post():
    try:
        client_ip = request.remote_addr
        current_app.logger.info(f"Analyze each day post request received from IP: {client_ip}")

        with connect_mongo() as mongo_client:
            # Create a db by userid
            db = mongo_client
            collection = db["posts"]
            
            # Count each day's posts
            current_app.logger.debug(f"Counting each day's posts")
            posts = collection.find()
            current_app.logger.debug(f"Posts found: {posts}")
            post_count = {}
            for post in posts:
                created_at = post["created_at"]
                created_at = created_at.strftime("%Y-%m-%d")
                if created_at in post_count:
                    post_count[created_at] += 1
                else:
                    post_count[created_at] = 1

            # Generate a Matplotlib plot
            dates = list(post_count.keys())
            counts = list(post_count.values())
            current_app.logger.debug(f"Generating plot for posts per day")
            plt.figure(figsize=(10, 6))
            plt.plot(dates, counts, marker='o', linestyle='-', color='b')
            plt.title("Posts Per Day")
            plt.xlabel("Date")
            plt.ylabel("Number of Posts")
            plt.xticks(rotation=45)
            plt.tight_layout()

            # Save the plot to a BytesIO buffer
            img_buffer = BytesIO()
            plt.savefig(img_buffer, format='png')
            img_buffer.seek(0)
            plt.close()  # Close the plot to free memory
            
            current_app.logger.info(f"Posts per day plot generated successfully")
            # Return the plot as an image response
            return send_file(img_buffer, mimetype='image/png')
        
    except Exception as e:
        # Log the full error with traceback
        error_details = traceback.format_exc()
        current_app.logger.error(f"Analyze each day post error for IP {client_ip}: {str(e)}\n{error_details}")
        return jsonify({"message": "An error occurred during analysis"}), 500
    
@analyze_bp.route("/top_ten_user_subscriber", methods=["GET"])
def top_ten_user_subscriber():
    try:
        client_ip = request.remote_addr
        current_app.logger.info(f"Top ten user subscriber request received from IP: {client_ip}")

        with connect_mongo() as mongo_client:
            db = mongo_client
            collection = db["users"]

            # Get the top 10 users with the most subscribers
            users = collection.find().sort("subscribers", -1).limit(10)
            current_app.logger.debug(f"Top ten users with most subscribers: {users}")
            top_users = []
            for user in users:
                top_users.append({
                    "username": user["username"],
                    "subscribers": len(user["subscribers"])
                })

            # Generate a Matplotlib plot
            current_app.logger.debug(f"Generating plot for top ten users with most subscribers")
            plt.figure(figsize=(10, 6))
            usernames = [user["username"] for user in top_users]
            subscribers = [user["subscribers"] for user in top_users]
            plt.bar(usernames, subscribers, color='b')
            plt.title("Top Ten Users with Most Subscribers")
            plt.xlabel("Username")
            plt.ylabel("Number of Subscribers")
            plt.xticks(rotation=45)
            plt.tight_layout()

            img_buffer = BytesIO()
            plt.savefig(img_buffer, format='png')
            img_buffer.seek(0)
            plt.close()
            current_app.logger.info(f"Top ten users with most subscribers plot generated successfully")
            return send_file(img_buffer, mimetype='image/png')
            
    except Exception as e:
        # Log the full error with traceback
        error_details = traceback.format_exc()
        current_app.logger.error(f"Top ten user subscriber error for IP {client_ip}: {str(e)}\n{error_details}")
        return jsonify({"message": "An error occurred during analysis"}), 500

