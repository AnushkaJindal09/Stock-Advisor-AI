import requests
import numpy as np

# (1, 20, 60) shape data banana hai
features = np.ones((1, 20, 60)).tolist()

res = requests.post(
    "http://127.0.0.1:5000/predict",
    json={"features": features}
)

print(res.json())
