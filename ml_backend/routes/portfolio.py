import datetime
from flask import Blueprint, request, jsonify
from flask_cors import cross_origin
from database import db  # Ensure ki connection sahi file se import ho raha hai

portfolio_bp = Blueprint('portfolio_engine', __name__)

# ------------------------------------------------------------------
# 1. SAVE PORTFOLIO (Frontend se holdings aayega, DB mein portfolio banega)
# ------------------------------------------------------------------
@portfolio_bp.route('/portfolio/save', methods=['POST', 'OPTIONS'])
@cross_origin()
def save_portfolio():
    if request.method == "OPTIONS":
        return jsonify({"status": "CORS Preflight OK"}), 200

    try:
        data = request.get_json() or {}
        email = data.get('email', '').strip().lower()
        
        # 🎯 FIX: Frontend 'holdings' bhej raha hai, hum use pakad rahe hain
        stocks_array = data.get('holdings', [])

        if not email:
            return jsonify({"error": "Email is required to map portfolio"}), 400

        # MongoDB mein 'portfolio' field ke andar array set kar rahe hain (Jaisa image mein hai)
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
        print(f"--- SUCCESS: Portfolio Saved for {email} with {len(stocks_array)} stocks ---")
        return jsonify({"status": "success", "message": "Portfolio database synced successfully"}), 200

    except Exception as e:
        print(f"--- ERROR IN SAVE: {str(e)} ---")
        return jsonify({"error": f"Internal Database Error: {str(e)}"}), 500


# ------------------------------------------------------------------
# 2. GET PORTFOLIO (DB se portfolio nikalega, Frontend ko holdings dega)
# ------------------------------------------------------------------
@portfolio_bp.route('/portfolio/get', methods=['GET'])
@cross_origin()
def get_portfolio():
    try:
        # Frontend URL query param se bhej raha hai: /portfolio/get?email=...
        email = request.args.get('email', '').strip().lower()

        if not email:
            return jsonify({"error": "Email parameter is missing"}), 400
        
        user_portfolio = db.portfolios.find_one({"user_email": email})
        
        # Agar user ka data nahi hai, toh frontend ko khali array return karo
        if not user_portfolio:
            return jsonify({"holdings": []}), 200
            
        # 🎯 FIX: Database se 'portfolio' uthaya par frontend ko 'holdings' ke naam se diya!
        saved_stocks = user_portfolio.get("portfolio", [])
        
        return jsonify({
            "user_email": email,
            "holdings": saved_stocks  # Frontend data.holdings ko check karta hai
        }), 200

    except Exception as e:
        print(f"--- ERROR IN GET: {str(e)} ---")
        return jsonify({"error": f"Failed to retrieve data: {str(e)}"}), 500