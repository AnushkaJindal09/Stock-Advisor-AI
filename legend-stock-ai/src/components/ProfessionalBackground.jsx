import React, { useEffect, useRef } from "react";
import "./ProfessionalBackground.css";

const STOCK_TICKERS = [
  "AAPL 192.15 ▲", "GOOG 2812.56 ▼", "NIFTY 50 19890.35 ▲", "TSLA 718.20 ▲", "AMZN 132.18 ▼",
  "INFY 1448.50 ▲", "RELIANCE 2521.65 ▼", "TCS 3625.80 ▲", "META 298.45 ▲", "MSFT 334.67 ▲","ONGC 188.45 ▼", "HCLTECH 1290.15 ▼"
];

export default function ProfessionalBackground() {
  const containerRef = useRef(null);

  useEffect(() => {
  const container = containerRef.current;
  if (!container) return;

  const createFloatingText = () => {
    const text = document.createElement("div");
    const value = STOCK_TICKERS[Math.floor(Math.random() * STOCK_TICKERS.length)];
    text.innerText = value;

    text.className = "stock-text";
    if (value.includes("▲")) text.classList.add("stock-up");
    else if (value.includes("▼")) text.classList.add("stock-down");

    text.style.top = `${Math.random() * 90}%`;
    text.style.left = `${Math.random() * 90}%`;
    text.style.fontSize = `${14 + Math.random() * 10}px`;
    text.style.animationDuration = `${5 + Math.random() * 2}s`;

    container.appendChild(text);

    setTimeout(() => {
      container.removeChild(text);
    }, 8000);
  };

  // Render 10 tickers instantly on load
  for (let i = 0; i < 10; i++) {
    createFloatingText();
  }

  // Then every 200ms continuously add
  const interval = setInterval(() => {
    for (let i = 0; i < 2; i++) {
      createFloatingText();
    }
  }, 200);

  return () => clearInterval(interval);
}, []);

  return <div className="stock-background-canvas" ref={containerRef}></div>;
}
