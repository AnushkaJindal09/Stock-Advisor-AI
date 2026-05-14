


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
import json
import re
from concurrent.futures import ThreadPoolExecutor
import feedparser
from bs4 import BeautifulSoup
 
load_dotenv()
 
app = Flask(__name__)
CORS(app)
 
# ─────────────────────────────────────
# CONFIG
# ─────────────────────────────────────
HF_API_URL = "https://anushka09092004-stock-ml-api.hf.space/predict"
 
SORTED_TICKERS = [
    'ADANIENT.NS', 'ADANIPORTS.NS', 'BAJFINANCE.NS', 'BHARTIARTL.NS',
    'COALINDIA.NS', 'HDFCBANK.NS', 'HINDUNILVR.NS', 'ICICIBANK.NS',
    'INFY.NS', 'LT.NS', 'MARUTI.NS', 'RELIANCE.NS', 'SBIN.NS', 'TCS.NS'
]
 
SECTOR_MAP = {
    "RELIANCE.NS": "Energy", "INFY.NS": "IT", "TCS.NS": "IT",
    "HDFCBANK.NS": "Banking", "ICICIBANK.NS": "Banking", "SBIN.NS": "Banking",
    "LT.NS": "Infrastructure", "MARUTI.NS": "Automobile",
    "BHARTIARTL.NS": "Telecom", "HINDUNILVR.NS": "FMCG",
    "COALINDIA.NS": "Energy", "ADANIENT.NS": "Conglomerate",
    "ADANIPORTS.NS": "Logistics", "BAJFINANCE.NS": "Finance"
}
 
COMPANY_SEARCH_NAMES = {
    "TCS": "Tata Consultancy Services TCS NSE",
    "RELIANCE": "Reliance Industries stock India",
    "HDFCBANK": "HDFC Bank stock India",
    "ICICIBANK": "ICICI Bank stock India",
    "INFY": "Infosys stock India",
    "SBIN": "State Bank India SBI stock",
    "HINDUNILVR": "Hindustan Unilever HUL stock",
    "BAJFINANCE": "Bajaj Finance stock India",
    "MARUTI": "Maruti Suzuki stock India",
    "LT": "Larsen Toubro LT stock India",
    "ADANIENT": "Adani Enterprises stock India",
    "ADANIPORTS": "Adani Ports stock India",
    "BHARTIARTL": "Bharti Airtel stock India",
    "COALINDIA": "Coal India stock NSE"
}
 
# Sector-level global news queries
# These fetch macro/global news that affect each sector
SECTOR_GLOBAL_QUERIES = {
    "IT":             "US Fed interest rate IT stocks India OR US recession tech",
    "Banking":        "RBI repo rate India banking OR credit growth NPA",
    "Energy":         "crude oil price India OR Brent oil OPEC",
    "Finance":        "RBI NBFC India OR interest rate finance sector",
    "Automobile":     "EV policy India automobile OR fuel prices",
    "Telecom":        "5G India telecom OR TRAI policy",
    "FMCG":           "inflation India FMCG rural demand OR CPI",
    "Infrastructure": "government capex India infrastructure OR budget",
    "Logistics":      "port traffic India logistics OR global trade",
    "Conglomerate":   "Adani group India OR conglomerate news"
}
 
# ─────────────────────────────────────
# CACHE
# ─────────────────────────────────────
market_cache = {"data": None, "time": None}
CACHE_MINUTES = 5
 
# Intelligence cache — 90 min (Gemini calls are expensive, don't call every 5 min)
intelligence_cache = {}
INTELLIGENCE_CACHE_MINUTES = 90
 
# Signal cache
signal_cache = {"data": {}, "time": {}}
SIGNAL_CACHE_MINUTES = 5
 
 
# ─────────────────────────────────────
# HOME
# ─────────────────────────────────────
@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "status": "Backend running 🚀",
        "routes": ["/predict", "/stock", "/news", "/signals", "/intelligence"]
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
            SORTED_TICKERS, period="6mo",
            progress=False, auto_adjust=True, threads=True
        )
        if data.empty:
            return None
 
        result = {}
        for ticker in SORTED_TICKERS:
            try:
                result[ticker] = {
                    "high":   data['High'][ticker].dropna().tail(20).tolist(),
                    "low":    data['Low'][ticker].dropna().tail(20).tolist(),
                    "open":   data['Open'][ticker].dropna().tail(20).tolist(),
                    "volume": data['Volume'][ticker].dropna().tail(20).tolist()
                }
                for key in result[ticker]:
                    if len(result[ticker][key]) < 20:
                        diff = 20 - len(result[ticker][key])
                        result[ticker][key] = [0.0] * diff + result[ticker][key]
            except:
                result[ticker] = {"high": [0]*20, "low": [0]*20, "open": [0]*20, "volume": [0]*20}
 
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
            feature_cols.append(all_data[ticker][feature])
 
    arr = np.array(feature_cols).T
    if arr.shape != (20, 56):
        raise Exception(f"Wrong shape: {arr.shape}")
    if not os.path.exists("x_scaler.pkl"):
        raise Exception("x_scaler.pkl missing")
 
    x_scaler = joblib.load("x_scaler.pkl")
    arr_scaled = x_scaler.transform(arr)
    return arr_scaled.reshape(1, 20, 56)
 
 
