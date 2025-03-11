from flask import Blueprint, request, jsonify, current_app
from utils.db import connect_mysql, connect_mongo
from datetime import datetime
from bson.objectid import ObjectId
from contextlib import contextmanager

history_bp = Blueprint('history', __name__)




@history_bp.route('/history/<string:username>', methods=['GET'])
def get_history(username):
    pass