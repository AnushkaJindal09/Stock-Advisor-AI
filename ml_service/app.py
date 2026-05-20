import os
import datetime
import numpy as np
import pandas as pd
import yfinance as yf
from flask import Flask, jsonify, request
from flask_cors import CORS
from xgboost import XGBRegressor
from sklearn.impute import SimpleImputer
import warnings

warnings.filterwarnings("ignore")

app = Flask(__name__)
CORS(app)  # Direct external pipeline connectivity rules ensure karne ke liye

def extract_advanced_features(df):
    X = pd.DataFrame(index=df.index)
    c, h, l, o = df['Close'], df['High'], df['Low'], df['Open']

    X['returns'] = c.pct_change()
    X['vol_7d'] = X['returns'].rolling(7).std()
    X['vol_21d'] = X['returns'].rolling(21).std()

    X['upper_wick'] = (h - np.maximum(c, o)) / c
    X['lower_wick'] = (np.minimum(c, o) - l) / c
    X['body_ratio'] = abs(c - o) / (h - l + 0.001)

    tr = pd.concat([h - l, abs(h - c.shift(1)), abs(l - c.shift(1))], axis=1).max(axis=1)
    X['atr_norm'] = tr.rolling(14).mean() / c

    delta = c.diff()
    up = delta.clip(lower=0).rolling(14).mean()
    down = -delta.clip(upper=0).rolling(14).mean()
    X['rsi'] = 100 - (100 / (1 + (up / down.replace(0, 0.001))))
    X['ma_20_dist'] = (c - c.rolling(20).mean()) / c

    return X.replace([np.inf, -np.inf], np.nan)

def get_stable_ltp(ticker_obj):
    try:
        return ticker_obj.fast_info['last_price']
    except:
        return ticker_obj.history(period="1d")['Close'].iloc[-1]

@app.route("/", methods=["GET"])
def home():
    return jsonify({"status": "Hugging Face Autonomous ML Range Service is Live"}), 200

@app.route("/predict", methods=["POST"])
def predict():
    try:
        data = request.get_json() or {}
        
        # Agar frontend abhi bhi purana framework bhej raha ho toh fallback safety
        company = data.get("company", "RELIANCE").upper().strip()

        # Formatting boundaries (.NS check code extension)
        ticker_symbol = company if company.endswith(".NS") else f"{company}.NS"

        ticker_obj = yf.Ticker(ticker_symbol)
        df = ticker_obj.history(period="5y", interval="1d", auto_adjust=False)

        if len(df) < 100:
            return jsonify({"error": f"Insufficient dataset matrix pool for {company}"}), 400

        ltp = get_stable_ltp(ticker_obj)
        X_raw = extract_advanced_features(df)

        y = (df['Close'].shift(-1) / df['Close'] - 1).loc[X_raw.index].dropna()
        X = X_raw.loc[y.index]

        # On-the-fly execution structure
        imputer = SimpleImputer(strategy='median')
        X_imputed = imputer.fit_transform(X)

        model = XGBRegressor(
            n_estimators=250,
            max_depth=6,
            learning_rate=0.015,
            objective='reg:absoluteerror',
            random_state=42
        )
        model.fit(X_imputed, y)

        last_feat = imputer.transform(X_raw.iloc[[-1]])
        pred_return = model.predict(last_feat)[0]
        target_price = ltp * (1 + pred_return)

        curr_atr = float(X_raw['atr_norm'].iloc[-1])
        avg_atr = float(X_raw['atr_norm'].tail(100).mean())

        # NaN Safety Layer
        if np.isnan(curr_atr) or curr_atr <= 0:
            curr_atr = 0.02

        if np.isnan(avg_atr) or avg_atr <= 0:
            avg_atr = 0.02

        vol_ratio = curr_atr / avg_atr

        # Dynamic range control
        dynamic_buffer = max(curr_atr * (1.1 if vol_ratio > 1 else 0.9), 0.01)

        low_bound = float(target_price * (1 - dynamic_buffer))
        high_bound = float(target_price * (1 + dynamic_buffer))

        # Final safety
        if np.isnan(low_bound):
            low_bound = float(target_price * 0.98)

        if np.isnan(high_bound):
            high_bound = float(target_price * 1.02)

        conf_score = "High" if vol_ratio < 1.1 else "Moderate"

        low_bound = target_price * (1 - dynamic_buffer)
        high_bound = target_price * (1 + dynamic_buffer)
        conf_score = "High" if vol_ratio < 1.1 else "Moderate"

        # Key mappings are clean and directly formatted for standard array rendering
        return jsonify({
            "status": "success",
            "prediction": [{
                "company": company,
                "live_ltp": round(float(ltp), 2),
                "predicted_price": round(float(target_price), 2),
                "range_low": round(float(low_bound), 2),
                "range_high": round(float(high_bound), 2),
                "confidence": conf_score
            }]
        }), 200

    except Exception as e:
        return jsonify({"error": f"HF Executive Matrix Exception: {str(e)}"}), 500

if __name__ == "__main__":
    # Hugging Face Spaces environment execution standards
    app.run(host="0.0.0.0", port=7860)

'''
from flask import Flask, request, jsonify
import tensorflow as tf
import numpy as np
import keras
import joblib

app = Flask(__name__)

model = keras.models.load_model("companies_stock.keras", compile=False)
y_scaler = joblib.load("y_scaler.save")

@app.route("/", methods=["GET"])
def home():
    return jsonify({"status": "API is running!"})

@app.route("/predict", methods=["POST"])
def predict():
    data = request.json
    last_n_days = np.array(data["features"])

    # Shape check karke sahi dimension mein daalo
    if last_n_days.ndim == 2:
        # User ne (20, 56) bheja — expand karo (1, 20, 56)
        features = np.expand_dims(last_n_days, axis=0)
    elif last_n_days.ndim == 3:
        # User ne already (1, 20, 56) bheja — as it is rakho
        features = last_n_days
    else:
        return jsonify({"error": f"Invalid input shape: {last_n_days.shape}"}), 400

    pred_scaled = model.predict(features)
    pred_actual = y_scaler.inverse_transform(pred_scaled)

    return jsonify({"prediction": pred_actual.tolist()})

if __name__ == "__main__":
    app.run()
    '''