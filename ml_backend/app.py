


from flask import Flask, request, jsonify
import numpy as np
import joblib
import traceback
from flask_cors import CORS
import requests
import datetime
from dotenv import load_dotenv
import os
import yfinance as yf
from nsetools import Nse
import pytz

load_dotenv()

app = Flask(__name__)
CORS(app)

# ─────────────────────────────────────
# CONFIG
# ─────────────────────────────────────
HF_API_URL = "https://anushka09092004-stock-ml-api.hf.space/predict"

SORTED_TICKERS = [
    'ADANIENT.NS',
    'ADANIPORTS.NS',
    'BAJFINANCE.NS',
    'BHARTIARTL.NS',
    'COALINDIA.NS',
    'HDFCBANK.NS',
    'HINDUNILVR.NS',
    'ICICIBANK.NS',
    'INFY.NS',
    'LT.NS',
    'MARUTI.NS',
    'RELIANCE.NS',
    'SBIN.NS',
    'TCS.NS'
]

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
    "RELIANCE": "Reliance Industries stock",
    "HDFCBANK": "HDFC Bank stock",
    "ICICIBANK": "ICICI Bank stock",
    "INFY": "Infosys stock",
    "SBIN": "State Bank India stock",
    "HINDUNILVR": "Hindustan Unilever stock",
    "BAJFINANCE": "Bajaj Finance stock",
    "MARUTI": "Maruti Suzuki stock",
    "LT": "Larsen Toubro stock",
    "ADANIENT": "Adani Enterprises stock",
    "ADANIPORTS": "Adani Ports stock",
    "BHARTIARTL": "Bharti Airtel stock",
    "COALINDIA": "Coal India stock"
}

# ─────────────────────────────────────
# CACHE
# ─────────────────────────────────────
market_cache = {
    "data": None,
    "time": None
}

CACHE_MINUTES = 5

# NEWS CACHE
news_cache = {}
NEWS_CACHE_MINUTES = 60

# SIGNAL CACHE
signal_cache = {
    "data": {},
    "time": {}
}

SIGNAL_CACHE_MINUTES = 5


# ─────────────────────────────────────
# HOME
# ─────────────────────────────────────
@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "status": "Backend running 🚀",
        "routes": [
            "/predict",
            "/stock",
            "/news",
            "/signals"
        ]
    })


# ─────────────────────────────────────
# CACHE CHECK
# ─────────────────────────────────────
def cache_valid():

    if market_cache["time"] is None:
        return False

    diff = datetime.datetime.now() - market_cache["time"]

    return diff.total_seconds() < CACHE_MINUTES * 60


# ─────────────────────────────────────
# FETCH OHLCV
# ─────────────────────────────────────
def fetch_all_ohlcv():

    try:

        if cache_valid():
            return market_cache["data"]

        data = yf.download(
            SORTED_TICKERS,
            period="6mo",
            progress=False,
            auto_adjust=True,
            threads=True
        )

        if data.empty:
            return None

        result = {}

        for ticker in SORTED_TICKERS:

            try:

                result[ticker] = {

                    "high":
                        data['High'][ticker]
                        .dropna()
                        .tail(20)
                        .tolist(),

                    "low":
                        data['Low'][ticker]
                        .dropna()
                        .tail(20)
                        .tolist(),

                    "open":
                        data['Open'][ticker]
                        .dropna()
                        .tail(20)
                        .tolist(),

                    "volume":
                        data['Volume'][ticker]
                        .dropna()
                        .tail(20)
                        .tolist()
                }

                for key in result[ticker]:

                    if len(result[ticker][key]) < 20:

                        diff = 20 - len(result[ticker][key])

                        result[ticker][key] = (
                            [0.0] * diff +
                            result[ticker][key]
                        )

            except:

                result[ticker] = {
                    "high": [0] * 20,
                    "low": [0] * 20,
                    "open": [0] * 20,
                    "volume": [0] * 20
                }

        market_cache["data"] = result
        market_cache["time"] = datetime.datetime.now()

        return result

    except:
        return None


