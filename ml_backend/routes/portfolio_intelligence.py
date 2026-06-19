from flask import Blueprint, request, jsonify
import requests

portfolio_intelligence_bp = Blueprint(
    "portfolio_intelligence",
    __name__
)


def calculate_exposure(holding, total_capital):

    invested = (
        float(holding.get("quantity", 0))
        *
        float(holding.get("buyPrice", 0))
    )

    if total_capital <= 0:
        return 0

    return round(
        (invested / total_capital) * 100,
        2
    )


@portfolio_intelligence_bp.route(
    "/intelligence",
    methods=["POST"]
)
def portfolio_intelligence():

    try:

        body = request.get_json() or {}

        holdings = body.get(
            "holdings",
            []
        )

        if not holdings:

            return jsonify({

                "portfolio_health": 100,

                "attention_required": 0,

                "priority_stocks": [],

                "stocks": [],

                "portfolio_story": ""

            })

        # -------------------------------------------------
        # TOTAL CAPITAL
        # -------------------------------------------------

        total_capital = 0

        for stock in holdings:

            total_capital += (

                float(
                    stock.get(
                        "quantity",
                        0
                    )
                )

                *

                float(
                    stock.get(
                        "buyPrice",
                        0
                    )
                )
            )

        results = []

        top_risk_stock = None
        top_opportunity_stock = None

        portfolio_news_impact = []

        highest_risk_score = -1
        highest_opportunity_score = -1

        total_health_score = 0

        # -------------------------------------------------
        # PROCESS EACH HOLDING
        # -------------------------------------------------

        for stock in holdings:

            symbol = str(
                stock.get(
                    "symbol",
                    ""
                )
            ).replace(
                ".NS",
                ""
            ).upper()

            if not symbol:
                continue

            capital_exposure = calculate_exposure(
                stock,
                total_capital
            )

            sentiment = "Neutral"
            news_score = 50
            percent_change = 0

            major_headlines = []

            institutional_view = ""

            money_flow_view = ""

            market_psychology = ""

            short_term_outlook = {}

            medium_term_outlook = {}

            # -------------------------------------------------
            # STOCK DATA
            # -------------------------------------------------

            try:

                stock_res = requests.get(
                    f"https://stock-backend-gsyw.onrender.com/stock?symbol={symbol}",
                    timeout=15
                )

                stock_data = stock_res.json()

                percent_change = float(
                    str(
                        stock_data.get(
                            "percent_change",
                            "0"
                        )
                    ).replace(
                        "%",
                        ""
                    )
                )

            except Exception:

                sentiment = "Neutral"
                news_score = 50

                major_news = []

                short_term_outlook = {}

                medium_term_outlook = {}

                institutional_view = ""

                money_flow_view = ""

                market_psychology = ""

            # -------------------------------------------------
            # AI INTELLIGENCE
            # -------------------------------------------------

            try:

                ai_res = requests.post(
                    "https://stock-backend-gsyw.onrender.com/intelligence",
                    json={
                        "company": symbol,
                        "ticker_data": {}
                    },
                    timeout=45
                )

                ai_data = ai_res.json()

                print("\n========== AI RESPONSE ==========")
                print(symbol)
                print(ai_data)
                print("=================================\n")

                sentiment = ai_data.get(
                    "sentiment",
                    ai_data.get(
                        "overall_sentiment",
                        "Neutral"
                    )
                )

                news_score = ai_data.get(
                    "news_score",
                    50
                )

                major_headlines = ai_data.get(
                    "major_headlines",
                    []
                )

                institutional_view = ai_data.get(
                    "institutional_view",
                    ""
                )

                money_flow_view = ai_data.get(
                    "money_flow_view",
                    ""
                )

                market_psychology = ai_data.get(
                    "market_psychology",
                    ""
                )

                short_term_outlook = ai_data.get(
                    "short_term_outlook",
                    {}
                )

                medium_term_outlook = ai_data.get(
                    "medium_term_outlook",
                    {}
                )

            except Exception:
                pass

            # -------------------------------------------------
            # IMPACT SCORE
            # -------------------------------------------------

            impact_score = 0

            high_news_count = len([
                h
                for h in major_headlines
                if str(
                    h.get(
                        "importance",
                        ""
                    )
                ).lower() == "high"
            ])

            if high_news_count > 0:
                impact_score += 15

            inst = str(
                institutional_view
            ).lower()

            if "selling" in inst:
                impact_score += 15

            elif "cautious" in inst:
                impact_score += 10

            flow = str(
                money_flow_view
            ).lower()

            if "distribution" in flow:
                impact_score += 10
                
            # Exposure Weight

            if capital_exposure > 30:

                impact_score += 35

            elif capital_exposure > 15:

                impact_score += 20

            else:

                impact_score += 10

            # Sentiment Weight

            if str(
                sentiment
            ).lower() == "bearish":

                impact_score += 25

            elif str(
                sentiment
            ).lower() == "bullish":

                impact_score += 15

            # News Weight

            if news_score < 40:

                impact_score += 20

            elif news_score > 70:

                impact_score += 10

            # Volatility Weight

            if abs(percent_change) > 3:

                impact_score += 15

            impact_score = min(
                impact_score,
                100
            )

            # -------------------------------------------------
            # WHY TODAY
            # -------------------------------------------------

            why_today = []

            if high_news_count > 0:

                why_today.append(
                    f"{high_news_count} high importance news events detected"
                )

            if "selling" in inst:

                why_today.append(
                    "Institutional selling pressure detected"
                )

            elif "cautious" in inst:

                why_today.append(
                    "Institutional activity has turned cautious"
                )

            if "distribution" in flow:

                why_today.append(
                    "Money flow suggests distribution activity"
                )


            if capital_exposure > 20:

                why_today.append(
                    f"{capital_exposure}% of your portfolio capital is allocated here"
                )

            if str(
                sentiment
            ).lower() == "bearish":

                why_today.append(
                    "News sentiment has weakened"
                )

            elif str(
                sentiment
            ).lower() == "bullish":

                why_today.append(
                    "Positive news sentiment detected"
                )

            if news_score < 40:

                why_today.append(
                    "Low news confidence score"
                )

            elif news_score > 70:

                why_today.append(
                    "Strong news momentum detected"
                )

            if abs(percent_change) > 3:

                why_today.append(
                    f"Large price movement today ({percent_change}%)"
                )

            # -------------------------------------------------
            # STATUS
            # -------------------------------------------------

            if impact_score >= 70:

                status = "HIGH IMPACT"

            elif impact_score >= 40:

                status = "WATCH"

            else:

                status = "LOW IMPACT"

            health_score = 100 - impact_score

            total_health_score += health_score

            # -----------------------------
            # PORTFOLIO NEWS IMPACT
            # -----------------------------

            for news in major_headlines[:3]:

                portfolio_news_impact.append({

                    "symbol": symbol,

                    "headline": news.get("headline"),

                    "impact": news.get("impact"),

                    "importance": news.get("importance")

                })


            # -----------------------------
            # TOP RISK DETECTION
            # -----------------------------

            risk_score = impact_score

            if risk_score > highest_risk_score:

                highest_risk_score = risk_score

                top_risk_stock = {

                    "symbol": symbol,

                    "reason":
                        ", ".join(why_today[:3])

                }


            # -----------------------------
            # TOP OPPORTUNITY DETECTION
            # -----------------------------

            opportunity_score = 0

            if str(sentiment).lower() == "bullish":
                opportunity_score += 40

            if news_score > 60:
                opportunity_score += 20

            if medium_term_outlook.get("direction") == "Up":
                opportunity_score += 30

            if opportunity_score > highest_opportunity_score:

                highest_opportunity_score = opportunity_score

                top_opportunity_stock = {

                    "symbol": symbol,

                    "reason":
                        medium_term_outlook.get(
                            "reasoning",
                            ""
                        )

                }           

            results.append({

                "symbol": symbol,

                "impact_score": impact_score,

                "capital_exposure": capital_exposure,

                "status": status,

                "why_today": why_today,

                "sentiment": sentiment,

                "news_score": news_score,

                "daily_move_percent": percent_change,

                "major_news": major_headlines[:3],

                "institutional_view": institutional_view,

                "money_flow_view": money_flow_view,

                "market_psychology": market_psychology,

                "short_term_outlook": short_term_outlook,

                "medium_term_outlook": medium_term_outlook
            })

        # -------------------------------------------------
        # PORTFOLIO HEALTH
        # -------------------------------------------------

        portfolio_health = round(
            total_health_score /
            len(results)
        )

        # -------------------------------------------------
        # CONCENTRATION RISK
        # -------------------------------------------------

        largest_position = max(
            results,
            key=lambda x: x["capital_exposure"]
        )

        largest_exposure = largest_position[
            "capital_exposure"
        ]

        if largest_exposure >= 50:

            concentration_risk = "VERY HIGH"

        elif largest_exposure >= 35:

            concentration_risk = "HIGH"

        elif largest_exposure >= 20:

            concentration_risk = "MODERATE"

        else:

            concentration_risk = "LOW"

        # -------------------------------------------------
        # PRIORITY RANKING
        # -------------------------------------------------

        priority_stocks = sorted(

            results,

            key=lambda x: x[
                "impact_score"
            ],

            reverse=True

        )[:5]

        attention_required = len(

            [

                stock

                for stock in results

                if stock[
                    "impact_score"
                ] >= 70

            ]

        )

        # -------------------------------------------------
        # AI PORTFOLIO SUMMARY
        # -------------------------------------------------

        summary_lines = []

        if top_risk_stock:

            summary_lines.append(

                f"{top_risk_stock['symbol']} currently requires the most attention in your portfolio."

            )

        if top_opportunity_stock:

            summary_lines.append(

                f"{top_opportunity_stock['symbol']} appears to have the strongest opportunity profile."

            )

        summary_lines.append(

            f"Portfolio concentration risk is {concentration_risk.lower()}."

        )

        portfolio_summary = " ".join(
            summary_lines
        )

        # -------------------------------------------------
        # RESPONSE
        # -------------------------------------------------

        return jsonify({

            "portfolio_health":
                portfolio_health,

            "attention_required":
                attention_required,

            "total_holdings":
                len(results),

            "concentration_risk":
                concentration_risk,

            "portfolio_summary":
                portfolio_summary,

            "top_risk":
                top_risk_stock,

            "top_opportunity":
                top_opportunity_stock,

            "portfolio_news_impact":
                portfolio_news_impact[:10],

            "priority_stocks":
                priority_stocks,

            "stocks":
                results

        })

    except Exception as e:

        return jsonify({

            "error": str(e)

        }), 500