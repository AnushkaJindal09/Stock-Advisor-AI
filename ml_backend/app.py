from flask import Flask, request, jsonify
from tensorflow.keras.models import load_model
import numpy as np
import joblib, traceback
from flask_cors import CORS
import requests
import datetime
from dotenv import load_dotenv
import os

load_dotenv()
app = Flask(__name__)
CORS(app)

# ---------- API KEYS ----------
NEWS_API_KEY = os.getenv("NEWS_API_KEY")
FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY")
ALPHA_API_KEY = os.getenv("ALPHA_API_KEY")

# ---------- Cache — date based ----------
prediction_cache = {
    "data": None,
    "date": None
}

def is_cache_valid():
    if not prediction_cache["data"] or not prediction_cache["date"]:
        return False
    today = datetime.date.today().isoformat()
    return prediction_cache["date"] == today

# ---------- Companies ----------
tickers = [
    'RELIANCE.NS','HDFCBANK.NS','ICICIBANK.NS','INFY.NS','TCS.NS',
    'HINDUNILVR.NS','LT.NS','BHARTIARTL.NS','ADANIENT.NS','ADANIPORTS.NS',
    'TATAMOTORS.NS','MARUTI.NS','BAJFINANCE.NS','SBIN.NS','COALINDIA.NS'
]

# Model expects features in this order (sorted):
# High_ADANIENT, High_ADANIPORTS, ..., Low_ADANIENT, ..., Open_ADANIENT, ..., Volume_ADANIENT, ...
# i.e. X = df.filter(regex='^(High|Low|Open|Volume)_')
# Sorted tickers for model input:
SORTED_TICKERS = [
    'ADANIENT.NS','ADANIPORTS.NS','BAJFINANCE.NS','BHARTIARTL.NS','COALINDIA.NS',
    'HDFCBANK.NS','HINDUNILVR.NS','ICICIBANK.NS','INFY.NS','LT.NS',
    'MARUTI.NS','RELIANCE.NS','SBIN.NS','TCS.NS'
]  # 14 companies for INPUT (x_scaler — TATAMOTORS missing from training data)

# Output: 14 companies (TATAMOTORS removed — not in training data)
company_names = [
    'ADANIENT.NS','ADANIPORTS.NS','BAJFINANCE.NS','BHARTIARTL.NS','COALINDIA.NS',
    'HDFCBANK.NS','HINDUNILVR.NS','ICICIBANK.NS','INFY.NS','LT.NS',
    'MARUTI.NS','RELIANCE.NS','SBIN.NS','TCS.NS'
]

AV_SYMBOLS = {
    'RELIANCE.NS': 'RELIANCE.BSE',
    'HDFCBANK.NS': 'HDFCBANK.BSE',
    'ICICIBANK.NS': 'ICICIBANK.BSE',
    'INFY.NS': 'INFY.BSE',
    'TCS.NS': 'TCS.BSE',
    'HINDUNILVR.NS': 'HINDUNILVR.BSE',
    'LT.NS': 'LT.BSE',
    'BHARTIARTL.NS': 'BHARTIARTL.BSE',
    'ADANIENT.NS': 'ADANIENT.BSE',
    'ADANIPORTS.NS': 'ADANIPORTS.BSE',
    'TATAMOTORS.NS': 'TATAMOTORS.BSE',
    'MARUTI.NS': 'MARUTI.BSE',
    'BAJFINANCE.NS': 'BAJFINANCE.BSE',
    'SBIN.NS': 'SBIN.BSE',
    'COALINDIA.NS': 'COALINDIA.BSE'
}


def fetch_ohlv_20days(ticker):
    """
    Fetch last 20 days High, Low, Open, Volume from Alpha Vantage.
    Returns dict with keys: high, low, open, volume — each list of 20 values.
    """
    try:
        av_symbol = AV_SYMBOLS.get(ticker, ticker.replace('.NS', '.BSE'))
        url = "https://www.alphavantage.co/query"
        params = {
            "function": "TIME_SERIES_DAILY",
            "symbol": av_symbol,
            "outputsize": "compact",
            "apikey": ALPHA_API_KEY
        }
        res = requests.get(url, params=params, timeout=15)
        data = res.json()

        time_series = data.get("Time Series (Daily)", {})
        if not time_series:
            msg = data.get('Note') or data.get('Information') or 'No data'
            print(f"No data for {ticker}: {msg}")
            return None

        sorted_dates = sorted(time_series.keys(), reverse=True)[:20]
        sorted_dates.reverse()  # oldest first

        if len(sorted_dates) < 20:
            return None

        high   = [float(time_series[d]["2. high"])   for d in sorted_dates]
        low    = [float(time_series[d]["3. low"])    for d in sorted_dates]
        open_  = [float(time_series[d]["1. open"])   for d in sorted_dates]
        volume = [float(time_series[d]["5. volume"]) for d in sorted_dates]

        print(f"OK {ticker}: last close={float(time_series[sorted_dates[-1]]['4. close']):.2f}")
        return {"high": high, "low": low, "open": open_, "volume": volume}

    except Exception as e:
        print(f"Error fetching {ticker}: {e}")
        return None


