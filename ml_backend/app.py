from flask import Flask, request, jsonify
import numpy as np
import joblib, traceback
from flask_cors import CORS
import requests
import datetime
from dotenv import load_dotenv
import os
import yfinance as yf
import pandas as pd
from nsetools import Nse

load_dotenv()
app = Flask(__name__)
CORS(app)

# ---------- HOME ROUTE ----------
@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "status": "Backend is running 🚀",
        "routes": ["/predict (POST)", "/stock?symbol=RELIANCE", "/news?company=RELIANCE"]
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

# ---------- Technical Indicators ----------
def compute_indicators(close, high, low, vol):
    result = {}
    result['ma7']          = close.rolling(7).mean()
    result['ma21']         = close.rolling(21).mean()
    result['ma50']         = close.rolling(50).mean()

    delta = close.diff()
    gain  = delta.clip(lower=0).rolling(14).mean()
    loss  = (-delta.clip(upper=0)).rolling(14).mean()
    rs    = gain / (loss + 1e-10)
    result['rsi']          = 100 - (100 / (1 + rs))

    ema12 = close.ewm(span=12).mean()
    ema26 = close.ewm(span=26).mean()
    result['macd']         = ema12 - ema26
    result['macd_signal']  = result['macd'].ewm(span=9).mean()

    ma20  = close.rolling(20).mean()
    std20 = close.rolling(20).std()
    result['bb_upper']     = ma20 + 2 * std20
    result['bb_lower']     = ma20 - 2 * std20
    result['bb_width']     = result['bb_upper'] - result['bb_lower']

    result['vol_ma7']      = vol.rolling(7).mean()
    result['price_change'] = close.pct_change()

    return result

# ---------- Fetch OHLCV + Indicators ----------
def fetch_all_ohlv():
    try:
        data = yf.download(SORTED_TICKERS, period="6mo", progress=False, auto_adjust=True)

        if data.empty:
            return None

        result = {}
        for ticker in SORTED_TICKERS:
            try:
                close  = data['Close'][ticker].dropna()
                high   = data['High'][ticker].dropna()
                low    = data['Low'][ticker].dropna()
                volume = data['Volume'][ticker].dropna()

                if len(close) < 25:
                    continue

                indicators = compute_indicators(close, high, low, volume)

                ticker_data = {
                    "high":         high.tail(20).tolist(),
                    "low":          low.tail(20).tolist(),
                    "open":         data['Open'][ticker].dropna().tail(20).tolist(),
                    "volume":       volume.tail(20).tolist(),
                    "ma7":          indicators['ma7'].tail(20).tolist(),
                    "ma21":         indicators['ma21'].tail(20).tolist(),
                    "ma50":         indicators['ma50'].tail(20).tolist(),
                    "rsi":          indicators['rsi'].tail(20).tolist(),
                    "macd":         indicators['macd'].tail(20).tolist(),
                    "macd_signal":  indicators['macd_signal'].tail(20).tolist(),
                    "bb_upper":     indicators['bb_upper'].tail(20).tolist(),
                    "bb_lower":     indicators['bb_lower'].tail(20).tolist(),
                    "bb_width":     indicators['bb_width'].tail(20).tolist(),
                    "vol_ma7":      indicators['vol_ma7'].tail(20).tolist(),
                    "price_change": indicators['price_change'].tail(20).tolist(),
                }

                for key in ticker_data:
                    if len(ticker_data[key]) < 20:
                        diff = 20 - len(ticker_data[key])
                        ticker_data[key] = [0.0] * diff + ticker_data[key]

                result[ticker] = ticker_data

            except:
                continue

        return result if result else None

    except:
        return None

# ---------- Build Feature Matrix ----------
def build_feature_matrix():
    print("NEW VERSION RUNNING 🚀")
    if not os.path.exists("x_scaler.pkl"):
        raise Exception("x_scaler.pkl missing")

    x_scaler = joblib.load('x_scaler.pkl')
    has_old = os.path.exists("last_20_days.npy")

    if has_old:
        old = np.load("last_20_days.npy")
        if old.shape[1] != 210:
            print("Old cache wrong shape, deleting...")
            os.remove("last_20_days.npy")
            has_old = False

    all_data = fetch_all_ohlv()

    if all_data is None:
        print("Using cached last_20_days.npy")
        return np.load("last_20_days.npy")

    feature_order = [
        'high', 'low', 'open', 'volume',
        'ma7', 'ma21', 'ma50',
        'rsi', 'macd', 'macd_signal',
        'bb_upper', 'bb_lower', 'bb_width',
        'vol_ma7', 'price_change'
    ]

    feature_cols = []
    for feature in feature_order:
        for ticker in SORTED_TICKERS:
            if ticker in all_data:
                feature_cols.append(all_data[ticker][feature])
            else:
                # Missing ticker — zeros se fill karo
                feature_cols.append([0.0] * 20)

    arr = np.array(feature_cols).T
    print(f"Feature matrix shape: {arr.shape}")

    if arr.shape[1] < 210:
        padding = np.zeros((20, 210 - arr.shape[1]))
        arr = np.concatenate([arr, padding], axis=1)
        print(f"Padded to: {arr.shape}")

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
            timeout=60
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

# ---------- Debug ----------
@app.route("/debug", methods=["GET"])
def debug():
    import yfinance as yf
    data = yf.download(SORTED_TICKERS, period="6mo", progress=False, auto_adjust=True)
    result = {}
    for t in SORTED_TICKERS:
        try:
            c = data['Close'][t].dropna()
            result[t] = len(c)
        except:
            result[t] = "MISSING"
    return jsonify(result)

# ---------- News ----------

# ---------- News ----------
@app.route("/news", methods=["GET"])
def get_news():
    try:
        company = request.args.get("company", "")
        GNEWS_API_KEY = os.getenv("GNEWS_API_KEY")

        if not GNEWS_API_KEY:
            return jsonify({"error": "API key missing"}), 500

        url = f"https://gnews.io/api/v4/search?q={company}&lang=en&max=5&token={GNEWS_API_KEY}"
        response = requests.get(url, timeout=10)

        if response.status_code != 200:
            return jsonify({"error": "GNews API failed"}), 500

        data = response.json()
        articles = []
        for article in data.get("articles", []):
            articles.append({
                "headline": article.get("title", ""),
                "summary": article.get("description", ""),
                "url": article.get("url", "")
            })

        if not articles:
            articles = [{
                "headline": f"{company} stock updates unavailable",
                "summary": "No recent news found",
                "url": ""
            }]

        return jsonify({"articles": articles})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ---------- Run ----------
if __name__ == "__main__":
    app.run(debug=True)