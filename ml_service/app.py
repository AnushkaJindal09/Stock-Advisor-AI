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