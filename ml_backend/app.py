from flask import Flask, request, jsonify
import numpy as np
import joblib, traceback
from flask_cors import CORS
import requests
import datetime
from dotenv import load_dotenv
import os
import yfinance as yf
from nsetools import Nse

load_dotenv()
app = Flask(__name__)
CORS(app)

# ---------- HOME ----------
@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "status": "Backend is running 🚀",
        "routes": ["/predict (POST)", "/stock", "/news"]
    })

# ---------- CONFIG ----------
HF_API_URL = "https://anushka09092004-stock-ml-api.hf.space/predict"

# ---------- CACHE ----------
prediction_cache = {"data": None, "date": None}

def is_cache_valid():
    return prediction_cache["date"] == datetime.date.today().isoformat()

# ---------- TICKERS ----------
SORTED_TICKERS = [
    'ADANIENT.NS','ADANIPORTS.NS','BAJFINANCE.NS','BHARTIARTL.NS','COALINDIA.NS',
    'HDFCBANK.NS','HINDUNILVR.NS','ICICIBANK.NS','INFY.NS','LT.NS',
    'MARUTI.NS','RELIANCE.NS','SBIN.NS','TCS.NS'
]

# ---------- FETCH DATA ----------
def fetch_all_ohlcv():
    try:
        data = yf.download(SORTED_TICKERS, period="6mo", progress=False, auto_adjust=True)

        if data.empty:
            return None

        result = {}

        for ticker in SORTED_TICKERS:
            try:
                result[ticker] = {
                    "high": data['High'][ticker].dropna().tail(20).tolist(),
                    "low": data['Low'][ticker].dropna().tail(20).tolist(),
                    "open": data['Open'][ticker].dropna().tail(20).tolist(),
                    "volume": data['Volume'][ticker].dropna().tail(20).tolist()
                }

                # ensure length = 20
                for key in result[ticker]:
                    if len(result[ticker][key]) < 20:
                        diff = 20 - len(result[ticker][key])
                        result[ticker][key] = [0.0]*diff + result[ticker][key]

            except:
                result[ticker] = {
                    "high": [0]*20,
                    "low": [0]*20,
                    "open": [0]*20,
                    "volume": [0]*20
                }

        return result

    except:
        return None

# ---------- BUILD FEATURES (56 FEATURES) ----------
def build_feature_matrix():
    print("🔥 USING 56 FEATURES VERSION")

    all_data = fetch_all_ohlcv()
    if all_data is None:
        raise Exception("Market data fetch failed")

    feature_order = ['high', 'low', 'open', 'volume']

    feature_cols = []

    for feature in feature_order:
        for ticker in SORTED_TICKERS:
            feature_cols.append(all_data[ticker][feature])

    arr = np.array(feature_cols).T  # (20, 56)

    print("RAW SHAPE:", arr.shape)

    if arr.shape != (20, 56):
        raise Exception(f"Shape error: got {arr.shape}, expected (20,56)")

    # 🔥 LOAD SCALER
    if not os.path.exists("x_scaler.pkl"):
        raise Exception("x_scaler.pkl missing")

    x_scaler = joblib.load("x_scaler.pkl")
    arr_scaled = x_scaler.transform(arr)

    final = arr_scaled.reshape(1, 20, 56)

    print("FINAL SHAPE:", final.shape)

    return final

# ---------- PREDICT ----------
@app.route("/predict", methods=["POST"])
def predict():
    try:
        today = datetime.date.today().isoformat()

        if is_cache_valid():
            return jsonify({"prediction": prediction_cache["data"], "cached": True})

        features = build_feature_matrix()

        hf_response = requests.post(
            HF_API_URL,
            json={"features": features.tolist()},
            timeout=60
        )

        if hf_response.status_code != 200:
            return jsonify({"error": "HF API failed"}), 500

        pred = hf_response.json()["prediction"][0]

        result = [
            {"company": SORTED_TICKERS[i], "predicted_price": round(float(pred[i]), 2)}
            for i in range(len(SORTED_TICKERS))
        ]

        prediction_cache["data"] = result
        prediction_cache["date"] = today

        return jsonify({"prediction": result, "cached": False})

    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

# ---------- STOCK ----------
@app.route("/stock", methods=["GET"])
def get_stock():
    try:
        symbol = request.args.get("symbol", "").upper().replace(".NS", "")
        nse = Nse()
        quote = nse.get_quote(symbol)

        if quote:
            return jsonify({
                "price": quote['lastPrice'],
                "change": quote['change'],
                "percent_change": str(round(quote['pChange'], 2)) + "%"
            })

    except:
        try:
            ticker = yf.Ticker(symbol + ".NS")
            hist = ticker.history(period="1d")

            price = float(hist["Close"].iloc[-1])
            open_price = float(hist["Open"].iloc[-1])
            percent_change = ((price - open_price) / open_price) * 100

            return jsonify({
                "price": round(price, 2),
                "percent_change": str(round(percent_change, 2)) + "%"
            })
        except:
            return jsonify({"error": "Stock fetch failed"}), 500

# ---------- NEWS ----------
@app.route("/news", methods=["GET"])
def get_news():
    try:
        company = request.args.get("company", "")
        GNEWS_API_KEY = os.getenv("GNEWS_API_KEY")

        url = f"https://gnews.io/api/v4/search?q={company}&lang=en&max=5&token={GNEWS_API_KEY}"
        res = requests.get(url)

        data = res.json()
        articles = [
            {
                "headline": a.get("title", ""),
                "summary": a.get("description", ""),
                "url": a.get("url", "")
            }
            for a in data.get("articles", [])
        ]

        return jsonify({"articles": articles})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ---------- RUN ----------
if __name__ == "__main__":
    app.run(debug=True)