import requests
import traceback
from flask import Blueprint, jsonify, request
from flask_cors import cross_origin

analytics_bp = Blueprint('analytics', __name__)

@analytics_bp.route("/predict", methods=["POST", "OPTIONS"])
@cross_origin()
def predict():
    # Browser ke CORS preflight request ko handle karne ke liye
    if request.method == "OPTIONS":
        return jsonify({"status": "CORS Preflight OK"}), 200

    try:
        body = request.get_json() or {}
        
        # ─── STRICT VALIDATION (No Defaults) ───
        # Frontend se jo real company select hui h vahi uthayega
        raw_company = body.get("company") 
        
        if not raw_company:
            return jsonify({
                "error": "Required parameter 'company' is missing.",
                "model_status": "bad_request"
            }), 400
            
        # Ticker se .NS hata kar saaf naam (e.g. TCS, INFY) Hugging Face ko bhejne ke liye
        company = raw_company.upper().strip().replace(".NS", "")

        # Tumhaara Hugging Face Space Application URL
        HF_SPACE_URL = "https://anushka09092004-stock-ml-api.hf.space/predict"

        # ─── CALLING YOUR TRAINED HUGGING FACE MODEL ───
        try:
            hf_response = requests.post(HF_SPACE_URL, json={"company": company}, timeout=25)
            
            if hf_response.status_code == 200:
                hf_data = hf_response.json()
                prediction_data = hf_data.get("prediction", [])
                
                # Agar trained model se valid prediction array aaya h toh return karo
                if prediction_data and len(prediction_data) > 0:
                    return jsonify({
                        "prediction": prediction_data,
                        "model_status": "active",
                        "framework": "XGBoost Autonomous Range"
                    }), 200
                else:
                    # Agar model ke database me us stock ka matrix data nahi mila
                    return jsonify({
                        "error": f"No trained mathematical range matrix found for {company}.",
                        "model_status": "insufficient_data"
                    }), 404
            else:
                # Agar Hugging Face server down h ya recalibrate ho raha h
                return jsonify({
                    "error": "Prediction engine is temporarily offline or recalibrating.",
                    "model_status": "offline"
                }), 503

        except requests.exceptions.Timeout:
            return jsonify({
                "error": "Prediction request timed out. AI server is under high traffic.",
                "model_status": "timeout"
            }), 504
            
        except Exception as hf_err:
            return jsonify({
                "error": f"AI Engine Connection Lost: {str(hf_err)}",
                "model_status": "error"
            }), 500

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

        