# ─────────────────────────────────────
# PREDICT
# ─────────────────────────────────────
@app.route("/predict", methods=["POST"])
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
 
 
# ─────────────────────────────────────
# STOCK
# ─────────────────────────────────────
@app.route("/stock", methods=["GET"])
def get_stock():
    try:
        symbol = request.args.get("symbol", "").upper().replace(".NS", "")
 
        # Nifty 50 index — special handling
        if symbol in ("NIFTY50", "NIFTY"):
            try:
                ticker         = yf.Ticker("^NSEI")
                price          = float(ticker.fast_info["last_price"])
                previous_close = float(ticker.fast_info["regular_market_previous_close"])
                change         = round(price - previous_close, 2)
                percent_change = round((change / previous_close) * 100, 2)
                return jsonify({
                    "price":          round(price, 2),
                    "change":         change,
                    "percent_change": f"{'+' if percent_change >= 0 else ''}{percent_change}%"
                })
            except Exception as e:
                return jsonify({"error": str(e)}), 500
 
        # Regular NSE stock — try nsetools first, fallback to yfinance
        try:
            nse   = Nse()
            quote = nse.get_quote(symbol)
            if quote:
                return jsonify({
                    "price":          quote.get('lastPrice'),
                    "change":         quote.get('change'),
                    "percent_change": str(round(quote.get('pChange', 0), 2)) + "%",
                    "price_source":   "NSE Live"
                })
        except:
            pass
 
        ticker = yf.Ticker(symbol + ".NS")
        hist   = ticker.history(period="5d")
        if hist.empty:
            raise Exception("No stock data")
        price          = float(hist["Close"].iloc[-1])
        previous_close = float(hist["Close"].iloc[-2])
        percent_change = ((price - previous_close) / previous_close) * 100
        return jsonify({
            "price":          round(price, 2),
            "change":         round(price - previous_close, 2),
            "percent_change": str(round(percent_change, 2)) + "%",
            "price_source":   "Yahoo Finance Delayed"
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500
 
 
# ─────────────────────────────────────
# NEWS (general route — news page ke liye)
# ─────────────────────────────────────
# ─────────────────────────────────────
# ADVANCED AI NEWS ENGINE
# ─────────────────────────────────────

NEWS_CACHE = {}
NEWS_CACHE_MINUTES = 15


def clean_text(text):
    if not text:
        return ""
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def is_news_cache_valid(key):
    if key not in NEWS_CACHE:
        return False

    age = (
        datetime.datetime.now() -
        NEWS_CACHE[key]["time"]
    ).total_seconds() / 60

    return age < NEWS_CACHE_MINUTES


def extract_full_article(url):
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        res  = requests.get(url, headers=headers, timeout=8)
        soup = BeautifulSoup(res.text, "html.parser")
        # Remove scripts/styles
        for tag in soup(["script", "style", "nav", "footer"]):
            tag.decompose()
        text = soup.get_text(separator=" ", strip=True)
        if len(text) < 200:
            return ""
        return text[:8000]
    except:
        return ""


def fetch_company_news_finnhub(company, max_results=8):
    """
    Google News RSS se company-specific news fetch karo.
    Finnhub Indian stocks ke liye free tier pe available nahi.
    """
    articles = []

    search_name = COMPANY_SEARCH_NAMES.get(company, f"{company} stock India NSE")

    # Source 1 — Google News RSS
    try:
        rss_url = (
            "https://news.google.com/rss/search?q="
            + requests.utils.quote(search_name)
            + "&hl=en-IN&gl=IN&ceid=IN:en"
        )
        headers  = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        response = requests.get(rss_url, headers=headers, timeout=10)

        if response.status_code == 200:
            feed = feedparser.parse(response.content)
            for entry in feed.entries[:max_results]:
                title = entry.get("title", "").strip()
                if title and len(title) > 15:
                    articles.append({
                        "headline":    title,
                        "summary":     entry.get("summary", "")[:300],
                        "source":      "Google News",
                        "url":         entry.get("link", ""),
                        "publishedAt": entry.get("published", ""),
                        "content":     title + ". " + entry.get("summary", "")[:500]
                    })
    except:
        pass

    # Source 2 — yfinance news (fallback/supplement)
    if len(articles) < 3:
        try:
            t    = yf.Ticker(company + ".NS")
            news = t.news or []
            for a in news[:5]:
                content = a.get("content", {})
                title   = content.get("title", "") if content else a.get("title", "")
                if title and len(title) > 15:
                    if not any(title[:30] in x["headline"] for x in articles):
                        articles.append({
                            "headline":    title.strip(),
                            "summary":     content.get("summary", "")[:300] if content else "",
                            "source":      "Yahoo Finance",
                            "url":         "",
                            "publishedAt": "",
                            "content":     title
                        })
        except:
            pass

    return articles[:max_results]

def fetch_google_news(query, max_results=5):

    try:

        rss_url = (
            "https://news.google.com/rss/search?q="
            + requests.utils.quote(query)
            + "&hl=en-IN&gl=IN&ceid=IN:en"
        )

        headers = {
            "User-Agent": (
                "Mozilla/5.0 "
                "(Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 "
                "(KHTML, like Gecko) "
                "Chrome/120.0 Safari/537.36"
            )
        }

        response = requests.get(
            rss_url,
            headers=headers,
            timeout=15
        )

        print("GOOGLE RSS STATUS:", response.status_code)

        if response.status_code != 200:
            return []

        feed = feedparser.parse(response.content)

        articles = []

        for entry in feed.entries[:max_results]:

            articles.append({
                "headline": entry.get("title", ""),
                "summary": "",
                "source": "Google News",
                "url": entry.get("link", ""),
                "publishedAt": entry.get("published", ""),
                "content": entry.get("title", "")
            })

        print("GOOGLE ARTICLES:", len(articles))

        return articles

    except Exception:
        traceback.print_exc()
        return []

def fetch_yahoo_finance_news(query, max_results=5):

    try:

        search_url = (
            f"https://finance.yahoo.com/quote/{query}/news"
        )

        headers = {
            "User-Agent": "Mozilla/5.0"
        }

        response = requests.get(
            search_url,
            headers=headers,
            timeout=15
        )

        if response.status_code != 200:
            return []

        soup = BeautifulSoup(response.text, "html.parser")

        articles = []

        links = soup.find_all("a")

        added = set()

        for link in links:

            title = link.get_text(strip=True)
            href = link.get("href")

            if (
                not title or
                len(title) < 20 or
                not href
            ):
                continue

            if "/news/" not in href:
                continue

            if href.startswith("/"):
                href = "https://finance.yahoo.com" + href

            if href in added:
                continue

            added.add(href)

            articles.append({
                "headline": title,
                "summary": "",
                "source": "Yahoo Finance",
                "url": href,
                "publishedAt": "",
                "content": title
            })

            if len(articles) >= max_results:
                break

        return articles

    except:
        traceback.print_exc()
        return []

def fetch_global_news(query, max_results=5):

    try:

        rss_url = (
            "https://news.google.com/rss/search?q="
            + requests.utils.quote(query)
            + "&hl=en-IN&gl=IN&ceid=IN:en"
        )

        headers = {
            "User-Agent": "Mozilla/5.0"
        }

        response = requests.get(
            rss_url,
            headers=headers,
            timeout=15
        )

        if response.status_code != 200:
            return []

        feed = feedparser.parse(response.content)

        articles = []

        for entry in feed.entries[:max_results]:

            full_content = extract_full_article(
                entry.get("link", "")
            )

            articles.append({

                "headline": entry.get("title", ""),
                "summary": "",
                "source": "Google News",
                "url": entry.get("link", ""),
                "publishedAt": entry.get("published", ""),
                "content": (
                    full_content
                    if full_content
                    else entry.get("title", "")
                )

            })

        print("GLOBAL ARTICLES:", len(articles))

        return articles

    except Exception:
        traceback.print_exc()
        return []
# ─────────────────────────────────────
# AI NEWS INTELLIGENCE
# ─────────────────────────────────────

def analyse_with_gemini(
    company,
    sector,
    ticker_data,
    company_articles,
    global_articles
):

    try:

        GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

        def format_articles(articles):

            if not articles:
                return "No relevant news found."

            formatted = ""

            for idx, article in enumerate(articles, 1):

                formatted += f"""
NEWS {idx}

Headline:
{article.get("headline")}

Article Content:
{article.get("content")}

Source:
{article.get("source")}

Published:
{article.get("publishedAt")}
"""

            return formatted

        company_news_text = format_articles(company_articles)
        global_news_text = format_articles(global_articles)

        prompt = f"""
You are India's top institutional stock market research analyst.

You are not a news summarizer.

You think like:
- hedge funds
- smart money
- professional traders
- institutional investors

Your job:
Convert raw news into HIGH-VALUE stock intelligence.

==================================================
STOCK DETAILS
==================================================

Company: {company}
Sector: {sector}

Current Price: ₹{ticker_data.get('price')}
Today's Change: {ticker_data.get('percent_change')}%

Technical Verdict: {ticker_data.get('verdict')}
Technical Strength: {ticker_data.get('technical_strength')}/100

RSI: {ticker_data.get('rsi')}
MACD: {ticker_data.get('macd')}
Trend: {ticker_data.get('trend')}

Support: ₹{ticker_data.get('support')}
Resistance: ₹{ticker_data.get('resistance')}

==================================================
COMPANY NEWS
==================================================

{company_news_text}

==================================================
GLOBAL + SECTOR NEWS
==================================================

{global_news_text}

==================================================
VERY IMPORTANT ANALYSIS RULES
==================================================

1. Ignore useless news.
2. Ignore PR/news that won't affect stock movement.
3. Focus ONLY on market-moving information.
4. Think about:
   - earnings
   - margins
   - future growth
   - regulations
   - FII/DII sentiment
   - macro economy
   - interest rates
   - oil prices
   - sector rotation
   - institutional activity
   - business impact
5. Explain WHY news matters.
6. Connect global events with this stock.
7. Combine technical + news analysis together.
8. Be realistic.
9. Do NOT give fake hype.
10. Do NOT act like financial influencer.
11. Sound like Bloomberg terminal + hedge fund analyst.

==================================================
RETURN STRICT JSON ONLY
==================================================

{{
  "smart_summary": "",

  "overall_sentiment": "",

  "sentiment_strength": "",

  "institutional_view": "",

  "money_flow_view": "",

  "market_psychology": "",

  "news_score": 0,

  "key_market_drivers": [],

  "major_headlines": [
    {{
      "headline": "",
      "source": "",
      "impact": "",
      "importance": "",
      "reason": ""
    }}
  ],

  "bull_case": [],

  "bear_case": [],

  "risk_factors": [],

  "opportunities": [],

  "short_term_outlook": {{
    "direction": "",
    "confidence": "",
    "reasoning": ""
  }},

  "medium_term_outlook": {{
    "direction": "",
    "confidence": "",
    "reasoning": ""
  }},

  "smart_money_strategy": "",

  "retail_trap_risk": "",

  "expert_verdict": "",

  "action_bias": "",

  "confidence_score": 0
}}
"""

        response = requests.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}",
            headers={
                "Content-Type": "application/json"
            },
            json={
                "contents": [
                    {
                        "parts": [
                            {
                                "text": prompt
                            }
                        ]
                    }
                ],
                "generationConfig": {
                    "temperature": 0.25,
                    "topP": 0.9,
                    "maxOutputTokens": 2500
                }
            },
            timeout=35
        )

        if response.status_code != 200:
            print(response.text)
            return None

        raw = response.json()["candidates"][0]["content"]["parts"][0]["text"]

        cleaned = raw.strip()

        if cleaned.startswith("```"):
            cleaned = cleaned.replace("```json", "")
            cleaned = cleaned.replace("```", "")
            cleaned = cleaned.strip()

        return json.loads(cleaned)

    except Exception:
        traceback.print_exc()
        return None


