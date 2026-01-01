import axios from "axios";
import { useEffect, useState, useRef } from "react";
import { Link } from "react-router-dom";
import { fetchNewsData, filterNewsByCompany } from "../utils/news";
import { lookupSymbolFromName, fetchStockData } from "../utils/stockutils";

function Aichat() {
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef(null);

  // ✅ Helper to add AI messages
  const addBotMessage = (text) => {
    setMessages((prev) => [...prev, { role: "ai_assistant", content: text }]);
  };

// ✅ Trigger ML Prediction (Corrected)
const triggerMLPrediction = async (userMessage) => {
  try {
    const res = await fetch("http://localhost:5000/predict", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({}), // agar backend mein company pass karna optional hai toh empty hi theek hai
    });

    const data = await res.json();
    if (!res.ok) throw new Error(data.error || "Server error");

    // company detect from user message
    const lowerMsg = userMessage.toLowerCase();
    let companyPrediction = null;

    if (Array.isArray(data.prediction)) {
      for (let p of data.prediction) {
        if (
          p.company &&
          lowerMsg.includes(p.company.toLowerCase().split(".")[0])
        ) {
          companyPrediction = p;
          break;
        }
      }
    }

    if (companyPrediction) {
      const msg = `📈 ML Prediction for ${companyPrediction.company}:\n➡️ Predicted Price: ₹${companyPrediction.predicted_price}`;
      addBotMessage(msg);
      return msg;
    } else if (Array.isArray(data.prediction) && data.prediction.length > 0) {
      let allPreds = "📊 ML Predictions:\n";
      data.prediction.slice(0, 3).forEach((p, i) => {
        allPreds += `\n${i + 1}. ${p.company}: ₹${p.predicted_price}`;
      });
      addBotMessage(allPreds);
      return allPreds;
    } else {
      addBotMessage("⚠️ No predictions available.");
      return null;
    }
  } catch (err) {
    addBotMessage("⚠️ ML Prediction failed: " + err.message);
    return null;
  }
};

