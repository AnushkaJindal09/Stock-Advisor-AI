
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
        search_query = f"{company} stock India"
        url = f"https://gnews.io/api/v4/search?q={search_query}&lang=en&max=5&sortby=publishedAt&token={GNEWS_API_KEY}"

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
def timeframe_trend(df):

    try:

        close = df['Close']

        ema20 = close.ewm(span=20).mean().iloc[-1]
        ema50 = close.ewm(span=50).mean().iloc[-1]

        price = close.iloc[-1]

        if price > ema20 > ema50:
            return "Bullish"

        elif price < ema20 < ema50:
            return "Bearish"

        return "Sideways"

    except:
        return "Unknown"


SECTOR_MAP = {

    "RELIANCE.NS": "Energy",
    "INFY.NS": "IT",
    "TCS.NS": "IT",
    "HDFCBANK.NS": "Banking",
    "ICICIBANK.NS": "Banking",
    "SBIN.NS": "Banking",
    "LT.NS": "Infrastructure",
    "MARUTI.NS": "Automobile",
    "BHARTIARTL.NS": "Telecom",
    "HINDUNILVR.NS": "FMCG",
    "COALINDIA.NS": "Energy",
    "ADANIENT.NS": "Conglomerate",
    "ADANIPORTS.NS": "Logistics",
    "BAJFINANCE.NS": "Finance"
}

COMPANY_SEARCH_NAMES = {
    "TCS": "Tata Consultancy Services TCS NSE share price",
    "RELIANCE"   : "Reliance Industries stock",
    "HDFCBANK"   : "HDFC Bank stock",
    "ICICIBANK"  : "ICICI Bank stock",
    "INFY"       : "Infosys stock",
    "SBIN"       : "State Bank India stock",
    "HINDUNILVR" : "Hindustan Unilever stock",
    "BAJFINANCE" : "Bajaj Finance stock",
    "MARUTI"     : "Maruti Suzuki stock",
    "LT"         : "Larsen Toubro stock",
    "ADANIENT"   : "Adani Enterprises stock",
    "ADANIPORTS" : "Adani Ports stock",
    "BHARTIARTL" : "Bharti Airtel stock",
    "COALINDIA"  : "Coal India stock"
}

# ---------- NEWS SENTIMENT ----------
def get_news_sentiment(company_name):
    try:
        GNEWS_API_KEY = os.getenv("GNEWS_API_KEY")
        search_name = COMPANY_SEARCH_NAMES.get(
            company_name,
            f"{company_name} stock India NSE"
        )
        
        url = f"https://gnews.io/api/v4/search?q={search_name}&lang=en&max=5&sortby=publishedAt&country=in&token={GNEWS_API_KEY}"

        
        res = requests.get(url, timeout=5)
        data = res.json()
        articles = data.get("articles", [])

        if not articles:
            return "Neutral", []

        # Simple sentiment keywords
        positive_words = ["surge", "rally", "profit", "growth", "strong",
                         "beat", "record", "gain", "up", "positive",
                         "bullish", "buy", "upgrade", "outperform"]
        negative_words = ["fall", "drop", "loss", "decline", "weak",
                         "miss", "down", "negative", "bearish", "sell",
                         "downgrade", "underperform", "concern", "risk"]

        pos_count = 0
        neg_count = 0
        headlines = []

        for a in articles[:5]:
            title = (a.get("title", "") + " " + a.get("description", "")).lower()
            headlines.append(a.get("title", ""))
            for w in positive_words:
                if w in title:
                    pos_count += 1
            for w in negative_words:
                if w in title:
                    neg_count += 1

        if pos_count > neg_count:
            sentiment = "Positive"
        elif neg_count > pos_count:
            sentiment = "Negative"
        else:
            sentiment = "Neutral"

        return sentiment, headlines[:3]

    except:
        return "Neutral", []



