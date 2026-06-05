import React, { useState, useEffect, useRef } from 'react';
import { Link } from "react-router-dom";

// Register service worker for background notifications
if ('serviceWorker' in navigator) {
  navigator.serviceWorker.register('/sw.js').catch(() => {});
}

export default function Portfolio() {
  const [portfolio, setPortfolio] = useState([]); 
  const [symbol, setSymbol] = useState("");
  const [quantity, setQuantity] = useState("");
  const [buyPrice, setBuyPrice] = useState("");
  const [targetPrice, setTargetPrice] = useState("");
  const [loadingPrice, setLoadingPrice] = useState(false);
  const [alerts, setAlerts] = useState([]);
  const [showChart, setShowChart] = useState(false);
  const [menuOpen, setMenuOpen] = useState(false);
  const portfolioRef = useRef(portfolio);

  // Track last alert state per stock — to avoid repeated alerts for same condition
  const lastAlertState = useRef({});

  // 1. BACKEND SYNC FUNCTION: Tumhare Deployed Render Backend par hi save hoga
  const savePortfolioToBackend = async (updatedPortfolio) => {
    const userEmail = localStorage.getItem("userEmail");
    const token = localStorage.getItem("token");

    if (!userEmail || !token) return; 

    try {
      await fetch('https://stock-backend-gsyw.onrender.com/portfolio/save', {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          email: userEmail,
          holdings: updatedPortfolio
        }),
      });
      console.log("Portfolio synced with render backend!");
    } catch (err) {
      console.error("Backend sync failed:", err);
    }
  };

  // 2. FETCH FROM BACKEND ON LOAD: Tumhare Deployed Render Backend se hi get karega
  useEffect(() => {
    const fetchPortfolioFromBackend = async () => {
      const userEmail = localStorage.getItem("userEmail");
      const token = localStorage.getItem("token");

      if (!userEmail || !token) {
        const saved = localStorage.getItem("portfolioData");
        if (saved) setPortfolio(JSON.parse(saved));
        return;
      }

      try {
        const response = await fetch(`https://stock-backend-gsyw.onrender.com/portfolio/get?email=${userEmail}`, {
          headers: { 'Authorization': `Bearer ${token}` }
        });
        if (response.ok) {
          const data = await response.json();
          if (data && data.holdings) {
            setPortfolio(data.holdings);
            localStorage.setItem("portfolioData", JSON.stringify(data.holdings));
          }
        }
      } catch (err) {
        console.error("Failed to fetch from database, using localStorage fallback:", err);
        const saved = localStorage.getItem("portfolioData");
        if (saved) setPortfolio(JSON.parse(saved));
      }
    };

    fetchPortfolioFromBackend();
    if (Notification.permission === "default") Notification.requestPermission();
  }, []);

  // Update refs and LocalStorage
  useEffect(() => {
    portfolioRef.current = portfolio;
    localStorage.setItem("portfolioData", JSON.stringify(portfolio));
  }, [portfolio]);

  const fetchCurrentPrice = async (sym) => {
    try {
      const clean = sym.toUpperCase().replace('.NS', '').replace('.BO', '');
      const res = await fetch(`https://stock-backend-gsyw.onrender.com/stock?symbol=${clean}`);
      const data = await res.json();
      if (data.price) return { price: data.price, change: data.percent_change };
      return null;
    } catch { return null; }
  };

  const fetchMLPrediction = async (sym) => {
    try {
      const res = await fetch("https://stock-backend-gsyw.onrender.com/analytics/predict", {
        method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({}),
      });
      const data = await res.json();
      if (data?.prediction) {
        const clean = sym.replace('.NS', '').toUpperCase();
        const found = data.prediction.find(p => p.company.replace('.NS', '').toUpperCase() === clean);
        return found ? found.predicted_price : null;
      }
      return null;
    } catch { return null; }
  };

  const fetchNewsSentiment = async (sym) => {
    try {
      const clean = sym.replace('.NS', '').toUpperCase();
      const res = await fetch(`https://stock-backend-gsyw.onrender.com/news?company=${clean}`);
      const data = await res.json();
      if (!data.articles || data.articles.length === 0) return "neutral";
      const headlines = data.articles.map(a => (a.headline || a.summary || "").toLowerCase()).join(" ");
      const negWords = ["fall", "drop", "loss", "down", "decline", "crash", "weak", "sell", "concern", "risk", "cut", "slump"];
      const posWords = ["rise", "gain", "profit", "up", "growth", "strong", "buy", "rally", "surge", "record", "beat"];
      const negScore = negWords.filter(w => headlines.includes(w)).length;
      const posScore = posWords.filter(w => headlines.includes(w)).length;
      if (negScore > posScore) return "negative";
      if (posScore > negScore) return "positive";
      return "neutral";
    } catch { return "neutral"; }
  };

  const sendBrowserNotification = (title, body) => {
    if (Notification.permission === "granted") {
      if (navigator.serviceWorker.controller) {
        navigator.serviceWorker.ready.then(reg => {
          reg.showNotification(title, { body, icon: "/favicon.ico", badge: "/favicon.ico" });
        });
      } else {
        new Notification(title, { body, icon: "/favicon.ico" });
      }
    }
  };

  const checkAlarms = async () => {
    const currentPortfolio = portfolioRef.current;
    if (currentPortfolio.length === 0) return;

    for (const stock of currentPortfolio) {
      const priceData = await fetchCurrentPrice(stock.symbol);
      if (!priceData) continue;

      const { price: currentPrice, change: percentChange } = priceData;
      const changeNum = parseFloat(percentChange);
      const plPercent = ((currentPrice - stock.buyPrice) / stock.buyPrice) * 100;

      const [mlPrediction, newsSentiment] = await Promise.all([
        fetchMLPrediction(stock.symbol),
        fetchNewsSentiment(stock.symbol)
      ]);

      const mlDiff = mlPrediction ? ((mlPrediction - currentPrice) / currentPrice) * 100 : 0;
      const mlDirection = mlDiff > 1.5 ? "up" : mlDiff < -1.5 ? "down" : "neutral";

      let alertType = null;
      let urgency = "medium";
      let reasons = [];
      let action = "";

      // ==========================================================================================
      // 🎯 STAGE 1, 2, & 3: ADVANCED DYNAMIC TARGET ALERTS (100% SEBI COMPLIANT)
      // ==========================================================================================
      if (stock.targetPrice && currentPrice >= stock.targetPrice) {
        urgency = "high";
        reasons = [`🎯 Target ₹${stock.targetPrice} reached!`];

        // Perfect Hit Setup
        if (currentPrice === stock.targetPrice) {
          alertType = "TARGET HIT";
          action = "Target hit ... take action before it's too late";
        } 
        // Price has surged past the target (Stage 2)
        else if (currentPrice > stock.targetPrice) {
          alertType = "VOLATILITY EXPANSION";
          action = `Price has rallied past your target to ₹${currentPrice.toFixed(1)}! Track your gains carefully.`;
          if (mlDirection === "up") {
            reasons.push("ML models indicate continuing upside momentum strength");
          } else if (mlDirection === "down") {
            reasons.push("Warning: Price is higher but ML predicts a potential cooling drop tomorrow");
          }
        }

        // Common descriptive reasons for targets without direct BUY/SELL commands
        if (mlDirection === "down" && currentPrice === stock.targetPrice) {
          reasons.push("ML predicts price drop tomorrow");
          action = "Price hit target but ML predicts immediate drop — review your safety nets";
        } else if (mlDirection === "up" && currentPrice === stock.targetPrice) {
          reasons.push("ML still bullish — further upside baseline support possible");
        }
      }

      // ==========================================================================================
      // 📉 RISK & BREAKOUT ALERTS (CONVERTED TO COMPLIANT MILESTONE ANALYSIS)
      // ==========================================================================================
      else if (plPercent <= -5 && mlDirection === "down") {
        alertType = "RISK ALERT";
        urgency = "high";
        reasons = [`⚠️ ${plPercent.toFixed(1)}% loss from buy price`, "ML predicts further drop tomorrow"];
        action = "Review your risk management safety nets — avoid deeper drawdown limits";
      }

      else if (plPercent >= 3 && mlDirection === "down" && newsSentiment === "negative") {
        alertType = "PRICE ALERT";
        urgency = "high";
        reasons = [`📈 +${plPercent.toFixed(1)}% profit logged`, "ML bearish tomorrow", "Negative news volume observed"];
        action = "3 tracking indicators aligned on pressure — evaluate protection strategies";
      }

      else if (plPercent >= 5 && mlDirection === "down") {
        alertType = "PROFIT MILESTONE";
        urgency = "high";
        reasons = [`💰 +${plPercent.toFixed(1)}% profit achieved`, "ML predicts price adjustment tomorrow"];
        action = "Consider capital tracking strategies before potential market shift";
      }

      else if (changeNum >= 4 && plPercent >= 3) {
        alertType = "VOLATILITY BREAKOUT";
        urgency = "high";
        reasons = [`⚡ Price spiked +${changeNum.toFixed(1)}% today`, `+${plPercent.toFixed(1)}% profit from purchase`];
        action = mlDirection === "down"
          ? "Big intra-day spike observed but ML is turning bearish — track closely"
          : "Big intra-day spike supported by bullish ML projections — trend holding strong";
      }

      else if (changeNum <= -4) {
        alertType = "CRITICAL DIP";
        urgency = "high";
        reasons = [`📉 Price dropped ${changeNum.toFixed(1)}% today`];
        if (mlDirection === "up") {
          alertType = "DIP WITH SUPPORT";
          reasons.push("ML models predict stabilization/recovery tomorrow");
          action = "Sharp drop but technical metrics expect structural bounce — watch closely";
        } else {
          reasons.push("ML also modeling downside continuation — dual indicator pressure");
          action = "Serious macro drop combined with bearish internal algorithms — review position setup";
        }
      }

      else if (plPercent <= -3 && mlDirection === "up" && newsSentiment === "positive") {
        alertType = "SUPPORT ZONE";
        urgency = "medium";
        reasons = [`📊 ${plPercent.toFixed(1)}% current position drawdown`, "ML models predict near-term stabilization", "Positive news dynamic today"];
        action = "Trend monitoring suggest potential structural cushion ahead";
      }

      else if (plPercent <= -8 && mlDirection === "up") {
        alertType = "VALUE DEMAND";
        urgency = "medium";
        reasons = [`🔍 ${plPercent.toFixed(1)}% deep dip from buy reference`, "ML projecting possible technical structural bounce"];
        action = "Mathematical accumulation or position averaging opportunity detected";
      }

      // ==========================================================================================
      // 🔄 IF TARGET HIT WAS ACTIVE BUT PRICE DROPPED BACK BELOW TARGET (Fallback Handling)
      // ==========================================================================================
      // Note: If price slips below target but user was expecting alert, it flows cleanly into standard P&L rules or defaults safely.
      if (!alertType && stock.targetPrice && currentPrice < stock.targetPrice && plPercent < 0) {
        // Safe default tracker to ensure system always catches custom movements smoothly
        alertType = "PRICE RETRACEMENT";
        urgency = "medium";
        reasons = [`📉 Price operating below your hit target of ₹${stock.targetPrice}`];
        action = "Price slipping below your target parameters. Review your safety nets.";
      }

      // ==========================================================================================
      // 🛑 SAFE RE-INJECTION: ALL YOUR ORIGINAL STATE WORKERS & NOTIFICATIONS REMAIN INTACT
      // ==========================================================================================
      if (!alertType) {
        setAlerts(prev => prev.filter(a => a.symbol !== stock.symbol));
        lastAlertState.current[stock.symbol] = null;
        continue; // Loops cleanly without disruption
      }

      const conditionKey = `${alertType}-${Math.round(plPercent)}-${mlDirection}-${newsSentiment}`;
      const lastKey = lastAlertState.current[stock.symbol];

      const alertData = {
        symbol: stock.symbol,
        type: alertType, // Pass descriptive labels like TARGET HIT, RISK ALERT instead of BUY/SELL
        urgency,
        currentPrice,
        plPercent: plPercent.toFixed(1),
        changeNum: changeNum.toFixed(1),
        mlPrediction,
        mlDirection,
        newsSentiment,
        reasons,
        action,
        time: new Date().toLocaleTimeString(),
        conditionKey,
      };

      setAlerts(prev => {
        const exists = prev.find(a => a.symbol === stock.symbol);
        if (exists) return prev.map(a => a.symbol === stock.symbol ? alertData : a);
        return [...prev, alertData];
      });

      if (conditionKey !== lastKey && urgency === "high") {
        lastAlertState.current[stock.symbol] = conditionKey;
        sendBrowserNotification(
          `${alertType} — ${stock.symbol}`, // Safe browser popup layout
          `₹${currentPrice} | ${reasons[0]} → ${action}`
        );
      }
    }
  };

  useEffect(() => {
    const refreshPrices = async () => {
      const current = portfolioRef.current;
      if (current.length === 0) return;
      const updated = await Promise.all(current.map(async (stock) => {
        const data = await fetchCurrentPrice(stock.symbol);
        return data ? { ...stock, currentPrice: data.price } : stock;
      }));
      setPortfolio(updated);
      await checkAlarms();
    };
    refreshPrices();
    const interval = setInterval(refreshPrices, 60000);
    return () => clearInterval(interval);
  }, []);

  const handleAddStock = async () => {
    if (!symbol || !quantity || !buyPrice) return;
    setLoadingPrice(true);
    const data = await fetchCurrentPrice(symbol);
    
    const newStock = {
      symbol: symbol.toUpperCase(),
      quantity: parseFloat(quantity),
      buyPrice: parseFloat(buyPrice),
      targetPrice: targetPrice ? parseFloat(targetPrice) : null,
      currentPrice: data?.price || 0,
      dateAdded: new Date().toLocaleDateString('en-IN'),
    };

    const updatedPortfolio = [...portfolio, newStock];
    setPortfolio(updatedPortfolio);
    savePortfolioToBackend(updatedPortfolio); // Trigger render production API

    setSymbol(""); setQuantity(""); setBuyPrice(""); setTargetPrice("");
    setLoadingPrice(false);
  };

  const handleDelete = (index) => {
    const updatedPortfolio = portfolio.filter((_, i) => i !== index);
    setPortfolio(updatedPortfolio);
    savePortfolioToBackend(updatedPortfolio); // Trigger render production API
  };
  
  const dismissAlert = (sym) => setAlerts(prev => prev.filter(a => a.symbol !== sym));
  const calculatePL = (stock) => ((stock.currentPrice - stock.buyPrice) * stock.quantity).toFixed(2);
  const calculatePLPercent = (stock) => stock.buyPrice > 0 ? (((stock.currentPrice - stock.buyPrice) / stock.buyPrice) * 100).toFixed(2) : 0;

  const totalInvested = portfolio.reduce((sum, s) => sum + s.buyPrice * s.quantity, 0);
  const totalCurrent = portfolio.reduce((sum, s) => sum + s.currentPrice * s.quantity, 0);
  const totalPL = (totalCurrent - totalInvested).toFixed(2);
  const totalPLPercent = totalInvested > 0 ? (((totalCurrent - totalInvested) / totalInvested) * 100).toFixed(2) : 0;

  const alertColors = {
    SELL: { bg: "bg-red-900/20", border: "border-red-500/50", badge: "bg-red-500/20 text-red-400", icon: "🔴" },
    HOLD: { bg: "bg-blue-900/20", border: "border-blue-500/50", badge: "bg-blue-500/20 text-blue-400", icon: "🔵" },
    BUY: { bg: "bg-emerald-900/20", border: "border-emerald-500/50", badge: "bg-emerald-500/20 text-emerald-400", icon: "🟢" },
    WATCH: { bg: "bg-yellow-900/20", border: "border-yellow-500/50", badge: "bg-yellow-500/20 text-yellow-400", icon: "👀" },
  };

  const AllocationChart = () => {
    const maxValue = Math.max(...portfolio.map(s => Math.max(s.buyPrice * s.quantity, s.currentPrice * s.quantity)));
    if (maxValue === 0) return null;
    const chartH = 200, chartW = 900, padL = 50, padR = 20;
    const usableW = chartW - padL - padR;
    const barGroupW = Math.floor(usableW / portfolio.length);
    const barW = Math.min(52, barGroupW * 0.38);
    const gap = 8;
    return (
      <div className="bg-gray-900 rounded-2xl border border-white/10 p-6 mb-6">
        <div className="flex items-center justify-between mb-6">
          <div className="text-xs text-gray-400 uppercase tracking-widest">Invested vs Current Value</div>
          <div className="flex items-center gap-4 text-xs text-gray-400">
            <div className="flex items-center gap-1.5"><div className="w-3 h-3 rounded-sm bg-blue-500"></div><span>Invested</span></div>
            <div className="flex items-center gap-1.5"><div className="w-3 h-3 rounded-sm bg-cyan-500"></div><span>Current</span></div>
          </div>
        </div>
        <div className="w-full overflow-x-auto">
          <svg viewBox={`0 0 ${chartW} ${chartH + 60}`} width="100%" style={{ minWidth: `${portfolio.length * 100}px` }}>
            {[0.25, 0.5, 0.75, 1].map((frac, i) => {
              const y = chartH - frac * chartH;
              const val = frac * maxValue;
              const label = val >= 1000 ? `₹${(val/1000).toFixed(1)}k` : `₹${val.toFixed(0)}`;
              return (
                <g key={i}>
                  <line x1={padL} y1={y} x2={chartW - padR} y2={y} stroke="#ffffff08" strokeWidth="1" strokeDasharray="4 4" />
                  <text x={padL - 6} y={y + 4} textAnchor="end" fill="#4b5563" fontSize="10">{label}</text>
                </g>
              );
            })}
            <line x1={padL} y1={chartH} x2={chartW - padR} y2={chartH} stroke="#ffffff20" strokeWidth="1" />
            {portfolio.map((stock, i) => {
              const invested = stock.buyPrice * stock.quantity;
              const current = stock.currentPrice * stock.quantity;
              const isProfit = current >= invested;
              const investedH = Math.max((invested / maxValue) * chartH, 4);
              const currentH = Math.max((current / maxValue) * chartH, 4);
              const groupX = padL + i * barGroupW + barGroupW / 2;
              const investedX = groupX - barW - gap / 2;
              const currentX = groupX + gap / 2;
              const plPct = (((current - invested) / invested) * 100).toFixed(1);
              const investedLabel = invested >= 1000 ? `₹${(invested/1000).toFixed(1)}k` : `₹${invested.toFixed(0)}`;
              const currentLabel = current >= 1000 ? `₹${(current/1000).toFixed(1)}k` : `₹${current.toFixed(0)}`;
              return (
                <g key={i}>
                  <rect x={investedX} y={chartH - investedH} width={barW} height={investedH} rx="5" fill="#3b82f6" opacity="0.9" />
                  <text x={investedX + barW / 2} y={chartH - investedH - 6} textAnchor="middle" fill="#93c5fd" fontSize="9" fontWeight="500">{investedLabel}</text>
                  <rect x={currentX} y={chartH - currentH} width={barW} height={currentH} rx="5" fill={isProfit ? '#06b6d4' : '#ef4444'} opacity="0.9" />
                  <text x={currentX + barW / 2} y={chartH - currentH - 6} textAnchor="middle" fill={isProfit ? '#67e8f9' : '#fca5a5'} fontSize="9" fontWeight="500">{currentLabel}</text>
                  <text x={groupX} y={chartH + 18} textAnchor="middle" fill="#d1d5db" fontSize="12" fontWeight="600">{stock.symbol}</text>
                  <text x={groupX} y={chartH + 34} textAnchor="middle" fill={isProfit ? '#06b6d4' : '#ef4444'} fontSize="11" fontWeight="700">{isProfit ? '+' : ''}{plPct}%</text>
                </g>
              );
            })}
          </svg>
        </div>
      </div>
    );
  };

  return (
    <div className="min-h-screen bg-gray-950 text-white">
      <div className="max-w-7xl mx-auto px-6 py-10">
        <div className="mb-6 flex flex-wrap items-center justify-between gap-3">
          <div>
            <div className="text-xs text-cyan-500 tracking-widest uppercase mb-2">Real-time Tracking</div>
            <h1 className="text-2xl md:text-4xl font-bold text-white mb-1">Your Portfolio</h1>
            <p className="text-gray-400">Smart alerts powered by AI + ML + News</p>
          </div>
          {portfolio.length > 0 && (
            <button onClick={() => setShowChart(!showChart)} className="px-4 py-2 rounded-xl text-sm border border-white/10 text-gray-400 hover:text-white hover:border-cyan-500/50 transition flex-shrink-0">
              {showChart ? '📊 Hide Chart' : '📊 Show Chart'}
            </button>
          )}
        </div>

        {/* Alerts box */}
        {alerts.length > 0 && (
          <div className="mb-8">
            <div className="text-xs text-yellow-500 tracking-widest uppercase mb-3">🔔 Smart Alerts</div>
            <div className="space-y-3">
              {alerts.map((alert) => {
                const colors = alertColors[alert.type] || alertColors.WATCH;
                return (
                  <div key={alert.symbol} className={`rounded-2xl border p-4 md:p-5 ${colors.bg} ${colors.border}`}>
                    <div className="flex justify-between items-start mb-2">
                      <div className="flex items-center gap-2 flex-wrap flex-1">
                        <span className="text-base">{colors.icon}</span>
                        <span className="font-bold text-white text-sm md:text-base">{alert.symbol}</span>
                        <span className={`px-2 py-0.5 rounded-lg text-xs font-bold ${colors.badge}`}>{alert.type}</span>
                        <span className="text-gray-400 text-xs">₹{alert.currentPrice}</span>
                        <span className={`text-xs font-semibold ${parseFloat(alert.plPercent) >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                          {parseFloat(alert.plPercent) >= 0 ? '+' : ''}{alert.plPercent}% from buy
                        </span>
                      </div>
                      <button onClick={() => dismissAlert(alert.symbol)} className="text-gray-500 hover:text-white ml-4 text-xl flex-shrink-0">✕</button>
                    </div>
                    <div className="flex flex-wrap gap-1.5 mb-2">
                      {alert.reasons.map((r, i) => (
                        <span key={i} className="text-xs bg-white/5 border border-white/10 rounded-lg px-2 py-0.5 text-gray-300">{r}</span>
                      ))}
                    </div>
                    <p className="text-white font-semibold text-xs md:text-sm mb-2">→ {alert.action}</p>
                    <div className="flex flex-wrap gap-3 text-xs text-gray-500">
                      {alert.mlPrediction && <span>ML: ₹{alert.mlPrediction} ({alert.mlDirection})</span>}
                      <span>News: {alert.newsSentiment}</span>
                      <span>{alert.time}</span>
                    </div>
                    <p className="text-xs text-gray-600 mt-2 italic border-t border-white/5 pt-2">For educational purposes only — not financial advice</p>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* Summary Cards */}
        {portfolio.length > 0 && (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
            {[
              { label: "Total Invested", value: `₹${totalInvested.toFixed(0)}`, color: "text-white" },
              { label: "Current Value", value: `₹${totalCurrent.toFixed(0)}`, color: "text-white" },
              { label: "Total P&L", value: `${parseFloat(totalPL) >= 0 ? '+' : ''}₹${totalPL}`, color: parseFloat(totalPL) >= 0 ? "text-emerald-400" : "text-red-400" },
              { label: "Returns", value: `${parseFloat(totalPLPercent) >= 0 ? '+' : ''}${totalPLPercent}%`, color: parseFloat(totalPLPercent) >= 0 ? "text-emerald-400" : "text-red-400" },
            ].map((card, i) => (
              <div key={i} className="bg-gray-900 rounded-2xl border border-white/10 p-5">
                <div className="text-gray-400 text-xs uppercase tracking-widest mb-2">{card.label}</div>
                <div className={`text-2xl font-bold ${card.color}`}>{card.value}</div>
              </div>
            ))}
          </div>
        )}

        {showChart && portfolio.length > 0 && <AllocationChart />}

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          <div className="lg:col-span-3">
            <div className="bg-gray-900 rounded-2xl border border-white/10 p-6">
              <div className="text-xs text-gray-400 uppercase tracking-widest mb-5">Add Stock</div>
              <div className="space-y-3">
                {[
                  { label: "Symbol", placeholder: "e.g. RELIANCE", value: symbol, onChange: setSymbol, type: "text" },
                  { label: "Quantity", placeholder: "e.g. 10", value: quantity, onChange: setQuantity, type: "number" },
                  { label: "Buy Price (₹)", placeholder: "e.g. 1400", value: buyPrice, onChange: setBuyPrice, type: "number" },
                  { label: "Target Price (₹) — Optional", placeholder: "e.g. 1600", value: targetPrice, onChange: setTargetPrice, type: "number" },
                ].map((field, i) => (
                  <div key={i}>
                    <label className="text-xs text-gray-500 mb-1 block">{field.label}</label>
                    <input
                      type={field.type}
                      placeholder={field.placeholder}
                      value={field.value}
                      onChange={(e) => field.onChange(e.target.value)}
                      className="w-full bg-gray-800 border border-white/10 rounded-xl px-4 py-3 text-white text-sm placeholder-gray-600 focus:outline-none focus:border-cyan-500/50"
                    />
                  </div>
                ))}
                <button
                  onClick={handleAddStock}
                  disabled={loadingPrice}
                  className="w-full py-3 rounded-xl font-semibold text-sm transition-all bg-gradient-to-r from-blue-600 via-cyan-600 to-emerald-600 hover:opacity-90 disabled:opacity-40 mt-2"
                >
                  {loadingPrice ? (
                    <span className="flex items-center justify-center gap-2">
                      <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                      Fetching...
                    </span>
                  ) : '+ Add to Portfolio'}
                </button>
              </div>
            </div>
          </div>

          <div className="lg:col-span-9">
            <div className="bg-gray-900 rounded-2xl border border-white/10 overflow-hidden">
              <div className="px-6 py-4 border-b border-white/10 flex items-center justify-between">
                <span className="text-xs text-gray-400 uppercase tracking-widest">Holdings</span>
                <span className="text-xs text-gray-600">{portfolio.length} stocks</span>
              </div>
              {portfolio.length === 0 ? (
                <div className="text-center py-20 text-gray-600">
                  <div className="text-4xl mb-3">📊</div>
                  <p>No stocks added yet</p>
                  <p className="text-xs mt-1">Add your first stock to get started</p>
                </div>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead>
                      <tr className="border-b border-white/5">
                        {["Symbol", "Qty", "Buy Price", "Current", "Progress", "P&L", "Returns", "Target", "Added", ""].map((h, i) => (
                          <th key={i} className="px-4 py-4 text-left text-xs text-gray-500 uppercase tracking-widest whitespace-nowrap">{h}</th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {portfolio.map((stock, index) => {
                        const pl = calculatePL(stock);
                        const plPercent = calculatePLPercent(stock);
                        const isProfit = parseFloat(pl) >= 0;
                        const progressPercent = Math.min(Math.max(((stock.currentPrice - stock.buyPrice) / stock.buyPrice) * 100 + 50, 0), 100);
                        const targetReached = stock.targetPrice && stock.currentPrice >= stock.targetPrice;
                        const stockAlert = alerts.find(a => a.symbol === stock.symbol);
                        return (
                          <tr key={index} className={`border-b border-white/5 hover:bg-white/5 transition ${isProfit ? 'shadow-[inset_3px_0_0_#10b981]' : 'shadow-[inset_3px_0_0_#ef4444]'}`}>
                            <td className="px-4 py-4">
                              <div className="font-semibold text-white flex items-center gap-2">
                                {stock.symbol}
                                {stockAlert && (
                                  <span className={`text-xs px-1.5 py-0.5 rounded-md font-bold ${alertColors[stockAlert.type]?.badge}`}>
                                    {alertColors[stockAlert.type]?.icon}
                                  </span>
                                )}
                              </div>
                              <div className="text-xs text-gray-500">NSE</div>
                            </td>
                            <td className="px-4 py-4 text-gray-300 text-sm">{stock.quantity}</td>
                            <td className="px-4 py-4 text-gray-300 text-sm">₹{stock.buyPrice}</td>
                            <td className="px-4 py-4 text-white font-medium text-sm">₹{stock.currentPrice}</td>
                            <td className="px-4 py-4">
                              <div className="w-24">
                                <div className="h-1.5 bg-gray-700 rounded-full overflow-hidden">
                                  <div className={`h-full rounded-full transition-all duration-500 ${isProfit ? 'bg-emerald-400' : 'bg-red-400'}`} style={{ width: `${progressPercent}%` }}></div>
                                </div>
                                <div className="text-xs text-gray-600 mt-1">{isProfit ? '+' : ''}{plPercent}%</div>
                              </div>
                            </td>
                            <td className={`px-4 py-4 font-semibold text-sm ${isProfit ? 'text-emerald-400' : 'text-red-400'}`}>{isProfit ? '+' : ''}₹{pl}</td>
                            <td className={`px-4 py-4 text-sm ${isProfit ? 'text-emerald-400' : 'text-red-400'}`}>{isProfit ? '+' : ''}{plPercent}%</td>
                            <td className="px-4 py-4 text-sm">
                              {stock.targetPrice ? (
                                <span className={`px-2 py-1 rounded-lg text-xs ${targetReached ? 'bg-emerald-900/50 text-emerald-400' : 'bg-gray-800 text-gray-400'}`}>
                                  {targetReached ? '🎯 Hit!' : `₹${stock.targetPrice}`}
                                </span>
                              ) : <span className="text-gray-700 text-xs">—</span>}
                            </td>
                            <td className="px-4 py-4 text-xs text-gray-600 whitespace-nowrap">{stock.dateAdded || '—'}</td>
                            <td className="px-4 py-4">
                              <button onClick={() => handleDelete(index)} className="text-gray-600 hover:text-red-400 transition px-2 py-1 rounded-lg hover:bg-red-900/20">🗑️</button>
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}