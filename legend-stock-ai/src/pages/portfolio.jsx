import React, { useState, useEffect, useRef } from 'react';
import { Link } from "react-router-dom";

export default function Portfolio() {
  const [portfolio, setPortfolio] = useState(() => {
    const saved = localStorage.getItem("portfolioData");
    return saved ? JSON.parse(saved) : [];
  });
  const [symbol, setSymbol] = useState("");
  const [quantity, setQuantity] = useState("");
  const [buyPrice, setBuyPrice] = useState("");
  const [targetPrice, setTargetPrice] = useState("");
  const [loadingPrice, setLoadingPrice] = useState(false);
  const [alerts, setAlerts] = useState([]);
  const [showChart, setShowChart] = useState(false);
  const portfolioRef = useRef(portfolio);

  useEffect(() => {
    portfolioRef.current = portfolio;
    localStorage.setItem("portfolioData", JSON.stringify(portfolio));
  }, [portfolio]);

  useEffect(() => {
    if (Notification.permission === "default") Notification.requestPermission();
  }, []);

  const fetchCurrentPrice = async (sym) => {
    try {
      const clean = sym.toUpperCase().replace('.NS', '').replace('.BO', '');
      const res = await fetch(`http://localhost:5000/stock?symbol=${clean}`);
      const data = await res.json();
      if (data.price) return { price: data.price, change: data.percent_change };
      return null;
    } catch { return null; }
  };

  const fetchMLPrediction = async (sym) => {
    try {
      const res = await fetch("http://localhost:5000/predict", {
        method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({}),
      });
      const data = await res.json();
      if (data?.prediction) {
        const found = data.prediction.find(p => p.company.replace('.NS', '').toUpperCase() === sym.toUpperCase());
        return found ? found.predicted_price : null;
      }
      return null;
    } catch { return null; }
  };

  const checkAlarms = async () => {
    const currentPortfolio = portfolioRef.current;
    if (currentPortfolio.length === 0) return;
    for (const stock of currentPortfolio) {
      const priceData = await fetchCurrentPrice(stock.symbol);
      if (!priceData) continue;
      const { price: currentPrice, change: percentChange } = priceData;
      const mlPrediction = await fetchMLPrediction(stock.symbol);
      let signals = 0, reasons = [], action = "";
      const changeNum = parseFloat(percentChange);
      if (Math.abs(changeNum) >= 2) { signals++; reasons.push(changeNum < 0 ? `Price ${changeNum}% gira` : `Price ${changeNum}% badha`); }
      const plPercent = ((currentPrice - stock.buyPrice) / stock.buyPrice) * 100;
      if (plPercent <= -3) { signals++; reasons.push(`Buy price se ${plPercent.toFixed(1)}% neeche`); }
      else if (plPercent >= 5) { signals++; reasons.push(`Buy price se +${plPercent.toFixed(1)}% upar`); }
      if (mlPrediction) {
        const mlDiff = ((mlPrediction - currentPrice) / currentPrice) * 100;
        if (mlDiff < -1.5) { signals++; reasons.push(`ML: kal giregi`); }
        else if (mlDiff > 1.5) { signals++; reasons.push(`ML: kal badhegi`); }
      }
      if (stock.targetPrice && currentPrice >= stock.targetPrice) {
        signals++;
        reasons.push(`🎯 Target ₹${stock.targetPrice} reach ho gaya!`);
        if (Notification.permission === "granted") {
          new Notification(`🎯 Target Hit — ${stock.symbol}!`, {
            body: `${stock.symbol} ne aapka target price ₹${stock.targetPrice} reach kar liya!`,
            icon: "/favicon.ico"
          });
        }
      }
      if (signals === 0) continue;
      if (plPercent >= 5 && mlPrediction && mlPrediction < currentPrice) action = "🟢 SELL KAR — Munafa + ML girne ka signal!";
      else if (plPercent >= 5 && mlPrediction && mlPrediction > currentPrice) action = "🔵 HOLD KAR — Munafa + ML badhne ka signal!";
      else if (plPercent <= -3 && mlPrediction && mlPrediction < currentPrice) action = "🔴 SELL KAR — Loss + ML aur girne ka signal!";
      else if (plPercent <= -3 && mlPrediction && mlPrediction > currentPrice) action = "🟡 HOLD KAR — Loss hai lekin ML recovery predict kar raha hai";
      else if (signals >= 2) action = "🟡 DHYAN DO — Market volatile hai!";
      else action = "👀 Watch karo";
      const alertMsg = `${stock.symbol}: ${reasons.join(" | ")} → ${action}`;
      setAlerts(prev => {
        const exists = prev.find(a => a.symbol === stock.symbol);
        if (exists) return prev.map(a => a.symbol === stock.symbol ? { ...a, message: alertMsg, time: new Date().toLocaleTimeString() } : a);
        return [...prev, { symbol: stock.symbol, message: alertMsg, time: new Date().toLocaleTimeString(), signals }];
      });
      if (signals >= 2 && Notification.permission === "granted") {
        new Notification(`FinTrack Alert — ${stock.symbol}`, { body: alertMsg, icon: "/favicon.ico" });
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
    setPortfolio(prev => [...prev, {
      symbol: symbol.toUpperCase(),
      quantity: parseFloat(quantity),
      buyPrice: parseFloat(buyPrice),
      targetPrice: targetPrice ? parseFloat(targetPrice) : null,
      currentPrice: data?.price || 0,
      dateAdded: new Date().toLocaleDateString('en-IN'),
    }]);
    setSymbol(""); setQuantity(""); setBuyPrice(""); setTargetPrice("");
    setLoadingPrice(false);
  };

  const handleDelete = (index) => setPortfolio(prev => prev.filter((_, i) => i !== index));
  const dismissAlert = (sym) => setAlerts(prev => prev.filter(a => a.symbol !== sym));
  const calculatePL = (stock) => ((stock.currentPrice - stock.buyPrice) * stock.quantity).toFixed(2);
  const calculatePLPercent = (stock) => stock.buyPrice > 0 ? (((stock.currentPrice - stock.buyPrice) / stock.buyPrice) * 100).toFixed(2) : 0;

  const totalInvested = portfolio.reduce((sum, s) => sum + s.buyPrice * s.quantity, 0);
  const totalCurrent = portfolio.reduce((sum, s) => sum + s.currentPrice * s.quantity, 0);
  const totalPL = (totalCurrent - totalInvested).toFixed(2);
  const totalPLPercent = totalInvested > 0 ? (((totalCurrent - totalInvested) / totalInvested) * 100).toFixed(2) : 0;

  const CHART_HEIGHT = 160;

const AllocationChart = () => {
    const [tooltip, setTooltip] = useState(null);
    const maxValue = Math.max(...portfolio.map(s => Math.max(s.buyPrice * s.quantity, s.currentPrice * s.quantity)));
    if (maxValue === 0) return null;

    const chartH = 200;
    const chartW = 900;
    const padL = 50;
    const padR = 20;
    const usableW = chartW - padL - padR;
    const barGroupW = Math.floor(usableW / portfolio.length);
    const barW = Math.min(52, barGroupW * 0.38);
    const gap = 8;

    return (
      <div className="bg-gray-900 rounded-2xl border border-white/10 p-6 mb-6">
        <div className="flex items-center justify-between mb-6">
          <div className="text-xs text-gray-400 uppercase tracking-widest">Invested vs Current Value</div>
          <div className="flex items-center gap-4 text-xs text-gray-400">
            <div className="flex items-center gap-1.5">
              <div className="w-3 h-3 rounded-sm" style={{ backgroundColor: '#3b82f6' }}></div>
              <span>Invested</span>
            </div>
            <div className="flex items-center gap-1.5">
              <div className="w-3 h-3 rounded-sm" style={{ backgroundColor: '#06b6d4' }}></div>
              <span>Current Value</span>
            </div>
          </div>
        </div>

        <div className="w-full overflow-x-auto">
          <svg viewBox={`0 0 ${chartW} ${chartH + 60}`} width="100%" style={{ minWidth: `${portfolio.length * 100}px` }}>

            {/* Y axis grid lines with labels */}
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

            {/* Baseline */}
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

              // Value labels above bars
              const investedLabel = invested >= 1000 ? `₹${(invested/1000).toFixed(1)}k` : `₹${invested.toFixed(0)}`;
              const currentLabel = current >= 1000 ? `₹${(current/1000).toFixed(1)}k` : `₹${current.toFixed(0)}`;

              return (
                <g key={i}>
                  {/* Invested bar */}
                  <rect
                    x={investedX} y={chartH - investedH}
                    width={barW} height={investedH}
                    rx="5" fill="#3b82f6" opacity="0.9"
                  />
                  {/* Value label above invested bar */}
                  <text x={investedX + barW / 2} y={chartH - investedH - 6}
                    textAnchor="middle" fill="#93c5fd" fontSize="9" fontWeight="500">
                    {investedLabel}
                  </text>

                  {/* Current bar */}
                  <rect
                    x={currentX} y={chartH - currentH}
                    width={barW} height={currentH}
                    rx="5" fill={isProfit ? '#06b6d4' : '#ef4444'} opacity="0.9"
                  />
                  {/* Value label above current bar */}
                  <text x={currentX + barW / 2} y={chartH - currentH - 6}
                    textAnchor="middle" fill={isProfit ? '#67e8f9' : '#fca5a5'} fontSize="9" fontWeight="500">
                    {currentLabel}
                  </text>

                  {/* Stock symbol */}
                  <text x={groupX} y={chartH + 18} textAnchor="middle" fill="#d1d5db" fontSize="12" fontWeight="600">
                    {stock.symbol}
                  </text>
                  {/* P&L % */}
                  <text x={groupX} y={chartH + 34} textAnchor="middle"
                    fill={isProfit ? '#06b6d4' : '#ef4444'} fontSize="11" fontWeight="700">
                    {isProfit ? '+' : ''}{plPct}%
                  </text>
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
      <div className="border-b border-white/10 px-8 py-4 flex items-center justify-between bg-gray-950/80 backdrop-blur sticky top-0 z-50">
        <div className="text-2xl font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-blue-400 via-cyan-400 to-emerald-400">FinTrack</div>
        <div className="flex gap-8 text-sm text-gray-400">
          <Link to="/home" className="hover:text-white transition">Home</Link>
          <Link to="/graph" className="hover:text-white transition">Forecast</Link>
          <Link to="/news" className="hover:text-white transition">News</Link>
          <Link to="/portfolio" className="text-white font-semibold">Portfolio</Link>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-6 py-10">
        <div className="mb-8 flex items-end justify-between">
          <div>
            <div className="text-xs text-cyan-500 tracking-widest uppercase mb-2">Real-time Tracking</div>
            <h1 className="text-4xl font-bold text-white mb-2">Your Portfolio</h1>
            <p className="text-gray-400">Smart alerts powered by AI + ML predictions</p>
          </div>
          {portfolio.length > 0 && (
            <button
              onClick={() => setShowChart(!showChart)}
              className="px-4 py-2 rounded-xl text-sm border border-white/10 text-gray-400 hover:text-white hover:border-cyan-500/50 transition"
            >
              {showChart ? '📊 Hide Chart' : '📊 Show Chart'}
            </button>
          )}
        </div>

        {alerts.length > 0 && (
          <div className="mb-8">
            <div className="text-xs text-yellow-500 tracking-widest uppercase mb-3">🔔 Smart Alerts</div>
            <div className="space-y-3">
              {alerts.map((alert) => (
                <div key={alert.symbol} className={`rounded-2xl border p-4 flex justify-between items-start ${alert.signals >= 2 ? "bg-red-900/20 border-red-500/50" : "bg-yellow-900/20 border-yellow-500/50"}`}>
                  <div>
                    <p className="text-white font-medium text-sm">{alert.message}</p>
                    <p className="text-xs text-gray-500 mt-1">{alert.time}</p>
                  </div>
                  <button onClick={() => dismissAlert(alert.symbol)} className="text-gray-500 hover:text-white ml-4 text-lg">✕</button>
                </div>
              ))}
            </div>
          </div>
        )}

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
                        return (
                          <tr key={index} className={`border-b border-white/5 hover:bg-white/5 transition ${isProfit ? 'shadow-[inset_3px_0_0_#10b981]' : 'shadow-[inset_3px_0_0_#ef4444]'}`}>
                            <td className="px-4 py-4">
                              <div className="font-semibold text-white">{stock.symbol}</div>
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
