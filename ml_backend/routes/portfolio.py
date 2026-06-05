import os
import datetime
from flask import Blueprint, request, jsonify, make_response
from flask_cors import cross_origin
from pymongo import MongoClient

# 1. PEHLA LAYER: Direct database.py se import karne ka try karega
from database import portfolio_collection, news_cache_collection

portfolio_bp = Blueprint('portfolio_engine', __name__)

# ==========================================================================================
# 🌐 PRODUCTION CORS HANDSHAKE (ALLOWING FRONTEND REQUESTS)
# ==========================================================================================
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")

def add_cors_headers(response):
    response.headers.add("Access-Control-Allow-Origin", FRONTEND_URL)
    response.headers.add("Access-Control-Allow-Headers", "Content-Type,Authorization")
    response.headers.add("Access-Control-Allow-Methods", "GET,POST,OPTIONS")
    return response

# ==========================================================================================
# 🛑 DOOSRA LAYER (TERA SETUP): FALLBACK EXPLICIT MONGO CONNECTION FOR EXTRA SAFETY
# ==========================================================================================
# Agar database.py se import mein koi dikkat aayi, toh yeh backup connection save karega!
try:
    MONGO_URI = os.getenv("MONGO_URI")
    backup_client = MongoClient(
        MONGO_URI,
        tls=True,
        tlsAllowInvalidCertificates=True,
        tlsAllowInvalidHostnames=True,
        serverSelectionTimeoutMS=30000,
        connectTimeoutMS=30000,
        socketTimeoutMS=30000
    )
    backup_db = backup_client["stock_advisor_ai"]
    
    # Safely assign collections (ya toh imported chalegi, ya fir backup direct connect karegi)
    p_col = portfolio_collection if portfolio_collection is not None else backup_db["portfolios"]
    n_col = news_cache_collection if news_cache_collection is not None else backup_db["news_cache"]
except Exception as db_err:
    # Safe error catching agar env local pe runtime issues de
    print(f"Database Fallback Layer Error: {str(db_err)}")
    p_col = portfolio_collection
    n_col = news_cache_collection

# ==========================================================================================
# 📰 ASLI AI NEWS INTEGRATION (Using Protected Connection)
# ==========================================================================================
def get_live_ai_news_sentiment(symbol):
    try:
        # Protected collection variable use ho raha hai ab yahan
        cached_news = n_col.find_one({"symbol": symbol.upper()})
        if cached_news and "sentiment" in cached_news:
            return cached_news["sentiment"].lower()
        return "neutral"
    except Exception:
        return "neutral"

# ------------------------------------------------------------------
# 1. SAVE PORTFOLIO (POST)
# ------------------------------------------------------------------
@portfolio_bp.route('/save', methods=['POST', 'OPTIONS'])
@cross_origin(origins=[FRONTEND_URL], headers=["Content-Type", "Authorization"])
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

        # 🔥 Using Protected Safety Connection for Save Operations
        p_col.update_one(
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
# 2. GET PORTFOLIO (GET)
# ------------------------------------------------------------------
@portfolio_bp.route('/get', methods=['GET', 'OPTIONS'])
@cross_origin(origins=[FRONTEND_URL], headers=["Content-Type", "Authorization"])
def get_portfolio():
    if request.method == "OPTIONS":
        response = make_response(jsonify({"status": "CORS Preflight OK"}), 200)
        return add_cors_headers(response)

    try:
        email = request.args.get('email', '').strip().lower()

        if not email:
            res = make_response(jsonify({"error": "Email parameter missing"}), 400)
            return add_cors_headers(res)
        
        # 🔥 Using Protected Safety Connection for Fetch Operations
        user_portfolio = p_col.find_one({"user_email": email})
        
        if not user_portfolio:
            res = make_response(jsonify({"holdings": []}), 200)
            return add_cors_headers(res)
            
        saved_stocks = user_portfolio.get("portfolio", [])
        
        enriched_holdings = []
        for stock in saved_stocks:
            symbol = stock.get("symbol")
            if symbol:
                live_sentiment = get_live_ai_news_sentiment(symbol)
                stock["newsSentiment"] = live_sentiment 
            enriched_holdings.append(stock)
        
        res = make_response(jsonify({
            "user_email": email,
            "holdings": enriched_holdings
        }), 200)
        return add_cors_headers(res)

    except Exception as e:
        res = make_response(jsonify({"error": str(e)}), 500)
        return add_cors_headers(res)