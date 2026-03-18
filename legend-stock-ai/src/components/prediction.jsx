import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';

const COMPANIES = [
  { symbol: 'RELIANCE.NS', name: 'Reliance Industries' },
  { symbol: 'HDFCBANK.NS', name: 'HDFC Bank' },
  { symbol: 'ICICIBANK.NS', name: 'ICICI Bank' },
  { symbol: 'INFY.NS', name: 'Infosys' },
  { symbol: 'TCS.NS', name: 'TCS' },
  { symbol: 'HINDUNILVR.NS', name: 'Hindustan Unilever' },
  { symbol: 'LT.NS', name: 'Larsen & Toubro' },
  { symbol: 'BHARTIARTL.NS', name: 'Bharti Airtel' },
  { symbol: 'ADANIENT.NS', name: 'Adani Enterprises' },
  { symbol: 'ADANIPORTS.NS', name: 'Adani Ports' },
  { symbol: 'TATAMOTORS.NS', name: 'Tata Motors' },
  { symbol: 'MARUTI.NS', name: 'Maruti Suzuki' },
  { symbol: 'BAJFINANCE.NS', name: 'Bajaj Finance' },
  { symbol: 'SBIN.NS', name: 'State Bank of India' },
  { symbol: 'COALINDIA.NS', name: 'Coal India' },
];

