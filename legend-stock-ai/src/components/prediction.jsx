
import React, { useState } from 'react';


function Prediction() {
  const [selectedCompany, setSelectedCompany] = useState('');
  const [predictionResult, setPredictionResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handlePrediction = () => {
  if (!selectedCompany) {
    alert('Please select a company first');
    return;
  }

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
    if (!res.ok) {
      // Force show backend error if response is 500 or 400
      throw new Error(data.error || 'Server returned an error.');
    }
    return data;
  })
  .then(data => {
    console.log("📦 Received prediction from backend:", data);
    if (data?.prediction) {
      const companyData = data.prediction.find(
        c => c.company.toUpperCase().trim() === selectedCompany.toUpperCase().trim()
      );
      if (companyData) {
        setPredictionResult(companyData);
      } else {
        setError('Prediction not available for the selected company.');
      }
    } else {
      setError('Unexpected response format.');
    }
  })
  .catch(err => {
    console.error('Prediction fetch error:', err);
    setError('⚠️ ' + err.message);
  })
  .finally(() => {
    setLoading(false);
  });
};
  
  return (
    <div className="min-h-[500px] bg-gradient-to-br from-gray-900 via-indigo-800 to-black w-full max-w-4xl text-white p-6 rounded-xl shadow-xl mt-16  mx-auto">
      <h2 className="text-3xl font-bold text-center mb-6 tracking-wide text-indigo-300">
         AI Stock Price Predictor
      </h2>

      <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
        <select
          className="text-black p-3 rounded-lg w-full sm:w-2/3 max-w-md shadow-md focus:outline-none"
          value={selectedCompany}
          onChange={(e) => setSelectedCompany(e.target.value)}
        >
          <option value="">📊 Select a company ...</option>
          {[
            'RELIANCE.NS','HDFCBANK.NS','ICICIBANK.NS','INFY.NS','TCS.NS',
            'HINDUNILVR.NS','LT.NS','BHARTIARTL.NS','ADANIENT.NS','ADANIPORTS.NS',
            'TATAMOTORS.NS','MARUTI.NS','BAJFINANCE.NS','SBIN.NS','COALINDIA.NS'
          ].map(company => (
            <option key={company} value={company}>{company}</option>
          ))}
        </select>

        <button
          onClick={handlePrediction}
          className="bg-indigo-600 hover:bg-indigo-700 transition px-6 py-2 rounded-lg font-semibold shadow-md"
        >
          Predict
        </button>
      </div>

      {loading && (
        <div className="mt-6 text-yellow-400 text-center animate-pulse font-semibold">
          Fetching prediction...
        </div>
      )}

      {error && (
        <div className="mt-6 bg-red-600 text-white p-4 rounded-md text-center font-medium">
          {error}
        </div>
      )}

      {predictionResult && (
        <div className="mt-10 bg-white rounded-xl p-6 shadow-lg text-gray-800 transition-all duration-300 hover:shadow-2xl">
          <h3 className="text-2xl font-bold text-center text-indigo-700 mb-4">📈 Prediction Result</h3>
          <div className="text-lg flex justify-between">
            <span className="font-medium">Company:</span>
            <span>{predictionResult.company}</span>
          </div>
          <div className="text-lg flex justify-between mt-2">
            <span className="font-medium">Predicted Price:</span>
            <span>₹{predictionResult.predicted_price}</span>
          </div>
        </div>
      )}
    </div>
  );
}

export default Prediction;
