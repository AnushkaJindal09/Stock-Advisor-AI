import React, { useState } from 'react';
import ProfessionalBackground from "../components/ProfessionalBackground";
import AnimatedGraph from '../components/AnimatedGraph';
import { Link } from 'react-router-dom';

function Home(){
    const [menuOpen, setMenuOpen] = useState(false);

    return(
    <div className="relative text-white min-h-screen">

      {/* Navbar */}
      <div className="sticky top-0 z-50 backdrop-blur-md bg-black/30 border-b border-white/10 shadow-md">
        <div className="w-full px-6 py-4 flex items-center justify-between">
          <div className="text-2xl font-extrabold tracking-wide text-transparent bg-clip-text bg-gradient-to-r from-blue-500 via-cyan-400 to-green-400 select-none">
            FinTrack
          </div>

          {/* Desktop Nav */}
          <div className="hidden md:flex space-x-8 text-sm font-medium tracking-wide text-gray-300">
            {[
              { label: "Home", to: "/home" },
              { label: "Forecast", to: "/graph" },
              { label: "News", to: "/news" },
              { label: "Portfolio", to: "/portfolio" },
            ].map((link) => (
              <Link key={link.to} to={link.to} className="relative group hover:text-white transition">
                {link.label}
                <span className="absolute left-0 -bottom-0.5 w-0 h-0.5 bg-cyan-400 transition-all duration-300 group-hover:w-full"></span>
              </Link>
            ))}
          </div>

          {/* Mobile Hamburger */}
          <button className="md:hidden text-gray-300 hover:text-white" onClick={() => setMenuOpen(!menuOpen)}>
            {menuOpen ? '✕' : '☰'}
          </button>
        </div>

        {/* Mobile Menu */}
        {menuOpen && (
          <div className="md:hidden bg-black/90 border-t border-white/10 px-6 py-4 flex flex-col gap-4">
            {[
              { label: "Home", to: "/home" },
              { label: "Forecast", to: "/graph" },
              { label: "News", to: "/news" },
              { label: "Portfolio", to: "/portfolio" },
            ].map((link) => (
              <Link key={link.to} to={link.to} onClick={() => setMenuOpen(false)}
                className="text-gray-300 hover:text-white text-sm font-medium transition">
                {link.label}
              </Link>
            ))}
          </div>
        )}
      </div>

      {/* Fixed background tickers */}
      <ProfessionalBackground />

      {/* Hero Section */}
      <div className="relative z-10 flex flex-col items-center justify-center min-h-[90vh] px-6 text-center">
        <div className="absolute inset-0 bg-gradient-to-b from-black/50 via-black/20 to-black/60 pointer-events-none"></div>

        <div className="relative z-10 max-w-3xl mx-auto w-full">
          <div className="text-xs tracking-[0.25em] text-cyan-400/80 uppercase mb-5 font-medium">
            Analyse &nbsp;·&nbsp; Predict &nbsp;·&nbsp; Invest Smarter
          </div>
          <h1 className="text-3xl md:text-4xl font-bold text-white mb-4 leading-tight">
            AI-Powered Stock Market Advisor
          </h1>
          <p className="text-gray-400 text-sm max-w-lg mx-auto mb-8 leading-relaxed">
            Real-time market insights, ML-based price predictions, and an AI advisor — built for Indian investors.
          </p>
          <Link to="/aichat">
            <button className="px-8 py-3 rounded-xl font-semibold text-md bg-gradient-to-r from-blue-600 via-cyan-600 to-emerald-600 hover:opacity-90 transition shadow-lg shadow-cyan-500/20">
              Start AI Chat
            </button>
          </Link>

          <div className="mt-10 pointer-events-none w-full">
            <AnimatedGraph />
          </div>
        </div>
      </div>

      {/* Stats Bar */}
      <div className="relative z-10 px-4 md:px-8 mb-16 md:mb-20">
        <div className="backdrop-blur-md bg-white/5 border border-white/10 rounded-2xl px-4 md:px-8 py-6 max-w-3xl mx-auto grid grid-cols-3 divide-x divide-white/10 text-center">
          {[
            { value: "15+", label: "Companies Tracked" },
            { value: "Real-time", label: "Live NSE Prices" },
            { value: "AI + ML", label: "Powered Predictions" },
          ].map((stat, i) => (
            <div key={i} className="px-2 md:px-6">
              <div className="text-lg md:text-2xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 to-emerald-400">{stat.value}</div>
              <div className="text-xs text-gray-500 mt-1 uppercase tracking-widest">{stat.label}</div>
            </div>
          ))}
        </div>
      </div>

      {/* Features Section */}
      <div className="relative z-10 px-4 md:px-8 max-w-5xl mx-auto mb-16 md:mb-24">
        <div className="text-xs text-cyan-500 tracking-widest uppercase text-center mb-3">Features</div>
        <h2 className="text-2xl font-bold text-center text-white mb-2">Everything in one place</h2>
        <p className="text-gray-500 text-sm text-center mb-10">No need to switch between apps — FinTrack has it all</p>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {[
            { icon: "🤖", title: "AI Chat Advisor", desc: "Ask anything about stocks and get direct buy/sell/hold recommendations", link: "/aichat" },
            { icon: "📈", title: "ML Price Forecast", desc: "Machine learning model predicts next-day stock prices", link: "/graph" },
            { icon: "💼", title: "Smart Portfolio", desc: "Track your holdings with real-time P&L and intelligent alerts", link: "/portfolio" },
            { icon: "📰", title: "Market News", desc: "Latest India & global stock market news in real time", link: "/news" },
          ].map((feature, i) => (
            <Link to={feature.link} key={i}>
              <div className="backdrop-blur-md bg-white/5 border border-white/10 rounded-2xl p-4 md:p-6 hover:border-cyan-500/40 hover:bg-white/8 transition-all duration-300 h-full cursor-pointer group">
                <div className="text-2xl md:text-3xl mb-3">{feature.icon}</div>
                <div className="text-white font-semibold text-xs md:text-sm mb-2 group-hover:text-cyan-400 transition">{feature.title}</div>
                <div className="text-gray-500 text-xs leading-relaxed hidden md:block">{feature.desc}</div>
              </div>
            </Link>
          ))}
        </div>
      </div>

      {/* How it works */}
      <div className="relative z-10 px-4 md:px-8 max-w-4xl mx-auto mb-16 md:mb-24">
        <div className="text-xs text-cyan-500 tracking-widest uppercase text-center mb-3">How it works</div>
        <h2 className="text-2xl font-bold text-center text-white mb-2">Three simple steps</h2>
        <p className="text-gray-500 text-sm text-center mb-10">Get started in minutes — no expertise needed</p>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {[
            { step: "01", title: "Build your portfolio", desc: "Add your stocks with buy price, quantity, and target price in seconds" },
            { step: "02", title: "Get AI predictions", desc: "Our ML model predicts tomorrow's price and sends smart buy/sell alerts" },
            { step: "03", title: "Ask the AI advisor", desc: "Chat with FinTrack AI — get direct answers on what to buy, sell, or hold" },
          ].map((item, i) => (
            <div key={i} className="backdrop-blur-md bg-white/5 border border-white/10 rounded-2xl p-6 text-center hover:border-white/20 transition">
              <div className="text-4xl md:text-5xl font-black text-transparent bg-clip-text bg-gradient-to-b from-cyan-400/30 to-transparent mb-4 leading-none">{item.step}</div>
              <div className="text-white font-semibold text-sm mb-3">{item.title}</div>
              <div className="text-gray-500 text-xs leading-relaxed">{item.desc}</div>
            </div>
          ))}
        </div>
      </div>

    </div>
    );
}

export default function Myhome(){
    return( <Home /> );
}
