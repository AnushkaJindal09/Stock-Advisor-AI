
import axios from "axios";
import { useEffect, useState, useRef } from "react";
import { Link } from "react-router-dom";
import { fetchNewsData, filterNewsByCompany } from "../utils/news";
import { lookupSymbolFromName } from "../utils/stockUtils";

const generateTitle = (msg) => {
  return msg.length > 30 ? msg.substring(0, 30) + "..." : msg;
};

const SUGGESTED = [
  "Reliance aaj kharidein?",
  "Nifty 50 ka future kya hai?",
  "Mera portfolio analyze karo",
  "TCS prediction batao",
  "IPO mein invest karein?",
  "HDFC Bank news batao"
];

function Aichat() {
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [chats, setChats] = useState(() => {
    const saved = localStorage.getItem("fintrack_chats");
    return saved ? JSON.parse(saved) : [];
  });
  const [activeChatId, setActiveChatId] = useState(null);
  const [sidebarOpen, setSidebarOpen] = useState(window.innerWidth >= 768);
  const messagesEndRef = useRef(null);

  useEffect(() => {
    localStorage.setItem("fintrack_chats", JSON.stringify(chats));
  }, [chats]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleNewChat = () => {
    setActiveChatId(null);
    setMessages([]);
    if (window.innerWidth < 768) setSidebarOpen(false);
  };

  const handleLoadChat = (chatId) => {
    const chat = chats.find((c) => c.id === chatId);
    if (chat) {
      setActiveChatId(chatId);
      setMessages(chat.messages);
      if (window.innerWidth < 768) setSidebarOpen(false);
    }
  };

  const handleDeleteChat = (chatId, e) => {
    e.stopPropagation();
    const updated = chats.filter((c) => c.id !== chatId);
    setChats(updated);
    if (activeChatId === chatId) {
      setActiveChatId(null);
      setMessages([]);
    }
  };

  const addBotMessage = (text) => {
    setMessages((prev) => [...prev, { role: "ai_assistant", content: text }]);
  };

  const triggerMLPrediction = async (userMessage) => {
    try {
      const res = await fetch("https://stock-backend-gsyw.onrender.com/analytics/predict", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({}),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || "Server error");

      const lowerMsg = userMessage.toLowerCase();
      let companyPrediction = null;

      if (Array.isArray(data.prediction)) {
        for (let p of data.prediction) {
          if (p.company && lowerMsg.includes(p.company.toLowerCase().split(".")[0])) {
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



  const callAIChat = async (userMessage, currentMessages) => {
    setLoading(true);
    try {
      // 🚀 1. Local Storage se portfolio ka real data uthao (Jo pehle se synced hai!)
      const portfolioData = JSON.parse(localStorage.getItem("portfolioData") || "[]");
      const userQuery = userMessage.toLowerCase();

      // 🚀 2. Automatic Ticker Identification (E.g., Query mein se company ka naam nikalna)
      const companyMap = {
          "reliance": "RELIANCE",
          "tcs": "TCS",
          "infy": "INFY",
          "infosys": "INFY",
          "airtel": "BHARTIARTL",
          "bharti": "BHARTIARTL",
          "hdfc": "HDFCBANK",
          "icici": "ICICIBANK",
          "sbi": "SBIN",
          "state bank": "SBIN",
          "maruti": "MARUTI",
          "adani": "ADANIENT",
          "bajaj": "BAJFINANCE",
          "lt": "LT",
          "larsen": "LT",
          "coal india": "COALINDIA",
          "hul": "HINDUNILVR",
          "hindustan": "HINDUNILVR"
      };

      let targetCompany = "GLOBAL";
      for (let [keyword, symbol] of Object.entries(companyMap)) {
          if (userQuery.includes(keyword)) {
              targetCompany = symbol;
              break;
          }
      }

      // 🚀 3. Seedha apne Python Backend ke Ecosystem Brain ko hit karo!
      // Hum render wale url par humara naya '/chat' forward karenge aur portfolio sath bhejenge
      const response = await axios.post("https://stock-backend-gsyw.onrender.com/chat", {
        query: userMessage,
        company: targetCompany,
        portfolio: portfolioData // Frontend ka live portfolio backend ko injection ke liye de diya
      });

      if (response.data && response.data.response) {
        addBotMessage(response.data.response);
      } else {
        throw new Error("Invalid terminal matrix response.");
      }

    } catch (err) {
      console.error("TERMINAL ECOSYSTEM CHAT ERROR:", err);
      addBotMessage("⚠️ Terminal Desk Connection Interrupted. Unable to stream institutional data.");
    } finally {
      setLoading(false);
    }
  };

  const handleSend = async (customMsg) => {
    const msg = customMsg || input;
    if (!msg.trim()) return;

    const userMsg = { role: "user", content: msg };
    const updatedMessages = [...messages, userMsg];
    setMessages(updatedMessages);
    setInput("");

    let currentChatId = activeChatId;
    if (!currentChatId) {
      const newChat = {
        id: Date.now().toString(),
        title: generateTitle(msg),
        messages: updatedMessages,
        createdAt: new Date().toISOString(),
      };
      currentChatId = newChat.id;
      setActiveChatId(newChat.id);
      setChats((prev) => [newChat, ...prev]);
    }

    await callAIChat(msg, updatedMessages);

    setMessages((prev) => {
      setChats((prevChats) =>
        prevChats.map((c) =>
          c.id === currentChatId ? { ...c, messages: prev } : c
        )
      );
      return prev;
    });
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter") handleSend();
  };

  return (
    <div className="flex h-[calc(100vh-64px)] bg-gradient-to-br from-black via-gray-900 to-black text-white overflow-hidden">

      <div className={`${sidebarOpen ? "w-32 md:w-64" : "w-0"} transition-all duration-300 overflow-hidden bg-black/40 border-r border-white/10 flex flex-col flex-shrink-0`}>
        <div className="p-4 flex flex-col h-full">
          <button onClick={handleNewChat}
            className="w-full bg-indigo-600 hover:bg-indigo-700 px-4 py-2 rounded-lg text-sm font-medium mb-4">
            + New Chat
          </button>

          <div className="text-xs text-gray-400 mb-2">Recent Chats</div>
          <div className="overflow-y-auto flex-1">
            {chats.map((chat) => (
              <div key={chat.id} onClick={() => handleLoadChat(chat.id)}
                className={`flex items-center justify-between p-2 rounded-lg cursor-pointer mb-1 text-sm hover:bg-white/10 ${activeChatId === chat.id ? "bg-white/20" : ""}`}>
                <span className="truncate flex-1">{chat.title}</span>
                <button onClick={(e) => handleDeleteChat(chat.id, e)}
                  className="text-red-400 hover:text-red-600 ml-2 text-xs">🗑️</button>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="flex flex-col flex-1 overflow-hidden h-full">

        <div className="p-4 flex items-center border-b border-white/5 flex-shrink-0">
          <button onClick={() => setSidebarOpen(!sidebarOpen)} 
            className="text-gray-400 hover:text-white transition font-mono text-lg font-bold px-2 py-0.5 rounded hover:bg-white/5">
            {sidebarOpen ? "<" : ">"}
          </button>
        </div>

        <div className="flex-1 overflow-y-auto px-4 py-3">
          {messages.length === 0 && (
            <div className="flex flex-col items-center justify-center h-full px-4">
              <div className="text-4xl mb-4">📈</div>
              <p className="text-gray-500 mb-6 text-sm text-center">Ask me anything about stocks, portfolio, or market news!</p>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3 w-full max-w-xl">
                {SUGGESTED.map((q, i) => (
                  <button key={i} onClick={() => handleSend(q)}
                    className="text-left px-4 py-3 rounded-xl bg-white/5 border border-white/10 text-sm text-gray-400 hover:text-white hover:border-white/20 transition">
                    {q}
                  </button>
                ))}
              </div>
            </div>
          )}
          {messages.map((msg, idx) => (
            <div key={idx}
              className={`mb-3 px-4 py-3 rounded-xl max-w-[85%] md:max-w-[70%] shadow-md text-sm ${
                msg.role === "user"
                  ? "ml-auto bg-indigo-600 text-white"
                  : "bg-white/10 text-indigo-200"
              }`}>
              {msg.content}
            </div>
          ))}
          <div ref={messagesEndRef} />
          {loading && (
            <div className="text-white/80 ml-2 mt-2 animate-pulse text-sm">
              AI is typing...
            </div>
          )}
        </div>

        <div className="flex items-center px-4 py-3 border-t border-white/10 bg-gray-950/20 flex-shrink-0">
          <input
            type="text"
            placeholder="Ask about stocks, portfolio, news..."
            className="flex-grow px-4 py-2 rounded-l-xl bg-white/10 text-white border border-white/20 focus:outline-none focus:ring-2 focus:ring-indigo-500 placeholder:text-gray-400 text-sm"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
          />
          <button onClick={() => handleSend()}
            className="px-4 md:px-5 py-2 bg-indigo-600 hover:bg-indigo-700 text-white font-semibold rounded-r-xl text-sm">
            Send
          </button>
        </div>
      </div>
    </div>
  );
}

export default Aichat;