// ✅ Chat logic (main flow) -> bas ML ka check use karega
const callAIChat = async (userMessage) => {
  setLoading(true);
  try {
    const portfolioData = JSON.parse(localStorage.getItem("portfolioData") || "[]");
    const userQuery = userMessage.toLowerCase();

    // 🔹 1. ML Prediction Check
    if (
      userQuery.includes("predict") ||
      userQuery.includes("tomorrow price") ||
      userQuery.includes("forecast")
    ) {
      await triggerMLPrediction(userMessage);
      setLoading(false);
      return;
    }

    // 🔹 2. Real-time Stock Price Check
    let stockText = "";
    const potentialSymbol = await lookupSymbolFromName(userQuery);
    if (potentialSymbol) {
      const stockData = await fetchStockData(potentialSymbol);
      if (stockData && stockData.c) {
        stockText = `📊 Real-time Stock Data for ${potentialSymbol}:
- Current Price: ₹${stockData.c}
- Change: ₹${stockData.d} (${stockData.dp}%)
- High: ₹${stockData.h}
- Low: ₹${stockData.l}
- Open: ₹${stockData.o}
- Previous Close: ₹${stockData.pc}`;
      }
    }

    // 🔹 3. News Fetch
    let newsSummary = "";
    if (userQuery.includes("news") || userQuery.includes("headline")) {
      const articles = await fetchNewsData(userQuery);
      const filteredArticles = filterNewsByCompany(articles, userQuery);
      if (filteredArticles.length > 0) {
        newsSummary = "📰 Latest News:\n";
        filteredArticles.slice(0, 3).forEach((a, i) => {
          newsSummary += `\n${i + 1}. ${a.title}`;
        });
      }
    }

    // 🔹 4. Final Prompt for LLM
    const finalPrompt = `
You are a professional AI-based financial advisor.

User asked: "${userMessage}"

Available Data:
${stockText ? stockText : ""}
${portfolioData.length > 0 && userQuery.includes("portfolio") ? 
  `📂 Portfolio Data: ${JSON.stringify(portfolioData, null, 2)}` : ""}
${newsSummary ? newsSummary : ""}

Rules:
- If user asks about stock → only use stockText.
- If user asks about portfolio → only use portfolioData.
- If user asks about news → only use newsSummary.
- If ML predictions were already provided, don't repeat them.
- If none of these match, just answer naturally like a professional assistant.
Special Rule:
- If user asks **whether they should sell their stock**:
   1. First, check the user’s holdings in 'portfolioData' (to confirm stock presence and quantity).
   2. Then, check the 'mlPrediction' for the next day (expected up or down).
   3. Also, check the 'newsSummary' for sentiment/trend.
   4. Based on all three, give a **final recommendation style answer like a financial analyst** (NOT a disclaimer). Example:
      - If portfolio has stock + ML trend is negative + news is bearish → say: “Based on your portfolio holdings, the model predicts a likely decline tomorrow and news sentiment is weak. You may consider selling or reducing your position.”
      - If portfolio has stock + ML trend is positive + news is supportive → say: “You hold Reliance in your portfolio, the model shows likely growth tomorrow, and news sentiment is positive. Holding might be a better choice.”
`;

    const response = await axios.post(
      "https://openrouter.ai/api/v1/chat/completions",
      {
        model: "mistralai/mixtral-8x7b-instruct",
        messages: [{ role: "user", content: finalPrompt }],
      },
      {
        headers: {
          Authorization: `Bearer ${import.meta.env.VITE_OPENROUTER_API_KEY}`,
          "Content-Type": "application/json",
        },
      }
    );

    const aiReply = response.data.choices[0].message.content;
    addBotMessage(aiReply);
  } catch (err) {
    console.error("AIChat Error:", err);
    addBotMessage("⚠️ Something went wrong. Try again later.");
  } finally {
    setLoading(false);
  }
};


  // ✅ Handle user send
  const handleSend = async () => {
    if (!input.trim()) return;
    setMessages((prev) => [...prev, { role: "user", content: input }]);
    const msg = input;
    setInput("");
    await callAIChat(msg);
  };

  // ✅ Auto scroll
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleKeyDown = (e) => {
    if (e.key === "Enter") handleSend();
  };

  return (
    <div className="flex flex-col h-screen relative bg-gradient-to-br from-black via-gray-900 to-black text-white px-1 text-lg">
      
      <div className="sticky top-0 z-50 backdrop-blur-md bg-black/20 border-b border-white/10 shadow-md">
        <div className="w-full mb-9 px-6 py-4 bg-white/10 flex items-center justify-between">
          <div className="text-2xl sm:text-3xl font-extrabold tracking-wide text-transparent bg-clip-text bg-gradient-to-r from-blue-500 via-cyan-400 to-green-400 select-none">
            FinTrack
          </div>
          <div className="space-x-6 text-sm sm:text-base font-medium tracking-wide text-white">
            <Link to="/home" className="hover:text-cyan-400">Home</Link>
            <Link to="/graph" className="hover:text-cyan-400">Forecast</Link>
            <Link to="/news" className="hover:text-cyan-400">News</Link>
            <Link to="/portfolio" className="hover:text-cyan-400">Portfolio</Link>
          </div>
        </div>
      </div>

      
      <div className="flex-1 overflow-y-auto rounded-xl bg-black/30 border border-white/10 backdrop-blur-md shadow-inner px-4 py-3 mb-4">
        {messages.map((msg, idx) => (
          <div
            key={idx}
            className={`mb-3 px-4 py-2 rounded-xl max-w-[55%] m-5 shadow-md ${
              msg.role === "user"
                ? "self-end bg-indigo-600 text-white ml-auto"
                : "self-start bg-white/10 text-indigo-200"
            }`}
          >
            {msg.content}
          </div>
        ))}
        <div ref={messagesEndRef} />
        {loading && (
          <div className="text-white/80 ml-2 mt-2 text-xl animate-pulse">
            AI is typing...
          </div>
        )}
      </div>

      
      <div className="flex items-center mt-2 mb-9">
        <input
          type="text"
          placeholder="Enter your message..."
          className="flex-grow px-4 py-2 rounded-l-xl bg-white/10 text-white border-t border-l border-b border-white/20 focus:outline-none focus:ring-2 focus:ring-indigo-500 placeholder:text-gray-400"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
        />
        <button
          onClick={handleSend}
          className="px-5 py-2 bg-indigo-600 hover:bg-indigo-700 text-white font-semibold rounded-r-xl"
        >
          Send
        </button>
      </div>
    </div>
  );
}

export default Aichat;











