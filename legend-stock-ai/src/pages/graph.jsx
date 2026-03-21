import React, { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import Prediction from "../components/prediction";

function Graph() {
  const [companyName, setCompanyName] = useState("");
  const [userSymbol, setUserSymbol] = useState("NASDAQ:AAPL");
  const [menuOpen, setMenuOpen] = useState(false);

  useEffect(() => {
    const script = document.createElement("script");
    script.src = "https://s3.tradingview.com/external-embedding/embed-widget-advanced-chart.js";
    script.type = "text/javascript";
    script.async = true;

    script.text = JSON.stringify({
      symbol: userSymbol,
      interval: "D",
      theme: "dark",
      style: "1",
      locale: "en",
      width: "100%",
      height: "600",
      hide_top_toolbar: false,
      withdateranges: true,
      autosize: false,
    });

    const container = document.getElementById("tradingview-widget");
    container.innerHTML = "";
    container.appendChild(script);
  }, [userSymbol]);

  const handleShow = () => setUserSymbol(companyName.trim());
  const handleKeyDown = (event) => { if (event.key === "Enter") handleShow(); };

  return (
    <div className="min-h-screen bg-gradient-to-br from-black via-gray-900 to-black text-white px-1">

      {/* Navbar */}
      <div className="sticky top-0 z-50 backdrop-blur-md bg-black/20 shadow-md">
        <div className="w-full px-6 py-4 flex items-center justify-between">
          <div className="text-2xl font-extrabold tracking-wide text-transparent bg-clip-text bg-gradient-to-r from-blue-500 via-cyan-400 to-green-400 select-none">
            FinTrack
          </div>

          {/* Desktop Nav */}
          <div className="hidden md:flex space-x-6 text-sm font-medium tracking-wide text-white">
            {[
              { label: "Home", to: "/home" },
              { label: "Forecast", to: "/graph" },
              { label: "News", to: "/news" },
              { label: "Portfolio", to: "/portfolio" },
            ].map((link) => (
              <Link key={link.to} to={link.to} className="relative group hover:text-cyan-400 transition">
                {link.label}
                <span className="absolute left-0 -bottom-0.5 w-0 h-0.5 bg-cyan-400 transition-all duration-300 group-hover:w-full"></span>
              </Link>
            ))}
          </div>

          {/* Mobile Hamburger */}
          <button className="md:hidden text-gray-300 hover:text-white" onClick={() => setMenuOpen(!menuOpen)}>
            {menuOpen ? '✕' : '☰'}
          </button>
        </div>

        {/* Mobile Menu */}
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

      {/* Unified Container */}
      <div className="max-w-8xl mx-auto bg-white/5 backdrop-blur-lg border border-white/10 rounded-3xl p-4 md:p-8 shadow-xl space-y-10">

        {/* Input Area */}
        <div className="text-center space-y-4">
          <h2 className="text-2xl md:text-3xl font-semibold text-indigo-300">📊 Live Stock Chart</h2>
          <p className="text-sm text-gray-400">Enter a company symbol like : <code className="bg-gray-800 text-gray-200 px-2 py-1 rounded">RELIANCE</code> or <code className="bg-gray-800 text-gray-200 px-2 py-1 rounded">AAPL</code></p>

          <div className="flex flex-col sm:flex-row justify-center items-center gap-4 mt-4">
            <input
              type="text"
              placeholder="Enter company symbol..."
              className="text-black px-4 py-2 rounded-md w-full sm:w-2/3 max-w-md shadow-inner focus:outline-none"
              value={companyName}
              onChange={(e) => setCompanyName(e.target.value)}
              onKeyDown={handleKeyDown}
            />
            <button
              className="bg-blue-600 hover:bg-blue-700 px-5 py-2 rounded-md text-white font-medium shadow-md w-full sm:w-auto"
              onClick={handleShow}
            >
              Show Graph
            </button>
          </div>
        </div>

        {/* Graph */}
        <div id="tradingview-widget" className="h-[400px] md:h-[600px] w-full rounded-xl border border-gray-700 shadow-inner bg-black overflow-hidden" />

        {/* Divider */}
        <div className="border-t border-white/10 pt-6">
          <div className="pt-4 text-2xl md:text-3xl font-bold text-purple-300">Predict the future - Before it happens</div>
          <div className="text-md italic mt-2 text-gray-400">Tomorrow's price insights to guide your next move . <code className="text-white/90 font-semibold">INVEST WISELY...</code></div>
          <Prediction />
        </div>
      </div>
    </div>
  );
}

export default Graph;
