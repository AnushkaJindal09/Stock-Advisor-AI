from flask import Flask, request, jsonify
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
    try:
        data = request.json
        last_n_days = np.array(data["features"])

        # ✅ STRICT SHAPE FIX (MOST IMPORTANT)
        if last_n_days.shape == (20, 210):
            features = np.expand_dims(last_n_days, axis=0)
        elif last_n_days.shape == (1, 20, 210):
            features = last_n_days
        else:
            return jsonify({"error": f"Invalid input shape: {last_n_days.shape}"}), 400

        print("INPUT SHAPE:", features.shape)

        pred_scaled = model.predict(features)
        pred_actual = y_scaler.inverse_transform(pred_scaled)

        return jsonify({"prediction": pred_actual.tolist()})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run()