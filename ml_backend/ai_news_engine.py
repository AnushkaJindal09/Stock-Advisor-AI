import json
import datetime
from flask import Blueprint, jsonify, request
from concurrent.futures import ThreadPoolExecutor
from groq import Groq
# Hamein config se SECTOR_MAP bhi chahiye hoga yahan check karne ke liye
from config import GROQ_API_KEY, SECTOR_MAP, SECTOR_GLOBAL_QUERIES, COMPANY_SEARCH_NAMES, PREMIUM_AI_STOCKS, INTELLIGENCE_CACHE_MINUTES
from data_engine import fetch_company_news_finnhub, fetch_global_news, fetch_yahoo_finance_news

ai_news_bp = Blueprint('ai_news', __name__)
groq_client = Groq(api_key=GROQ_API_KEY)

intelligence_cache = {}

def should_run_gemini(percent_change, volume_ratio, breakout, breakdown, technical_strength):
    if breakout or breakdown: return True
    if abs(percent_change) >= 2: return True
    if volume_ratio >= 1.8: return True
    if technical_strength >= 80 or technical_strength <= 30: return True
    return False

def analyse_with_groq_mixtral(company, sector, ticker_data, company_articles, global_articles):
    try:
        model_name = "llama-3.1-8b-instant" 
        
        def format_full_context(articles):
            if not articles: 
                return "No high-impact news context found for this period."
            formatted = ""
            for idx, art in enumerate(articles, 1):
                headline = art.get('headline', '').strip()
                full_content = art.get('content', '').strip()[:600] 
                source = art.get('source', 'Financial Desk')
                formatted += f"\n--- REPORT {idx} ---\nSOURCE: {source}\nHEADLINE: {headline}\nCONTEXT: {full_content}...\n"
            return formatted

        rich_company_context = format_full_context(company_articles)
        rich_global_context = format_full_context(global_articles)

        # 🌟 AAPKA 100% EXACT ORIGINAL MASTER PROMPT 🌟
        prompt = f"""You are a senior hedge fund manager and lead financial analyst at Bloomberg Terminal.
Analyze {company} ({sector} sector) by cross-referencing technical indicators with full text news context.

TECHNICAL INDICATORS:
Price: ₹{ticker_data.get('price')} | Day Change: {ticker_data.get('percent_change')}%
Verdict: {ticker_data.get('verdict')} | Score: {ticker_data.get('technical_strength')}/100
RSI: {ticker_data.get('rsi')} | MACD: {ticker_data.get('macd')} | Current Trend: {ticker_data.get('trend')}
Support Zone: ₹{ticker_data.get('support')} | Resistance Zone: ₹{ticker_data.get('resistance')}
FII_Activity: {ticker_data.get('fii_action')} # (Yahan tumhare backend se 'Net Selling' ya 'Net Buying' jayega)

DEEP COMPANY NEWS CONTEXT (Analyze the full context text, catch hidden information, not just headlines):
{rich_company_context}

GLOBAL / GEOPOLITICAL / MACRO ECONOMIC CONTEXT:
{rich_global_context}



CRITICAL REASONING RULES (STRICTLY ENFORCED):
1. STRICT TRUTH, ANTI-SPECULATION & DATA SEGREGATION: 
   Be brutally honest. Do NOT fabricate, guess, or make up any financial insights. Analyze ONLY the text provided in the contexts above. If you do not have enough concrete data or if your AI financial knowledge is uncertain about how a macro event will affect the stock, state it honestly rather than generating fake or wrong information. 
   Furthermore, if the context contains mixed signals (e.g., overall net FII selling alongside a specific block deal buying event), you MUST explicitly reconcile and explain this nuance to the user. Do not flatly state "FIIs are buying" in one section and "FIIs are selling" in another without explaining why. Accuracy is non-negotiable.
2. NO REPETITION / VOCABULARY PENALTY: Do NOT use the exact same phrase, sentence, or explanation in more than one place. If you write "weak O2C segment", "margin pressure", or "brokerages remain bullish" in one section, you are strictly FORBIDDEN from using those exact phrases anywhere else in the JSON. Every single field must feature entirely new vocabulary and separate analytical angles.

3. GEOPOLITICAL & MACRO TRANSLATION: You must explicitly translate geopolitical/macro headlines (war, inflation, RBI rates, supply chain disruptions) into their financial impacts on {company}, even if the company's name is NOT mentioned in the headline. If it affects the sector or global markets, it affects the company. Detail how it impacts sourcing costs, revenue, or margins.

4. DEEP CONTEXT ONLY (NEVER HEADLINE ONLY): You must base your reasons on the entire internal 'CONTEXT' field of the reports, never the 'HEADLINE' alone. If a headline is clickbait or contradictory to the internal facts provided in the context, expose the truth. Never pass half-baked information to the user.

5. CHRONOLOGICAL LATEST-FIRST ORDER: You must sort and present all insights starting strictly from the most recent timestamped news downward. The latest news updates must form the foundation of your short-term outlook and market psychology.

6. EXHAUSTIVE EXTRACTION (NO SINGLE-NEWS BIAS): Do not just pick one prominent news article and ignore the rest. You MUST extract, synthesize, and present insights from AS MANY distinct news articles from the provided context as possible. Include all relevant company-specific and global macro updates sequentially to give the user the complete picture.
Return a valid JSON object matching this schema layout dynamically. Ensure all values are fully generated based on the financial analysis:
{{
  "smart_summary": "A high-density, sharp 1-sentence macro/fundamental summary of what is happening to {company} right now. Do not repeat words used below.",
  "overall_sentiment": "Bullish/Bearish/Neutral",
  "sentiment_strength": "Strong/Moderate/Weak",
  "institutional_view": "Deep reasoning on what Smart Money/FIIs are doing with this stock based on the news context and volume ratio. Avoid generic summaries.",
  "money_flow_view": "Contrast the exact volume action of FIIs block deals against retail distribution or trap metrics provided in the internal context body.",
  "market_psychology": "Fear/Greed breakdown of market participants based ONLY on the context text. Avoid generic fear/greed templates.",
  "news_score": 50,
  "major_headlines": [
    {{
      "headline": "Title of the news",
      "source": "Source name",
      "impact": "Positive/Negative/Neutral",
      "importance": "High/Medium/Low",
      "reason": "You must base this reason strictly on the internal 'CONTEXT' field, never headline only. Provide a deeply detailed, multi-sentence analysis explaining HOW the full context of this news dynamically impacts {company}'s core business financials, raw material costs, or stock movement."
    }}
  ],
  "bull_case": [
    "Point 1: Extract specific positive data points or growth segments mentioned ONLY in the context (e.g., specific retail growth numbers, telecom ARPU, or green energy timelines). Absolutely NO generic phrases like 'strong management' or 'diversified portfolio'.",
    "Point 2: Provide another completely distinct positive catalyst with deep financial reasoning."
  ],
  "bear_case": [
    "Point 1: Provide concrete data points regarding the squeeze or selling pressure. Link it strictly to specific operational costs, supply chains, or global demand dampeners stated in the text.",
    "Point 2: Provide another completely distinct risk factor or negative trigger using entirely fresh vocabulary."
  ],
  "short_term_outlook": {{"direction": "Up/Down/Sideways", "confidence": "High/Medium/Low", "reasoning": "Standalone short-term bias weighing recent technical data (RSI/MACD) against the chronological flow of the latest news updates. Zero repetition with bull/bear keys."}},
  "medium_term_outlook": {{"direction": "Up/Down/Sideways", "confidence": "High/Medium/Low", "reasoning": "Macro-driven outlook factoring in global trends, interest rates, or geopolitical shifts from the context and how they will shape structural margins."}},
  "expert_verdict": "Detailed professional trading tactic, entry/exit bias, or stop-loss/target strategy customized for this specific setup."
}}

FINAL COMPLIANCE WARNING: 
I will strictly reject this output if I see phrases like "weak O2C segment performance", "margin pressure", or "growth prospects" repeated across multiple sections. Every single JSON key must feature entirely new financial vocabulary and distinct analytical angles. Synthesize the context data, do not parrot it!"""
        
        completion = groq_client.chat.completions.create(
            model=model_name,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            max_tokens=1500,
            response_format={"type": "json_object"}
        )
        return json.loads(completion.choices[0].message.content.strip())
    except Exception as e:
        print(f"❌ GROQ INTELLIGENCE ERROR: {str(e)}")
        return None

