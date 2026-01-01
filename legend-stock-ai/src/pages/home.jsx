import React from 'react';
import ProfessionalBackground from "../components/ProfessionalBackground";
import AnimatedGraph from '../components/AnimatedGraph';
import { Link } from 'react-router-dom';

function Home(){
    return(
       
    <div className="relative text-white  px-1 text-xl min-h-screen">
    
                
  
      <div className="sticky top-0 z-50 backdrop-blur-md bg-black/20 shadow-md">
      <div className="w-full mb-9 px-6 py-4 flex items-center justify-between">
        {/* Logo */}
        <div className="text-2xl sm:text-3xl  font-extrabold tracking-wide text-transparent bg-clip-text bg-gradient-to-r from-blue-500 via-cyan-400 to-green-400 select-none">
          FinTrack
        </div>

        {/* Nav Links */}
        <div className="space-x-6 text-sm sm:text-base font-medium tracking-wide text-white">
          <Link
            to="/home"
            className="relative group hover:text-cyan-400 transition"
          >
            Home
            <span className="absolute left-0 -bottom-0.5 w-0 h-0.5 bg-cyan-400 transition-all duration-300 group-hover:w-full"></span>
          </Link>
          <Link
            to="/graph"
            className="relative group hover:text-cyan-400 transition"
          >
            Forecast
            <span className="absolute left-0 -bottom-0.5 w-0 h-0.5 bg-cyan-400 transition-all duration-300 group-hover:w-full"></span>
          </Link>

          <Link
            to="/news"
            className="relative group hover:text-cyan-400 transition"
          >
            News
            <span className="absolute left-0 -bottom-0.5 w-0 h-0.5 bg-cyan-400 transition-all duration-300 group-hover:w-full"></span>
          </Link>
          <Link
            to="/portfolio"
            className="relative group hover:text-cyan-400 transition"
          >
            Portfolio
            <span className="absolute left-0 -bottom-0.5 w-0 h-0.5 bg-cyan-400 transition-all duration-300 group-hover:w-full"></span>
          </Link>
        </div>
      </div>
    </div>
                
                
        <ProfessionalBackground />
        <AnimatedGraph />

        
            <p className="relative z-10 text-center py-2 text-bold text-2xl tracking-widest text-white/70 font-medium"> ANALYSE . PREDICT . INVEST SMARTER</p>
            <div className='flex justify-center items-center'>


            </div>

                  {/* Main Content */}
      <div className="relative z-10 flex flex-col items-center justify-center h-full px-6 text-center">
        <div className="backdrop-blur-md bg-white/10 p-8 rounded-xl shadow-lg max-w-3xl">
          <h1 className="text-3xl font-bold mb-4 tracking-wide"> AI-Powered Stock Market Companion</h1>
          <p className="text-lg opacity-90 mb-4 text-gray-400">
            Real-time market insights powered by AI. Get live graphs, forecasts & more.
          </p>
          <Link to = "/aichat">
          <button className="mt-2 px-6 py-2 border border-white rounded-md bg-blue-600 hover:bg-blue-700 text-white shadow">
            Start Chat
          </button>
          </Link>
        </div>
      </div>
            
          
        </div>
    );
}

export default function Myhome(){
    return(
        <Home />
    );
}






