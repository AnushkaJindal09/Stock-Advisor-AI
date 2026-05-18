// File: src/components/Navbar.jsx
import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';

export default function Navbar({ isLoggedIn, onLogout, setIsAuthOpen }) {
    const [menuOpen, setMenuOpen] = useState(false);
    const navigate = useNavigate();

    const handleNavigation = (targetPath) => {
        if (
            targetPath === "/home" || 
            targetPath === "/" || 
            targetPath === "/markets" || 
            targetPath === "/graph" || 
            targetPath === "/news"
        ) {
            navigate(targetPath);
            setMenuOpen(false);
            return;
        }

        // Sirf portfolio aur aichat ke liye global restriction
        if (!isLoggedIn) {
            setIsAuthOpen(true); 
        } else {
            navigate(targetPath); 
        }
        setMenuOpen(false);
    };

    return (
        // BG solid deep dark color (#050816) kar diya hai taaki peeche ka koi rang upar na jhalake
        <div className="sticky top-0 z-50 bg-[#050816] border-b border-white/10 shadow-md w-full">
            <div className="w-full px-6 py-4 flex items-center justify-between">
                <div className="text-2xl font-extrabold tracking-wide text-transparent bg-clip-text bg-gradient-to-r from-blue-500 via-cyan-400 to-green-400 select-none cursor-pointer" onClick={() => navigate('/home')}>
                    FinTrack
                </div>

                {/* Desktop Nav Tabs */}
                <div className="hidden md:flex space-x-8 text-sm font-medium tracking-wide text-gray-300 items-center">
                    {[
                        { label: "Home", to: "/home" },
                        { label: "Markets", to: "/markets" },
                        { label: "Forecast", to: "/graph" },
                        { label: "News", to: "/news" },
                        { label: "Portfolio", to: "/portfolio" },
                    ].map((link) => (
                        <button 
                            key={link.to} 
                            onClick={() => handleNavigation(link.to)} 
                            className="relative group hover:text-white transition cursor-pointer bg-transparent border-none outline-none font-medium text-sm tracking-wide text-gray-300"
                        >
                            {link.label}
                            <span className="absolute left-0 -bottom-0.5 w-0 h-0.5 bg-cyan-400 transition-all duration-300 group-hover:w-full"></span>
                        </button>
                    ))}

                    {/* Desktop Dynamic Login/Logout */}
                    {isLoggedIn ? (
                        <button 
                            onClick={() => { onLogout(); setMenuOpen(false); }}
                            className="border border-red-500/30 bg-red-500/10 text-red-400 px-4 py-1.5 rounded-lg hover:bg-red-500/20 transition-all font-medium text-xs tracking-wide uppercase"
                        >
                            Logout
                        </button>
                    ) : (
                        <button 
                            onClick={() => setIsAuthOpen(true)}
                            className="bg-slate-800 hover:bg-slate-700 text-white px-4 py-1.5 rounded-lg transition-all font-medium text-xs tracking-wide uppercase"
                        >
                            Login
                        </button>
                    )}
                </div>

                {/* Mobile Hamburger */}
                <button className="md:hidden text-gray-300 hover:text-white bg-transparent border-none outline-none text-xl" onClick={() => setMenuOpen(!menuOpen)}>
                    {menuOpen ? '✕' : '☰'}
                </button>
            </div>

            {/* Mobile Menu Options */}
            {menuOpen && (
                <div className="md:hidden bg-[#050816] border-t border-white/10 px-6 py-4 flex flex-col gap-4">
                    {[
                        { label: "Home", to: "/home" },
                        { label: "Markets", to: "/markets" },
                        { label: "Forecast", to: "/graph" },
                        { label: "News", to: "/news" },
                        { label: "Portfolio", to: "/portfolio" },
                    ].map((link) => (
                        <button 
                            key={link.to} 
                            onClick={() => handleNavigation(link.to)}
                            className="text-gray-300 hover:text-white text-sm font-medium transition text-left bg-transparent border-none outline-none"
                        >
                            {link.label}
                        </button>
                    ))}

                    {/* Mobile Dynamic Login/Logout */}
                    {isLoggedIn ? (
                        <button 
                            onClick={() => { onLogout(); setMenuOpen(false); }}
                            className="text-left text-red-400 text-sm font-medium transition bg-transparent border-none outline-none pt-2 border-t border-white/5"
                        >
                            🔴 Logout
                        </button>
                    ) : (
                        <button 
                            onClick={() => { setIsAuthOpen(true); setMenuOpen(false); }}
                            className="text-left text-cyan-400 text-sm font-medium transition bg-transparent border-none outline-none pt-2 border-t border-white/5"
                        >
                            🟢 Login / Sign Up
                        </button>
                    )}
                </div>
            )}
        </div>
    );
}