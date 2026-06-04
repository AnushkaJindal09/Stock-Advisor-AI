import datetime
from flask import Blueprint, request, jsonify, make_response
from flask_cors import cross_origin
from database import db

portfolio_bp = Blueprint('portfolio_engine', __name__)

# --- CORS HEADERS HELPER TO PASS PREFLIGHT CHECK ---
def add_cors_headers(response):
    response.headers.add("Access-Control-Allow-Origin", "http://localhost:5177")
    response.headers.add("Access-Control-Allow-Headers", "Content-Type,Authorization")
    response.headers.add("Access-Control-Allow-Methods", "GET,POST,OPTIONS")
    return response

# ------------------------------------------------------------------
# 1. SAVE PORTFOLIO (POST) -> Actual Route: /portfolio/save
# ------------------------------------------------------------------
@portfolio_bp.route('/save', methods=['POST', 'OPTIONS'])  # 🎯 FIX: Hataya '/portfolio' yahan se
@cross_origin(origins=["http://localhost:5177"], headers=["Content-Type", "Authorization"])
def save_portfolio():
    if request.method == "OPTIONS":
        response = make_response(jsonify({"status": "CORS Preflight OK"}), 200)
        return add_cors_headers(response)

    try:
        data = request.get_json() or {}
        email = data.get('email', '').strip().lower()
        stocks_array = data.get('holdings', [])

        if not email:
            res = make_response(jsonify({"error": "Email is required"}), 400)
            return add_cors_headers(res)

        # Database sync using portfolio key
        db.portfolios.update_one(
            {"user_email": email},
            {
                "$set": {
                    "portfolio": stocks_array,
                    "updated_at": datetime.datetime.utcnow()
                }
            },
            upsert=True
        )

        res = make_response(jsonify({"status": "success", "message": "Portfolio saved successfully"}), 200)
        return add_cors_headers(res)

    except Exception as e:
        res = make_response(jsonify({"error": str(e)}), 500)
        return add_cors_headers(res)


# ------------------------------------------------------------------
# 2. GET PORTFOLIO (GET) -> Actual Route: /portfolio/get
# ------------------------------------------------------------------
@portfolio_bp.route('/get', methods=['GET', 'OPTIONS'])  # 🎯 FIX: Hataya '/portfolio' yahan se
@cross_origin(origins=["http://localhost:5177"], headers=["Content-Type", "Authorization"])
def get_portfolio():
    if request.method == "OPTIONS":
        response = make_response(jsonify({"status": "CORS Preflight OK"}), 200)
        return add_cors_headers(response)

    try:
        email = request.args.get('email', '').strip().lower()

        if not email:
            res = make_response(jsonify({"error": "Email parameter missing"}), 400)
            return add_cors_headers(res)
        
        user_portfolio = db.portfolios.find_one({"user_email": email})
        
        if not user_portfolio:
            res = make_response(jsonify({"holdings": []}), 200)
            return add_cors_headers(res)
            
        saved_stocks = user_portfolio.get("portfolio", [])
        
        res = make_response(jsonify({
            "user_email": email,
            "holdings": saved_stocks
        }), 200)
        return add_cors_headers(res)

    except Exception as e:
        res = make_response(jsonify({"error": str(e)}), 500)
        return add_cors_headers(res)