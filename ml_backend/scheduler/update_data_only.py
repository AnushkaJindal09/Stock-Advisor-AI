def update_data_only():
    import numpy as np
    import pandas as pd
    import joblib
    import requests
    import os

    tickers = [
        'RELIANCE','HDFCBANK','ICICIBANK','INFY','TCS',
        'HINDUNILVR','LT','BHARTIARTL','ADANIENT','ADANIPORTS',
        'TATAMOTORS','MARUTI','BAJFINANCE','SBIN','COALINDIA'
    ]

    rows = []
    for ticker in tickers:
        try:
            res = requests.get(f"https://stock-backend-gsyw.onrender.com/stock?symbol={ticker}")
            data = res.json()
            if data.get('price'):
                rows.append({
                    f"High_{ticker}.NS": data['price'],
                    f"Low_{ticker}.NS": data['price'],
                    f"Open_{ticker}.NS": data['price'],
                    f"Volume_{ticker}.NS": 0,
                })
        except:
            pass

    if not rows:
        print("❌ No data fetched")
        return

    df = pd.DataFrame(rows)

    base_path = os.path.dirname(os.path.abspath(__file__))
    ml_backend_path = os.path.dirname(base_path)

    x_scaler = joblib.load(os.path.join(ml_backend_path, "x_scaler.pkl"))

    existing = np.load(os.path.join(base_path, "last_20_days.npy"))
    new_row = x_scaler.transform(df.fillna(0))

    updated = np.vstack([existing[1:], new_row])
    np.save(os.path.join(base_path, "last_20_days.npy"), updated)

    print("✅ Daily data updated successfully")

if __name__ == "__main__":
    print("🚀 update_data_only.py started")
    update_data_only()