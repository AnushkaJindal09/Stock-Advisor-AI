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

# ---------- HOME ROUTE ----------
@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "status": "Backend is running 🚀",
        "routes": ["/predict (POST)", "/stock?symbol=RELIANCE"]
    })

# ---------- CONFIG ----------
HF_API_URL = "https://anushka09092004-stock-ml-api.hf.space/predict"

# ---------- Cache ----------
prediction_cache = {
    "data": None,
    "date": None
}

def is_cache_valid():
    if not prediction_cache["data"] or not prediction_cache["date"]:
        return False
    return prediction_cache["date"] == datetime.date.today().isoformat()

# ---------- Companies ----------
SORTED_TICKERS = [
    'ADANIENT.NS','ADANIPORTS.NS','BAJFINANCE.NS','BHARTIARTL.NS','COALINDIA.NS',
    'HDFCBANK.NS','HINDUNILVR.NS','ICICIBANK.NS','INFY.NS','LT.NS',
    'MARUTI.NS','RELIANCE.NS','SBIN.NS','TCS.NS'
]

company_names = SORTED_TICKERS

# ---------- Fetch OHLCV ----------
def fetch_all_ohlv():
    try:
        data = yf.download(SORTED_TICKERS, period="3mo", progress=False, auto_adjust=True)

        if data.empty:
            return None

        result = {}
        for ticker in SORTED_TICKERS:
            try:
                high   = data['High'][ticker].dropna().tail(20).tolist()
                low    = data['Low'][ticker].dropna().tail(20).tolist()
                open_  = data['Open'][ticker].dropna().tail(20).tolist()
                volume = data['Volume'][ticker].dropna().tail(20).tolist()

                if len(high) < 20:
                    continue

                result[ticker] = {
                    "high": high,
                    "low": low,
                    "open": open_,
                    "volume": volume
                }
            except:
                continue

        return result if result else None

    except:
        return None

# ---------- Build Feature Matrix ----------
def build_feature_matrix():
    if not os.path.exists("x_scaler.pkl"):
        raise Exception("x_scaler.pkl missing — retrain required")

    x_scaler = joblib.load('x_scaler.pkl')
    has_old = os.path.exists("last_20_days.npy")
    all_data = fetch_all_ohlv()

    if all_data is None:
        return np.load("last_20_days.npy")

    feature_cols = []

    for feature in ["high", "low", "open", "volume"]:
        for ticker in SORTED_TICKERS:
            if ticker in all_data:
                feature_cols.append(all_data[ticker][feature])
            else:
                if has_old:
                    old = np.load("last_20_days.npy")
                    col_idx = SORTED_TICKERS.index(ticker) + (["high","low","open","volume"].index(feature) * len(SORTED_TICKERS))
                    feature_cols.append(old[:, col_idx].tolist())
                else:
                    feature_cols.append([0.0] * 20)

    arr = np.array(feature_cols).T

    if arr.shape[0] != 20:
        raise ValueError(f"Invalid shape: {arr.shape}")

    arr_scaled = x_scaler.transform(arr)
    np.save("last_20_days.npy", arr_scaled)

    return arr_scaled

# ---------- Prediction Route ----------
@app.route("/predict", methods=["POST"])
def predict():
    try:
        today = datetime.date.today().isoformat()

        if is_cache_valid():
            return jsonify({"prediction": prediction_cache["data"], "cached": True})

        last_n_days = build_feature_matrix()

        hf_response = requests.post(
            HF_API_URL,
            json={"features": last_n_days.tolist()},
            timeout=15
        )

        if hf_response.status_code != 200:
            return jsonify({"error": "HF API failed"}), 500

        pred_actual = hf_response.json()["prediction"][0]

        result = [
            {"company": name, "predicted_price": round(float(pred_actual[i]), 2)}
            for i, name in enumerate(company_names)
        ]

        prediction_cache["data"] = result
        prediction_cache["date"] = today

        return jsonify({"prediction": result, "cached": False})

    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

# ---------- Live Stock ----------
@app.route("/stock", methods=["GET"])
def get_stock():
    try:
        symbol = request.args.get("symbol", "").upper().replace(".NS", "")
        nse = Nse()

        quote = nse.get_quote(symbol)

        if quote:
            return jsonify({
                "symbol": symbol,
                "price": quote['lastPrice'],
                "change": quote['change'],
                "percent_change": str(round(quote['pChange'], 2)) + "%"
            })

        return jsonify({"error": "Stock not found"}), 404

    except:
        # fallback yfinance
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
            return jsonify({"error": "Failed to fetch stock"}), 500
@app.route("/news", methods=["GET"])
def get_news():
    try:
        company = request.args.get("company", "")

        url = f"https://gnews.io/api/v4/search?q={company} share price&lang=en&max=10&token={os.getenv('GNEWS_API_KEY')}"
        response = requests.get(url)
        data = response.json()
        print("NEWS URL:", url)
        print("RESPONSE:", data)


        return jsonify({
            "articles": data.get("articles", [])
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500
# ---------- Run ----------
if __name__ == "__main__":
    app.run(debug=True)