
from flask import Flask, request, jsonify
import numpy as np
import joblib, traceback
from flask_cors import CORS
import requests
import datetime
from dotenv import load_dotenv
import os
import yfinance as yf
from nsetools import Nse

load_dotenv()
app = Flask(__name__)
CORS(app)

# ---------- HOME ----------
@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "status": "Backend running 🚀",
        "routes": ["/predict", "/stock", "/news", "/signals"]

    })

# ---------- CONFIG ----------
HF_API_URL = "https://anushka09092004-stock-ml-api.hf.space/predict"

# ---------- CACHE ----------
prediction_cache = {"data": None, "date": None }

def is_cache_valid():
    return False   # 🔥 disable cache for now (important)

# ---------- TICKERS ----------
SORTED_TICKERS = [
    'ADANIENT.NS','ADANIPORTS.NS','BAJFINANCE.NS','BHARTIARTL.NS','COALINDIA.NS',
    'HDFCBANK.NS','HINDUNILVR.NS','ICICIBANK.NS','INFY.NS','LT.NS',
    'MARUTI.NS','RELIANCE.NS','SBIN.NS','TCS.NS'
]

# ---------- FETCH DATA ----------
def fetch_all_ohlcv():
    try:
        data = yf.download(SORTED_TICKERS, period="6mo", progress=False, auto_adjust=True)

        if data.empty:
            return None

        result = {}

        for ticker in SORTED_TICKERS:
            try:
                result[ticker] = {
                    "high": data['High'][ticker].dropna().tail(20).tolist(),
                    "low": data['Low'][ticker].dropna().tail(20).tolist(),
                    "open": data['Open'][ticker].dropna().tail(20).tolist(),
                    "volume": data['Volume'][ticker].dropna().tail(20).tolist()
                }

                # ensure length = 20
                for key in result[ticker]:
                    if len(result[ticker][key]) < 20:
                        diff = 20 - len(result[ticker][key])
                        result[ticker][key] = [0.0]*diff + result[ticker][key]

            except:
                result[ticker] = {
                    "high": [0]*20,
                    "low": [0]*20,
                    "open": [0]*20,
                    "volume": [0]*20
                }

        return result

    except:
        return None

# ---------- BUILD FEATURES (56 FEATURES ONLY) ----------
def build_feature_matrix():
    print("🔥 USING 56 FEATURES")

    all_data = fetch_all_ohlcv()
    if all_data is None:
        raise Exception("Market data fetch failed")

    feature_order = ['high', 'low', 'open', 'volume']

    feature_cols = []

    for feature in feature_order:
        for ticker in SORTED_TICKERS:
            feature_cols.append(all_data[ticker][feature])

    arr = np.array(feature_cols).T   # (20, 56)

    print("RAW SHAPE:", arr.shape)

    # ✅ STRICT CHECK
    if arr.shape != (20, 56):
        raise Exception(f"❌ WRONG SHAPE: {arr.shape}")

    # ---------- SCALER ----------
    if not os.path.exists("x_scaler.pkl"):
        raise Exception("x_scaler.pkl missing")

    x_scaler = joblib.load("x_scaler.pkl")
    arr_scaled = x_scaler.transform(arr)

    final = arr_scaled.reshape(1, 20, 56)

    print("FINAL SHAPE:", final.shape)

    return final

# ---------- PREDICT ----------
@app.route("/predict", methods=["POST"])
def predict():
    try:
        features = build_feature_matrix()

        try:
            hf_response = requests.post(
                HF_API_URL,
                json={"features": features.tolist()},
                timeout=30
            )

            if hf_response.status_code == 200:
                pred = hf_response.json()["prediction"][0]
            else:
                raise Exception("HF failed")

        except:
            print("⚠️ HF FAILED → fallback")

            # fallback safe prediction
            pred = [1000.0] * len(SORTED_TICKERS)

        result = [
            {"company": SORTED_TICKERS[i], "predicted_price": round(float(pred[i]), 2)}
            for i in range(len(SORTED_TICKERS))
        ]

        return jsonify({"prediction": result, "cached": False})

    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

# ---------- STOCK ----------
@app.route("/stock", methods=["GET"])
def get_stock():
    try:
        symbol = request.args.get("symbol", "").upper().replace(".NS", "")
        nse = Nse()
        quote = nse.get_quote(symbol)

        if quote:
            return jsonify({
                "price": quote['lastPrice'],
                "change": quote['change'],
                "percent_change": str(round(quote['pChange'], 2)) + "%"
            })

    except:
        try:
            ticker = yf.Ticker(symbol + ".NS")
            hist = ticker.history(period="1d")

            price = float(hist["Close"].iloc[-1])
            open_price = float(hist["Open"].iloc[-1])
            percent_change = ((price - open_price) / open_price) * 100

            return jsonify({
                "price": round(price, 2),
                "percent_change": str(round(percent_change, 2)) + "%"
            })
        except:
            return jsonify({"error": "Stock fetch failed"}), 500

