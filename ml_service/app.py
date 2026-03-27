from flask import Flask, request, jsonify
from tensorflow.keras.models import load_model
import numpy as np
import joblib

app = Flask(__name__)

# ✅ model load ho raha hai yaha
model = load_model("companies_stock.keras", compile=False)
y_scaler = joblib.load("y_scaler.save")

@app.route("/predict", methods=["POST"])
def predict():
    data = request.json
    last_n_days = np.array(data["features"])
    
    features = np.expand_dims(last_n_days, axis=0)
    pred_scaled = model.predict(features)
    pred_actual = y_scaler.inverse_transform(pred_scaled)

    return jsonify({"prediction": pred_actual.tolist()})

if __name__ == "__main__":
    app.run()