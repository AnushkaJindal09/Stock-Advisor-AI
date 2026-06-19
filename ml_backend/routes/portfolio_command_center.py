from flask import Blueprint, request, jsonify
import requests

portfolio_command_bp = Blueprint(
    "portfolio_command_center",
    __name__
)

def calculate_ai_risk(ai_data, stock_data):

    risk = 50

    sentiment = str(
        ai_data.get(
            "overall_sentiment",
            "Neutral"
        )
    ).lower()

    news_score = int(
        ai_data.get(
            "news_score",
            50
        )
    )

    institutional = str(
        ai_data.get(
            "institutional_view",
            ""
        )
    ).lower()

    psychology = str(
        ai_data.get(
            "market_psychology",
            ""
        )
    ).lower()

    percent_change = float(
        str(
            stock_data.get(
                "percent_change",
                0
            )
        ).replace("%", "")
    )

    if sentiment == "bullish":
        risk -= 15

    elif sentiment == "bearish":
        risk += 15

    risk += (50 - news_score) * 0.6

    if "selling" in institutional:
        risk += 10

    if "distribution" in psychology:
        risk += 8

    if abs(percent_change) > 5:
        risk += 5

    return max(
        0,
        min(
            round(risk),
            100
        )
    )
@portfolio_command_bp.route(
    "/command-center",
    methods=["POST"]
)
def command_center():

    try:

        body = request.get_json() or {}
        holdings = body.get("holdings", [])

        stocks = []

        strongest_stock = None
        weakest_stock = None

        portfolio_health_total = 0

        today_focus = []

        for item in holdings:

            symbol = item.get(
                "symbol",
                ""
            ).upper()

            if not symbol:
                continue

            try:

                stock_res = requests.get(
                    f"http://localhost:5000/stock?symbol={symbol}",
                    timeout=15
                )

                stock_data = stock_res.json()

            except:

                stock_data = {}

            try:

                ai_res = requests.post(
                    "http://localhost:5000/intelligence",
                    json={
                        "company": symbol,
                        "ticker_data": stock_data
                    },
                    timeout=60
                )

                ai_data = ai_res.json()

                print("\n\n========== AI DATA ==========")
                print(symbol)
                print(ai_data)
                print("=============================\n\n")
            except:

                ai_data = {}

            sentiment = ai_data.get(
                "overall_sentiment",
                "Neutral"
            )

            news_score = ai_data.get(
                "news_score",
                50
            )

            institutional_view = str(
                ai_data.get(
                    "institutional_view",
                    ""
                )
            )

            percent_change = float(
                str(
                    stock_data.get(
                        "percent_change",
                        0
                    )
                ).replace("%", "")
            )

            risk_score = calculate_ai_risk(
                ai_data,
                stock_data
            )
            health_score = 100 - risk_score

            portfolio_health_total += health_score

            stock_result = {

                "symbol": symbol,

                "risk_score": risk_score,

                "health_score": health_score,

                "sentiment": sentiment,

                "news_score": news_score,

                "smart_summary":
                    ai_data.get(
                        "smart_summary",
                        ""
                    ),

                "institutional_view":
                    ai_data.get(
                        "institutional_view",
                        ""
                    ),

                "market_psychology":
                    ai_data.get(
                        "market_psychology",
                        ""
                    ),

                "money_flow_view":
                    ai_data.get(
                        "money_flow_view",
                        ""
                    )

            }
            stocks.append(
                stock_result
            )

            if (
                strongest_stock is None
                or
                health_score >
                strongest_stock["health_score"]
            ):

                strongest_stock = stock_result

            if (
                weakest_stock is None
                or
                risk_score >
                weakest_stock["risk_score"]
            ):

                weakest_stock = stock_result

        portfolio_health = 0

        if stocks:

            portfolio_health = round(
                portfolio_health_total /
                len(stocks)
            )

        if weakest_stock:

            today_focus.append({

                "symbol":
                    weakest_stock["symbol"],

                "reason":
                    "Highest portfolio risk today"

            })

        if strongest_stock:

            today_focus.append({

                "symbol":
                    strongest_stock["symbol"],

                "reason":
                    "Strongest portfolio setup"

            })
        return jsonify({

            "portfolio_health":
                portfolio_health,

            "portfolio_risk_level":

                "LOW"
                if portfolio_health >= 80
                else

                "MEDIUM"
                if portfolio_health >= 60
                else

                "HIGH",

            "strongest_stock":
                strongest_stock,

            "biggest_risk_stock":
                weakest_stock,

            "today_focus":
                today_focus,

            "total_holdings":
                len(stocks),

            "stocks":
                stocks

        })

    except Exception as e:
        print("COMMAND CENTER ERROR:")
        print(str(e))

        return jsonify({
            "error": str(e)
        }), 500