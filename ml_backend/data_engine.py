import yfinance as yf
import datetime
import feedparser
import requests
import re
from bs4 import BeautifulSoup
from nsetools import Nse
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
        price = float(ticker.fast_info['last_price'])
        prev_close = float(ticker.fast_info['regular_market_previous_close'])
        change = round(price - prev_close, 2)
        pct_change = round((change / prev_close) * 100, 2)
        return {
            "price": round(price, 2),
            "change": change,
            "percent_change": f"{'+' if pct_change >= 0 else ''}{pct_change}%"
        }
    except Exception as e:
        print(f"Nifty Fetch Error: {e}")
        return {"price": 23605.0, "change": 0.0, "percent_change": "0.0%"}

def cache_valid():
    if market_cache["time"] is None:
        return False
    diff = datetime.datetime.now() - market_cache["time"]
    return diff.total_seconds() < CACHE_MINUTES * 60

def fetch_all_ohlcv():
    try:
        if cache_valid():
            return market_cache["data"]

        data = yf.download(SORTED_TICKERS, period="6mo", progress=False, auto_adjust=True, threads=True)
        if data.empty:
            return None

        result = {}
        for ticker in SORTED_TICKERS:
            try:
                highs = data['High'][ticker].dropna().tail(20).tolist()
                lows = data['Low'][ticker].dropna().tail(20).tolist()
                opens = data['Open'][ticker].dropna().tail(20).tolist()
                volumes = data['Volume'][ticker].dropna().tail(20).tolist()

                live_price = get_real_time_price(ticker)
                if live_price and len(highs) == 20:
                    highs[-1] = max(highs[-1], live_price)
                    lows[-1] = min(lows[-1], live_price)
                    
                result[ticker] = {"high": highs, "low": lows, "open": opens, "volume": volumes}
            except Exception as ticker_err:
                print(f"Error updating ticker {ticker}: {str(ticker_err)}")
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