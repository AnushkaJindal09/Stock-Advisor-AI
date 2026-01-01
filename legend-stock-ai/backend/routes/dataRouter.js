const express = require('express');
const router = express.Router();

// Dummy route to send graph/news/ml/portfolio data
router.post('/prepare', async (req, res) => {
  const { symbol, portfolio } = req.body;

  // Placeholder response (replace with real APIs)
  const graphData = `📈 Chart data for ${symbol}`;
  const prediction = `🧠 ML model says: HOLD ${symbol}`;
  const news = [`📰 News headline 1 for ${symbol}`, `📰 News headline 2`];
  const portfolioInfo = portfolio || [];

  res.json({
    graphData,
    prediction,
    news,
    portfolioInfo
  });
});

module.exports = router;
