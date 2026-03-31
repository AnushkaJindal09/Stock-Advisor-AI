from flask import Flask, request, jsonify
import yfinance as yf
import numpy as np
from tensorflow import keras
import joblib
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

model = keras.models.load_model("companies_stock.keras", compile=False)
y_scaler = joblib.load("y_scaler.save")

@app.route("/", methods=["GET"])
def home():
    return jsonify({"status": "API is running!"})

@app.route("/predict", methods=["POST"])
def predict():
    data = request.json

    if not data or "features" not in data:
        last_n_days = np.load("last_20_days.npy")
    else:
        last_n_days = np.array(data["features"])

    features = np.expand_dims(last_n_days, axis=0)

    pred_scaled = model.predict(features)
    pred_actual = y_scaler.inverse_transform(pred_scaled)

    companies = [
        "RELIANCE.NS","HDFCBANK.NS","ICICIBANK.NS","INFY.NS","TCS.NS",
        "HINDUNILVR.NS","LT.NS","BHARTIARTL.NS","ADANIENT.NS","ADANIPORTS.NS",
        "MARUTI.NS","BAJFINANCE.NS","SBIN.NS","COALINDIA.NS"
    ]

    result = []
    for i, price in enumerate(pred_actual[0]):
        result.append({
            "company": companies[i],
            "predicted_price": float(price)
        })

    return jsonify({"prediction": result})

@app.route("/stock", methods=["GET"])
def get_stock():
    symbol = request.args.get("symbol")

    if not symbol:
        return jsonify({"error": "Symbol required"}), 400

    symbol = symbol + ".NS"

    try:
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period="1d")

        if hist.empty:
            return jsonify({"error": "No data"}), 404

        price = float(hist["Close"].iloc[-1])
        open_price = float(hist["Open"].iloc[-1])

        percent_change = ((price - open_price) / open_price) * 100

        return jsonify({
            "price": round(price, 2),
            "percent_change": round(percent_change, 2)
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run()