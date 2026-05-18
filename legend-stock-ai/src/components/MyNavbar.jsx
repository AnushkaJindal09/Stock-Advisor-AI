// File: src/components/MyNavbar.jsx
import React from 'react';
import { Link } from 'react-router-dom';

export default function MyNavbar({ isAuthenticated, onLogout, onAuthRequired }) {
  return (
    <div className="w-full flex justify-between items-center p-6 bg-transparent text-white z-50 relative">
      {/* Left side Brand Logo */}
      <Link to="/" className="text-2xl font-bold tracking-wider text-cyan-400 font-sans">
        FinTrack
      </Link>
      
      {/* Center & Right Tabs */}
      <div className="flex items-center gap-6 text-sm font-medium">
        <Link to="/home" className="text-gray-400 hover:text-white transition">Home</Link>
        <Link to="/markets" className="text-gray-400 hover:text-white transition">Markets</Link>
        <Link to="/graph" className="text-gray-400 hover:text-white transition">Forecast</Link>
        <Link to="/news" className="text-gray-400 hover:text-white transition">News</Link>
        <Link to="/portfolio" className="text-gray-400 hover:text-white transition">Portfolio</Link>

        {/* Login / Logout dynamically toggled */}
        {isAuthenticated ? (
          <button 
            onClick={onLogout}
            className="bg-red-500/10 border border-red-500/30 text-red-400 px-4 py-1.5 rounded-xl hover:bg-red-500/20 transition text-xs font-bold uppercase tracking-wider"
          >
            Logout
          </button>
        ) : (
          <button 
            onClick={onAuthRequired}
            className="bg-gradient-to-r from-blue-600 to-cyan-600 text-white px-5 py-1.5 rounded-xl font-medium text-sm shadow-lg shadow-cyan-500/20 hover:opacity-90 transition"
          >
            Login
          </button>
        )}
      </div>
    </div>
  );
}