def build_feature_matrix():
    """
    Build (20, 56) feature matrix matching training format:
    X = df.filter(regex='^(High|Low|Open|Volume)_') — sorted columns

    Column order:
    High_ADANIENT, High_ADANIPORTS, ...(15 highs)
    Low_ADANIENT, ...(15 lows)
    Open_ADANIENT, ...(15 opens)
    Volume_ADANIENT, ...(15 volumes)

    Total = 15 * 4 = 60 features
    """
    x_scaler = joblib.load('x_scaler.pkl')

    # Fetch data for all companies
    all_data = {}
    failed = []
    has_old = os.path.exists("last_20_days.npy")

    for ticker in SORTED_TICKERS:
        result = fetch_ohlv_20days(ticker)
        if result:
            all_data[ticker] = result
        else:
            failed.append(ticker)
            print(f"FAILED: {ticker}")

    if failed:
        print(f"Failed to fetch: {failed}")

    # If all failed — use old npy
    if len(all_data) == 0:
        print("All fetches failed — using old last_20_days.npy")
        return np.load("last_20_days.npy"), 0

    # Build columns in correct order: High x15, Low x15, Open x15, Volume x15
    feature_cols = []

    for feature in ["high", "low", "open", "volume"]:
        for ticker in SORTED_TICKERS:
            if ticker in all_data:
                feature_cols.append(all_data[ticker][feature])
            else:
                # Fallback: use old data if available
                if has_old:
                    old = np.load("last_20_days.npy")
                    # Find approximate column index
                    col_idx = SORTED_TICKERS.index(ticker) + (["high","low","open","volume"].index(feature) * 15)
                    try:
                        unscaled = x_scaler.inverse_transform(old)
                        feature_cols.append(unscaled[:, col_idx].tolist())
                    except:
                        feature_cols.append([0.0] * 20)
                else:
                    feature_cols.append([0.0] * 20)

    # feature_cols: list of 60 lists, each 20 values
    # Transpose to (20, 56)
    arr = np.array(feature_cols).T  # shape (20, 56)
    print(f"Feature matrix shape: {arr.shape}")

    if arr.shape != (20, 56):
        raise ValueError(f"Shape mismatch: {arr.shape}, expected (20, 56)")

    # Scale
    arr_scaled = x_scaler.transform(arr)

    # Save for fallback
    np.save("last_20_days.npy", arr_scaled)
    print(f"last_20_days.npy updated! ({len(all_data)}/15 companies fresh)")

    return arr_scaled, len(all_data)


# ---------- Prediction Route ----------
@app.route("/predict", methods=["POST"])
def predict():
    try:
        today = datetime.date.today().isoformat()

        # Return cached result
        if is_cache_valid():
            print(f"Cache hit for {today}")
            return jsonify({"prediction": prediction_cache["data"], "cached": True, "date": today})

        print(f"\n{'='*50}")
        print(f"Fresh prediction for {today}")
        print(f"{'='*50}")

        model = load_model("companies_stock.h5", compile=False)
        y_scaler = joblib.load('y_scaler.save')

        last_n_days, success_count = build_feature_matrix()

        features = np.expand_dims(last_n_days, axis=0)  # (1, 20, 60)
        pred_scaled = model.predict(features)
        pred_actual = y_scaler.inverse_transform(pred_scaled)

        result = [
            {"company": name, "predicted_price": round(float(pred_actual[0][i]), 2)}
            for i, name in enumerate(company_names)
        ]

        prediction_cache["data"] = result
        prediction_cache["date"] = today

        reliance_pred = next((r['predicted_price'] for r in result if 'RELIANCE' in r['company']), 'N/A')
        print(f"Done! RELIANCE predicted = {reliance_pred} ({success_count}/15 fresh)")

        return jsonify({"prediction": result, "cached": False, "date": today})

    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


# ---------- News Route ----------
@app.route("/news", methods=["GET"])
def get_news():
    try:
        company = request.args.get("company", "")
        if not company:
            return jsonify({"articles": []})

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

        if "news" in user_input:
            company = None
            for c in tickers:
                if c.lower().replace(".ns", "") in user_input:
                    company = c
                    break
            if not company:
                company = "RELIANCE.NS"

            with app.test_request_context(f'/news?company={company}', method='GET'):
                response = get_news()
            news_data = response.get_json()

            articles = news_data.get("articles", [])
            if not articles:
                return jsonify({"reply": f"No news found for {company}"})

            news_summary = "\n".join([f"{i+1}. {a['headline']}" for i, a in enumerate(articles) if "headline" in a])
            return jsonify({"reply": f"Latest news about {company}:\n{news_summary}"})

        return jsonify({"reply": "Mujhe samajh nahi aaya. Prediction ya news poochho."})

    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


# ---------- Live Stock Price ----------
from nsetools import Nse

@app.route("/stock", methods=["GET"])
def get_stock():
    try:
        symbol = request.args.get("symbol", "").upper().replace(".NS", "").replace(".BSE", "")
        nse = Nse()
        quote = nse.get_quote(symbol)
        if quote:
            return jsonify({
                "symbol": symbol,
                "price": quote['lastPrice'],
                "change": quote['change'],
                "percent_change": str(round(quote['pChange'], 2)) + "%"
            })
        else:
            return jsonify({"error": "Stock not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True)
