import datetime
import pytz
import requests
from flask import Blueprint, jsonify, request, current_app, Response
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

        market_page_data = {"price": "N/A", "percent_change": "N/A", "rsi": 50, "macd_status": "Neutral"}

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
STYLE: Conversational, calm, human — like an experienced trader talking to a friend. Use clear line breaks and structural spacing for points.
COMPLIANCE: Never say buy, sell, invest directly. Never give direct financial advice.
"""

        # ─── REAL-TIME CHUNK BUFFER GENERATOR ───
        def generate_chunks():
            completion_stream = groq_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": AI_CHAT_SYSTEM_INSTRUCTION},
                    {"role": "user", "content": composite_payload}
                ],
                temperature=0.5,
                max_tokens=600,
                stream=True
            )
            
            for chunk in completion_stream:
                if chunk.choices and chunk.choices[0].delta and chunk.choices[0].delta.content:
                    token = chunk.choices[0].delta.content
                    # Raw token ke sath single newline append kiya taaki downstream flush ho sake
                    yield token

        # Response standard application/json stream content set kiya
        response = Response(generate_chunks(), content_type='text/plain; charset=utf-8')
        response.headers['Cache-Control'] = 'no-cache, no-transform'
        response.headers['X-Accel-Buffering'] = 'no'  # Forces Render/Nginx proxy downlinks to unbuffer
        response.headers['Connection'] = 'keep-alive'
        
        return response

    except Exception as e:
        return jsonify({"error": str(e)}), 500



'''import datetime
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














