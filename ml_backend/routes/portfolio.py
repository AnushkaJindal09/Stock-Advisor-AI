from flask import Blueprint, request, jsonify
from database import portfolio_collection
import datetime

portfolio_bp = Blueprint('portfolio', __name__)

@portfolio_bp.route('/add', methods=['POST'])
def add_to_portfolio():
    try:
        data = request.get_json()
        # Abhi hum manually user_id bhej rahe hain, baad mein token se nikalenge
        user_email = data.get('email') 
        stock_ticker = data.get('ticker')
        quantity = data.get('quantity')
        avg_price = data.get('avg_price')

        if not user_email or not stock_ticker:
            return jsonify({"error": "Missing data"}), 400

        new_entry = {
            "user_email": user_email,
            "ticker": stock_ticker,
            "quantity": quantity,
            "avg_price": avg_price,
            "added_at": datetime.datetime.utcnow()
        }

        portfolio_collection.insert_one(new_entry)
        return jsonify({"msg": f"{stock_ticker} added to your portfolio! 📈"}), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500