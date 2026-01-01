from flask import Flask, request, jsonify
from tensorflow.keras.models import load_model
import numpy as np
import joblib, traceback
from flask_cors import CORS
import requests, re
import datetime
from dotenv import load_dotenv
import os

load_dotenv()
app = Flask(__name__)
CORS(app)

# ---------- API KEYS ----------
NEWS_API_KEY = os.getenv("NEWS_API_KEY")
FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY")

# ---------- Companies ----------
tickers = [
    'RELIANCE.NS','HDFCBANK.NS','ICICIBANK.NS','INFY.NS','TCS.NS',
    'HINDUNILVR.NS','LT.NS','BHARTIARTL.NS','ADANIENT.NS','ADANIPORTS.NS',
    'TATAMOTORS.NS','MARUTI.NS','BAJFINANCE.NS','SBIN.NS','COALINDIA.NS'
]

company_names = [
    'ADANIENT.NS','ADANIPORTS.NS','BAJFINANCE.NS','BHARTIARTL.NS','COALINDIA.NS',
    'HDFCBANK.NS','HINDUNILVR.NS','ICICIBANK.NS','INFY.NS','LT.NS',
    'MARUTI.NS','RELIANCE.NS','SBIN.NS','TATAMOTORS.NS','TCS.NS'
]

# ---------- Prediction Route ----------
@app.route("/predict", methods=["POST"])
def predict():
    try:
        model = load_model("companies_stock.h5", compile=False)
        y_scaler = joblib.load('y_scaler.save')
        last_n_days = np.load("last_20_days.npy")

        features = np.expand_dims(last_n_days, axis=0)
        pred_scaled = model.predict(features)
        pred_actual = y_scaler.inverse_transform(pred_scaled)

        result = [
            {"company": name, "predicted_price": round(float(pred_actual[0][i]), 2)}
            for i, name in enumerate(company_names)
        ]
        return jsonify({"prediction": result})

    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


# ---------- News Route (Finnhub) ----------
@app.route("/news", methods=["GET"])
def get_news():
    try:
        company = request.args.get("company", "")
        if not company:
            return jsonify({"articles": []})

        # Ensure valid symbol
        symbol = company.upper()
        if not symbol.endswith(".NS"):
            symbol += ".NS"

        today = datetime.date.today()
        week_ago = today - datetime.timedelta(days=7)

        url = "https://finnhub.io/api/v1/company-news"
        params = {
            "symbol": symbol,
            "from": week_ago.isoformat(),
            "to": today.isoformat(),
            "token": FINNHUB_API_KEY
        }

        res = requests.get(url, params=params)
        data = res.json()

        if not isinstance(data, list):
            return jsonify({"articles": []})

        return jsonify({"articles": data[:5]})

    except Exception as e:
        traceback.print_exc()
        return jsonify({"articles": [], "error": str(e)})


# ---------- Chat Route ----------
@app.route("/chat", methods=["POST"])
def chat():
    try:
        data = request.json
        user_input = data.get("message", "").lower()

        # ✅ Prediction query
        if any(word in user_input for word in ["predict", "forecast", "price", "kal ka", "tomorrow"]):
            with app.test_request_context('/predict', method='POST'):
                response = predict()
            prediction_data = response.get_json()

            for c in tickers:
                if c.lower().replace(".ns", "") in user_input:
                    for p in prediction_data["prediction"]:
                        if p["company"].lower() == c.lower():
                            return jsonify({"reply": f"{c} ka predicted price hai {p['predicted_price']}"})
            return jsonify({"reply": str(prediction_data["prediction"])})

        # ✅ News query
        if "news" in user_input:
            company = None
            for c in tickers:
                if c.lower().replace(".ns", "") in user_input:
                    company = c
                    break

            if not company:
                company = "RELIANCE.NS"  # fallback default

            with app.test_request_context(f'/news?company={company}', method='GET'):
                response = get_news()
            news_data = response.get_json()

            articles = news_data.get("articles", [])
            if not articles:
                return jsonify({"reply": f"No news found for {company}"})

            news_summary = "\n".join([f"{i+1}. {a['headline']}" for i,a in enumerate(articles) if "headline" in a])
            return jsonify({"reply": f"📰 Latest news about {company}:\n{news_summary}"})

        return jsonify({"reply": "Mujhe samajh nahi aaya. Prediction ya news poochho."})

    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True)