# ─────────────────────────────────────
# FEATURE MATRIX
# ─────────────────────────────────────
def build_feature_matrix():

    all_data = fetch_all_ohlcv()

    if all_data is None:
        raise Exception("Market data fetch failed")

    feature_order = ['high', 'low', 'open', 'volume']

    feature_cols = []

    for feature in feature_order:

        for ticker in SORTED_TICKERS:

            feature_cols.append(
                all_data[ticker][feature]
            )

    arr = np.array(feature_cols).T

    if arr.shape != (20, 56):
        raise Exception(f"Wrong shape: {arr.shape}")

    if not os.path.exists("x_scaler.pkl"):
        raise Exception("x_scaler.pkl missing")

    x_scaler = joblib.load("x_scaler.pkl")

    arr_scaled = x_scaler.transform(arr)

    final = arr_scaled.reshape(1, 20, 56)

    return final


# ─────────────────────────────────────
# PREDICT
# ─────────────────────────────────────
@app.route("/predict", methods=["POST"])
def predict():

    try:

        features = build_feature_matrix()

        hf_response = requests.post(
            HF_API_URL,
            json={
                "features": features.tolist()
            },
            timeout=30
        )

        if hf_response.status_code != 200:

            return jsonify({
                "error":
                    "Prediction service unavailable"
            }), 503

        pred = hf_response.json()["prediction"][0]

        result = []

        for i in range(len(SORTED_TICKERS)):

            result.append({

                "company":
                    SORTED_TICKERS[i],

                "predicted_price":
                    round(float(pred[i]), 2)
            })

        return jsonify({
            "prediction": result,
            "model_status": "active"
        })

    except Exception as e:

        traceback.print_exc()

        return jsonify({
            "error": str(e)
        }), 500


# ─────────────────────────────────────
# STOCK
# ─────────────────────────────────────
@app.route("/stock", methods=["GET"])
def get_stock():

    try:

        symbol = (
            request.args
            .get("symbol", "")
            .upper()
            .replace(".NS", "")
        )

        # NIFTY50 — index hai, nsetools se nahi aata, yfinance use karo
        if symbol in ("NIFTY50", "NIFTY"):
            try:
                ticker         = yf.Ticker("^NSEI")
                hist           = ticker.history(period="5d")
                price          = float(ticker.fast_info["last_price"])
                previous_close = float(hist["Close"].iloc[-2])  # last completed day close
                change         = round(price - previous_close, 2)
                percent_change = round((change / previous_close) * 100, 2)
                return jsonify({
                    "price":          round(price, 2),
                    "change":         change,
                    "percent_change": f"{'+' if percent_change >= 0 else ''}{percent_change}%"
                })
            except Exception as e:
                return jsonify({"error": str(e)}), 500

        nse = Nse()

        quote = nse.get_quote(symbol)

        if quote:

            return jsonify({

                "price":
                    quote.get('lastPrice'),

                "change":
                    quote.get('change'),

                "percent_change":
                    str(
                        round(
                            quote.get('pChange', 0),
                            2
                        )
                    ) + "%",

                "price_source":
                    "NSE Live"
            })

    except:
        pass

    try:

        ticker = yf.Ticker(symbol + ".NS")

        hist = ticker.history(period="2d")

        if hist.empty:
            raise Exception("No stock data")

        price = float(hist["Close"].iloc[-1])

        previous_close = float(hist["Close"].iloc[-2])

        percent_change = (
            (price - previous_close)
            / previous_close
        ) * 100

        return jsonify({

            "price":
                round(price, 2),

            "change":
                round(
                    price - previous_close,
                    2
                ),

            "percent_change":
                str(
                    round(percent_change, 2)
                ) + "%",

            "price_source":
                "Yahoo Finance Delayed"
        })

    except Exception as e:

        return jsonify({
            "error": str(e)
        }), 500


# ─────────────────────────────────────
# NEWS
# ─────────────────────────────────────
@app.route("/news", methods=["GET"])
def get_news():

    try:

        company = request.args.get("company", "")

        GNEWS_API_KEY = os.getenv("GNEWS_API_KEY")

        search_query = f"{company} stock India"

        url = (
            "https://gnews.io/api/v4/search"
            f"?q={search_query}"
            "&lang=en"
            "&country=in"
            "&max=5"
            "&sortby=publishedAt"
            f"&token={GNEWS_API_KEY}"
        )

        res = requests.get(url, timeout=10)

        data = res.json()

        articles = []

        for a in data.get("articles", []):

            articles.append({

                "headline":
                    a.get("title", ""),

                "summary":
                    a.get("description", ""),

                "url":
                    a.get("url", ""),

                "publishedAt":
                    a.get("publishedAt", ""),

                "image":
                    a.get("image", ""),

                "source":
                    a.get("source", {})
                    .get("name", "News")
            })

        return jsonify({
            "articles": articles,
            "note": "News sentiment is AI-generated and approximate."
        })

    except Exception as e:

        return jsonify({
            "error": str(e)
        }), 500


