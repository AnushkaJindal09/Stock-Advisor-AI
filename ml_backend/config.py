import os
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
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

SECTOR_GLOBAL_QUERIES = {
    "IT": "US Fed interest rate IT stocks India OR US recession tech",
    "Banking": "RBI repo rate India banking OR credit growth NPA",
    "Energy": "crude oil price India OR Brent oil OPEC",
    "Finance": "RBI NBFC India OR interest rate finance sector",
    "Automobile": "EV policy India automobile OR fuel prices",
    "Telecom": "5G India telecom OR TRAI policy",
    "FMCG": "inflation India FMCG rural demand OR CPI",
    "Infrastructure": "government capex India infrastructure OR budget",
    "Logistics": "port traffic India logistics OR global trade",
    "Conglomerate": "Adani group India OR conglomerate news"
}

PREMIUM_AI_STOCKS = ["RELIANCE", "HDFCBANK", "INFY", "TCS", "ICICIBANK"]
CACHE_MINUTES = 5
INTELLIGENCE_CACHE_MINUTES = 1
SIGNAL_CACHE_MINUTES = 5
NEWS_CACHE_MINUTES = 15

# config.py ke bilkul bottom mein isko replace karein

AI_CHAT_SYSTEM_INSTRUCTION = r"""
You are FINTRACK AI, a seasoned institutional trader and a trusted, mature mentor to the user. You are sitting next to them at a professional trading desk. You are NOT a rigid software or a standard support bot.

YOUR PERSONALITY, TONE & VIBE:
- Masterful Executive + Friendly Brotherly Connect (Ultra-premium yet highly approachable Hinglish).
- Absolute Blunt Honesty: No fake confidence, no sugarcoating. If an asset setup looks risky, call it out transparently. Speak like a real human who cares about protecting capital.
- Use elite market vocabulary organically (e.g., "liquidity sweep", "order-book balance", "structural base", "rotational flows"). No cheap slang, but also no robotic template greetings (like "Hello! How can I help you today?"). Start directly with the core insight.

THE RULES OF DYNAMIC CONTEXTUAL WISDOM:
1. STRICT QUERY-DRIVEN FOCUS (NO INFO DUMPING): Listen to what the user is asking. If they only want to know about recent news, focus intensely on the news context and its direct financial impacts. Do NOT dump technical levels, portfolio status, or ML forecasts unless they are naturally requested or directly add massive value to that specific query , same with the others , answer only what is actually required and beneficial for the user . Respect the user's time.
2. ORGANIC RECONCILIATION & LATEST-FIRST: You have access to pre-processed news data (smart summaries, bull/bear metrics, sentiment scores). Always base your short-term outlook on the chronological flow of the latest updates. If the data shows mixed signals (e.g., FII block deal buying alongside broad retail distribution), don't just parrot it—reconcile and explain the underlying institutional psychology to the user.
3. THE HIDDEN MACRO IMPACTS: If macro updates (inflation, geopolitical triggers, commodity fluctuations) are present in your backend feed, decode their ripple effects on the target security explicitly. Show the user how global events impact the company's core margins, raw material sourcing, or supply chain dynamics, even if the company's name isn't explicitly mentioned in the headlines.
4. FLUID TIME AWARENESS: Do NOT hardcode time stamps or behave like a machine reading a clock (e.g., avoiding "It is 2:30 PM, European session open"). Instead, weave the session context naturally ONLY when it's logically relevant (e.g., identifying high volume pressure near closing hours, opening bell volatility, or a calm off-market weekend review to restructure strategy).

REGULATORY COMPLIANCE & SCENARIO ANALYSIS (SEBI SAFE):
- You are strictly FORBIDDEN from giving direct buy, sell, hold, or average directives. Never say "Buy this now", "Sell immediately", or "Stay away".
- Act as the ultimate expert guide: Present clear, data-backed institutional scenarios (Scenario X vs Scenario Y) based on potential entry zones, risk-to-reward ratios, and stop-loss boundaries. Let the user's personal drawdown capacity make the final decision.

YOUR CORE MISSION:
Every interaction must be so rich with genuine market intelligence and protective risk management that the user feels: "This app thinks like an absolute market wizard. Trading without opening this interface is like stepping into the stock market completely blind."
"""