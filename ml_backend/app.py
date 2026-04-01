'''
from flask import Flask, request, jsonify
from tensorflow.keras.models import load_model
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

# ---------- API KEYS ----------
NEWS_API_KEY = os.getenv("NEWS_API_KEY")
FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY")

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

SORTED_TICKERS = [
    'ADANIENT.NS','ADANIPORTS.NS','BAJFINANCE.NS','BHARTIARTL.NS','COALINDIA.NS',
    'HDFCBANK.NS','HINDUNILVR.NS','ICICIBANK.NS','INFY.NS','LT.NS',
    'MARUTI.NS','RELIANCE.NS','SBIN.NS','TCS.NS'
]

company_names = [
    'ADANIENT.NS','ADANIPORTS.NS','BAJFINANCE.NS','BHARTIARTL.NS','COALINDIA.NS',
    'HDFCBANK.NS','HINDUNILVR.NS','ICICIBANK.NS','INFY.NS','LT.NS',
    'MARUTI.NS','RELIANCE.NS','SBIN.NS','TCS.NS'
]

# ---------- Fetch OHLCV ----------
def fetch_all_ohlv():
    try:
        print("Fetching data from yfinance...")
        data = yf.download(
            SORTED_TICKERS,
            period="3mo",
            progress=False,
            auto_adjust=True
        )

        if data.empty:
            print("yfinance returned empty data!")
            return None

        result = {}
        for ticker in SORTED_TICKERS:
            try:
                high   = data['High'][ticker].dropna().tail(20).tolist()
                low    = data['Low'][ticker].dropna().tail(20).tolist()
                open_  = data['Open'][ticker].dropna().tail(20).tolist()
                volume = data['Volume'][ticker].dropna().tail(20).tolist()
                close  = data['Close'][ticker].dropna().tail(20).tolist()

                if len(high) < 20 or len(low) < 20 or len(open_) < 20 or len(volume) < 20:
                    print(f"Not enough data for {ticker}: {len(high)} days")
                    continue

                result[ticker] = {
                    "high": high, "low": low,
                    "open": open_, "volume": volume
                }
                print(f"OK {ticker}: last close={close[-1]:.2f}")
            except Exception as e:
                print(f"Error processing {ticker}: {e}")
                continue

        print(f"Fetched {len(result)}/14 companies successfully")
        return result if len(result) > 0 else None

    except Exception as e:
        print(f"yfinance download error: {e}")
        return None

# ---------- Build Feature Matrix ----------
def build_feature_matrix():
    x_scaler = joblib.load('x_scaler.pkl')
    has_old = os.path.exists("last_20_days.npy")
    all_data = fetch_all_ohlv()

    if all_data is None or len(all_data) == 0:
        print("All fetches failed — using cached last_20_days.npy (already scaled)")
        return np.load("last_20_days.npy"), 0, True

    failed = [t for t in SORTED_TICKERS if t not in all_data]
    if failed:
        print(f"Missing companies: {failed}")

    feature_cols = []
    for feature in ["high", "low", "open", "volume"]:
        for ticker in SORTED_TICKERS:
            if ticker in all_data:
                feature_cols.append(all_data[ticker][feature])
            else:
                if has_old:
                    old = np.load("last_20_days.npy")
                    col_idx = SORTED_TICKERS.index(ticker) + (["high","low","open","volume"].index(feature) * 14)
                    try:
                        unscaled = x_scaler.inverse_transform(old)
                        feature_cols.append(unscaled[:, col_idx].tolist())
                    except:
                        feature_cols.append([0.0] * 20)
                else:
                    feature_cols.append([0.0] * 20)

    arr = np.array(feature_cols).T
    print(f"Feature matrix shape: {arr.shape}")

    if arr.shape != (20, 56):
        raise ValueError(f"Shape mismatch: {arr.shape}, expected (20, 56)")

    arr_scaled = x_scaler.transform(arr)
    np.save("last_20_days.npy", arr_scaled)
    print(f"last_20_days.npy updated with fresh data!")
    return arr_scaled, len(all_data), False

# ---------- Prediction Route ----------
@app.route("/predict", methods=["POST"])
def predict():
    try:
        today = datetime.date.today().isoformat()
        if is_cache_valid():
            print(f"Cache hit for {today}")
            return jsonify({"prediction": prediction_cache["data"], "cached": True, "date": today})

        print(f"\n{'='*50}")
        print(f"Fresh prediction for {today}")
        print(f"{'='*50}")

        model = load_model("companies_stock.keras", compile=False)
        y_scaler = joblib.load('y_scaler.save')

        last_n_days, success_count, already_scaled = build_feature_matrix()
        if already_scaled:
            print("Using cached scaled data — no double scaling")

        features = np.expand_dims(last_n_days, axis=0)
        pred_scaled = model.predict(features)
        pred_actual = y_scaler.inverse_transform(pred_scaled)

        result = [
            {"company": name, "predicted_price": round(float(pred_actual[0][i]), 2)}
            for i, name in enumerate(company_names)
        ]

        prediction_cache["data"] = result
        prediction_cache["date"] = today

        reliance_pred = next((r['predicted_price'] for r in result if 'RELIANCE' in r['company']), 'N/A')
        print(f"Done! RELIANCE predicted = {reliance_pred} ({success_count}/14 fresh)")

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
    '''




