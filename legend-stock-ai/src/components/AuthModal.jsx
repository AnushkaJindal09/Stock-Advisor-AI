/*import React, { useState } from 'react';
import { X, ShieldCheck, ArrowRight } from 'lucide-react';
const BACKEND = "http://localhost:5000";

const AuthModal = ({ isOpen, onClose, onLoginSuccess }) => {
  const [isLogin, setIsLogin] = useState(true);
  const [formData, setFormData] = useState({ email: '', password: '', name: '' });
  const [errorMessage, setErrorMessage] = useState('');

  if (!isOpen) return null;

  const handleSubmit = async (e) => {
    e.preventDefault();
    setErrorMessage('');
    const endpoint = isLogin ? '/auth/login' : '/auth/register';
    
    try {
      const response = await fetch(`${BACKEND}${endpoint}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData),
      });
      const data = await response.json();

      if (response.ok) {
        localStorage.setItem('token', data.token);
        localStorage.setItem('userEmail', formData.email);
        onLoginSuccess(); 
        onClose(); 
      } else {
        setErrorMessage(data.error || "Authentication failed. Please check your credentials.");
      }
    } catch (err) {
      setErrorMessage("Database handshake error. Please check your network or server.");
      console.error("Auth Error:", err);
    }
  };

  return (
    <div className="fixed inset-0 bg-[#060813] flex items-center justify-center z-[99999] p-4 overflow-hidden select-none font-sans">
      
      <div className="absolute inset-0 opacity-50 pointer-events-none flex items-center justify-center lg:p-10">
        <svg className="w-full h-full text-cyan-500/30" viewBox="0 0 1200 600" fill="none" xmlns="http://www.w3.org/2000/svg">
        <path 
            d="M0 480 Q100 460 200 380 T400 320 T600 240 T800 260 T1000 140 T1200 90" 
            stroke="#06D3E1" 
            strokeWidth="3" 
            strokeLinecap="round" 
            strokeLinejoin="round"
        />
        
        <path 
            d="M0 510 C150 490 250 420 400 380 C550 340 650 310 800 290 C950 270 1050 180 1200 130" 
            stroke="rgba(59, 130, 246, 0.4)" 
            strokeWidth="2" 
            strokeLinecap="round"
        />

        <line x1="0" y1="140" x2="1200" y2="140" stroke="rgba(6, 211, 225, 0.15)" strokeWidth="1" strokeDasharray="4 4" />
        <line x1="0" y1="320" x2="1200" y2="320" stroke="rgba(255, 255, 255, 0.05)" strokeWidth="1" strokeDasharray="4 4" />
        <line x1="0" y1="480" x2="1200" y2="480" stroke="rgba(239, 68, 68, 0.15)" strokeWidth="1" strokeDasharray="4 4" />

        <g fill="rgba(255, 255, 255, 0.03)">
            <rect x="50" y="520" width="15" height="80" rx="2" />
            <rect x="100" y="480" width="15" height="120" rx="2" fill="rgba(6, 211, 225, 0.08)" />
            <rect x="150" y="540" width="15" height="60" rx="2" />
            <rect x="200" y="500" width="15" height="100" rx="2" />
            <rect x="250" y="460" width="15" height="140" rx="2" fill="rgba(6, 211, 225, 0.08)" />
            <rect x="300" y="510" width="15" height="90" rx="2" />
            <rect x="650" y="440" width="15" height="160" rx="2" fill="rgba(6, 211, 225, 0.08)" />
            <rect x="700" y="490" width="15" height="110" rx="2" />
            <rect x="750" y="530" width="15" height="70" rx="2" />
            <rect x="1000" y="420" width="15" height="180" rx="2" fill="rgba(6, 211, 225, 0.08)" />
            <rect x="1050" y="450" width="15" height="150" rx="2" />
            <rect x="1100" y="500" width="15" height="100" rx="2" />
        </g>

]        <circle cx="1000" cy="140" r="5" fill="#06D3E1" className="animate-ping" />
        <circle cx="1000" cy="140" r="3.5" fill="#06D3E1" />

        <path d="M0 100 H1200 M0 200 H1200 M0 300 H1200 M0 400 H1200 M0 500 H1200" stroke="rgba(255,255,255,0.015)" strokeWidth="1"/>
        <path d="M150 0 V600 M300 0 V600 M450 0 V600 M600 0 V600 M750 0 V600 M900 0 V600 M1050 0 V600" stroke="rgba(255,255,255,0.015)" strokeWidth="1"/>
        </svg>
      </div>

      <div className="absolute w-[500px] h-[500px] bg-cyan-500/10 rounded-full blur-[150px] pointer-events-none -top-20 -left-20" />
      <div className="absolute w-[500px] h-[500px] bg-blue-600/5 rounded-full blur-[180px] pointer-events-none -bottom-20 -right-20" />

      <div className="relative w-full max-w-md bg-[#09101C] border border-white p-8 rounded-2xl shadow-[0_30px_70px_rgba(0,0,0,0.8)] z-10">
        
\        <button onClick={onClose} className="absolute top-5 right-5 text-slate-400 hover:text-white bg-slate-800/40 hover:bg-slate-800/80 p-1.5 rounded-xl transition">
          <X size={16} />
        </button>

\        <div className="flex items-center justify-center gap-1.5 mb-5 text-cyan-400 text-[11px] font-semibold uppercase tracking-widest bg-cyan-500/10 w-fit mx-auto px-3 py-1 rounded-full border border-cyan-500/20">
          <ShieldCheck size={14} /> Secure Verification
        </div>

        <h2 className="text-2xl font-bold text-white mb-1.5 text-center tracking-tight">
          {isLogin ? "Welcome Back" : "Create Account"}
        </h2>
        <p className="text-slate-400 text-xs text-center mb-6">
          {isLogin ? "Log in to view your synced portfolio." : "Your data is private. Keep your holdings safe."}
        </p>

        {errorMessage && (
          <div className="bg-red-500/10 border border-red-500/20 text-red-400 p-3 rounded-xl text-xs mb-4 text-center font-medium">
            {errorMessage}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          {!isLogin && (
            <input 
              type="text" placeholder="Your Name" required
              className="w-full bg-[#151C2C] border border-slate-800 p-3.5 rounded-xl text-sm text-white placeholder-slate-500 focus:outline-none focus:border-cyan-500/50 transition"
              onChange={(e) => setFormData({...formData, name: e.target.value})}
            />
          )}
          <input 
            type="email" placeholder="Email Address" required
            className="w-full bg-[#151C2C] border border-slate-800 p-3.5 rounded-xl text-sm text-white placeholder-slate-500 focus:outline-none focus:border-cyan-500/50 transition"
            onChange={(e) => setFormData({...formData, email: e.target.value})}
          />
          <input 
            type="password" placeholder="Password" required
            className="w-full bg-[#151C2C] border border-slate-800 p-3.5 rounded-xl text-sm text-white placeholder-slate-500 focus:outline-none focus:border-cyan-500/50 transition"
            onChange={(e) => setFormData({...formData, password: e.target.value})}
          />
          
          <button className="w-full bg-gradient-to-r from-[#0F5AA1] to-[#06D3E1] hover:opacity-95 text-white p-3.5 rounded-xl font-semibold text-sm transition shadow-xl shadow-cyan-500/10 mt-2 flex items-center justify-center gap-2 transform active:scale-[0.98]">
            {isLogin ? "Sign In Securely" : "Get Started Now"}
            <ArrowRight size={15} />
          </button>
        </form>

        <p className="text-slate-400 mt-6 text-center text-xs">
          {isLogin ? "New to FinTrack?" : "Already have an account?"} 
          <button type="button" onClick={() => { setIsLogin(!isLogin); setErrorMessage(''); }} className="text-[#1EE9FE] ml-1 font-semibold hover:underline">
            {isLogin ? "Create an account" : "Sign in here"}
          </button>
        </p>

        <div className="mt-6 pt-4 border-t border-slate-800/60 text-center">
          <span className="text-[10px] text-slate-500 font-bold tracking-wider uppercase">
            🛡️ 100% Free for Individual Investors &middot; No Card Needed
          </span>
        </div>
      </div>
    </div>
  );
};

export default AuthModal;
*/