# ─────────────────────────────────────
# TIMEFRAME TREND
# ─────────────────────────────────────
def timeframe_trend(df):

    try:

        if df.empty:
            return "Unknown"

        close = df['Close']

        ema20 = (
            close
            .ewm(span=20)
            .mean()
            .iloc[-1]
        )

        ema50 = (
            close
            .ewm(span=50)
            .mean()
            .iloc[-1]
        )

        price = close.iloc[-1]

        if price > ema20 > ema50:
            return "Bullish"

        elif price < ema20 < ema50:
            return "Bearish"

        return "Sideways"

    except:
        return "Unknown"


# ─────────────────────────────────────
# NEWS SENTIMENT
# ─────────────────────────────────────
def get_news_sentiment(company_name):

    try:

        current_time = datetime.datetime.now()

        if company_name in news_cache:

            cached = news_cache[company_name]

            age = (
                current_time - cached["time"]
            ).total_seconds() / 60

            if age < NEWS_CACHE_MINUTES:
                return cached["data"]

        GNEWS_API_KEY = os.getenv("GNEWS_API_KEY")

        search_name = COMPANY_SEARCH_NAMES.get(
            company_name,
            f"{company_name} stock India NSE"
        )

        url = (
            "https://gnews.io/api/v4/search"
            f"?q={search_name}"
            "&lang=en"
            "&country=in"
            "&max=5"
            "&sortby=publishedAt"
            f"&token={GNEWS_API_KEY}"
        )

        res = requests.get(url, timeout=5)

        data = res.json()

        articles = data.get("articles", [])

        if not articles:

            result = ("Neutral", [])

            news_cache[company_name] = {
                "data": result,
                "time": current_time
            }

            return result

        positive_words = [
            "surge",
            "rally",
            "profit",
            "growth",
            "strong",
            "beat",
            "record",
            "gain",
            "bullish",
            "upgrade"
        ]

        negative_words = [
            "fall",
            "drop",
            "loss",
            "decline",
            "weak",
            "miss",
            "bearish",
            "downgrade",
            "risk",
            "concern"
        ]

        pos_count = 0
        neg_count = 0

        headlines = []

        for a in articles[:5]:

            text = (
                a.get("title", "") +
                " " +
                a.get("description", "")
            ).lower()

            headlines.append(
                a.get("title", "")
            )

            for word in positive_words:

                if word in text:
                    pos_count += 1

            for word in negative_words:

                if word in text:
                    neg_count += 1

        if pos_count > neg_count:
            sentiment = "Positive"

        elif neg_count > pos_count:
            sentiment = "Negative"

        else:
            sentiment = "Neutral"

        result = (
            sentiment,
            headlines[:3]
        )

        news_cache[company_name] = {
            "data": result,
            "time": current_time
        }

        return result

    except:
        return "Neutral", []


# ─────────────────────────────────────
# MARKET STATUS
# ─────────────────────────────────────
def get_market_status():

    IST = pytz.timezone("Asia/Kolkata")

    now = datetime.datetime.now(IST)

    if (
        now.weekday() < 5 and
        (
            (
                now.hour == 9 and
                now.minute >= 15
            )
            or
            (9 < now.hour < 15)
            or
            (
                now.hour == 15 and
                now.minute <= 30
            )
        )
    ):
        return "OPEN"

    return "CLOSED"


    # ─────────────────────────────────────
