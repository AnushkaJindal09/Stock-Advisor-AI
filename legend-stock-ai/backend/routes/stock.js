// for giving real time price values to llm (graph part )
const express = require('express');
const axios = require('axios');
const router = express.Router();

const FINNHUB_API_KEY = process.env.FINNHUB_API_KEY;

console.log("FINNHUB_API_KEY is:", FINNHUB_API_KEY);

router.get('/stock/:symbol', async (req, res) => {
  const { symbol } = req.params;
  try {
    const response = await axios.get(
      `https://finnhub.io/api/v1/quote?symbol=${symbol}&token=${FINNHUB_API_KEY}`
    );
    res.json(response.data);
  } catch (err) {
    console.error('Error fetching stock data:', err.message);
    res.status(500).json({ error: 'Failed to fetch stock data' });
  }
});

module.exports = router;
