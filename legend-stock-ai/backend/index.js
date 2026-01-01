require('dotenv').config();

const express = require('express');
const cors = require('cors');
const dataRouter = require('./routes/dataRouter');

const app = express();
app.use(cors());
app.use(express.json());

app.use('/api/data', dataRouter);  // Mount our data routes

const PORT = 5050;
app.listen(PORT, () => {
  console.log(`Backend server running on port ${PORT}`);
});

const stockRoutes = require('./routes/stock');
app.use('/api', stockRoutes);
