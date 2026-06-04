import datetime
import pytz
import requests
from flask import Blueprint, jsonify, request, current_app
from groq import Groq
from config import GROQ_API_KEY, AI_CHAT_SYSTEM_INSTRUCTION

ai_chat_bp = Blueprint('ai_chat', __name__)
groq_client = Groq(api_key=GROQ_API_KEY)

def identify_market_session():
    IST = pytz.timezone('Asia/Kolkata')
    now = datetime.datetime.now(IST)
    current_time = now.time()
    if datetime.time(9, 15) <= current_time <= datetime.time(10, 30):
        return f"Opening Bell session — {now.strftime('%I:%M %p')} IST"
    elif datetime.time(13, 30) <= current_time <= datetime.time(15, 30):
        return f"Institutional crossover session — {now.strftime('%I:%M %p')} IST"
    elif datetime.time(9, 15) <= current_time <= datetime.time(15, 30):
        return f"Market live — {now.strftime('%I:%M %p')} IST"
    else:
        return f"Market closed — {now.strftime('%I:%M %p')} IST"

@ai_chat_bp.route("/chat", methods=["POST"])
def financial_chat_advisor():
    try:
        body = request.get_json() or {}
        user_query = body.get("query", "").strip()
        company = body.get("company", "").upper().strip()
        frontend_portfolio = body.get("portfolio", [])

        if not user_query:
            return jsonify({"error": "Query required"}), 400

        session_context = identify_market_session()

        asset_portfolio_context = "No active holdings for this company."
        if company and frontend_portfolio:
            for item in frontend_portfolio:
                sym = str(item.get('symbol', '') or item.get('name', '')).upper()
                if company in sym or sym in company:
                    asset_portfolio_context = f"Active holding — Qty: {item.get('quantity', 0)} | Avg Price: ₹{item.get('avgPrice', item.get('buyPrice', 0))}"
                    break

        market_page_data = {
            "price": "N/A",
            "percent_change": "N/A",
            "rsi": 50,
            "macd_status": "Neutral"
        }

        try:
            with current_app.test_client() as client:
                stock_res = client.get(f'/stock?symbol={company}')
                if stock_res.status_code == 200:
                    raw_stock = stock_res.get_json()
                    market_page_data["price"] = raw_stock.get("price", "N/A")
                    market_page_data["percent_change"] = raw_stock.get("percent_change", "N/A")

                signal_res = client.get('/signals')
                if signal_res.status_code == 200:
                    signals_data = signal_res.get_json()
                    for sig in signals_data.get("signals", []):
                        if sig.get("company") == company:
                            market_page_data["rsi"] = sig.get("signals", {}).get("rsi", 50)
                            market_page_data["macd_status"] = sig.get("signals", {}).get("macd", "Neutral")
                            break
        except Exception as e:
            print(f"Market data error: {e}")

        ml_forecast_data = "Prediction unavailable."
        try:
            HF_URL = "https://anushka09092004-stock-ml-api.hf.space/predict"
            pred_res = requests.post(HF_URL, json={"company": company}, timeout=15)
            if pred_res.status_code == 200:
                predictions = pred_res.json().get("prediction", [])
                if predictions:
                    p = predictions[0]
                    ml_forecast_data = (
                        f"Target: ₹{p.get('predicted_price')} | "
                        f"Range: ₹{p.get('range_low')} - ₹{p.get('range_high')} | "
                        f"Confidence: {p.get('confidence')}"
                    )
        except Exception as e:
            print(f"Prediction error: {e}")

        groq_deep_news_intel = {}
        try:
            with current_app.test_client() as client:
                news_payload = {
                    "company": company or "GLOBAL",
                    "ticker_data": {
                        "price": market_page_data.get("price"),
                        "percent_change": market_page_data.get("percent_change"),
                        "rsi": market_page_data.get("rsi"),
                        "macd": market_page_data.get("macd_status"),
                        "technical_strength": 60,
                        "volume_ratio": 1.0,
                        "breakout": False,
                        "breakdown": False
                    }
                }
                news_res = client.post('/intelligence', json=news_payload)
                if news_res.status_code == 200:
                    groq_deep_news_intel = news_res.get_json()
        except Exception as e:
            print(f"News intel error: {e}")

        composite_payload = f"""
USER QUERY: {user_query}
COMPANY: {company or "General"}
SESSION: {session_context}

MARKET DATA:
Price: {market_page_data.get('price')}
Change: {market_page_data.get('percent_change')}
RSI: {market_page_data.get('rsi')}
MACD: {market_page_data.get('macd_status')}

PREDICTION: {ml_forecast_data}

NEWS SUMMARY: {groq_deep_news_intel.get('smart_summary', 'No major developments.')}
BULLISH: {groq_deep_news_intel.get('bull_case', 'No strong bullish catalyst.')}
BEARISH: {groq_deep_news_intel.get('bear_case', 'No major bearish pressure.')}
SENTIMENT SCORE: {groq_deep_news_intel.get('news_score', 50)}/100

PORTFOLIO: {asset_portfolio_context}

LANGUAGE: Respond in Hinglish only.
STYLE: Conversational, calm, human — like an experienced trader talking to a friend.
COMPLIANCE: Never say buy, sell, invest directly. Never give direct financial advice.
"""

        completion = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": AI_CHAT_SYSTEM_INSTRUCTION},
                {"role": "user", "content": composite_payload}
            ],
            temperature=0.5,
            max_tokens=500
        )

        return jsonify({
            "response": completion.choices[0].message.content.strip(),
            "status_metrics": {
                "rsi": market_page_data.get("rsi"),
                "macd": market_page_data.get("macd_status"),
                "news_connected": bool(groq_deep_news_intel),
                "prediction_connected": "Target" in ml_forecast_data
            }
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500




















'''
# ai_chat_engine.py
import datetime
import json
import pytz
import requests
from flask import Blueprint, jsonify, request, current_app
from groq import Groq
from config import GROQ_API_KEY, AI_CHAT_SYSTEM_INSTRUCTION

ai_chat_bp = Blueprint('ai_chat', __name__)
groq_client = Groq(api_key=GROQ_API_KEY)

def identify_market_session():
    """Upgrade: Real-time Time & Institutional Session Awareness (IST Fixed)"""
    IST = pytz.timezone('Asia/Kolkata')
    now = datetime.datetime.now(IST) 
    current_time = now.time()
    
    if datetime.time(9, 15) <= current_time <= datetime.time(10, 30):
        return f"Abhi subah ke {now.strftime('%I:%M %p')} ho rahe hain — Opening Bell Volatility Session progress mein hai, jahan structural breakout aur high momentum setup trades control hote hain."
    elif datetime.time(13, 30) <= current_time <= datetime.time(15, 30):
        return f"Abhi dopehar ke {now.strftime('%I:%M %p')} ho rahe hain — Intraday Institutional Crossover time chal raha hai, jab European indices open hote hain aur dynamic volume adjustments hote hain."
    elif datetime.time(9, 15) <= current_time <= datetime.time(15, 30):
        return f"Abhi {now.strftime('%I:%M %p')} baje hain — Domestic Market Live ongoing session hai, asset liquidity flows continuous chal rahe hain."
    else:
        return f"Abhi off-market hours ke {now.strftime('%I:%M %p')} baje hain — Domestic exchanges closed hain. Yeh structural balancing, data screening aur capital allocation review ka perfect execution time hai."

@ai_chat_bp.route("/chat", methods=["POST"])
def financial_chat_advisor():
    try:
        body = request.get_json() or {}
        user_query = body.get("query", "").strip()
        company = body.get("company", "").upper().strip()
        frontend_portfolio = body.get("portfolio", [])  # Live array passed directly from frontend localStorage

        if not user_query:
            return jsonify({"error": "Query string is a required internal parameter."}), 400

        # 1. Capture Time & Session Context
        session_context = identify_market_session()

        # 2. Extract Real Portfolio context for this specific asset from user's live portfolio
        asset_portfolio_context = "No current active holdings or open exposure found for this company in the portfolio storage."
        if company and frontend_portfolio:
            for item in frontend_portfolio:
                sym = str(item.get('symbol', '') or item.get('name', '')).upper()
                if company in sym or sym in company:
                    asset_portfolio_context = f"ACTIVE HOLDINGS SYNCED -> Qty: {item.get('quantity', 0)} | Entry Average Price: ₹{item.get('avgPrice', item.get('buyPrice', 0))}"
                    break

        # 3. Connect Market Page Data & Technical Metrics dynamically via internal requests
        # Signals route se real data lo
        signal_res = client.get(f'/signals', timeout=5)
        real_rsi = 50
        real_macd = "Neutral"

        if signal_res.status_code == 200:
            signals_data = signal_res.get_json()
            for sig in signals_data.get("signals", []):
                if sig.get("company") == company:
                    real_rsi = sig.get("signals", {}).get("rsi", 50)
                    real_macd = sig.get("signals", {}).get("macd", "Neutral")
                    break

        market_page_data = {
            "price": raw_stock.get("price", "N/A"),
            "percent_change": raw_stock.get("percent_change", "0%"),
            "rsi": real_rsi,
            "macd_status": real_macd,
            "volatility_index": "Normal Matrix"
        }
                else:
                    print(f"⚠️ Stock Route Returned Code {stock_res.status_code}")
        except Exception as e:
            print(f"⚠️ Stock Desk Sync Exception: {str(e)}")
            market_page_data = {"price": "Market Data Desk Sync Pending", "percent_change": "0%", "rsi": 50, "macd_status": "Awaiting Feed"}

        # 4. Connect Forecast / ML Prediction Range (INTEGRATED: Direct Hugging Face Autonomous Core)
        ml_forecast_data = "Mathematical prediction range calculations currently processing on the forecast matrix desk."
        try:
            # FIXED: Yahan dummy placeholder hata kar actual active Hugging Face link inject kar diya hai
            HF_SPACE_URL = "https://anushka09092004-stock-ml-api.hf.space/predict" 
            
            pred_res = requests.post(HF_SPACE_URL, json={"company": company}, timeout=45)
            if pred_res.status_code == 200:
                pred_data = pred_res.json()
                predictions_list = pred_data.get("prediction", [])
                if predictions_list:
                    p = predictions_list[0]
                    # Direct advanced metrics injection block
                    ml_forecast_data = (
                        f"XGBoost Quantitative Model Forecast Matrix: Target Price is ₹{p.get('predicted_price')}, "
                        f"with a mathematical Floor Range Low of ₹{p.get('range_low')} "
                        f"and a Ceiling Range High of ₹{p.get('range_high')}. "
                        f"Engine Confidence Model: {p.get('confidence')}."
                    )
            else:
                print(f"⚠️ Hugging Face Spaces returned status code {pred_res.status_code}")
        except Exception as e:
            ml_forecast_data = f"Forecast parameter lookup offline from HF cluster: {str(e)}"

        # 5. Connect the Ultimate Groq News Engine
        groq_deep_news_intel = {}
        try:
            with current_app.test_client() as client:
                news_payload = {
                    "company": company if company else "GLOBAL",
                    "ticker_data": {
                        "price": market_page_data.get("price"),
                        "percent_change": market_page_data.get("percent_change"),
                        "verdict": "Consolidating Setup",
                        "technical_strength": 60,
                        "rsi": market_page_data.get("rsi"),
                        "macd": market_page_data.get("macd_status"),
                        "trend": "Analyzing structural momentum bounds",
                        "support": "Internal baseline pricing structures",
                        "resistance": "Internal overhead ceiling benchmarks",
                        "fii_action": "Monitoring institutional order books",
                        "volume_ratio": 1.0,
                        "breakout": False,
                        "breakdown": False
                    }
                }
                news_res = client.post('/market_news/intelligence', json=news_payload)
                if news_res.status_code == 200:
                    groq_deep_news_intel = news_res.get_json()
                else:
                    print(f"⚠️ News Route Returned Code {news_res.status_code}")
        except Exception as e:
            print(f"⚠️ News Pipeline Extraction Notice: {str(e)}")

        # 6. Composite Core Payload Construction - Pure Contextual Wisdom Formulation
# ============================================================
# CONTEXTUAL DECISION INTELLIGENCE PAYLOAD
# ============================================================

        composite_terminal_payload = f"""

        USER QUERY:
        {user_query}

        TARGET ASSET:
        {company if company else "General Market Context"}

        ━━━━━━━━━━━━━━━━━━
        REAL-TIME MARKET CONTEXT
        ━━━━━━━━━━━━━━━━━━

        SESSION:
        {session_context}

        LIVE MARKET DATA:
        {market_page_data}

        PREDICTION CONTEXT:
        {ml_forecast_data}

        ━━━━━━━━━━━━━━━━━━
        NEWS & MARKET INTELLIGENCE
        ━━━━━━━━━━━━━━━━━━

        IMPORTANT NEWS SUMMARY:
        {groq_deep_news_intel.get('smart_summary', 'No major market-moving developments detected.')}

        BULLISH FACTORS:
        {groq_deep_news_intel.get('bull_case', 'No strong bullish catalyst currently dominating.')}

        BEARISH FACTORS:
        {groq_deep_news_intel.get('bear_case', 'No major bearish pressure currently dominating.')}

        MARKET SENTIMENT SCORE:
        {groq_deep_news_intel.get('news_score', 50)}/100

        ━━━━━━━━━━━━━━━━━━
        PORTFOLIO CONTEXT
        ━━━━━━━━━━━━━━━━━━

        {asset_portfolio_context}

        ━━━━━━━━━━━━━━━━━━
        AI RESPONSE BEHAVIOR RULES
        ━━━━━━━━━━━━━━━━━━

        Your task is NOT to impress the user with complex jargon.

        Your task is to help the user make calmer, smarter, and more disciplined trading decisions.

        IMPORTANT:

        - Only include information relevant to the user's query.
        - Do NOT force unnecessary sections.
        - Do NOT mention every metric available.
        - Do NOT behave like a fixed report template.
        - Avoid repetitive institutional buzzwords.
        - Avoid fake sophistication.
        - Avoid generic macro commentary unless directly relevant.
        - Avoid repeating the same response structure across queries.

        Adapt naturally based on:
        - user intent
        - emotional state
        - urgency
        - market conditions
        - portfolio risk
        - volatility environment

        If the user asks:
        - a short question → give focused insight
        - about risk → prioritize risk discussion
        - about holding → discuss structure, risk, exposure, sentiment, volatility
        - about news → focus mostly on news impact
        - about emotional trading → prioritize psychology guidance
        - about prediction → explain probabilities and invalidation risks
        - about losses → prioritize capital protection and emotional discipline

        ━━━━━━━━━━━━━━━━━━
        CRITICAL TRADING PSYCHOLOGY RULES
        ━━━━━━━━━━━━━━━━━━

        Actively help users avoid:

        - FOMO entries
        - revenge trading
        - emotional averaging
        - panic exits
        - oversized positions
        - impulsive decisions
        - overconfidence during volatility

        Never encourage:
        - guaranteed outcomes
        - aggressive loss recovery
        - blind conviction

        If emotional behavior is detected:
        subtly guide the user toward:
        - patience
        - smaller risk
        - discipline
        - structured thinking
        - emotional stability

        ━━━━━━━━━━━━━━━━━━
        COMMUNICATION RULES
        ━━━━━━━━━━━━━━━━━━

        The response must feel:
        - intelligent
        - human
        - adaptive
        - practical
        - psychologically stabilizing

        Use:
        - clean formatting
        - short sections
        - bullets where useful
        - concise explanations

        Avoid:
        - giant text walls
        - robotic repetition
        - repetitive buzzwords
        - forced institutional language
        - fake certainty

        Do NOT give direct buy/sell/hold advice.

        Instead discuss:
        - important risks
        - probability shifts
        - structure quality
        - invalidation areas
        - volatility concerns
        - sentiment changes
        - things worth monitoring


        EMOTIONAL DETECTION RULES:

        If user message contains words like:
        - "recover", "loss", "wapas", "jaldi", "FOMO", "miss", "fast", 
        "double", "gambling", "frustrated", "angry", "scared"

        Then FIRST acknowledge their emotional state calmly.
        Then show relevant real data.
        Then explain what typically happens in this situation statistically.
        Never dismiss emotions — address them directly.

        The final decision always belongs to the user.

        """

        # Stream / Generate the final adaptive response using Groq's high-speed engine
        completion = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": AI_CHAT_SYSTEM_INSTRUCTION},
                {"role": "system", "content": "Always respond in Hinglish — mix of Hindi and English, conversational tone. Never respond in pure English or pure Hindi."},
                {"role": "user", "content": composite_terminal_payload}
            ],
            temperature=0.5,
            max_tokens=600
        )

        terminal_wisdom_reply = completion.choices[0].message.content.strip()
        return jsonify({
            "response": terminal_wisdom_reply,
            "status_metrics": {
                "session_active": True,
                "portfolio_synced": True if "ACTIVE HOLDINGS" in asset_portfolio_context else False,
                "news_desk_linked": True if groq_deep_news_intel else False,
                "legacy_forecast_linked": True if "XGBoost" in ml_forecast_data else False
            }
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    '''