import React, { useState, useEffect } from 'react';

interface GothicGateEntranceProps {
  onEnterComplete: () => void;
}

export const GothicGateEntrance: React.FC<GothicGateEntranceProps> = ({ onEnterComplete }) => {
  const [isOpening, setIsOpening] = useState(false);
  const [isFadingOut, setIsFadingOut] = useState(false);
  const [embers, setEmbers] = useState<Array<{ id: number; left: number; duration: number; delay: number; size: number }>>([]);

  // Generate floating embers on mount
  useEffect(() => {
    const emberArray = Array.from({ length: 30 }).map((_, i) => ({
      id: i,
      left: Math.random() * 100,
      duration: 4 + Math.random() * 6,
      delay: Math.random() * 5,
      size: 2 + Math.random() * 4
    }));
    setEmbers(emberArray);
  }, []);

  // Web Audio API gate creak & low rumble sound synthesizer
  const playGateCreakSound = () => {
    try {
      const AudioCtx = window.AudioContext || (window as any).webkitAudioContext;
      if (!AudioCtx) return;
      const ctx = new AudioCtx();

      // 1. Deep Sub-Bass Rumble
      const rumbleOsc = ctx.createOscillator();
      const rumbleGain = ctx.createGain();
      const filter = ctx.createBiquadFilter();

      rumbleOsc.type = 'sawtooth';
      rumbleOsc.frequency.setValueAtTime(55, ctx.currentTime);
      rumbleOsc.frequency.exponentialRampToValueAtTime(25, ctx.currentTime + 2.5);

      filter.type = 'lowpass';
      filter.frequency.setValueAtTime(120, ctx.currentTime);

      rumbleGain.gain.setValueAtTime(0.01, ctx.currentTime);
      rumbleGain.gain.linearRampToValueAtTime(0.4, ctx.currentTime + 0.4);
      rumbleGain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 2.5);

      rumbleOsc.connect(filter);
      filter.connect(rumbleGain);
      rumbleGain.connect(ctx.destination);

      rumbleOsc.start();
      rumbleOsc.stop(ctx.currentTime + 2.6);

      // 2. Heavy Metal Creak (Frequency Modulation)
      const creakOsc = ctx.createOscillator();
      const creakGain = ctx.createGain();
      const creakFilter = ctx.createBiquadFilter();

      creakOsc.type = 'sawtooth';
      creakOsc.frequency.setValueAtTime(140, ctx.currentTime);
      creakOsc.frequency.linearRampToValueAtTime(85, ctx.currentTime + 1.2);
      creakOsc.frequency.linearRampToValueAtTime(170, ctx.currentTime + 2.2);

      creakFilter.type = 'bandpass';
      creakFilter.frequency.setValueAtTime(480, ctx.currentTime);
      creakFilter.Q.setValueAtTime(4.5, ctx.currentTime);

      creakGain.gain.setValueAtTime(0.01, ctx.currentTime);
      creakGain.gain.linearRampToValueAtTime(0.3, ctx.currentTime + 0.3);
      creakGain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 2.4);

      creakOsc.connect(creakFilter);
      creakFilter.connect(creakGain);
      creakGain.connect(ctx.destination);

      creakOsc.start();
      creakOsc.stop(ctx.currentTime + 2.5);
    } catch (e) {
      console.warn('AudioContext playback error:', e);
    }
  };

  const handleOpenGates = () => {
    if (isOpening) return;

    playGateCreakSound();
    setIsOpening(true);

    // Sequence: 2.2s gate swing -> portal glow fade out -> complete
    setTimeout(() => {
      setIsFadingOut(true);
    }, 2000);

    setTimeout(() => {
      sessionStorage.setItem('agentx_gate_opened', 'true');
      onEnterComplete();
    }, 2500);
  };

  return (
    <div 
      className={`fixed inset-0 z-[100] select-none overflow-hidden bg-[#070204] transition-opacity duration-700 ${
        isFadingOut ? 'opacity-0 pointer-events-none' : 'opacity-100'
      }`}
    >
      {/* 3D Scene Wrapper with Perspective */}
      <div 
        className="relative w-full h-full flex items-center justify-center transition-transform duration-[2400ms] ease-out"
        style={{
          perspective: '1400px',
          transform: isOpening ? 'scale(1.18)' : 'scale(1)'
        }}
      >
        {/* 1. STATIC BACKGROUND LAYER (gothic_bg.jpg - Pillars, Torches, Red Moon, Ground, Crimson Portal - NO GATE UNDERNEATH!) */}
        <div className="absolute inset-0 z-0">
          <div 
            className="w-full h-full bg-cover bg-center"
            style={{ backgroundImage: "url('/gothic_bg.jpg')" }}
          />

          {/* Intensifying Crimson Light Portal behind gates */}
          <div 
            className={`absolute inset-0 flex items-center justify-center transition-opacity duration-1000 ${
              isOpening ? 'opacity-100' : 'opacity-40'
            }`}
          >
            <div className="w-[50vw] h-[75vh] bg-gradient-to-t from-red-600 via-rose-600 to-amber-400 rounded-full blur-[90px] opacity-90 animate-pulse" />
            <div className="absolute w-[35vw] h-[55vh] bg-red-500 rounded-full blur-[60px] opacity-100" />
          </div>

          {/* Ground Fog & Dark Vignette */}
          <div className="absolute inset-0 bg-gradient-to-b from-black/80 via-transparent to-red-950/90 pointer-events-none" />
          <div 
            className={`absolute bottom-0 inset-x-0 h-64 bg-gradient-to-t from-black via-red-950/70 to-transparent blur-lg pointer-events-none transition-transform duration-[2200ms] ${
              isOpening ? 'scale-125 opacity-100' : 'scale-100 opacity-80'
            }`}
          />
        </div>

        {/* FLOATING RED EMBERS & PARTICLES */}
        <div className="absolute inset-0 z-10 pointer-events-none overflow-hidden">
          {embers.map((ember) => (
            <div
              key={ember.id}
              className="absolute bg-red-500 rounded-full blur-[1px] opacity-75"
              style={{
                left: `${ember.left}%`,
                bottom: '-10px',
                width: `${ember.size}px`,
                height: `${ember.size}px`,
                boxShadow: '0 0 8px #ef4444, 0 0 12px #dc2626',
                animation: `floatUp ${ember.duration}s infinite linear ${ember.delay}s`
              }}
            />
          ))}
        </div>

        {/* 2. LEFT GATE LAYER (gothic_left_gate.png) */}
        <div
          className="absolute inset-0 z-20 pointer-events-none"
          style={{
            backgroundImage: "url('/gothic_left_gate.png')",
            backgroundSize: 'cover',
            backgroundPosition: 'center',
            transformOrigin: 'left center',
            transform: isOpening
              ? 'translateX(-105%) rotateY(-25deg)'
              : 'translateX(0%) rotateY(0deg)',
            transition: 'transform 2.2s cubic-bezier(0.7, 0, 0.2, 1), filter 2.2s cubic-bezier(0.7, 0, 0.2, 1)',
            filter: isOpening 
              ? 'drop-shadow(-25px 0 40px rgba(0,0,0,0.95)) blur(0.5px)' 
              : 'drop-shadow(-5px 0 15px rgba(0,0,0,0.8))'
          }}
        />

        {/* 3. RIGHT GATE LAYER (gothic_right_gate.png) */}
        <div
          className="absolute inset-0 z-20 pointer-events-none"
          style={{
            backgroundImage: "url('/gothic_right_gate.png')",
            backgroundSize: 'cover',
            backgroundPosition: 'center',
            transformOrigin: 'right center',
            transform: isOpening
              ? 'translateX(105%) rotateY(25deg)'
              : 'translateX(0%) rotateY(0deg)',
            transition: 'transform 2.2s cubic-bezier(0.7, 0, 0.2, 1), filter 2.2s cubic-bezier(0.7, 0, 0.2, 1)',
            filter: isOpening 
              ? 'drop-shadow(25px 0 40px rgba(0,0,0,0.95)) blur(0.5px)' 
              : 'drop-shadow(5px 0 15px rgba(0,0,0,0.8))'
          }}
        />

        {/* AGENTX BRANDING & OPEN THE GATES UI */}
        <div 
          className={`relative z-30 flex flex-col items-center justify-center text-center px-6 transition-all duration-700 ${
            isOpening ? 'opacity-0 scale-90 pointer-events-none translate-y-6' : 'opacity-100 scale-100'
          }`}
        >
          {/* Title: AGENTX */}
          <h1 
            className="text-6xl sm:text-7xl md:text-9xl font-bold tracking-widest text-slate-100 drop-shadow-[0_10px_30px_rgba(0,0,0,0.95)]"
            style={{ fontFamily: "'Cinzel Decorative', 'Cinzel', serif" }}
          >
            AGENT<span className="text-red-600 drop-shadow-[0_0_35px_#ff1e38] animate-pulse">X</span>
          </h1>

          {/* Subtitle */}
          <p 
            className="text-xs sm:text-sm md:text-base font-semibold tracking-[0.35em] text-red-200/90 uppercase mt-2 mb-8 drop-shadow-[0_2px_10px_rgba(0,0,0,0.9)]"
            style={{ fontFamily: "'Cinzel', serif" }}
          >
            ENTER A HIGHER INTELLIGENCE
          </p>

          {/* Medieval Gothic Button: OPEN THE GATES */}
          <button
            onClick={handleOpenGates}
            className="group relative px-10 py-4 sm:px-14 sm:py-5 bg-black/85 hover:bg-black text-red-100 border-2 border-red-900/80 hover:border-red-500 rounded-none shadow-[0_0_25px_rgba(127,29,29,0.5)] hover:shadow-[0_0_50px_rgba(239,68,68,0.85)] transition-all duration-300 hover:scale-105 cursor-pointer overflow-hidden"
          >
            {/* Corner Medieval Accents */}
            <div className="absolute top-1 left-1 w-2 h-2 border-t-2 border-l-2 border-red-500" />
            <div className="absolute top-1 right-1 w-2 h-2 border-t-2 border-r-2 border-red-500" />
            <div className="absolute bottom-1 left-1 w-2 h-2 border-b-2 border-l-2 border-red-500" />
            <div className="absolute bottom-1 right-1 w-2 h-2 border-b-2 border-r-2 border-red-500" />

            <span 
              className="text-sm sm:text-lg font-bold tracking-[0.3em] uppercase text-slate-100 group-hover:text-red-400 transition-colors flex items-center gap-3"
              style={{ fontFamily: "'Cinzel', serif" }}
            >
              <span className="text-red-600 text-xs">♦</span>
              OPEN THE GATES
              <span className="text-red-600 text-xs">♦</span>
            </span>
          </button>

          {/* Tagline */}
          <p 
            className="text-[10px] sm:text-xs tracking-[0.4em] font-semibold text-slate-400/80 uppercase mt-8 drop-shadow-[0_2px_8px_rgba(0,0,0,0.9)]"
            style={{ fontFamily: "'Cinzel', serif" }}
          >
            AUTONOMOUS AI TEAMMATES FOR BUSINESS
          </p>
        </div>
      </div>

      {/* Floating Embers CSS Keyframes */}
      <style>{`
        @keyframes floatUp {
          0% {
            transform: translateY(0) scale(1);
            opacity: 0.8;
          }
          50% {
            opacity: 1;
          }
          100% {
            transform: translateY(-100vh) scale(0.4);
            opacity: 0;
          }
        }
      `}</style>
    </div>
  );
};
