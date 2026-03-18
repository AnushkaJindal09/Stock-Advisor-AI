// src/utils/stockUtils.js
import axios from "axios";

const FINNHUB_API_KEY = import.meta.env.VITE_FINNHUB_API_KEY;

// 🧹 Clean user input (extract only company name)
function cleanQuery(input) {
  return input
    .toLowerCase()
    .replace(/show me|latest|news|about|the|price|of|stock|tomorrow|today/gi, "")
    .trim();
}
// Indian stocks manual map
const INDIAN_STOCKS_MAP = {
  'reliance': 'RELIANCE',
  'tcs': 'TCS',
  'hdfc': 'HDFCBANK',
  'hdfcbank': 'HDFCBANK',
  'icici': 'ICICIBANK',
  'infosys': 'INFY',
  'infy': 'INFY',
  'bharti': 'BHARTIARTL',
  'airtel': 'BHARTIARTL',
  'adani': 'ADANIENT',
  'sbi': 'SBIN',
  'maruti': 'MARUTI',
  'tata motors': 'TATAMOTORS',
  'bajaj': 'BAJFINANCE',
  'coalindia': 'COALINDIA',
  'lt': 'LT',
  'hindunilvr': 'HINDUNILVR'
};

export const lookupSymbolFromName = async (input) => {
  const cleanInput = cleanQuery(input);
  
  // Pehle Indian map check karo
  for (const [key, value] of Object.entries(INDIAN_STOCKS_MAP)) {
    if (cleanInput.includes(key)) return value;
  }

  // Fallback Finnhub
  try {
    const res = await axios.get("https://finnhub.io/api/v1/search", {
      params: { q: cleanInput, token: FINNHUB_API_KEY },
    });
    const match = res.data.result.find((item) => item.symbol);
    return match?.symbol || null;
  } catch (e) {
    return null;
  }
};

// 2️⃣ Fetch real-time quote
export const fetchStockData = async (symbol) => {
  try {
    const res = await axios.get("https://finnhub.io/api/v1/quote", {
      params: { symbol, token: FINNHUB_API_KEY },
    });
    return res.data;
  } catch (e) {
    console.error("Stock data fetch failed", e);
    return null;
  }
};

// 3️⃣ Fetch news
export const fetchNewsData = async (company) => {
  const cleanInput = cleanQuery(company);
  try {
    const res = await axios.get(`http://localhost:5000/news?company=${cleanInput}`);
    return res.data;
  } catch (e) {
    console.error("News fetch failed", e);
    return { articles: [] };
  }
};
