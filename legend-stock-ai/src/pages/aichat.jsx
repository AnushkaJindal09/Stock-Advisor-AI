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
  const [menuOpen, setMenuOpen] = useState(false);
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
      const res = await fetch("https://stock-backend-gsyw.onrender.com/predict", {
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
      const portfolioData = JSON.parse(localStorage.getItem("portfolioData") || "[]");
      const userQuery = userMessage.toLowerCase();

      if (userQuery.includes("predict") || userQuery.includes("tomorrow price") || userQuery.includes("forecast")) {
        await triggerMLPrediction(userMessage);
        setLoading(false);
        return;
      }

      let stockText = "";
      const potentialSymbol = await lookupSymbolFromName(userQuery);
      if (potentialSymbol) {
        const symbol = potentialSymbol.replace(".NS", "").replace(".BO", "");
        const stockRes = await fetch(`https://stock-backend-gsyw.onrender.com/stock?symbol=${symbol}`);
        const stockData = await stockRes.json();
        if (stockData && stockData.price) {
          stockText = `📊 Real-time Stock Data for ${potentialSymbol}:\n- Current Price: ₹${stockData.price}\n- Change: ₹${stockData.change} (${stockData.percent_change})`;
        }
      }

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

      const conversationHistory = currentMessages.map((m) => ({
        role: m.role === "user" ? "user" : "assistant",
        content: m.content,
      }));

      const systemPrompt = `You are a professional AI-based financial advisor for Indian stock markets.
${stockText ? stockText : ""}
${portfolioData.length > 0 && userQuery.includes("portfolio") ? `📂 Portfolio: ${JSON.stringify(portfolioData)}` : ""}
${newsSummary ? newsSummary : ""}
Rules:
- Answer naturally like a professional financial advisor
- Use the data provided above when relevant
- If user asks should they sell/buy/hold — give a direct recommendation based on available data`;

      const response = await axios.post(
        "https://openrouter.ai/api/v1/chat/completions",
        {
          model: "mistralai/mixtral-8x7b-instruct",
          messages: [
            { role: "system", content: systemPrompt },
            ...conversationHistory,
            { role: "user", content: userMessage },
          ],
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
    <div className="flex h-screen bg-gradient-to-br from-black via-gray-900 to-black text-white overflow-hidden">

      {/* Sidebar */}
      <div className={`${sidebarOpen ? "w-32 md:w-64" : "w-0"} transition-all duration-300 overflow-hidden bg-black/40 border-r border-white/10 flex flex-col flex-shrink-0`}>
        <div className="p-4 flex flex-col h-full">
          <div className="text-xl font-bold text-cyan-400 mb-4">FinTrack</div>
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

      {/* Main */}
      <div className="flex flex-col flex-1 overflow-hidden">

        {/* Navbar */}
        <div className="sticky top-0 z-50 bg-white/10 border-b border-white/10 flex-shrink-0">
          <div className="px-4 md:px-6 py-4 flex items-center justify-between">
            <div className="flex items-center gap-3">
              {/* Sidebar toggle */}
              <button onClick={() => setSidebarOpen(!sidebarOpen)}
                className="text-gray-400 hover:text-white transition text-sm px-2 py-1 rounded-lg hover:bg-white/10">
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d={sidebarOpen ? "M15 19l-7-7 7-7" : "M9 5l7 7-7 7"} /></svg>
              </button>
              <div className="text-lg md:text-2xl font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-blue-500 via-cyan-400 to-green-400">
                FinTrack AI
              </div>
            </div>

            {/* Desktop nav links */}
            <div className="hidden md:flex space-x-8 text-sm font-medium tracking-wide text-gray-300">
              {[
                { label: "Home", to: "/home" },
                { label: "Forecast", to: "/graph" },
                { label: "News", to: "/news" },
                { label: "Portfolio", to: "/portfolio" },
              ].map((link) => (
                <Link key={link.to} to={link.to} className="relative group hover:text-white transition">
                  {link.label}
                  <span className="absolute left-0 -bottom-0.5 w-0 h-0.5 bg-cyan-400 transition-all duration-300 group-hover:w-full"></span>
                </Link>
              ))}
            </div>

            {/* Mobile hamburger */}
            <button className="md:hidden text-gray-300 hover:text-white" onClick={() => setMenuOpen(!menuOpen)}>
              {menuOpen ? "✕" : "☰"}
            </button>
          </div>

          {/* Mobile dropdown menu */}
          {menuOpen && (
            <div className="md:hidden bg-black/90 border-t border-white/10 px-6 py-4 flex flex-col gap-4">
              {[
                { label: "Home", to: "/home" },
                { label: "Forecast", to: "/graph" },
                { label: "News", to: "/news" },
                { label: "Portfolio", to: "/portfolio" },
              ].map((link) => (
                <Link key={link.to} to={link.to} onClick={() => setMenuOpen(false)}
                  className="text-gray-300 hover:text-white text-sm font-medium transition">
                  {link.label}
                </Link>
              ))}
            </div>
          )}
        </div>

        {/* Messages */}
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

        {/* Input */}
        <div className="flex items-center px-4 py-3 border-t border-white/10 flex-shrink-0">
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
