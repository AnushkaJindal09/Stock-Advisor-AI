from flask import Blueprint, request, jsonify
import requests

portfolio_intelligence_bp = Blueprint("portfolio_intelligence", __name__)


@portfolio_intelligence_bp.route("/intelligence", methods=["POST"])
def portfolio_intelligence():

    try:
        body = request.get_json() or {}

        holdings = body.get("holdings", [])

        results = []

        attention_count = 0
        safe_count = 0

        total_health_score = 0

        for stock in holdings:

            symbol = stock.get("symbol", "").replace(".NS", "").upper()

            if not symbol:
                continue

            attention_score = 0
            reasons = []

            # -----------------------------
            # CURRENT PRICE
            # -----------------------------

            try:
                stock_res = requests.get(
                    f"https://stock-backend-gsyw.onrender.com/stock?symbol={symbol}",
                    timeout=10
                )

                stock_data = stock_res.json()

                percent_change = float(
                    str(
                        stock_data.get("percent_change", "0")
                    ).replace("%", "")
                )

            except:
                percent_change = 0

            # -----------------------------
            # NEWS INTELLIGENCE
            # -----------------------------

            try:

                ai_res = requests.post(
                    "https://stock-backend-gsyw.onrender.com/intelligence",
                    json={
                        "company": symbol,
                        "ticker_data": {}
                    },
                    timeout=30
                )

                ai_data = ai_res.json()

                sentiment = ai_data.get(
                    "overall_sentiment",
                    "Neutral"
                )

                news_score = ai_data.get(
                    "news_score",
                    50
                )

            except:

                sentiment = "Neutral"
                news_score = 50

            # -----------------------------
            # ATTENTION SCORE
            # -----------------------------

            if sentiment.lower() == "bearish":
                attention_score += 30
                reasons.append(
                    "News sentiment turned bearish"
                )

            if sentiment.lower() == "bullish":
                attention_score += 10

            if abs(percent_change) > 3:
                attention_score += 20
                reasons.append(
                    f"Large price movement ({percent_change}%)"
                )

            if news_score < 40:
                attention_score += 25
                reasons.append(
                    "Weak news confidence score"
                )

            attention_score = min(
                attention_score,
                100
            )

            # -----------------------------
            # STATUS
            # -----------------------------

            if attention_score >= 70:

                status = "ATTENTION"
                attention_count += 1

            elif attention_score >= 40:

                status = "WATCH"
                attention_count += 1

            else:

                status = "SAFE"
                safe_count += 1

            health_score = 100 - attention_score

            total_health_score += health_score

            results.append({

                "symbol": symbol,

                "attention_score": attention_score,

                "health_score": health_score,

                "status": status,

                "reasons": reasons

            })

        # -----------------------------
        # PORTFOLIO HEALTH
        # -----------------------------

        portfolio_health = 100

        if len(results) > 0:

            portfolio_health = round(
                total_health_score / len(results)
            )

        return jsonify({

            "portfolio_health": portfolio_health,

            "attention_required": attention_count,

            "safe_holdings": safe_count,

            "stocks": results

        })

    except Exception as e:

        return jsonify({
            "error": str(e)
        }), 500