import yfinance as yf
import datetime
import feedparser
import requests
import re
from bs4 import BeautifulSoup
from nsetools import Nse
import pandas as pd
import numpy as np
from config import SORTED_TICKERS, CACHE_MINUTES, COMPANY_SEARCH_NAMES

market_cache = {"data": None, "time": None}

def get_real_time_price(symbol):
    try:
        ticker_symbol = symbol if symbol.endswith(".NS") else f"{symbol}.NS"
        ticker = yf.Ticker(ticker_symbol)
        return float(ticker.fast_info['last_price'])
    except Exception as e:
        print(f"Error fetching real-time price for {symbol}: {e}")
        return None

def get_nifty50_live():
    try:
        ticker = yf.Ticker("^NSEI")

        hist = ticker.history(
            period="5d",
            interval="1d",
            auto_adjust=False
        )

        if hist.empty:
            raise Exception("No data")

        price = float(hist["Close"].iloc[-1])
        prev_close = float(hist["Close"].iloc[-2])

        change = round(price - prev_close, 2)

        pct_change = round(
            (change / prev_close) * 100,
            2
        )

        return {
            "price": round(price, 2),
            "change": change,
            "percent_change":
            f"{'+' if pct_change >= 0 else ''}{pct_change}%"
        }

    except Exception as e:
        print(e)

        return {
            "error": "Nifty unavailable"
        }
        
def cache_valid():
    if market_cache["time"] is None:
        return False
    diff = datetime.datetime.now() - market_cache["time"]
    return diff.total_seconds() < CACHE_MINUTES * 60

def fetch_all_ohlcv():
    try:
        if cache_valid():
            return market_cache["data"]

        # STABLE FIX: Bulk download ke bajaye loop use kiya hai
        result = {}
        for ticker in SORTED_TICKERS:
            try:
                t = yf.Ticker(f"{ticker}.NS")
                hist = t.history(period="1mo") # 1mo is safer for memory
                if not hist.empty:
                    result[ticker] = {
                        "high": hist['High'].tail(20).tolist(),
                        "low": hist['Low'].tail(20).tolist(),
                        "open": hist['Open'].tail(20).tolist(),
                        "volume": hist['Volume'].tail(20).tolist()
                    }
                else:
                    result[ticker] = {"high": [0]*20, "low": [0]*20, "open": [0]*20, "volume": [0]*20}
            except Exception as ticker_err:
                result[ticker] = {"high": [0]*20, "low": [0]*20, "open": [0]*20, "volume": [0]*20}

        market_cache["data"] = result
        market_cache["time"] = datetime.datetime.now()
        return result
    except Exception as global_err:
        print(f"Global fetch error: {str(global_err)}")
        return None

def extract_full_article(url):
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        res = requests.get(url, headers=headers, timeout=8)
        soup = BeautifulSoup(res.text, "html.parser")
        for tag in soup(["script", "style", "nav", "footer"]):
            tag.decompose()
        text = soup.get_text(separator=" ", strip=True)
        return text[:1200] if len(text) >= 200 else ""
    except:
        return ""

def fetch_company_news_finnhub(company, max_results=8):
    articles = []
    search_name = COMPANY_SEARCH_NAMES.get(company, f"{company} stock India NSE")
    try:
        rss_url = "https://news.google.com/rss/search?q=" + requests.utils.quote(search_name) + "&hl=en-IN&gl=IN&ceid=IN:en"
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(rss_url, headers=headers, timeout=10)
        if response.status_code == 200:
            feed = feedparser.parse(response.content)
            for entry in feed.entries[:max_results]:
                title = entry.get("title", "").strip()
                if title and len(title) > 15:
                    articles.append({
                        "headline": title,
                        "summary": entry.get("summary", "")[:300],
                        "source": "Google News",
                        "url": entry.get("link", ""),
                        "publishedAt": entry.get("published", ""),
                        "content": title + ". " + entry.get("summary", "")[:500]
                    })
    except:
        pass
    return articles

def fetch_google_news(query, max_results=5):
    try:
        rss_url = "https://news.google.com/rss/search?q=" + requests.utils.quote(query) + "&hl=en-IN&gl=IN&ceid=IN:en"
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(rss_url, headers=headers, timeout=15)
        if response.status_code != 200: return []
        feed = feedparser.parse(response.content)
        return [{
            "headline": entry.get("title", ""), "summary": "", "source": "Google News",
            "url": entry.get("link", ""), "publishedAt": entry.get("published", ""), "content": entry.get("title", "")
        } for entry in feed.entries[:max_results]]
    except:
        return []

def fetch_yahoo_finance_news(query, max_results=5):
    try:
        search_url = f"https://finance.yahoo.com/quote/{query}/news"
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(search_url, headers=headers, timeout=15)
        if response.status_code != 200: return []
        soup = BeautifulSoup(response.text, "html.parser")
        articles, added = [], set()
        for link in soup.find_all("a"):
            title, href = link.get_text(strip=True), link.get("href")
            if not title or len(title) < 20 or not href or "/news/" not in href: continue
            if href.startswith("/"): href = "https://finance.yahoo.com" + href
            if href in added: continue
            added.add(href)
            articles.append({"headline": title, "summary": "", "source": "Yahoo Finance", "url": href, "publishedAt": "", "content": title})
            if len(articles) >= max_results: break
        return articles
    except:
        return []

def fetch_global_news(query, max_results=5):
    try:
        rss_url = "https://news.google.com/rss/search?q=" + requests.utils.quote(query) + "&hl=en-IN&gl=IN&ceid=IN:en"
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(rss_url, headers=headers, timeout=15)
        if response.status_code != 200: return []
        feed = feedparser.parse(response.content)
        articles = []
        for entry in feed.entries[:max_results]:
            full_content = extract_full_article(entry.get("link", ""))
            articles.append({
                "headline": entry.get("title", ""), "summary": "", "source": "Google News",
                "url": entry.get("link", ""), "publishedAt": entry.get("published", ""),
                "content": full_content if full_content else entry.get("title", "")
            })
        return articles


    except:
        return []

        
def calculate_technicals(symbol):

    try:

        ticker = yf.Ticker(symbol)

        hist = ticker.history(period="6mo")

        if hist.empty:
            return None

        close = hist["Close"]

        volume = hist["Volume"]

        delta = close.diff()

        gain = delta.where(delta > 0, 0)

        loss = -delta.where(delta < 0, 0)

        avg_gain = gain.rolling(14).mean()

        avg_loss = loss.rolling(14).mean()

        rs = avg_gain / avg_loss

        rsi = 100 - (100 / (1 + rs))

        ema20 = close.ewm(span=20).mean()

        ema50 = close.ewm(span=50).mean()

        latest_close = close.iloc[-1]

        volume_ratio = volume.iloc[-1] / volume.tail(20).mean()

        breakout = latest_close > close.tail(20).max()

        breakdown = latest_close < close.tail(20).min()

        strength = 50

        if rsi.iloc[-1] > 60:
            strength += 10

        if ema20.iloc[-1] > ema50.iloc[-1]:
            strength += 20

        if volume_ratio > 1.5:
            strength += 20

        return {
            "rsi": round(float(rsi.iloc[-1]), 2),
            "ema20": round(float(ema20.iloc[-1]), 2),
            "ema50": round(float(ema50.iloc[-1]), 2),
            "volume_ratio": round(float(volume_ratio), 2),
            "breakout": breakout,
            "breakdown": breakdown,
            "technical_strength": min(strength, 100)
        }

    except Exception as e:

        print(f"Technical Engine Error: {e}")

        return None