# SIGNALS ENGINE
# ─────────────────────────────────────
def calculate_signals(ticker):

    try:

        now = datetime.datetime.now(pytz.timezone('Asia/Kolkata'))

        # SIGNAL CACHE CHECK
        if ticker in signal_cache["time"]:

            age = (
                now - signal_cache["time"][ticker]
            ).total_seconds() / 60

            if age < SIGNAL_CACHE_MINUTES:

                return signal_cache["data"][ticker]

        stock = yf.Ticker(ticker)

        df = stock.history(
            period="6mo",
            interval="1d"
        )

        if df.empty or len(df) < 60:
            return None

        close = df['Close']
        high = df['High']
        low = df['Low']
        vol = df['Volume']

        # MULTI TIMEFRAME
        df_15m = stock.history(
            period="5d",
            interval="15m"
        )

        df_1h = stock.history(
            period="1mo",
            interval="1h"
        )

        multi_timeframe = {

            "15m":
                timeframe_trend(df_15m),

            "1h":
                timeframe_trend(df_1h),

            "1d":
                timeframe_trend(df)
        }

        # PRICE
        current_price = float(close.iloc[-1])

        price_source = "Yahoo Finance Delayed"

        try:

            nse = Nse()

            quote = nse.get_quote(
                ticker.replace(".NS", "")
            )

            if quote and quote.get("lastPrice"):

                current_price = float(
                    quote["lastPrice"]
                )

                price_source = "NSE Live"

        except:
            pass

        previous_close = float(close.iloc[-2])

        change = round(
            current_price - previous_close,
            2
        )

        percent_change = round(
            (
                change / previous_close
            ) * 100,
            2
        )

        # RSI
        delta = close.diff()

        gain = delta.clip(lower=0)

        loss = -delta.clip(upper=0)

        avg_gain = gain.rolling(14).mean()

        avg_loss = loss.rolling(14).mean()

        rs = avg_gain / avg_loss

        rsi = float(
            (
                100 -
                (100 / (1 + rs))
            ).iloc[-1]
        )

        if rsi >= 70:
            rsi_signal = "Overbought"
            rsi_score = 20

        elif rsi >= 60:
            rsi_signal = "Bullish Momentum"
            rsi_score = 70

        elif rsi <= 30:
            rsi_signal = "Oversold"
            rsi_score = 75

        elif rsi <= 40:
            rsi_signal = "Weak Momentum"
            rsi_score = 40

        else:
            rsi_signal = "Neutral"
            rsi_score = 50

        # MACD
        ema12 = close.ewm(span=12).mean()

        ema26 = close.ewm(span=26).mean()

        macd_series = ema12 - ema26

        signal_series = (
            macd_series
            .ewm(span=9)
            .mean()
        )

        macd_line = float(
            macd_series.iloc[-1]
        )

        signal_line = float(
            signal_series.iloc[-1]
        )

        macd_histogram = round(
            macd_line - signal_line,
            2
        )

        if macd_line > signal_line:
            macd_signal = "Bullish"
            macd_score = 75
        else:
            macd_signal = "Bearish"
            macd_score = 25

        # EMA
        ema20 = float(
            close.ewm(span=20).mean().iloc[-1]
        )

        ema50 = float(
            close.ewm(span=50).mean().iloc[-1]
        )

        ema200 = float(
            close.ewm(span=200).mean().iloc[-1]
        )

        # TREND
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

        # BOLLINGER
        mid = close.rolling(20).mean()

        std = close.rolling(20).std()

        bb_upper = float(
            (mid + 2 * std).iloc[-1]
        )

        bb_lower = float(
            (mid - 2 * std).iloc[-1]
        )

        if current_price >= bb_upper * 0.98:
            bb_signal = "Upper Band"
            bb_score = 30

        elif current_price <= bb_lower * 1.02:
            bb_signal = "Lower Band"
            bb_score = 70

        else:
            bb_signal = "Mid Band"
            bb_score = 50

        # ATR
        tr = np.maximum(
            high - low,
            np.maximum(
                abs(high - close.shift()),
                abs(low - close.shift())
            )
        )

        atr = float(
            tr.rolling(14).mean().iloc[-1]
        )

        atr_pct = round(
            (atr / current_price) * 100,
            2
        )

        # VOLUME
        # VOLUME — real-time from nsetools, avg from completed days only
        try:
            quote_full = nse.get_quote(ticker.replace(".NS", ""), all_data=True)
            vol_today  = float(quote_full['marketDeptOrderBook']['tradeInfo']['tradedVolume'])
        except:
            vol_today = float(vol.iloc[-1])  # fallback to yfinance if nsetools fails

        # Average from previous 20 COMPLETED days — exclude today's partial candle
        vol_avg      = float(vol.iloc[:-1].rolling(20).mean().iloc[-1])
        volume_ratio = round(vol_today / vol_avg, 2) if vol_avg > 0 else 1.0
        vol_spike    = volume_ratio >= 1.5

        # SUPPORT / RESISTANCE
        support = round(
            low.rolling(20).min().iloc[-1],
            2
        )

        resistance = round(
            high.rolling(20).max().iloc[-1],
            2
        )

        # BREAKOUT
        breakout = (
            current_price >= resistance * 0.995
            and volume_ratio > 1.5
        )

        breakdown = (
            current_price <= support * 1.005
            and volume_ratio > 1.5
        )

        # BREAKOUT STRENGTH
        breakout_strength = 0

        if resistance > 0:

            breakout_strength = round(

                (
                    (
                        current_price - resistance
                    ) / resistance
                ) * 100,

                2
            )

            if breakout_strength < 0:
                breakout_strength = 0

        # TECHNICAL STRENGTH SCORE
        technical_strength = int(

            (
                trend_score * 0.35 +
                rsi_score * 0.20 +
                macd_score * 0.25 +
                bb_score * 0.10 +
                min(volume_ratio * 20, 100) * 0.10
            )
        )

        # CONFIDENCE SCORE
        confidence_score = technical_strength

        # VERDICT
        if technical_strength >= 70:

            verdict = "BUY"
            verdict_emoji = "🟢"

        elif technical_strength <= 35:

            verdict = "AVOID"
            verdict_emoji = "🔴"

        else:

            verdict = "WAIT"
            verdict_emoji = "🟡"

        if technical_strength >= 70:
            market_sentiment = "Bullish"

        elif technical_strength <= 35:
            market_sentiment = "Bearish"

        else:
            market_sentiment = "Neutral"

        # SIGNAL QUALITY
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

        # RISK
        if atr_pct > 3 or rsi > 75:
            risk_level = "High"

        elif atr_pct > 1.8:
            risk_level = "Medium"

        else:
            risk_level = "Low"

        # TARGETS
        entry_low = round(
            current_price - atr * 0.5,
            2
        )

        entry_high = round(
            current_price + atr * 0.5,
            2
        )

        stop_loss = round(
            current_price - atr * 1.5,
            2
        )

        target = round(
            current_price + atr * 3,
            2
        )

        upside_percent = round(
            (
                (target - current_price)
                / current_price
            ) * 100,
            2
        )

        downside_percent = round(
            (
                (current_price - stop_loss)
                / current_price
            ) * 100,
            2
        )

        risk = current_price - stop_loss

        reward = target - current_price

        risk_reward = round(
            reward / risk,
            2
        ) if risk > 0 else 0

        if breakout and volume_ratio > 1.5:
            entry_timing = "Immediate"

        elif verdict == "BUY":
            entry_timing = "Wait for Dip"

        else:
            entry_timing = "Avoid Entry"

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
                else "High Risk Traders"
        }
                # ACTION
        if verdict == "BUY":

            action = (
                "Potential bullish setup detected."
            )

        elif verdict == "WAIT":

            action = (
                "Wait for stronger confirmation."
            )

        else:

            action = (
                "Risk currently high."
            )

        # INSTITUTIONAL
        if volume_ratio >= 2 and breakout:

            institutional_activity = (
                "High Volume Breakout Activity"
            )

        elif volume_ratio >= 2 and breakdown:

            institutional_activity = (
                "High Volume Selling Pressure"
            )

        else:

            institutional_activity = (
                "Normal Market Activity"
            )

        # NEWS SENTIMENT
        company_name = ticker.replace(".NS", "")

        news_sentiment, news_headlines = (
            get_news_sentiment(company_name)
        )

        # REASONS
        reasons = []

        reasons.append(
            f"RSI at {round(rsi,1)} "
            f"shows {rsi_signal.lower()}."
        )

        if macd_line > signal_line:
            reasons.append(
                "MACD bullish crossover detected."
            )
        else:
            reasons.append(
                "MACD remains bearish."
            )

        if current_price > ema20 > ema50:
            reasons.append(
                "Price trading above EMA20 & EMA50."
            )

        if vol_spike:
            reasons.append(
                f"Volume spike detected "
                f"({volume_ratio}x average)."
            )

        if breakout:
            reasons.append(
                "Potential breakout near resistance."
            )

        # ALERTS
        alerts = []

        if breakout:
            alerts.append(
                "Possible breakout zone."
            )

        if breakdown:
            alerts.append(
                "Possible breakdown risk."
            )

        if rsi >= 70:
            alerts.append(
                "RSI indicates overbought conditions."
            )

        if rsi <= 30:
            alerts.append(
                "RSI indicates oversold conditions."
            )

        if vol_spike:
            alerts.append(
                "Unusual volume activity detected."
            )

        # FINAL RESPONSE
        result = {

            "ticker": ticker,

            "alerts": alerts,

            "company":
                ticker.replace(".NS", ""),

            "action":
                action,

            "sector":
                SECTOR_MAP.get(
                    ticker,
                    "Other"
                ),

            "market_sentiment":
                market_sentiment,

            "entry_timing":
                entry_timing,

            "trade_plan":
                trade_plan,

            "breakout_strength":
                breakout_strength,

            "price":
                round(current_price, 2),

            "price_source":
                price_source,

            "change":
                change,

            "percent_change":
                percent_change,

            "technical_strength":
                technical_strength,

            "confidence_score":
                confidence_score,

            "setup_score":
                technical_strength,

            "signal_quality":
                signal_quality,

            "verdict":
                verdict,

            "verdict_emoji":
                verdict_emoji,

            "risk_level":
                risk_level,

            "support":
                support,

            "resistance":
                resistance,

            "entry_zone": {

                "low":
                    entry_low,

                "high":
                    entry_high
            },

            "stop_loss":
                stop_loss,

            "target":
                target,

            "risk_reward":
                risk_reward,

            "upside_percent":
                upside_percent,

            "downside_percent":
                downside_percent,

            "volume_ratio":
                volume_ratio,

            "breakout":
                breakout,

            "breakdown":
                breakdown,

            "institutional_activity":
                institutional_activity,

            "market_status":
                get_market_status(),

            "multi_timeframe":
                multi_timeframe,

            "news_sentiment":
                news_sentiment,

            "sentiment_note":
                "AI-generated approximate news sentiment based on recent headlines.",

            "news_headlines":
                news_headlines,

            "mini_chart": [
                round(x, 2)
                for x in close.tail(20).tolist()
            ],

            "signals": {

                "rsi":
                    round(rsi, 1),

                "rsi_signal":
                    rsi_signal,

                "macd":
                    macd_signal,

                "macd_histogram":
                    macd_histogram,

                "trend":
                    trend_signal,

                "bollinger":
                    bb_signal,

                "volatility":
                    f"{atr_pct}%",

                "ema20":
                    round(ema20, 2),

                "ema50":
                    round(ema50, 2),

                "ema200":
                    round(ema200, 2)
            },

            "why":
                reasons
        }

        # SAVE SIGNAL CACHE
        signal_cache["data"][ticker] = result
        signal_cache["time"][ticker] = now

        return result

    except Exception as e:

        traceback.print_exc()

        return {
            "ticker": ticker,
            "error": str(e)
        }


# ─────────────────────────────────────
# SIGNALS ROUTE
# ─────────────────────────────────────
@app.route("/signals", methods=["GET"])
def get_signals():

    try:

        ticker = (
            request.args
            .get("ticker", "")
            .upper()
        )

        if ticker:

            if not ticker.endswith(".NS"):
                ticker += ".NS"

            result = calculate_signals(ticker)

            if result and not result.get("error"):
                return jsonify(result)

            return jsonify({
                "error":
                    "Signal calculation failed"
            }), 500

        all_signals = []

        for t in SORTED_TICKERS:

            sig = calculate_signals(t)

            if sig and not sig.get("error"):
                all_signals.append(sig)

        all_signals.sort(
            key=lambda x: x.get(
                "technical_strength",
                0
            ),
            reverse=True
        )

        return jsonify({

            "signals":
                all_signals,

            "generated_at":
                datetime.datetime.now()
                .strftime("%Y-%m-%d %H:%M:%S"),

            "total":
                len(all_signals)
        })

    except Exception as e:

        traceback.print_exc()

        return jsonify({
            "error": str(e)
        }), 500


# ─────────────────────────────────────
# RUN
# ─────────────────────────────────────
if __name__ == "__main__":

    app.run(
        debug=True,
        threaded=True
    )