# ─────────────────────────────────────
# NEWS ROUTE
# ─────────────────────────────────────

@app.route("/news", methods=["GET"])
def get_news():

    try:

        company = request.args.get("company", "").upper().strip()

        if not company:
            return jsonify({
                "error": "company required"
            }), 400

        company_query = company + ".NS"

        sector = "Other"

        for ticker, sec in SECTOR_MAP.items():
            if company in ticker:
                sector = sec
                break

        # SAHI
        global_query = SECTOR_GLOBAL_QUERIES.get(sector, f"India {sector} sector stock market news")

        with ThreadPoolExecutor(max_workers=4) as executor:

            future_finnhub = executor.submit(
                fetch_company_news_finnhub,
                company,
                8
            )

            future_google = executor.submit(
                fetch_google_news,
                global_query,
                5
            )

            future_yahoo = executor.submit(
                fetch_yahoo_finance_news,
                company,
                5
            )

            company_articles = future_finnhub.result()
            google_articles = future_google.result()
            yahoo_articles = future_yahoo.result()

        # FALLBACK LOGIC

        if not company_articles:
            company_articles = yahoo_articles

        combined_global = google_articles

        # Remove duplicates
        seen = set()
        filtered_global = []

        for article in combined_global:

            title = article.get("headline", "")

            if title in seen:
                continue

            seen.add(title)
            filtered_global.append(article)

        return jsonify({
            "company_news": company_articles,
            "global_news": filtered_global,
            "sector": sector,
            "total_company_news": len(company_articles),
            "total_global_news": len(filtered_global)
        })

    except Exception as e:
        traceback.print_exc()

        return jsonify({
            "error": str(e)
        }), 500
 
