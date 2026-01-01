import React, { useState, useEffect } from 'react';
import { Link } from "react-router-dom";

export default function Portfolio() {
  const [portfolio, setPortfolio] = useState(() => {
    const saved = localStorage.getItem("portfolioData");
    return saved ? JSON.parse(saved) : [];
  });

  const [symbol, setSymbol] = useState("");
  const [quantity, setQuantity] = useState("");
  const [buyPrice, setBuyPrice] = useState("");
  const [currentPrice, setCurrentPrice] = useState("");

  useEffect(() => {
    localStorage.setItem("portfolioData", JSON.stringify(portfolio));
  }, [portfolio]);

  const handleAddStock = () => {
    if (!symbol || !quantity || !buyPrice || !currentPrice) return;

    const newEntry = {
      symbol: symbol.toUpperCase(),
      quantity: parseFloat(quantity),
      buyPrice: parseFloat(buyPrice),
      currentPrice: parseFloat(currentPrice),
    };

    setPortfolio([...portfolio, newEntry]);
    setSymbol("");
    setQuantity("");
    setBuyPrice("");
    setCurrentPrice("");
  };

  const calculateProfitLoss = (stock) => {
    const diff = (stock.currentPrice - stock.buyPrice) * stock.quantity;
    return diff.toFixed(2);
  };

  return (
    <div className="bg-black text-white  px-1 min-h-screen">
      <div className="sticky top-0 z-50 backdrop-blur-md bg-black/20 border-b border-white/10 shadow-md">
      <div className="w-full mb-9 px-6 py-4 bg-white/10 flex items-center justify-between">
        {/* Logo */}
        <div className="text-2xl sm:text-3xl  font-extrabold tracking-wide text-transparent bg-clip-text bg-gradient-to-r from-blue-500 via-cyan-400 to-green-400 select-none">
          FinTrack
        </div>

        {/* Nav Links */}
        <div className="space-x-6 text-sm sm:text-base font-medium tracking-wide text-white">
          <Link
            to="/home"
            className="relative group hover:text-cyan-400 transition"
          >
            Home
            <span className="absolute left-0 -bottom-0.5 w-0 h-0.5 bg-cyan-400 transition-all duration-300 group-hover:w-full"></span>
          </Link>
          <Link
            to="/graph"
            className="relative group hover:text-cyan-400 transition"
          >
            Forecast
            <span className="absolute left-0 -bottom-0.5 w-0 h-0.5 bg-cyan-400 transition-all duration-300 group-hover:w-full"></span>
          </Link>

          <Link
            to="/news"
            className="relative group hover:text-cyan-400 transition"
          >
            News
            <span className="absolute left-0 -bottom-0.5 w-0 h-0.5 bg-cyan-400 transition-all duration-300 group-hover:w-full"></span>
          </Link>
          <Link
            to="/portfolio"
            className="relative group hover:text-cyan-400 transition"
          >
            Portfolio
            <span className="absolute left-0 -bottom-0.5 w-0 h-0.5 bg-cyan-400 transition-all duration-300 group-hover:w-full"></span>
          </Link>
        </div>
      </div>
    </div>


      <h2 className="text-3xl font-bold mb-4">📈 Your Stock Portfolio</h2>

      <div className="bg-white/10 p-4 rounded-lg shadow-md mb-6 max-w-md">
        <input
          type="text"
          placeholder="Stock Symbol (e.g. AAPL)"
          value={symbol}
          onChange={(e) => setSymbol(e.target.value)}
          className="mb-2 p-2 rounded w-full text-black"
        />
        <input
          type="number"
          placeholder="Quantity"
          value={quantity}
          onChange={(e) => setQuantity(e.target.value)}
          className="mb-2 p-2 rounded w-full text-black"
        />
        <input
          type="number"
          placeholder="Buy Price"
          value={buyPrice}
          onChange={(e) => setBuyPrice(e.target.value)}
          className="mb-2 p-2 rounded w-full text-black"
        />
        <input
          type="number"
          placeholder="Current Price"
          value={currentPrice}
          onChange={(e) => setCurrentPrice(e.target.value)}
          className="mb-2 p-2 rounded w-full text-black"
        />

        <button
          onClick={handleAddStock}
          className="bg-blue-600 hover:bg-blue-700 px-6 py-2 rounded-md mb-2 mt-4"
        >
          ➕ Add to Portfolio
        </button>
      </div>

      <table className="w-full table-auto text-left border-collapse border border-white/20">
        <thead>
          <tr className="bg-white/10">
            <th className="px-4 py-2">Symbol</th>
            <th className="px-4 py-2">Quantity</th>
            <th className="px-4 py-2">Buy Price</th>
            <th className="px-4 py-2">Current Price</th>
            <th className="px-4 py-2">Profit / Loss</th>
          </tr>
        </thead>
        <tbody>
          {portfolio.map((stock, index) => (
            <tr key={index} className="border-t border-white/10">
              <td className="px-4 py-2">{stock.symbol}</td>
              <td className="px-4 py-2">{stock.quantity}</td>
              <td className="px-4 py-2">${stock.buyPrice}</td>
              <td className="px-4 py-2">${stock.currentPrice}</td>
              <td className={`px-4 py-2 ${calculateProfitLoss(stock) >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                ${calculateProfitLoss(stock)}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