import React, { useState } from 'react';
import { X, ShieldCheck, ArrowRight } from 'lucide-react';
const BACKEND = "https://stock-backend-gsyw.onrender.com";

const AuthModal = ({ isOpen, onClose, onLoginSuccess }) => {
  const [isLogin, setIsLogin] = useState(true);
  const [formData, setFormData] = useState({ email: '', password: '', name: '' });
  const [errorMessage, setErrorMessage] = useState('');

  if (!isOpen) return null;

  // Custom Close Handler जो बंद होने पर सब साफ़ (Reset) कर देगा
  const handleClose = () => {
    setFormData({ email: '', password: '', name: '' }); // Clear input fields
    setErrorMessage(''); // Clear any old error message
    onClose(); // Call original close function
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setErrorMessage('');
    const endpoint = isLogin ? '/auth/login' : '/auth/register';
    
    try {
      const response = await fetch(`${BACKEND}${endpoint}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData),
      });
      const data = await response.json();

      if (response.ok) {
        localStorage.setItem('token', data.token);
        localStorage.setItem('userEmail', formData.email);
        
        // SUCCESS FIX: fields को तुरंत खाली करो ताकि बाद में कचरा न दिखे
        setFormData({ email: '', password: '', name: '' });
        setErrorMessage('');
        
        onLoginSuccess(); 
        onClose(); 
      } else {
        setErrorMessage(data.error || "Authentication failed. Please check your credentials.");
      }
    } catch (err) {
      setErrorMessage("Database handshake error. Please check your network or server.");
      console.error("Auth Error:", err);
    }
  };

  return (
    <div className="fixed inset-0 bg-[#060813] flex items-center justify-center z-[99999] p-4 overflow-hidden select-none font-sans">
      
      {/* INBUILT PREMIUM BACKGROUND GRAPH */}
      <div className="absolute inset-0 opacity-50 pointer-events-none flex items-center justify-center lg:p-10">
        <svg className="w-full h-full text-cyan-500/30" viewBox="0 0 1200 600" fill="none" xmlns="http://www.w3.org/2000/svg">
        <path 
            d="M0 480 Q100 460 200 380 T400 320 T600 240 T800 260 T1000 140 T1200 90" 
            stroke="#06D3E1" 
            strokeWidth="3" 
            strokeLinecap="round" 
            strokeLinejoin="round"
        />
        <path 
            d="M0 510 C150 490 250 420 400 380 C550 340 650 310 800 290 C950 270 1050 180 1200 130" 
            stroke="rgba(59, 130, 246, 0.4)" 
            strokeWidth="2" 
            strokeLinecap="round"
        />
        <line x1="0" y1="140" x2="1200" y2="140" stroke="rgba(6, 211, 225, 0.15)" strokeWidth="1" strokeDasharray="4 4" />
        <line x1="0" y1="320" x2="1200" y2="320" stroke="rgba(255, 255, 255, 0.05)" strokeWidth="1" strokeDasharray="4 4" />
        <line x1="0" y1="480" x2="1200" y2="480" stroke="rgba(239, 68, 68, 0.15)" strokeWidth="1" strokeDasharray="4 4" />

        <g fill="rgba(255, 255, 255, 0.03)">
            <rect x="50" y="520" width="15" height="80" rx="2" />
            <rect x="100" y="480" width="15" height="120" rx="2" fill="rgba(6, 211, 225, 0.08)" />
            <rect x="150" y="540" width="15" height="60" rx="2" />
            <rect x="200" y="500" width="15" height="100" rx="2" />
            <rect x="250" y="460" width="15" height="140" rx="2" fill="rgba(6, 211, 225, 0.08)" />
            <rect x="300" y="510" width="15" height="90" rx="2" />
            <rect x="650" y="440" width="15" height="160" rx="2" fill="rgba(6, 211, 225, 0.08)" />
            <rect x="700" y="490" width="15" height="110" rx="2" />
            <rect x="750" y="530" width="15" height="70" rx="2" />
            <rect x="1000" y="420" width="15" height="180" rx="2" fill="rgba(6, 211, 225, 0.08)" />
            <rect x="1050" y="450" width="15" height="150" rx="2" />
            <rect x="1100" y="500" width="15" height="100" rx="2" />
        </g>

        <circle cx="1000" cy="140" r="5" fill="#06D3E1" className="animate-ping" />
        <circle cx="1000" cy="140" r="3.5" fill="#06D3E1" />

        <path d="M0 100 H1200 M0 200 H1200 M0 300 H1200 M0 400 H1200 M0 500 H1200" stroke="rgba(255,255,255,0.015)" strokeWidth="1"/>
        <path d="M150 0 V600 M300 0 V600 M450 0 V600 M600 0 V600 M750 0 V600 M900 0 V600 M1050 0 V600" stroke="rgba(255,255,255,0.015)" strokeWidth="1"/>
        </svg>
      </div>

      <div className="absolute w-[500px] h-[500px] bg-cyan-500/10 rounded-full blur-[150px] pointer-events-none -top-20 -left-20" />
      <div className="absolute w-[500px] h-[500px] bg-blue-600/5 rounded-full blur-[180px] pointer-events-none -bottom-20 -right-20" />

      {/* Main Login Card */}
      <div className="relative w-full max-w-md bg-[#09101C] border border-white p-8 rounded-2xl shadow-[0_30px_70px_rgba(0,0,0,0.8)] z-10">
        
        {/* Close Button - Updated to use handleClose */}
        <button onClick={handleClose} className="absolute top-5 right-5 text-slate-400 hover:text-white bg-slate-800/40 hover:bg-slate-800/80 p-1.5 rounded-xl transition">
          <X size={16} />
        </button>

        {/* Top Badge */}
        <div className="flex items-center justify-center gap-1.5 mb-5 text-cyan-400 text-[11px] font-semibold uppercase tracking-widest bg-cyan-500/10 w-fit mx-auto px-3 py-1 rounded-full border border-cyan-500/20">
          <ShieldCheck size={14} /> Secure Verification
        </div>

        <h2 className="text-2xl font-bold text-white mb-1.5 text-center tracking-tight">
          {isLogin ? "Welcome Back" : "Create Account"}
        </h2>
        <p className="text-slate-400 text-xs text-center mb-6">
          {isLogin ? "Log in to view your synced portfolio." : "Your data is private. Keep your holdings safe."}
        </p>

        {/* Error Notification Box */}
        {errorMessage && (
          <div className="bg-red-500/10 border border-red-500/20 text-red-400 p-3 rounded-xl text-xs mb-4 text-center font-medium">
            {errorMessage}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          {!isLogin && (
            <input 
              type="text" placeholder="Your Name" required
              value={formData.name}
              className="w-full bg-[#151C2C] border border-slate-800 p-3.5 rounded-xl text-sm text-white placeholder-slate-500 focus:outline-none focus:border-cyan-500/50 transition"
              onChange={(e) => setFormData({...formData, name: e.target.value})}
            />
          )}
          <input 
            type="email" placeholder="Email Address" required
            value={formData.email}
            className="w-full bg-[#151C2C] border border-slate-800 p-3.5 rounded-xl text-sm text-white placeholder-slate-500 focus:outline-none focus:border-cyan-500/50 transition"
            onChange={(e) => setFormData({...formData, email: e.target.value})}
          />
          <input 
            type="password" placeholder="Password" required
            value={formData.password}
            className="w-full bg-[#151C2C] border border-slate-800 p-3.5 rounded-xl text-sm text-white placeholder-slate-500 focus:outline-none focus:border-cyan-500/50 transition"
            onChange={(e) => setFormData({...formData, password: e.target.value})}
          />
          
          <button className="w-full bg-gradient-to-r from-[#0F5AA1] to-[#06D3E1] hover:opacity-95 text-white p-3.5 rounded-xl font-semibold text-sm transition shadow-xl shadow-cyan-500/10 mt-2 flex items-center justify-center gap-2 transform active:scale-[0.98]">
            {isLogin ? "Sign In Securely" : "Get Started Now"}
            <ArrowRight size={15} />
          </button>
        </form>

        {/* Toggle Mode */}
        <p className="text-slate-400 mt-6 text-center text-xs">
          {isLogin ? "New to FinTrack?" : "Already have an account?"} 
          <button type="button" onClick={() => { setIsLogin(!isLogin); setErrorMessage(''); }} className="text-[#1EE9FE] ml-1 font-semibold hover:underline">
            {isLogin ? "Create an account" : "Sign in here"}
          </button>
        </p>

        {/* Bottom Note */}
        <div className="mt-6 pt-4 border-t border-slate-800/60 text-center">
          <span className="text-[10px] text-slate-500 font-bold tracking-wider uppercase">
            🛡️ 100% Free for Individual Investors · No Card Needed
          </span>
        </div>
      </div>
    </div>
  );
};

export default AuthModal;