'''
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

# ---------- API KEYS ----------
NEWS_API_KEY = os.getenv("NEWS_API_KEY")
FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY")
HF_API_URL = "https://anushka09092004-stock-ml-api.hf.space/predict"

# ---------- Cache ----------
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
SORTED_TICKERS = [
    'ADANIENT.NS','ADANIPORTS.NS','BAJFINANCE.NS','BHARTIARTL.NS','COALINDIA.NS',
    'HDFCBANK.NS','HINDUNILVR.NS','ICICIBANK.NS','INFY.NS','LT.NS',
    'MARUTI.NS','RELIANCE.NS','SBIN.NS','TCS.NS'
]

tickers = [
    'RELIANCE.NS','HDFCBANK.NS','ICICIBANK.NS','INFY.NS','TCS.NS',
    'HINDUNILVR.NS','LT.NS','BHARTIARTL.NS','ADANIENT.NS','ADANIPORTS.NS',
    'TATAMOTORS.NS','MARUTI.NS','BAJFINANCE.NS','SBIN.NS','COALINDIA.NS'
]

company_names = [
    'ADANIENT.NS','ADANIPORTS.NS','BAJFINANCE.NS','BHARTIARTL.NS','COALINDIA.NS',
    'HDFCBANK.NS','HINDUNILVR.NS','ICICIBANK.NS','INFY.NS','LT.NS',
    'MARUTI.NS','RELIANCE.NS','SBIN.NS','TCS.NS'
]

# ---------- Fetch OHLCV ----------
def fetch_all_ohlv():
    try:
        print("Fetching data from yfinance...")
        data = yf.download(
            SORTED_TICKERS,
            period="3mo",
            progress=False,
            auto_adjust=True
        )

        if data.empty:
            print("yfinance returned empty data!")
            return None

        result = {}
        for ticker in SORTED_TICKERS:
            try:
                high   = data['High'][ticker].dropna().tail(20).tolist()
                low    = data['Low'][ticker].dropna().tail(20).tolist()
                open_  = data['Open'][ticker].dropna().tail(20).tolist()
                volume = data['Volume'][ticker].dropna().tail(20).tolist()
                close  = data['Close'][ticker].dropna().tail(20).tolist()

                if len(high) < 20:
                    print(f"Not enough data for {ticker}")
                    continue

                result[ticker] = {
                    "high": high, "low": low,
                    "open": open_, "volume": volume
                }
            except Exception as e:
                print(f"Error processing {ticker}: {e}")
                continue

        return result if len(result) > 0 else None

    except Exception as e:
        print(f"yfinance error: {e}")
        return None

# ---------- Build Feature Matrix ----------
def build_feature_matrix():
    x_scaler = joblib.load('x_scaler.pkl')
    has_old = os.path.exists("last_20_days.npy")
    all_data = fetch_all_ohlv()

    if all_data is None:
        print("Using cached last_20_days.npy")
        return np.load("last_20_days.npy"), 0, True

    feature_cols = []
    for feature in ["high", "low", "open", "volume"]:
        for ticker in SORTED_TICKERS:
            if ticker in all_data:
                feature_cols.append(all_data[ticker][feature])
            else:
                if has_old:
                    old = np.load("last_20_days.npy")
                    col_idx = SORTED_TICKERS.index(ticker) + (["high","low","open","volume"].index(feature) * 14)
                    try:
                        unscaled = x_scaler.inverse_transform(old)
                        feature_cols.append(unscaled[:, col_idx].tolist())
                    except:
                        feature_cols.append([0.0] * 20)
                else:
                    feature_cols.append([0.0] * 20)

    arr = np.array(feature_cols).T
    if arr.shape != (20, 56):
        raise ValueError(f"Shape mismatch: {arr.shape}")

    arr_scaled = x_scaler.transform(arr)
    np.save("last_20_days.npy", arr_scaled)
    return arr_scaled, len(all_data), False

# ---------- Prediction Route ----------
@app.route("/predict", methods=["POST"])
def predict():
    try:
        today = datetime.date.today().isoformat()
        if is_cache_valid():
            print(f"Cache hit for {today}")
            return jsonify({"prediction": prediction_cache["data"], "cached": True})

        print(f"Fresh prediction for {today}")

        # Feature matrix banao
        last_n_days, success_count, already_scaled = build_feature_matrix()

        # HF API call karo
        features = last_n_days.tolist()
        hf_response = requests.post(
            HF_API_URL,
            json={"features": features},
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
            return jsonify({"reply": f"Latest news:\n{news_summary}"})

        return jsonify({"reply": "Mujhe samajh nahi aaya. Prediction ya news poochho."})
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

# ---------- Live Stock Price ----------
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
    '''







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

# ---------- Run ----------
if __name__ == "__main__":
    app.run(debug=True)