from flask import Blueprint, request, jsonify
import datetime
import jwt
import os
from database import users_collection
from flask_bcrypt import Bcrypt
from flask_cors import cross_origin

auth_bp = Blueprint('auth', __name__)
bcrypt = Bcrypt()

SECRET_KEY = os.getenv("JWT_SECRET_KEY", "FOUNDER_SECRET_KEY_2026")

# ── REGISTER ──
@auth_bp.route('/register', methods=['POST', 'OPTIONS'])
@cross_origin()
def signup():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400

        name     = data.get('name')
        email    = data.get('email')
        password = data.get('password')

        if not email or not password or not name:
            return jsonify({"error": "Name, Email and Password are required"}), 400

        existing_user = users_collection.find_one({"email": email})
        if existing_user:
            return jsonify({"error": "User already exists with this email"}), 400

        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

        new_user = {
            "name":       name,
            "email":      email,
            "password":   hashed_password,
            "portfolio":  [],
            "watchlist":  [],
            "created_at": datetime.datetime.utcnow()
        }

        users_collection.insert_one(new_user)
        return jsonify({"msg": "User registered successfully! 🚀"}), 201

    except Exception as e:
        return jsonify({"error": f"Internal Server Error: {str(e)}"}), 500


# ── LOGIN ──
@auth_bp.route('/login', methods=['POST', 'OPTIONS'])
@cross_origin()
def login():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400

        email    = data.get('email')
        password = data.get('password')

        user = users_collection.find_one({"email": email})

        if user and bcrypt.check_password_hash(user['password'], password):
            token = jwt.encode({
                'user_id': str(user['_id']),
                'email':   user['email'],
                'exp':     datetime.datetime.utcnow() + datetime.timedelta(hours=24)
            }, SECRET_KEY, algorithm="HS256")

            return jsonify({
                "msg":   "Login Success! Welcome back.",
                "token": token,
                "user":  {
                    "name":  user['name'],
                    "email": user['email']
                }
            }), 200

        return jsonify({"error": "Invalid email or password"}), 401

    except Exception as e:
        return jsonify({"error": f"Internal Server Error: {str(e)}"}), 500