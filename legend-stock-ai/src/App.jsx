// File: src/App.jsx
import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Home from './pages/home';
import Aichat from './pages/aichat'; 
import Graph from './pages/graph';
import NewsFeed from './pages/news';
import Portfolio from './pages/portfolio';
import Markets from "./pages/markets"; 
import AuthModal from "./components/AuthModal";
import Navbar from "./components/Navbar"; 

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isAuthModalOpen, setIsAuthModalOpen] = useState(false);
  // NEW: Ek loading state jo refresh hone par check poora hone ka wait karegi
  const [loading, setLoading] = useState(true);

  // Check login on load
  useEffect(() => {
    const token = localStorage.getItem("token");
    if (token) {
      setIsAuthenticated(true);
    }
    setLoading(false); // Token check hote hi loading band
  }, []);

  const handleLoginSuccess = () => {
    setIsAuthenticated(true);
    setIsAuthModalOpen(false);
  };

  const handleLogout = () => {
    localStorage.removeItem("token");
    localStorage.removeItem("userEmail");
    localStorage.removeItem("portfolioData");
    setIsAuthenticated(false);
  };

  // PROTECTED ROUTE FIXED: Jab tak loading true hai, tab tak modal nahi khulega
  const ProtectedRoute = ({ element }) => {
    useEffect(() => {
      if (!loading && !isAuthenticated) {
        setIsAuthModalOpen(true);
      }
    }, [loading, isAuthenticated]);

    if (loading) {
      return (
        <div className="flex h-screen w-full bg-black items-center justify-center text-white">
          Loading FinTrack...
        </div>
      );
    }

    return isAuthenticated ? element : <Navigate to="/home" replace />;
  };

  return (
    <Router>
      {/* GLOBAL NAVBAR */}
      <Navbar 
        isLoggedIn={isAuthenticated} 
        onLogout={handleLogout} 
        setIsAuthOpen={setIsAuthModalOpen} 
      />

      <Routes>
        <Route path="/" element={<Home isLoggedIn={isAuthenticated} onLogout={handleLogout} setIsAuthOpen={setIsAuthModalOpen} />} />
        <Route path="/home" element={<Home isLoggedIn={isAuthenticated} onLogout={handleLogout} setIsAuthOpen={setIsAuthModalOpen} />} />
        
        <Route path="/graph" element={<Graph />} />
        <Route path="/news" element={<NewsFeed />} />
        <Route path="/markets" element={<Markets />} />

        {/* Protected Pages */}
        <Route path="/aichat" element={<ProtectedRoute element={<Aichat isAuthenticated={isAuthenticated} setIsAuthenticated={setIsAuthenticated} />} />} />
        <Route path="/portfolio" element={<ProtectedRoute element={<Portfolio />} />} />
      </Routes>

      {/* GLOBAL AUTH MODAL */}
      <AuthModal 
        isOpen={isAuthModalOpen} 
        onClose={() => setIsAuthModalOpen(false)} 
        onLoginSuccess={handleLoginSuccess} 
      />
    </Router>
  );
}

export default App;