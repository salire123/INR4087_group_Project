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
    client_ip = request.remote_addr
    current_app.logger.info(f"Analyze each day post request received from IP: {client_ip}")

    with connect_mongo() as mongo_client:
        # Create a db by userid
        db = mongo_client
        collection = db["posts"]
        
        # Count each day's posts
        posts = collection.find()
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

        # Return the plot as an image response
        return send_file(img_buffer, mimetype='image/png')