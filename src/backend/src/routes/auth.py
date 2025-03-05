from flask import Blueprint, request, jsonify
from database.db import create_db_connection
from models.user import User
import logging

auth_bp = Blueprint('auth', __name__)
logger = logging.getLogger('MyAppLogger')

@auth_bp.route("/login", methods=["POST"])
# for login, we need to check if the user exists in the database
def login():
    pass

@auth_bp.route("/register", methods=["POST"])
# for registration, we need to insert the user into the database
def register():
    pass

@auth_bp.route("/logout", methods=["POST"])
# for logout, we need to invalidate the token
def logout():
    pass

@auth_bp.route("/renew_token", methods=["POST"])
# for renewing the token, we need to check if the token is valid and renew it
def renew_token():
    pass