function Prediction() {
  const [selectedCompany, setSelectedCompany] = useState('');
  const [predictionResult, setPredictionResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [livePrice, setLivePrice] = useState(null);
  const [livePriceLoading, setLivePriceLoading] = useState(false);

  useEffect(() => {
    if (!selectedCompany) return;
    setLivePrice(null);
    setLivePriceLoading(true);

    const symbol = selectedCompany.replace('.NS', '');
    fetch(`http://localhost:5000/stock?symbol=${symbol}`)
      .then(res => res.json())
      .then(data => { if (data.price) setLivePrice(data); })
      .catch(() => {})
      .finally(() => setLivePriceLoading(false));

    const interval = setInterval(() => {
      fetch(`http://localhost:5000/stock?symbol=${symbol}`)
        .then(res => res.json())
        .then(data => { if (data.price) setLivePrice(data); })
        .catch(() => {});
    }, 60000);

    return () => clearInterval(interval);
  }, [selectedCompany]);

  const handlePrediction = () => {
    if (!selectedCompany) return;
    setLoading(true);
    setPredictionResult(null);
    setError('');

    fetch('http://localhost:5000/predict', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({})
    })
      .then(async res => {
        const data = await res.json();
        if (!res.ok) throw new Error(data.error || 'Server error');
        return data;
      })
      .then(data => {
        if (data?.prediction) {
          const companyData = data.prediction.find(
            c => c.company.toUpperCase().trim() === selectedCompany.toUpperCase().trim()
          );
          if (companyData) setPredictionResult(companyData);
          else setError('Prediction not available for this company.');
        }
      })
      .catch(err => setError(err.message))
      .finally(() => setLoading(false));
  };

  const selectedInfo = COMPANIES.find(c => c.symbol === selectedCompany);
  const priceDiff = predictionResult && livePrice
    ? (predictionResult.predicted_price - livePrice.price).toFixed(2) : null;
  const priceDiffPercent = predictionResult && livePrice
    ? (((predictionResult.predicted_price - livePrice.price) / livePrice.price) * 100).toFixed(2) : null;
  const isUp = parseFloat(priceDiff) >= 0;
  const changeNum = livePrice ? parseFloat(livePrice.percent_change) : 0;

  return (
    <div className="min-h-screen bg-gray-950 text-white">

      {/* Navbar */}
      <div className="border-b border-white/10 px-8 py-4 flex items-center justify-between bg-gray-950/80 backdrop-blur sticky top-0 z-50">
        <div className="text-2xl font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-blue-400 via-cyan-400 to-emerald-400">
          FinTrack
        </div>
        <div className="flex gap-8 text-sm text-gray-400">
          <Link to="/home" className="hover:text-white transition">Home</Link>
          <Link to="/graph" className="hover:text-white transition">Forecast</Link>
          <Link to="/news" className="hover:text-white transition">News</Link>
          <Link to="/portfolio" className="hover:text-white transition">Portfolio</Link>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-6 py-10">

        {/* Page Header */}
        <div className="mb-10">
          <div className="text-xs text-cyan-500 tracking-widest uppercase mb-2">AI Powered</div>
          <h1 className="text-4xl font-bold text-white mb-2">Stock Price Predictor</h1>
          <p className="text-gray-400">LSTM neural network trained on historical NSE data</p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">

          {/* Left — Company List */}
          <div className="lg:col-span-3">
            <div className="bg-gray-900 rounded-2xl border border-white/10 overflow-hidden">
              <div className="px-4 py-3 border-b border-white/10">
                <span className="text-xs text-gray-400 uppercase tracking-widest">Select Company</span>
              </div>
              <div className="p-2 max-h-[500px] overflow-y-auto">
                {COMPANIES.map(company => (
                  <div
                    key={company.symbol}
                    onClick={() => { setSelectedCompany(company.symbol); setPredictionResult(null); setError(''); }}
                    className={`px-4 py-3 rounded-xl cursor-pointer transition-all mb-1 ${
                      selectedCompany === company.symbol
                        ? 'bg-cyan-500/20 border border-cyan-500/50'
                        : 'hover:bg-white/5 border border-transparent'
                    }`}
                  >
                    <div className={`font-semibold text-sm ${selectedCompany === company.symbol ? 'text-cyan-400' : 'text-white'}`}>
                      {company.name}
                    </div>
                    <div className="text-xs text-gray-500 mt-0.5">{company.symbol}</div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Right — Main Content */}
          <div className="lg:col-span-9 space-y-6">

            {/* Live Price Card */}
            <div className="bg-gray-900 rounded-2xl border border-white/10 p-6">
              <div className="text-xs text-gray-400 uppercase tracking-widest mb-4">Live Market Data</div>

              {!selectedCompany && (
                <div className="text-gray-600 text-center py-8">← Select a company to begin</div>
              )}

              {selectedCompany && livePriceLoading && (
                <div className="flex items-center gap-3 py-4">
                  <div className="w-4 h-4 border-2 border-cyan-500 border-t-transparent rounded-full animate-spin"></div>
                  <span className="text-gray-400 text-sm">Fetching live price...</span>
                </div>
              )}

              {selectedCompany && !livePriceLoading && !livePrice && (
                <div className="text-yellow-500 text-sm py-4">
                  ⚠️ Live price unavailable — market may be closed
                </div>
              )}

              {livePrice && (
                <div className="flex flex-wrap gap-8 items-end">
                  <div>
                    <div className="text-gray-400 text-xs mb-1">Company</div>
                    <div className="text-white text-xl font-bold">{selectedInfo?.name}</div>
                    <div className="text-gray-500 text-xs">{selectedCompany}</div>
                  </div>
                  <div>
                    <div className="text-gray-400 text-xs mb-1">Current Price</div>
                    <div className="text-white text-4xl font-bold">₹{livePrice.price}</div>
                  </div>
                  <div>
                    <div className="text-gray-400 text-xs mb-1">Today's Change</div>
                    <div className={`text-2xl font-bold ${changeNum >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                      {changeNum >= 0 ? '▲' : '▼'} {livePrice.percent_change}
                    </div>
                  </div>
                  <div className="flex items-center gap-2 mb-1">
                    <div className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></div>
                    <span className="text-emerald-400 text-xs">NSE Live</span>
                  </div>
                </div>
              )}
            </div>

            {/* Predict Button */}
            <button
              onClick={handlePrediction}
              disabled={!selectedCompany || loading}
              className="w-full py-4 rounded-2xl font-bold text-lg tracking-wide transition-all disabled:opacity-30 disabled:cursor-not-allowed bg-gradient-to-r from-blue-600 via-cyan-600 to-emerald-600 hover:from-blue-500 hover:via-cyan-500 hover:to-emerald-500 shadow-lg shadow-cyan-900/30"
            >
              {loading ? (
                <span className="flex items-center justify-center gap-3">
                  <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                  Running LSTM Model...
                </span>
              ) : '🤖 Run AI Prediction'}
            </button>

            {/* Error */}
            {error && (
              <div className="bg-red-900/30 border border-red-500/50 rounded-2xl p-4 text-red-400 text-sm">
                ⚠️ {error}
              </div>
            )}

            {/* Prediction Result */}
            {predictionResult && (
              <div className="bg-gray-900 rounded-2xl border border-white/10 overflow-hidden">
                <div className="px-6 py-4 border-b border-white/10 flex items-center justify-between">
                  <span className="text-xs text-gray-400 uppercase tracking-widest">AI Prediction Result</span>
                  <span className="text-xs text-gray-600">T+1 Day Forecast</span>
                </div>

                <div className="p-6">
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-6 mb-6">
                    <div className="bg-gray-800/50 rounded-xl p-4">
                      <div className="text-gray-400 text-xs mb-2">Predicted Price</div>
                      <div className="text-white text-2xl font-bold">₹{predictionResult.predicted_price}</div>
                    </div>
                    <div className="bg-gray-800/50 rounded-xl p-4">
                      <div className="text-gray-400 text-xs mb-2">Current Price</div>
                      <div className="text-white text-2xl font-bold">₹{livePrice?.price || '—'}</div>
                    </div>
                    {priceDiff && (
                      <div className="bg-gray-800/50 rounded-xl p-4">
                        <div className="text-gray-400 text-xs mb-2">Expected Move</div>
                        <div className={`text-2xl font-bold ${isUp ? 'text-emerald-400' : 'text-red-400'}`}>
                          {isUp ? '+' : ''}₹{priceDiff}
                        </div>
                      </div>
                    )}
                    {priceDiffPercent && (
                      <div className="bg-gray-800/50 rounded-xl p-4">
                        <div className="text-gray-400 text-xs mb-2">% Move</div>
                        <div className={`text-2xl font-bold ${isUp ? 'text-emerald-400' : 'text-red-400'}`}>
                          {isUp ? '+' : ''}{priceDiffPercent}%
                        </div>
                      </div>
                    )}
                  </div>

                  {/* AI Signal */}
                  <div className={`rounded-xl p-5 border ${isUp ? 'bg-emerald-900/20 border-emerald-500/30' : 'bg-red-900/20 border-red-500/30'}`}>
                    <div className="text-xs text-gray-400 mb-2 uppercase tracking-widest">AI Signal</div>
                    <div className={`text-2xl font-bold mb-1 ${isUp ? 'text-emerald-400' : 'text-red-400'}`}>
                      {isUp ? '📈 BULLISH — Price likely to rise' : '📉 BEARISH — Price may fall'}
                    </div>
                    <div className="text-gray-400 text-sm">
                      {isUp
                        ? 'ML model predicts upward movement. Consider holding or reviewing your position.'
                        : 'ML model predicts downward movement. Review your position carefully.'}
                    </div>
                  </div>

                  <div className="mt-4 text-gray-600 text-xs text-center">
                    ⚠️ For educational purposes only. Not financial advice.
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default Prediction;