# ─────────────────────────────────────
# GET INTELLIGENCE (main function called per stock)
# ─────────────────────────────────────
def get_stock_intelligence(company, sector, ticker_data):
    """
    Fetch news + run Gemini analysis.
    Cache result for 90 minutes to avoid excessive API calls.
    """
    try:
        current_time = datetime.datetime.now()
 
        # Check cache
        if company in intelligence_cache:
            cached = intelligence_cache[company]
            age = (current_time - cached["time"]).total_seconds() / 60
            if age < INTELLIGENCE_CACHE_MINUTES:
                return cached["data"]
 
        # Fetch company-specific news (5 articles)
        company_query    = COMPANY_SEARCH_NAMES.get(company, f"{company} stock India NSE")
        # Company news — Google RSS se (same jo /news route use karta hai)
        company_articles = fetch_company_news_finnhub(company, max_results=6)

        # Global/macro news — sector specific
        global_query    = SECTOR_GLOBAL_QUERIES.get(sector, f"India stock market {sector} sector news")
        global_articles = fetch_global_news(global_query, max_results=4)
 
        # Run Gemini analysis
        intelligence = analyse_with_gemini(
            company        = company,
            sector         = sector,
            ticker_data    = ticker_data,
            company_articles = company_articles,
            global_articles  = global_articles
        )
 
        if intelligence is None:
            # Fallback if Gemini fails
            intelligence = {
                "smart_summary":        "News analysis temporarily unavailable.",
                "overall_sentiment":    "Neutral",
                "sentiment_strength":   "Weak",
                "news_categories_found": [],
                "major_headlines":      [],
                "the_connect":          {
                    "global_impact":    "Not available",
                    "sector_impact":    "Not available",
                    "company_specific": "Not available"
                },
                "short_term_outlook":  {"timeframe": "1-3 days",  "direction": "Sideways", "key_trigger": "N/A", "risk_factor": "N/A"},
                "medium_term_outlook": {"timeframe": "1-4 weeks", "direction": "Sideways", "key_trigger": "N/A", "risk_factor": "N/A"},
                "expert_verdict":      "Insufficient news data for analysis.",
                "action_bias":         "Watch",
                "news_data_quality":   "No relevant news"
            }
 
        # Cache it
        intelligence_cache[company] = {
            "data": intelligence,
            "time": current_time
        }
 
        return intelligence
 
    except Exception as e:
        traceback.print_exc()
        return None
 
 
