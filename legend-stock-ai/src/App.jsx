// File: src/App.jsx
import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Myhome from './pages/home';
import Aichat from './pages/aichat'; // Make sure this path and file exist
import Graph from './pages/graph';
import NewsFeed from './pages/news';
import Home from './pages/home';
import Portfolio from './pages/portfolio';



function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Myhome />} />
        <Route path="/aichat" element={<Aichat />} />
        <Route path="/graph" element = {<Graph />} />
        <Route path="/news" element = {<NewsFeed />} />
        <Route path="/home" element = {<Home/>} />
        <Route path="/portfolio" element = {<Portfolio/>} />
       
      </Routes>
    </Router>
  );
}

export default App;
