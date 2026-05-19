import requests
import traceback
from flask import Blueprint, jsonify, request

analytics_bp = Blueprint('analytics', __name__)

@analytics_bp.route("/predict", methods=["POST"])
def predict():
    try:
        body = request.get_json() or {}
        # Frontend se selected stock symbol uthao (e.g., "RELIANCE.NS")
        company = body.get("company", "RELIANCE.NS").upper().strip()

        # Hugging Face Space ka direct application URL
        HF_SPACE_URL = "https://anushka09092004-stock-ml-api.hf.space/predict"

        # Sidhe Hugging Face engine ko call maaro, saara calculation wahi karega
        hf_response = requests.post(HF_SPACE_URL, json={"company": company}, timeout=45)
        
        if hf_response.status_code != 200:
            return jsonify({"error": "Autonomous prediction engine temporarily offline"}), 503

        hf_data = hf_response.json()
        
        # Hugging Face se aaya hua range matrix data sidhe frontend ko pass kar do
        return jsonify({
            "prediction": hf_data.get("prediction", []),
            "model_status": "active",
            "framework": "XGBoost Autonomous Range"
        }), 200

    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": f"Internal Gateway Proxy Error: {str(e)}"}), 500



'''
import numpy as np
import joblib
import os
import requests
import traceback
from flask import Blueprint, jsonify, request
from config import HF_API_URL, SORTED_TICKERS
from data_engine import fetch_all_ohlcv
from flask_cors import cross_origin

analytics_bp = Blueprint('analytics', __name__)

def build_feature_matrix():
    all_data = fetch_all_ohlcv()
    if all_data is None:
        raise Exception("Market data fetch failed")
 
    feature_order = ['high', 'low', 'open', 'volume']
    feature_cols = []
    for feature in feature_order:
        for ticker in SORTED_TICKERS:
            feature_cols.append(all_data[ticker][feature])
 
    arr = np.array(feature_cols).T
    if arr.shape != (20, 56):
        raise Exception(f"Wrong shape: {arr.shape}")
        
    # Production Check: Deployment ke waqt root absolute matching safe rakhegi
    scaler_path = os.path.join(os.path.dirname(__file__), "x_scaler.pkl")
    if not os.path.exists(scaler_path):
        raise Exception("x_scaler.pkl missing from backend server path")
 
    x_scaler = joblib.load(scaler_path)
    arr_scaled = x_scaler.transform(arr)
    return arr_scaled.reshape(1, 20, 56)

@analytics_bp.route("/predict", methods=["POST"])
def predict():
    try:
        features = build_feature_matrix()
        hf_response = requests.post(HF_API_URL, json={"features": features.tolist()}, timeout=30)
        if hf_response.status_code != 200:
            return jsonify({"error": "Prediction service unavailable"}), 503
        pred = hf_response.json()["prediction"][0]
        result = [{"company": SORTED_TICKERS[i], "predicted_price": round(float(pred[i]), 2)} for i in range(len(SORTED_TICKERS))]
        return jsonify({"prediction": result, "model_status": "active"})
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500
        '''

        