# 🌟 NEW ROUTE ADDED HERE — AB INTELLIGENCE FRONTEND SE DIRECT CONNECTED HAI 🌟
@ai_news_bp.route("/intelligence", methods=["POST"])
def get_intelligence_endpoint():
    try:
        body = request.get_json() or {}
        company = body.get("company", "").upper().strip()
        ticker_data = body.get("ticker_data", {})

        if not company:
            return jsonify({"error": "company name required"}), 400

        # Sector identification logic
        sector = "Other"
        for ticker, sec in SECTOR_MAP.items():
            if company in ticker:
                sector = sec
                break

        # Cache implementation matching your system strategy
        current_time = datetime.datetime.now()
        if company in intelligence_cache:
            cached = intelligence_cache[company]
            age = (current_time - cached["time"]).total_seconds() / 60
            if age < INTELLIGENCE_CACHE_MINUTES:
                return jsonify(cached["data"])

        # Technical filtering for Gemini processing rule validation
        p_change = float(str(ticker_data.get("percent_change", 0)).replace("%", ""))
        v_ratio = float(ticker_data.get("volume_ratio", 1))
        b_out = ticker_data.get("breakout", False)
        b_down = ticker_data.get("breakdown", False)
        t_strength = ticker_data.get("technical_strength", 50)

        # Evaluating dynamic execution safety guard
        if not should_run_gemini(p_change, v_ratio, b_out, b_down, t_strength):
            return jsonify({"status": "Skipped AI Engine", "reason": "Technical triggers not met."})

        # Multi-thread data collection flow
        global_query = SECTOR_GLOBAL_QUERIES.get(sector, f"India stock market {sector} sector news")
        with ThreadPoolExecutor(max_workers=3) as executor:
            f_company = executor.submit(fetch_company_news_finnhub, company, 6)
            f_global = executor.submit(fetch_global_news, global_query, 4)

            company_articles = f_company.result()
            global_articles = f_global.result()

        # Processing final payload transformation
        ai_response = analyse_with_groq_mixtral(company, sector, ticker_data, company_articles, global_articles)
        
        if ai_response:
            intelligence_cache[company] = {"data": ai_response, "time": current_time}
            return jsonify(ai_response)
        else:
            return jsonify({"error": "Failed to generate AI insights"}), 500

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@ai_news_bp.route("/news", methods=["GET"])
def get_news():
    try:
        company = request.args.get("company", "").upper().strip()
        if not company: return jsonify({"error": "company required"}), 400

        sector = "Other"
        for ticker, sec in SECTOR_MAP.items():
            if company in ticker:
                sector = sec
                break

        global_query = SECTOR_GLOBAL_QUERIES.get(sector, f"India {sector} sector stock market news")

        with ThreadPoolExecutor(max_workers=4) as executor:
            future_finnhub = executor.submit(fetch_company_news_finnhub, company, 8)
            future_google = executor.submit(fetch_global_news, global_query, 5)
            future_yahoo = executor.submit(fetch_yahoo_finance_news, company, 5)

            company_articles = future_finnhub.result()
            google_articles = future_google.result()
            yahoo_articles = future_yahoo.result()

        if not company_articles: company_articles = yahoo_articles

        combined_global = google_articles
        seen = set()
        filtered_global = []

        for article in combined_global:
            title = article.get("headline", "")
            if title in seen: continue
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
        return jsonify({"error": str(e)}), 500