# ---------- NEWS ----------
@app.route("/news", methods=["GET"])
def get_news():
    try:
        company = request.args.get("company", "")
        GNEWS_API_KEY = os.getenv("GNEWS_API_KEY")

        # ✅ max 10 kiya, sortby publishedAt added
        url = f"https://gnews.io/api/v4/search?q={company}&lang=en&max=10&sortby=publishedAt&token={GNEWS_API_KEY}"
        res = requests.get(url)
        data = res.json()

        articles = [
            {
                "headline": a.get("title", ""),
                "summary": a.get("description", ""),
                "url": a.get("url", ""),
                "publishedAt": a.get("publishedAt", ""),  # ✅ date add kiya
                "image": a.get("image", ""),              # ✅ image add kiya
                "source": a.get("source", {}).get("name", "News")  # ✅ source add kiya
            }
            for a in data.get("articles", [])
        ]

        return jsonify({"articles": articles})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


        # ---------- TECHNICAL SIGNALS ----------
def calculate_signals(ticker):
    try:
        stock = yf.Ticker(ticker)
        df = stock.history(period="3mo")

        if df.empty or len(df) < 50:
            return None

        close = df['Close']
        high  = df['High']
        low   = df['Low']
        vol   = df['Volume']

        # ── RSI ──────────────────────────────
        delta = close.diff()
        gain  = delta.clip(lower=0).rolling(14).mean()
        loss  = -delta.clip(upper=0).rolling(14).mean()
        rs    = gain / loss
        rsi   = float((100 - (100 / (1 + rs))).iloc[-1])

        # ── MACD ─────────────────────────────
        ema12       = close.ewm(span=12).mean()
        ema26       = close.ewm(span=26).mean()
        macd_line   = float((ema12 - ema26).iloc[-1])
        signal_line = float((ema12 - ema26).ewm(span=9).mean().iloc[-1])

        # ── EMA ──────────────────────────────
        ema20 = float(close.ewm(span=20).mean().iloc[-1])
        ema50 = float(close.ewm(span=50).mean().iloc[-1])

        # ── Bollinger Bands ───────────────────
        mid      = close.rolling(20).mean()
        std      = close.rolling(20).std()
        bb_upper = float((mid + 2*std).iloc[-1])
        bb_lower = float((mid - 2*std).iloc[-1])

        # ── ATR ──────────────────────────────
        tr  = np.maximum(
                high - low,
                np.maximum(
                    abs(high - close.shift()),
                    abs(low  - close.shift())
                )
              )
        atr = float(tr.rolling(14).mean().iloc[-1])

        # ── Volume ───────────────────────────
        vol_avg   = float(vol.rolling(20).mean().iloc[-1])
        vol_today = float(vol.iloc[-1])
        vol_spike = vol_today > vol_avg * 1.5

        # ── PRICE — yfinance se pehle ────────
        current_price = float(close.iloc[-1])

        # ── NSE se exact real-time price ─────
        try:
            nse          = Nse()
            symbol_clean = ticker.replace(".NS", "")
            quote        = nse.get_quote(symbol_clean)
            if quote and quote.get('lastPrice'):
                current_price = float(quote['lastPrice'])
        except:
            pass  # yfinance fallback

        atr_pct   = (atr / current_price) * 100
        vol_spike = vol_today > vol_avg * 1.5

        # ── SIGNALS ──────────────────────────
        if rsi < 30:
            rsi_signal = "Oversold 🔴"
            rsi_score  = 70
        elif rsi < 45:
            rsi_signal = "Slightly Oversold 🟡"
            rsi_score  = 55
        elif rsi > 70:
            rsi_signal = "Overbought 🔴"
            rsi_score  = 20
        elif rsi > 60:
            rsi_signal = "Slightly Overbought 🟡"
            rsi_score  = 35
        else:
            rsi_signal = "Neutral 🟢"
            rsi_score  = 50

        if macd_line > signal_line:
            macd_signal = "Bullish 🟢"
            macd_score  = 70
        else:
            macd_signal = "Bearish 🔴"
            macd_score  = 30

        if current_price > ema20 > ema50:
            trend_signal = "Strong Uptrend 🟢"
            trend_score  = 80
        elif current_price > ema20:
            trend_signal = "Mild Uptrend 🟡"
            trend_score  = 60
        elif current_price < ema20 < ema50:
            trend_signal = "Strong Downtrend 🔴"
            trend_score  = 20
        else:
            trend_signal = "Mixed 🟡"
            trend_score  = 40

        if current_price >= bb_upper * 0.98:
            bb_signal = "Near Upper — Caution 🔴"
            bb_score  = 25
        elif current_price <= bb_lower * 1.02:
            bb_signal = "Near Lower — Watch 🟢"
            bb_score  = 70
        else:
            bb_signal = "Mid Band 🟡"
            bb_score  = 50

        vol_signal = "Unusual Spike ⚡" if vol_spike else "Normal 🟢"

        if atr_pct > 3:
            vol_risk = "Very High ⚠️"
        elif atr_pct > 2:
            vol_risk = "High ⚠️"
        else:
            vol_risk = "Normal ✅"

        # ── SETUP SCORE ──────────────────────
        setup_score = int(
            (rsi_score   * 0.25) +
            (macd_score  * 0.25) +
            (trend_score * 0.35) +
            (bb_score    * 0.15)
        )

        # ── VERDICT ──────────────────────────
        if setup_score >= 65:
            verdict       = "BUY"
            verdict_emoji = "🟢"
            action        = "Bullish setup — consider entry with proper risk management"
        elif setup_score <= 35:
            verdict       = "AVOID"
            verdict_emoji = "🔴"
            action        = "Weak setup — expert would avoid or wait"
        else:
            verdict       = "WAIT"
            verdict_emoji = "🟡"
            action        = "No clear setup — wait for confirmation"

        # ── RISK LEVEL ────────────────────────
        if atr_pct > 2.5 or rsi > 70 or rsi < 25:
            risk_level = "High 🔴"
        elif atr_pct > 1.5:
            risk_level = "Medium 🟡"
        else:
            risk_level = "Low 🟢"

        # ── STOP LOSS & TARGET ────────────────
        stop_loss = round(current_price - (atr * 1.5), 2)
        target    = round(current_price + (atr * 3),   2)

        # ── WHY THIS SIGNAL ───────────────────
        reasons = []
        if rsi < 35:
            reasons.append(f"RSI {rsi:.1f} — oversold zone, reversal possible")
        elif rsi > 65:
            reasons.append(f"RSI {rsi:.1f} — overbought, correction possible")
        else:
            reasons.append(f"RSI {rsi:.1f} — neutral zone")

        if macd_line > signal_line:
            reasons.append("MACD bullish crossover — momentum positive")
        else:
            reasons.append("MACD bearish — momentum weak")

        if current_price > ema20 > ema50:
            reasons.append("Price above EMA20 & EMA50 — strong uptrend")
        elif current_price < ema20 < ema50:
            reasons.append("Price below EMA20 & EMA50 — downtrend")

        if vol_spike:
            reasons.append("Unusual volume spike — strong interest detected")

        return {
            "ticker"        : ticker,
            "company"       : ticker.replace(".NS", ""),
            "price"         : round(current_price, 2),
            "setup_score"   : setup_score,
            "verdict"       : verdict,
            "verdict_emoji" : verdict_emoji,
            "action"        : action,
            "risk_level"    : risk_level,
            "stop_loss"     : stop_loss,
            "target"        : target,
            "signals": {
                "rsi"        : round(rsi, 1),
                "rsi_signal" : rsi_signal,
                "macd"       : macd_signal,
                "trend"      : trend_signal,
                "bollinger"  : bb_signal,
                "volume"     : vol_signal,
                "volatility" : vol_risk
            },
            "why": reasons
        }

    except Exception as e:
        return {"ticker": ticker, "error": str(e)}


@app.route("/signals", methods=["GET"])
def get_signals():
    try:
        ticker = request.args.get("ticker", "").upper()

        # Single stock
        if ticker:
            if not ticker.endswith(".NS"):
                ticker += ".NS"
            result = calculate_signals(ticker)
            if result:
                return jsonify(result)
            return jsonify({"error": "Signal calculation failed"}), 500

        # All stocks
        all_signals = []
        for t in SORTED_TICKERS:
            sig = calculate_signals(t)
            if sig:
                all_signals.append(sig)

        # Score ke hisaab se sort karo
        all_signals.sort(key=lambda x: x.get("setup_score", 0), reverse=True)

        return jsonify({
            "signals"    : all_signals,
            "generated_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "total"      : len(all_signals)
        })

    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

# ---------- RUN ----------
if __name__ == "__main__":
    app.run(debug=True)
