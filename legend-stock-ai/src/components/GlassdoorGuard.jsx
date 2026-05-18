import React from 'react';
import { ShieldCheck } from 'lucide-react';

const GlassdoorGuard = ({ children, isLoggedIn, onTriggerAuth, pageTitle }) => {
  // User agar login hai, toh bina kisi rukawat ke direct screen pass kar do
  if (isLoggedIn) return children;

  return (
    <div className="relative min-h-screen w-full overflow-hidden">
      
      {/* Background UI jise hum user ke liye blur and non-clickable karenge */}
      <div className="filter blur-md pointer-events-none select-none opacity-20 transition-all duration-500">
        {children}
      </div>

      {/* The Central Premium Overlaid Box */}
      <div className="absolute inset-0 flex items-center justify-center bg-black/40 z-40 p-4 backdrop-blur-sm">
        <div className="bg-[#0b0c10]/95 border border-white/10 p-8 rounded-2xl max-w-sm w-full text-center shadow-2xl animate-fade-in">
          
          <div className="inline-flex p-3 bg-cyan-500/10 text-cyan-400 rounded-full mb-4">
            <ShieldCheck size={26} />
          </div>
          
          <h3 className="text-xl font-bold text-white mb-2 tracking-tight">
            Secure Workspace Access
          </h3>
          <p className="text-gray-400 text-xs mb-6 leading-relaxed">
            FinTrack encrypts your session metrics. Please activate your secure vault to access {pageTitle || "this area"}.
          </p>
          
          <button 
            onClick={onTriggerAuth}
            className="w-full bg-gradient-to-r from-blue-600 to-cyan-600 hover:opacity-90 text-white p-3 rounded-xl font-semibold text-sm transition shadow-lg shadow-cyan-500/10"
          >
            Unlock Vault Now
          </button>
          
          <div className="mt-5 pt-4 border-t border-white/5 text-center">
            <span className="text-[10px] text-gray-500 font-medium tracking-wider uppercase">
              🛡️ 100% Free &middot; Encrypted Session
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default GlassdoorGuard;