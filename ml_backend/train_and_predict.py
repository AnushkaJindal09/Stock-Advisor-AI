import yfinance as yf
import pandas as pd
import numpy as np
import joblib
from sklearn.preprocessing import MinMaxScaler
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense
from tensorflow.keras.callbacks import EarlyStopping

# ✅ Same tickers as yours
tickers = ['RELIANCE.NS','HDFCBANK.NS','ICICIBANK.NS','INFY.NS','TCS.NS','HINDUNILVR.NS','LT.NS','BHARTIARTL.NS','ADANIENT.NS','ADANIPORTS.NS','TATAMOTORS.NS','MARUTI.NS','BAJFINANCE.NS','SBIN.NS','COALINDIA.NS']

# ✅ Auto-updating data till today's date
data = yf.download(tickers, start="2018-01-01")
data.to_csv("combined_stock_data.csv")

df = pd.read_csv("combined_stock_data.csv", header=[0,1], index_col=0)
df.columns = ['_'.join(col).strip() if isinstance(col, tuple) else col for col in df.columns.values]
df.index = pd.to_datetime(df.index)
df.dropna(inplace=True)

# ✅ Feature columns
X = df.filter(regex='^(High|Low|Open|Volume)_')
Y = df.filter(regex='^Close_')

# ✅ Scale and Save scalers
x_scaler = MinMaxScaler()
y_scaler = MinMaxScaler()
x_scaled = x_scaler.fit_transform(X)
y_scaled = y_scaler.fit_transform(Y)
joblib.dump(x_scaler, "x_scaler.pkl")
joblib.dump(y_scaler, "y_scaler.pkl")

# ✅ Create sequences
n_days = 20
X_seq, Y_seq = [], []
for i in range(n_days, len(x_scaled)):
    X_seq.append(x_scaled[i - n_days:i])
    Y_seq.append(y_scaled[i])
X_seq, Y_seq = np.array(X_seq), np.array(Y_seq)

# ✅ Split & Train
split = int(0.8 * len(X_seq))
X_train, X_test = X_seq[:split], X_seq[split:]
Y_train, Y_test = Y_seq[:split], Y_seq[split:]

model = Sequential([
    LSTM(64, return_sequences=True, input_shape=(n_days, X_seq.shape[2])),
    LSTM(32),
    Dense(15)
])
model.compile(optimizer='adam', loss='mse')
model.fit(X_train, Y_train, epochs=40, batch_size=32, validation_data=(X_test, Y_test), callbacks=[EarlyStopping(monitor='val_loss', patience=10, restore_best_weights=True)])

# ✅ Save model
model.save("companies_stock.h5")

# ✅ Save last 20 days for React frontend prediction
last_n_days = x_scaled[-n_days:]
np.save("last_20_days.npy", last_n_days)

# ✅ Prediction (next day)
next_input = np.expand_dims(last_n_days, axis=0)
next_day_scaled_pred = model.predict(next_input)
next_day_actual_pred = y_scaler.inverse_transform(next_day_scaled_pred)

# ✅ Print nicely
company_names = list(Y.columns)
print("\n🔮 Tomorrow's Predictions:")
for i, name in enumerate(company_names):
    print(f"{name} ➤ ₹{next_day_actual_pred[0][i]:.2f}")