def calculate_signals(ticker):

    try:

        stock = yf.Ticker(ticker)


        df = stock.history(period="6mo", interval="1d")

        if df.empty or len(df) < 60:
            return None

        close = df['Close']
        high = df['High']
        low = df['Low']
        openp = df['Open']
        vol = df['Volume']


        df_15m = stock.history(period="5d", interval="15m")
        df_1h = stock.history(period="1mo", interval="1h")
        df_1d = stock.history(period="6mo", interval="1d")

        multi_timeframe = {
            "15m": timeframe_trend(df_15m),
            "1h": timeframe_trend(df_1h),
            "1d": timeframe_trend(df_1d)
        }

        # ─────────────────────────────────────
        # REAL TIME PRICE
        # ─────────────────────────────────────
        current_price = float(close.iloc[-1])

        try:

            nse = Nse()

            symbol_clean = ticker.replace(".NS", "")

            quote = nse.get_quote(symbol_clean)

            if quote and quote.get("lastPrice"):
                current_price = float(quote["lastPrice"])

        except:
            pass

        previous_close = float(close.iloc[-2])

        change = round(current_price - previous_close, 2)

        percent_change = round(
            (change / previous_close) * 100,
            2
        )

        # ─────────────────────────────────────
        # RSI
        # ─────────────────────────────────────
        delta = close.diff()

        gain = delta.clip(lower=0)
        loss = -delta.clip(upper=0)

        avg_gain = gain.rolling(14).mean()
        avg_loss = loss.rolling(14).mean()

        rs = avg_gain / avg_loss

        rsi = float(
            (100 - (100 / (1 + rs))).iloc[-1]
        )

        # ─────────────────────────────────────
        # MACD
        # ─────────────────────────────────────
        ema12 = close.ewm(span=12).mean()
        ema26 = close.ewm(span=26).mean()

        macd_series = ema12 - ema26

        macd_line = float(macd_series.iloc[-1])

        signal_series = macd_series.ewm(span=9).mean()

        signal_line = float(signal_series.iloc[-1])

        macd_histogram = round(
            macd_line - signal_line,
            2
        )

        # ─────────────────────────────────────
        # EMA
        # ─────────────────────────────────────
        ema20 = float(close.ewm(span=20).mean().iloc[-1])

        ema50 = float(close.ewm(span=50).mean().iloc[-1])

        ema200 = float(close.ewm(span=200).mean().iloc[-1])

        # ─────────────────────────────────────
        # TREND STRENGTH
        # ─────────────────────────────────────
        trend_strength = round(
            abs((ema20 - ema50) / ema50) * 100,
            2
        )

        # ─────────────────────────────────────
        # BOLLINGER BANDS
        # ─────────────────────────────────────
        mid = close.rolling(20).mean()

        std = close.rolling(20).std()

        bb_upper = float((mid + 2 * std).iloc[-1])

        bb_lower = float((mid - 2 * std).iloc[-1])

        # ─────────────────────────────────────
        # ATR
        # ─────────────────────────────────────
        tr = np.maximum(
            high - low,
            np.maximum(
                abs(high - close.shift()),
                abs(low - close.shift())
            )
        )

        atr = float(tr.rolling(14).mean().iloc[-1])

        atr_pct = round(
            (atr / current_price) * 100,
            2
        )

        # ─────────────────────────────────────
        # VOLUME
        # ─────────────────────────────────────
        vol_avg = float(
            vol.rolling(20).mean().iloc[-1]
        )

        vol_today = float(vol.iloc[-1])

        volume_ratio = round(
            vol_today / vol_avg,
            2
        )

        vol_spike = volume_ratio >= 1.5

        # ─────────────────────────────────────
        # SUPPORT / RESISTANCE
        # ─────────────────────────────────────
        support = round(
            float(low.tail(20).min()),
            2
        )

        resistance = round(
            float(high.tail(20).max()),
            2
        )

        # ─────────────────────────────────────
        # BREAKOUT
        # ─────────────────────────────────────
        breakout = (
            current_price > resistance * 0.995
            and volume_ratio > 1.5
        )

        breakdown = (
            current_price < support * 1.005
            and volume_ratio > 1.5
        )

        # ─────────────────────────────────────
        # BREAKOUT STRENGTH
        # ─────────────────────────────────────
        if breakout and volume_ratio > 2:
            breakout_strength = "Strong"

        elif breakout:
            breakout_strength = "Moderate"

        else:
            breakout_strength = "None"

        # ─────────────────────────────────────
        # TREND
        # ─────────────────────────────────────
        if current_price > ema20 > ema50:

            trend_signal = "Strong Uptrend"

            trend_score = 85

        elif current_price > ema20:

            trend_signal = "Mild Uptrend"

            trend_score = 65

        elif current_price < ema20 < ema50:

            trend_signal = "Strong Downtrend"

            trend_score = 20

        else:

            trend_signal = "Sideways"

            trend_score = 45

        # ─────────────────────────────────────
        # RSI SIGNAL
        # ─────────────────────────────────────
        if rsi < 30:

            rsi_signal = "Oversold"

            rsi_score = 75

        elif rsi < 45:

            rsi_signal = "Weak"

            rsi_score = 55

        elif rsi > 70:

            rsi_signal = "Overbought"

            rsi_score = 20

        elif rsi > 60:

            rsi_signal = "Strong"

            rsi_score = 40

        else:

            rsi_signal = "Neutral"

            rsi_score = 50

        # ─────────────────────────────────────
        # MACD SIGNAL
        # ─────────────────────────────────────
        if macd_line > signal_line:

            macd_signal = "Bullish"

            macd_score = 75

        else:

            macd_signal = "Bearish"

            macd_score = 25

        # ─────────────────────────────────────
        # BOLLINGER SIGNAL
        # ─────────────────────────────────────
        if current_price >= bb_upper * 0.98:

            bb_signal = "Upper Band"

            bb_score = 30

        elif current_price <= bb_lower * 1.02:

            bb_signal = "Lower Band"

            bb_score = 70

        else:

            bb_signal = "Mid Band"

            bb_score = 50

        # ─────────────────────────────────────
        # CONFIDENCE
        # ─────────────────────────────────────
        confidence = int(
            (
                trend_score * 0.35 +
                rsi_score * 0.20 +
                macd_score * 0.25 +
                bb_score * 0.10 +
                min(volume_ratio * 20, 100) * 0.10
            )
        )

        setup_score = confidence

        # ─────────────────────────────────────
        # VERDICT
        # ─────────────────────────────────────
        if confidence >= 70:

            verdict = "BUY"

            verdict_emoji = "🟢"

        elif confidence <= 35:

            verdict = "AVOID"

            verdict_emoji = "🔴"

        else:

            verdict = "WAIT"

            verdict_emoji = "🟡"

        # ─────────────────────────────────────
        # SIGNAL QUALITY
        # ─────────────────────────────────────
        if (
            breakout and
            volume_ratio > 1.8 and
            macd_line > signal_line and
            current_price > ema20
        ):

            signal_quality = "A+"

        elif (
            macd_line > signal_line and
            current_price > ema20
        ):

            signal_quality = "B"

        else:

            signal_quality = "C"

        # ─────────────────────────────────────
        # RISK
        # ─────────────────────────────────────
        if atr_pct > 3 or rsi > 75:

            risk_level = "High"

        elif atr_pct > 1.8:

            risk_level = "Medium"

        else:

            risk_level = "Low"

        # ─────────────────────────────────────
        # ENTRY
        # ─────────────────────────────────────
        entry_low = round(
            current_price - (atr * 0.5),
            2
        )

        entry_high = round(
            current_price + (atr * 0.5),
            2
        )

        stop_loss = round(
            current_price - (atr * 1.5),
            2
        )

        target = round(
            current_price + (atr * 3),
            2
        )

        # ─────────────────────────────────────
        # UPSIDE / DOWNSIDE
        # ─────────────────────────────────────
        upside_percent = round(
            ((target - current_price) / current_price) * 100,
            2
        )

        downside_percent = round(
            ((current_price - stop_loss) / current_price) * 100,
            2
        )

        # ─────────────────────────────────────
        # ENTRY TIMING
        # ─────────────────────────────────────
        if breakout and volume_ratio > 1.5:

            entry_timing = "Immediate"

        elif verdict == "BUY":

            entry_timing = "Wait for Dip"

        else:

            entry_timing = "Avoid Entry"

        # ─────────────────────────────────────
        # RISK REWARD
        # ─────────────────────────────────────
        risk = current_price - stop_loss

        reward = target - current_price

        if risk > 0:

            risk_reward = round(
                reward / risk,
                2
            )

        else:

            risk_reward = 0

        # ─────────────────────────────────────
        # MARKET SENTIMENT
        # ─────────────────────────────────────
        if confidence >= 70:

            market_sentiment = "Bullish"

        elif confidence <= 35:

            market_sentiment = "Bearish"

        else:

            market_sentiment = "Neutral"

        # ─────────────────────────────────────
        # INSTITUTIONAL ACTIVITY
        # ─────────────────────────────────────
        if volume_ratio >= 2 and breakout:

            institutional_activity = (
                "Possible Smart Money Buying"
            )

        elif volume_ratio >= 2 and breakdown:

            institutional_activity = (
                "Possible Institutional Selling"
            )

        else:

            institutional_activity = (
                "No Major Activity"
            )

        # ─────────────────────────────────────
        # SMART ALERTS
        # ─────────────────────────────────────
        alerts = []

        if breakout:
            alerts.append("Breakout Watch")

        if breakdown:
            alerts.append("Breakdown Risk")

        if rsi < 30:
            alerts.append("Oversold Opportunity")

        if rsi > 70:
            alerts.append("Overbought Warning")

        # ─────────────────────────────────────
        # CONFIDENCE REASON
        # ─────────────────────────────────────
        confidence_reason = []

        if trend_score > 70:

            confidence_reason.append(
                "Strong trend structure"
            )

        if macd_score > 70:

            confidence_reason.append(
                "Momentum confirmation"
            )

        if volume_ratio > 1.5:

            confidence_reason.append(
                "Volume participation strong"
            )

        # ─────────────────────────────────────
        # MARKET STATUS
        # ─────────────────────────────────────
        now = datetime.datetime.now()

        if (
            now.hour >= 9 and
            now.hour < 15
        ):

            market_status = "OPEN"

        else:

            market_status = "CLOSED"


        # ─────────────────────────────────────
        # NEWS SENTIMENT
        # ─────────────────────────────────────
        company_name = ticker.replace(".NS", "")
        news_sentiment, news_headlines = get_news_sentiment(company_name)

        # ─────────────────────────────────────
        # SECTOR
        # ─────────────────────────────────────
        sector = SECTOR_MAP.get(
            ticker,
            "Other"
        )

        # ─────────────────────────────────────
        # TRADE PLAN
        # ─────────────────────────────────────
        trade_plan = {

            "entry_strategy":
                f"Preferred accumulation near ₹{entry_low} - ₹{entry_high}",

            "stop_loss_strategy":
                f"Strict SL below ₹{stop_loss}",

            "target_strategy":
                f"Potential upside towards ₹{target}",

            "position_sizing":
                "Risk only 1-2% capital on this trade",

            "best_for":
                "Swing Traders"
                if atr_pct < 3
                else "Intraday High Risk Traders"
        }

        # ─────────────────────────────────────
        # ACTION
        # ─────────────────────────────────────
        if verdict == "BUY":

            action = (
                "Momentum strong hai. Entry possible hai "
                "with proper stop loss management."
            )

        elif verdict == "AVOID":

            action = (
                "Structure weak hai. Better setups ka "
                "wait karna safer hoga."
            )

        else:

            action = (
                "Mixed confirmation. Clear breakout "
                "ya reversal ka wait karo."
            )

        # ─────────────────────────────────────
        # REASONS
        # ─────────────────────────────────────
        reasons = []

        reasons.append(
            f"RSI at {round(rsi,1)} indicates "
            f"{rsi_signal.lower()} momentum."
        )

        if macd_line > signal_line:

            reasons.append(
                "MACD bullish crossover detected."
            )

        else:

            reasons.append(
                "MACD still bearish."
            )

        if current_price > ema20 > ema50:

            reasons.append(
                "Price trading above EMA20 & EMA50 "
                "confirms strength."
            )

        elif current_price < ema20 < ema50:

            reasons.append(
                "Price below key EMAs shows weakness."
            )

        if vol_spike:

            reasons.append(
                f"Volume spike detected "
                f"({volume_ratio}x average volume)."
            )

        if breakout:

            reasons.append(
                "Potential breakout setup forming "
                "near resistance."
            )

        if breakdown:

            reasons.append(
                "Potential breakdown risk near support."
            )

        # ─────────────────────────────────────
        # FINAL RESPONSE
        # ─────────────────────────────────────
        return {

            "ticker": ticker,

            "company": ticker.replace(".NS", ""),

            "sector": sector,

            "price": round(current_price, 2),

            "change": change,

            "percent_change": percent_change,

            "setup_score": setup_score,

            "confidence": confidence,

            "signal_quality": signal_quality,

            "trend_strength": trend_strength,

            "verdict": verdict,

            "verdict_emoji": verdict_emoji,

            "market_sentiment": market_sentiment,

            "news_sentiment": news_sentiment,

            "news_headlines": news_headlines,

            "risk_level": risk_level,

            "support": support,

            "resistance": resistance,

            "entry_timing": entry_timing,

            "entry_zone": {

                "low": entry_low,
                "high": entry_high
            },

            "stop_loss": stop_loss,

            "target": target,

            "upside_percent": upside_percent,

            "downside_percent": downside_percent,

            "risk_reward": risk_reward,

            "volume_ratio": volume_ratio,

            "breakout": breakout,

            "breakdown": breakdown,

            "breakout_strength": breakout_strength,

            "institutional_activity":
                institutional_activity,

            "market_status":
                market_status,

            "multi_timeframe":
                multi_timeframe,

            "trade_plan":
                trade_plan,

            "confidence_reason":
                confidence_reason,

            "alerts":
                alerts,

            "mini_chart": [
                round(x, 2)
                for x in close.tail(20).tolist()
            ],

            "action": action,

            "signals": {

                "rsi": round(rsi, 1),

                "rsi_signal": rsi_signal,

                "macd": macd_signal,

                "macd_histogram": macd_histogram,

                "trend": trend_signal,

                "bollinger": bb_signal,

                "volatility": f"{atr_pct}%",

                "ema20": round(ema20, 2),

                "ema50": round(ema50, 2),

                "ema200": round(ema200, 2)
            },

            "why": reasons
        }

    except Exception as e:

        traceback.print_exc()

        return {
            "ticker": ticker,
            "error": str(e)
        }

# ---------- SIGNALS ROUTE ----------
@app.route("/signals", methods=["GET"])
def get_signals():

    try:

        ticker = request.args.get("ticker", "").upper()

        # SINGLE STOCK
        if ticker:

            if not ticker.endswith(".NS"):
                ticker += ".NS"

            result = calculate_signals(ticker)

            if result:
                return jsonify(result)

            return jsonify({
                "error": "Signal calculation failed"
            }), 500

        # ALL STOCKS
        all_signals = []

        for t in SORTED_TICKERS:

            sig = calculate_signals(t)

            if sig and not sig.get("error"):
                all_signals.append(sig)

        # SORT BY SCORE
        all_signals.sort(
            key=lambda x: x.get("setup_score", 0),
            reverse=True
        )

        return jsonify({

            "signals": all_signals,

            "generated_at":
                datetime.datetime.now().strftime(
                    "%Y-%m-%d %H:%M:%S"
                ),

            "total": len(all_signals)
        })

    except Exception as e:

        traceback.print_exc()

        return jsonify({
            "error": str(e)
        }), 500

# ---------- RUN ----------
if __name__ == "__main__":
    app.run(debug=True)