# ─────────────────────────────────────
# INTELLIGENCE ROUTE (on-demand — called when user clicks "View Report")
# ─────────────────────────────────────
@app.route("/intelligence", methods=["GET"])
def get_intelligence():
    """
    Frontend se call hoga jab user "View Full Intelligence Report" click kare.
    ticker parameter required.
    """
    try:
        ticker = request.args.get("ticker", "").upper().strip()
        if not ticker:
            return jsonify({"error": "ticker parameter required"}), 400
 
        if not ticker.endswith(".NS"):
            ticker += ".NS"
 
        company = ticker.replace(".NS", "")
        sector  = SECTOR_MAP.get(ticker, "Other")
 
        # Get cached signal data if available
        ticker_data = {}
        if ticker in signal_cache["data"]:
            sig = signal_cache["data"][ticker]
            ticker_data = {
                "price":              sig.get("price"),
                "percent_change":     sig.get("percent_change"),
                "verdict":            sig.get("verdict"),
                "technical_strength": sig.get("technical_strength"),
                "rsi":                sig.get("signals", {}).get("rsi"),
                "macd":               sig.get("signals", {}).get("macd"),
                "trend":              sig.get("signals", {}).get("trend"),
                "support":            sig.get("support"),
                "resistance":         sig.get("resistance")
            }
 
        intelligence = get_stock_intelligence(company, sector, ticker_data)
 
        if intelligence:
            return jsonify({
                "company":      company,
                "sector":       sector,
                "intelligence": intelligence,
                "generated_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
 
        return jsonify({"error": "Intelligence generation failed"}), 500
 
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500
 
 
# ─────────────────────────────────────
# TIMEFRAME TREND
# ─────────────────────────────────────
def timeframe_trend(df):
    try:
        if df.empty:
            return "Unknown"
        close = df['Close']
        ema20 = close.ewm(span=20).mean().iloc[-1]
        ema50 = close.ewm(span=50).mean().iloc[-1]
        price = close.iloc[-1]
        if price > ema20 > ema50:   return "Bullish"
        elif price < ema20 < ema50: return "Bearish"
        return "Sideways"
    except:
        return "Unknown"
 
 
# ─────────────────────────────────────
# MARKET STATUS
# ─────────────────────────────────────
def get_market_status():
    IST = pytz.timezone("Asia/Kolkata")
    now = datetime.datetime.now(IST)
    market_open = (
        now.weekday() < 5 and
        (
            (now.hour == 9 and now.minute >= 15) or
            (9 < now.hour < 15) or
            (now.hour == 15 and now.minute <= 30)
        )
    )
    return "OPEN" if market_open else "CLOSED"
 
 
# ─────────────────────────────────────
# SIGNALS ENGINE
# ─────────────────────────────────────
def calculate_signals(ticker):
    try:
        now = datetime.datetime.now(pytz.timezone('Asia/Kolkata'))
 
        # Signal cache check
        if ticker in signal_cache["time"]:
            age = (now - signal_cache["time"][ticker]).total_seconds() / 60
            if age < SIGNAL_CACHE_MINUTES:
                return signal_cache["data"][ticker]
 
        stock = yf.Ticker(ticker)
        df    = stock.history(period="6mo", interval="1d")
 
        if df.empty or len(df) < 60:
            return None
 
        close = df['Close']
        high  = df['High']
        low   = df['Low']
        vol   = df['Volume']
 
        # Multi timeframe
        df_15m = stock.history(period="5d",  interval="15m")
        df_1h  = stock.history(period="1mo", interval="1h")
        multi_timeframe = {
            "15m": timeframe_trend(df_15m),
            "1h":  timeframe_trend(df_1h),
            "1d":  timeframe_trend(df)
        }
 
        # Price
        current_price = float(close.iloc[-1])
        price_source  = "Yahoo Finance Delayed"
        nse = None
        try:
            nse   = Nse()
            quote = nse.get_quote(ticker.replace(".NS", ""))
            if quote and quote.get("lastPrice"):
                current_price = float(quote["lastPrice"])
                price_source  = "NSE Live"
        except:
            pass
 
        previous_close = float(close.iloc[-2])
        change         = round(current_price - previous_close, 2)
        percent_change = round((change / previous_close) * 100, 2)
 
        # RSI
        delta    = close.diff()
        gain     = delta.clip(lower=0)
        loss     = -delta.clip(upper=0)
        avg_gain = gain.rolling(14).mean()
        avg_loss = loss.rolling(14).mean()
        rs       = avg_gain / avg_loss
        rsi      = float((100 - (100 / (1 + rs))).iloc[-1])
 
        if rsi >= 70:   rsi_signal, rsi_score = "Overbought",       20
        elif rsi >= 60: rsi_signal, rsi_score = "Bullish Momentum",  70
        elif rsi <= 30: rsi_signal, rsi_score = "Oversold",          75
        elif rsi <= 40: rsi_signal, rsi_score = "Weak Momentum",     40
        else:           rsi_signal, rsi_score = "Neutral",           50
 
        # MACD
        ema12          = close.ewm(span=12).mean()
        ema26          = close.ewm(span=26).mean()
        macd_series    = ema12 - ema26
        signal_series  = macd_series.ewm(span=9).mean()
        macd_line      = float(macd_series.iloc[-1])
        signal_line    = float(signal_series.iloc[-1])
        macd_histogram = round(macd_line - signal_line, 2)
        macd_signal    = "Bullish" if macd_line > signal_line else "Bearish"
        macd_score     = 75 if macd_line > signal_line else 25
 
        # EMA
        ema20  = float(close.ewm(span=20).mean().iloc[-1])
        ema50  = float(close.ewm(span=50).mean().iloc[-1])
        ema200 = float(close.ewm(span=200).mean().iloc[-1])
 
        # Trend
        if current_price > ema20 > ema50:   trend_signal, trend_score = "Strong Uptrend",   85
        elif current_price > ema20:          trend_signal, trend_score = "Mild Uptrend",     65
        elif current_price < ema20 < ema50:  trend_signal, trend_score = "Strong Downtrend", 20
        else:                                trend_signal, trend_score = "Sideways",         45
 
        # Bollinger
        mid      = close.rolling(20).mean()
        std      = close.rolling(20).std()
        bb_upper = float((mid + 2 * std).iloc[-1])
        bb_lower = float((mid - 2 * std).iloc[-1])
        if current_price >= bb_upper * 0.98:   bb_signal, bb_score = "Upper Band", 30
        elif current_price <= bb_lower * 1.02: bb_signal, bb_score = "Lower Band", 70
        else:                                  bb_signal, bb_score = "Mid Band",   50
 
        # ATR
        tr      = np.maximum(high - low, np.maximum(abs(high - close.shift()), abs(low - close.shift())))
        atr     = float(tr.rolling(14).mean().iloc[-1])
        atr_pct = round((atr / current_price) * 100, 2)
 
        # Volume — real-time from nsetools, avg from completed days
        try:
            if nse:
                quote_full = nse.get_quote(ticker.replace(".NS", ""), all_data=True)
                vol_today  = float(quote_full['marketDeptOrderBook']['tradeInfo']['tradedVolume'])
            else:
                raise Exception("nse not available")
        except:
            vol_today = float(vol.iloc[-1])
 
        vol_avg      = float(vol.iloc[:-1].rolling(20).mean().iloc[-1])
        volume_ratio = round(vol_today / vol_avg, 2) if vol_avg > 0 else 1.0
        vol_spike    = volume_ratio >= 1.5
 
        # Support / Resistance
        support    = round(low.rolling(20).min().iloc[-1],  2)
        resistance = round(high.rolling(20).max().iloc[-1], 2)
 
        # Breakout
        breakout  = bool(current_price >= resistance * 0.995 and volume_ratio > 1.5)
        breakdown = bool(current_price <= support * 1.005   and volume_ratio > 1.5)
 
        breakout_strength = 0
        if resistance > 0:
            breakout_strength = round(((current_price - resistance) / resistance) * 100, 2)
            if breakout_strength < 0:
                breakout_strength = 0
 
        # Technical strength score
        technical_strength = int(
            trend_score * 0.35 +
            rsi_score   * 0.20 +
            macd_score  * 0.25 +
            bb_score    * 0.10 +
            min(volume_ratio * 20, 100) * 0.10
        )
 
        # Verdict
        if technical_strength >= 70:   verdict, verdict_emoji = "BUY",   "🟢"
        elif technical_strength <= 35: verdict, verdict_emoji = "AVOID", "🔴"
        else:                          verdict, verdict_emoji = "WAIT",  "🟡"
 
        market_sentiment = "Bullish" if technical_strength >= 70 else "Bearish" if technical_strength <= 35 else "Neutral"
 
        # Signal quality
        if breakout and volume_ratio > 1.8 and macd_line > signal_line and current_price > ema20:
            signal_quality = "A+"
        elif macd_line > signal_line and current_price > ema20:
            signal_quality = "B"
        else:
            signal_quality = "C"
 
        # Risk level
        if atr_pct > 3 or rsi > 75:  risk_level = "High"
        elif atr_pct > 1.8:           risk_level = "Medium"
        else:                          risk_level = "Low"
 
        # Targets
        entry_low        = round(current_price - atr * 0.5,  2)
        entry_high       = round(current_price + atr * 0.5,  2)
        stop_loss        = round(current_price - atr * 1.5,  2)
        target           = round(current_price + atr * 3,    2)
        upside_percent   = round(((target - current_price) / current_price) * 100, 2)
        downside_percent = round(((current_price - stop_loss) / current_price) * 100, 2)
        risk             = current_price - stop_loss
        reward           = target - current_price
        risk_reward      = round(reward / risk, 2) if risk > 0 else 0
 
        if breakout and volume_ratio > 1.5: entry_timing = "Immediate"
        elif verdict == "BUY":              entry_timing = "Wait for Dip"
        else:                               entry_timing = "Avoid Entry"
 
        trade_plan = {
            "entry_strategy":    f"Preferred accumulation near ₹{entry_low} - ₹{entry_high}",
            "stop_loss_strategy": f"Strict SL below ₹{stop_loss}",
            "target_strategy":   f"Potential upside towards ₹{target}",
            "position_sizing":   "Risk only 1-2% capital on this trade",
            "best_for":          "Swing Traders" if atr_pct < 3 else "High Risk Traders"
        }
 
        if verdict == "BUY":   action = "Potential bullish setup detected."
        elif verdict == "WAIT": action = "Wait for stronger confirmation."
        else:                   action = "Risk currently high."
 
        if volume_ratio >= 2 and breakout:    institutional_activity = "High Volume Breakout Activity"
        elif volume_ratio >= 2 and breakdown: institutional_activity = "High Volume Selling Pressure"
        else:                                 institutional_activity = "Normal Market Activity"
 
        # Reasons (technical)
        reasons = [f"RSI at {round(rsi,1)} shows {rsi_signal.lower()}."]
        if macd_line > signal_line: reasons.append("MACD bullish crossover detected.")
        else:                       reasons.append("MACD remains bearish.")
        if current_price > ema20 > ema50: reasons.append("Price trading above EMA20 & EMA50.")
        if vol_spike:  reasons.append(f"Volume spike detected ({volume_ratio}x average).")
        if breakout:   reasons.append("Potential breakout near resistance.")
 
        # Alerts
        alerts = []
        if breakout:   alerts.append("Possible breakout zone.")
        if breakdown:  alerts.append("Possible breakdown risk.")
        if rsi >= 70:  alerts.append("RSI indicates overbought conditions.")
        if rsi <= 30:  alerts.append("RSI indicates oversold conditions.")
        if vol_spike:  alerts.append("Unusual volume activity detected.")
 
        # Smart summary from intelligence cache (if available — don't block signals for it)
        company_name = ticker.replace(".NS", "")
        smart_summary = None
        news_sentiment = "Neutral"
        if company_name in intelligence_cache:
            cached_intel = intelligence_cache[company_name]["data"]
            smart_summary  = cached_intel.get("smart_summary")
            news_sentiment = cached_intel.get("overall_sentiment", "Neutral")
 
        result = {
            "ticker":                ticker,
            "alerts":                alerts,
            "company":               company_name,
            "action":                action,
            "sector":                SECTOR_MAP.get(ticker, "Other"),
            "market_sentiment":      market_sentiment,
            "entry_timing":          entry_timing,
            "trade_plan":            trade_plan,
            "breakout_strength":     breakout_strength,
            "price":                 round(current_price, 2),
            "price_source":          price_source,
            "change":                change,
            "percent_change":        percent_change,
            "technical_strength":    technical_strength,
            "confidence_score":      technical_strength,
            "setup_score":           technical_strength,
            "signal_quality":        signal_quality,
            "verdict":               verdict,
            "verdict_emoji":         verdict_emoji,
            "risk_level":            risk_level,
            "support":               support,
            "resistance":            resistance,
            "entry_zone":            {"low": entry_low, "high": entry_high},
            "stop_loss":             stop_loss,
            "target":                target,
            "risk_reward":           risk_reward,
            "upside_percent":        upside_percent,
            "downside_percent":      downside_percent,
            "volume_ratio":          volume_ratio,
            "breakout":              breakout,
            "breakdown":             breakdown,
            "institutional_activity": institutional_activity,
            "market_status":         get_market_status(),
            "multi_timeframe":       multi_timeframe,
            "news_sentiment":        news_sentiment,
            "smart_summary":         smart_summary,
            "mini_chart":            [round(x, 2) for x in close.tail(20).tolist()],
            "signals": {
                "rsi":           round(rsi, 1),
                "rsi_signal":    rsi_signal,
                "macd":          macd_signal,
                "macd_histogram": macd_histogram,
                "trend":         trend_signal,
                "bollinger":     bb_signal,
                "volatility":    f"{atr_pct}%",
                "ema20":         round(ema20, 2),
                "ema50":         round(ema50, 2),
                "ema200":        round(ema200, 2)
            },
            "why": reasons
        }
 
        signal_cache["data"][ticker] = result
        signal_cache["time"][ticker] = now
 
        return result
 
    except Exception as e:
        traceback.print_exc()
        return {"ticker": ticker, "error": str(e)}
 
 
# ─────────────────────────────────────
# SIGNALS ROUTE
# ─────────────────────────────────────
@app.route("/signals", methods=["GET"])
def get_signals():
    try:
        ticker = request.args.get("ticker", "").upper().strip()
 
        if ticker:
            if not ticker.endswith(".NS"):
                ticker += ".NS"
            result = calculate_signals(ticker)
            if result and not result.get("error"):
                return jsonify(result)
            return jsonify({"error": "Signal calculation failed"}), 500
 
        all_signals = []
        for t in SORTED_TICKERS:
            sig = calculate_signals(t)
            if sig and not sig.get("error"):
                all_signals.append(sig)
 
        all_signals.sort(key=lambda x: x.get("technical_strength", 0), reverse=True)
 
        return jsonify({
            "signals":      all_signals,
            "generated_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "total":        len(all_signals)
        })
 
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500
        
 
 
# ─────────────────────────────────────
# RUN
# ─────────────────────────────────────
if __name__ == "__main__":
    app.run(debug=True, threaded=True)