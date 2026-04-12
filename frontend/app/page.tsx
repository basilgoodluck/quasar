"use client";
import React, { useState, useEffect, useRef } from 'react';
import { 
  Menu, 
  X, 
  ArrowRight, 
  Check, 
  Shield, 
  Zap, 
  Eye, 
  TrendingUp, 
  Activity, 
  ChevronRight 
} from 'lucide-react';
import { 
  FaGithub, 
  FaLinkedin, 
  FaEnvelope 
} from 'react-icons/fa';
import { FiExternalLink } from 'react-icons/fi';
import { motion, useInView } from 'framer-motion';
import Link from 'next/link';
import Head from 'next/head';
import landingData from '@/data/landing.json';

const NAV_HEIGHT = 74;

function SEO() {
  return (
    <Head>
      <title>Quasar – On-Chain AI Trading Agent | Verifiable, Transparent, Self-Improving</title>
      <meta name="description" content="Quasar is a trustless on-chain AI trading agent. It classifies market regimes, uses EMA and Fisher Transform signals, trains an LSTM model on its own decisions, enforces risk via smart contracts. Every action is EIP-712 signed and verifiable on Sepolia." />
      <meta name="keywords" content="on-chain trading agent, AI trading bot, EIP-712, smart contract trading, LSTM trading model, Kelly criterion, verifiable trading, DeFi agent, Sepolia testnet, transparent trading" />
      <meta property="og:title" content="Quasar – On-Chain AI Trading Agent" />
      <meta property="og:description" content="A self-improving trading agent with on-chain identity, EIP-712 signed decisions, and smart contract risk enforcement. Every trade is verifiable. Nothing is a black box." />
      <meta property="og:type" content="website" />
      <meta name="twitter:card" content="summary_large_image" />
      <meta name="twitter:title" content="Quasar – On-Chain AI Trading Agent" />
      <meta name="twitter:description" content="Trustless AI trading with on-chain accountability. Regime-aware, self-improving, Kelly-sized." />
      <link rel="canonical" href="https://quasar.finance" />
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{
          __html: JSON.stringify({
            "@context": "https://schema.org",
            "@type": "SoftwareApplication",
            "name": "Quasar",
            "description": "An on-chain AI trading agent that classifies market regimes, learns from its own decisions via LSTM, and enforces risk controls via smart contracts.",
            "applicationCategory": "FinanceApplication",
            "operatingSystem": "Web",
            "offers": { "@type": "Offer", "price": "0" }
          })
        }}
      />
    </Head>
  );
}

function Header() {
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const navLinks = [
    { href: "#how", label: "How It Works" },
    { href: "#features", label: "Features" },
    { href: "#faq", label: "FAQ" },
  ];

  useEffect(() => {
    document.body.style.overflow = isMenuOpen ? 'hidden' : 'unset';
    return () => { document.body.style.overflow = 'unset'; };
  }, [isMenuOpen]);

  return (
    <>
      <motion.nav
        initial={{ y: -100 }}
        animate={{ y: 0 }}
        transition={{ duration: 0.18, ease: "easeOut" }}
        style={{ height: NAV_HEIGHT }}
        className="fixed top-0 left-0 right-0 z-50 px-4 sm:px-6 md:px-12 bg-white/80 backdrop-blur-md border-b border-gray-200 flex items-center"
      >
        <div className="w-full max-w-7xl mx-auto flex items-center justify-between">
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.05, duration: 0.25 }}
            className="flex items-center space-x-2"
          >
            <div className="w-9 h-9 bg-blue-600 rounded-full flex items-center justify-center">
              <span className="text-white font-bold text-sm">Q</span>
            </div>
            <span className="text-gray-900 font-bold tracking-wide text-xl">Quasar</span>
          </motion.div>

          <div className="hidden md:flex items-center space-x-8 lg:space-x-16">
            <div className="flex items-center space-x-8 lg:space-x-10">
              {navLinks.map((link, i) => (
                <motion.a
                  key={link.label}
                  href={link.href}
                  initial={{ opacity: 0, y: -10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.12 + i * 0.03, duration: 0.2 }}
                  whileHover={{ y: -2 }}
                  className="text-gray-600 hover:text-blue-600 transition text-base font-medium"
                >
                  {link.label}
                </motion.a>
              ))}
            </div>

            <motion.a
              href="/overview"
              initial={{ opacity: 0, scale: 0.8 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: 0.18, duration: 0.25 }}
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              className="btn-slide btn-slide-dark bg-black text-white px-6 py-3 rounded-full font-bold text-base transition"
            >
              Launch Agent
            </motion.a>
          </div>

          <button onClick={() => setIsMenuOpen(!isMenuOpen)} className="md:hidden text-gray-900 z-50 relative">
            {isMenuOpen ? <X size={26} /> : <Menu size={26} />}
          </button>
        </div>
      </motion.nav>

      <div className={`fixed inset-0 bg-white z-40 md:hidden transition-all duration-300 ${isMenuOpen ? 'opacity-100 pointer-events-auto' : 'opacity-0 pointer-events-none'}`}>
        <div className="h-full flex flex-col items-center justify-center space-y-10">
          {navLinks.map((link, i) => (
            <a key={link.label} href={link.href} onClick={() => setIsMenuOpen(false)}
              className={`text-gray-900 font-bold text-2xl transition-all duration-200 ${isMenuOpen ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-8'}`}
              style={{ transitionDelay: isMenuOpen ? `${i * 30}ms` : '0ms' }}>
              {link.label}
            </a>
          ))}
          <a href="/overview"
            className="btn-slide btn-slide-dark mt-4 bg-black text-white px-10 py-4 rounded-full font-bold text-lg">
            Launch Agent
          </a>
        </div>
      </div>
    </>
  );
}

function Hero() {
  const words = landingData.heroWords;
  const [currentIndex, setCurrentIndex] = useState(0);
  const [grid, setGrid] = useState({ cols: 0, rows: 0 });
  const sectionRef = useRef<HTMLElement>(null);
  const longestWord = words.reduce((a, b) => a.length > b.length ? a : b, '');

  useEffect(() => {
    const interval = setInterval(() => setCurrentIndex(p => (p + 1) % words.length), 3000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    const BOX = 56;
    const GAP = 8;
    function calculate() {
      if (!sectionRef.current) return;
      const { width, height } = sectionRef.current.getBoundingClientRect();
      const cols = Math.ceil(width / (BOX + GAP));
      const rows = Math.ceil(height / (BOX + GAP));
      setGrid({ cols, rows });
    }
    calculate();
    const ro = new ResizeObserver(calculate);
    if (sectionRef.current) ro.observe(sectionRef.current);
    return () => ro.disconnect();
  }, []);

  const BOX = 56;
  const GAP = 8;
  const colors = [
    'bg-purple-200', 'bg-purple-100', 'bg-pink-200', 'bg-pink-100',
    'bg-fuchsia-200', 'bg-fuchsia-100', 'bg-violet-200', 'bg-violet-100',
  ];

  return (
    <section
      ref={sectionRef}
      className="relative px-4 sm:px-6 md:px-12 flex flex-col justify-center overflow-hidden min-h-[calc(100vh-74px)]"
      style={{ marginTop: NAV_HEIGHT, background: '#0a0a0f' }}
    >
      <div className="pointer-events-none absolute inset-0 overflow-hidden">
        <div style={{
          display: 'grid',
          gridTemplateColumns: `repeat(${grid.cols}, ${BOX}px)`,
          gridTemplateRows: `repeat(${grid.rows}, ${BOX}px)`,
          gap: GAP,
          padding: GAP / 2,
        }}>
          {Array.from({ length: grid.cols * grid.rows }).map((_, i) => {
            const color = colors[i % colors.length];
            const sparkle = i % 17 === 0;
            return (
              <div
                key={i}
                className={`${color} rounded-xl relative`}
                style={{ width: BOX, height: BOX, opacity: 0.4 + (i % 4) * 0.1 }}
              >
                {sparkle && (
                  <div className="absolute inset-0 flex items-center justify-center">
                    <div
                      className="w-1.5 h-1.5 bg-white rounded-full"
                      style={{
                        boxShadow: '0 0 6px 2px rgba(255,255,255,0.9)',
                        animation: `sparkle-pulse ${1.5 + i % 3}s ease-in-out infinite`,
                      }}
                    />
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>

      <div className="pointer-events-none absolute inset-0" style={{ background: 'rgba(10,10,15,0.75)' }} />

      <div className="max-w-4xl mx-auto relative z-10 w-full px-4">
        <div className="text-center">
          <h1 className="text-3xl sm:text-4xl md:text-5xl font-bold mb-4">
            <span className="text-blue-600">On-Chain</span> <span className="text-white">AI Trading</span>
          </h1>
          <h2 className="text-4xl sm:text-5xl md:text-6xl font-black mb-8 text-white relative inline-block h-[1.2em] overflow-hidden mx-auto">
            <span className="invisible">{longestWord}</span>
            <span key={currentIndex} className="absolute inset-0 flex items-center justify-center animate-slideUp">
              <span className="relative inline-block">
                {words[currentIndex]}
                <span className="absolute -bottom-1 left-0 w-full h-1 bg-blue-600 transform -skew-x-12" />
              </span>
            </span>
          </h2>
          <p className="text-base sm:text-lg text-gray-400 max-w-2xl mb-10 leading-relaxed mx-auto">
            A trustless trading agent that classifies market regimes, learns from its own decisions via LSTM, and enforces every trade through EIP-712 signed smart contract risk controls. Every decision is verifiable. Nothing is a black box.
          </p>
          <div className="flex flex-wrap gap-4 justify-center">
            <a href="/overview"
              className="btn-slide btn-slide-dark bg-white text-black px-8 py-4 rounded-full font-bold text-base transition active:scale-95">
              View Live Agent →
            </a>
            <a href="#contracts"
              className="btn-slide btn-slide-border border border-gray-700 text-gray-400 px-8 py-4 rounded-full text-base transition">
              On-Chain Activity
            </a>
          </div>
          <div className="flex flex-wrap gap-6 sm:gap-8 mt-14 pt-10 border-t border-gray-800 justify-center">
            {landingData.heroStats.map((s: any) => (
              <div key={s.label} className="text-center">
                <div className="text-2xl text-blue-400 font-bold">{s.value}</div>
                <div className="text-sm text-gray-500 mt-1">{s.label}</div>
              </div>
            ))}
          </div>
        </div>
      </div>

      <style jsx>{`
        @keyframes slideUp {
          0% { opacity: 0; transform: translateY(100%); }
          100% { opacity: 1; transform: translateY(0); }
        }
        .animate-slideUp { animation: slideUp 0.5s ease-in-out forwards; }
        @keyframes sparkle-pulse {
          0%, 100% { opacity: 0.2; transform: scale(0.7); }
          50% { opacity: 1; transform: scale(1.4); }
        }
      `}</style>
    </section>
  );
}

function HowItWorks() {
  const steps = landingData.howItWorksSteps;
  return (
    <section id="how" className="relative px-4 sm:px-6 md:px-12 py-16 md:py-24 bg-white">
      <div className="max-w-7xl mx-auto">
        <h2 className="text-2xl sm:text-3xl font-bold text-center mb-4 text-gray-900">How It Works</h2>
        <p className="text-center text-gray-400 max-w-xl mx-auto mb-12 md:mb-16 text-sm sm:text-base leading-relaxed">
          Quasar operates a fully auditable decision pipeline — from raw market data to an on-chain checkpoint — with no human intervention required.
        </p>
        <div className="grid md:grid-cols-2 gap-10 md:gap-16 items-start">
          {/* Pipeline diagram — shown second on mobile, first on desktop */}
          <div className="relative flex justify-center order-2 md:order-1">
            <div className="w-full max-w-xs sm:max-w-sm md:max-w-md bg-gray-50 rounded-2xl border border-gray-200 p-4 md:p-6 font-mono text-sm">
              {["TradeDecision", "TradeIntent", "EIP-712 Signature", "RiskRouter Validation", "Execution", "Checkpoint"].map((s, i, arr) => (
                <div key={s}>
                  <div className="flex items-center gap-3 py-2.5 md:py-3">
                    <div className="w-7 h-7 rounded-full border border-blue-200 bg-blue-50 flex items-center justify-center text-blue-600 text-xs font-bold flex-shrink-0">
                      {String(i + 1).padStart(2, '0')}
                    </div>
                    <span className="text-gray-700 text-sm md:text-base min-w-0">{s}</span>
                  </div>
                  {i < arr.length - 1 && <div className="ml-3 text-blue-300 text-lg">↓</div>}
                </div>
              ))}
            </div>
          </div>

          {/* Steps — shown first on mobile */}
          <div className="flex flex-col space-y-8 md:space-y-10 order-1 md:order-2">
            {steps.map((step: any, index: number) => (
              <div key={index} className="flex gap-4 flex-col">
                <div className="flex items-baseline gap-3 text-xl md:text-2xl text-gray-200 leading-none font-black">
                  {step.number}.
                  <h3 className="text-lg md:text-xl font-semibold text-gray-700">{step.title}</h3>
                </div>
                <div className="pl-8 md:pl-10">
                  <p className="text-sm md:text-base text-gray-400 leading-relaxed">{step.description}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}

function MarketRegimes() {
  const regimes = [
    {
      name: "Trending",
      description: "Strong directional order flow. CVD is rising consistently, buy aggression is elevated, and open interest confirms positioning. EMA trend-following signals are trusted. Fisher Transform reversals are monitored but deprioritised.",
      signals: ["CVD slope confirmed", "Buy aggression elevated", "OI expanding"],
    },
    {
      name: "Volatile",
      description: "High price variance with no clear direction. Realised volatility and HL range are spiking, CVD is flipping frequently. Both EMA and Fisher Transform signals are treated with scepticism. The agent waits for confirmation before acting.",
      signals: ["Realised vol spike", "CVD flipping", "Liquidation imbalance low"],
    },
    {
      name: "Ranging",
      description: "Sideways price action with weak order flow. EMA trend signals are ignored entirely. Fisher Transform reversal signals take priority. Trade frequency is significantly reduced.",
      signals: ["CVD slope near zero", "Low return slope", "Fisher Transform prioritised"],
    },
  ];

  return (
    <section className="relative px-4 sm:px-6 md:px-12 py-16 md:py-24 bg-gray-50">
      <div className="max-w-5xl mx-auto">
        <h2 className="text-2xl sm:text-3xl font-bold text-center mb-4 text-gray-900">Market Regime Classification</h2>
        <p className="text-center text-gray-400 max-w-2xl mx-auto mb-12 md:mb-16 text-sm sm:text-base leading-relaxed">
          Before evaluating any signal, Quasar classifies the current market into one of three regimes. The regime determines whether EMA trend-following or Fisher Transform reversal signals are trusted — and how aggressively the agent acts.
        </p>
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4 md:gap-6">
          {regimes.map((r) => (
            <div key={r.name} className="bg-white rounded-2xl border border-gray-100 p-5 md:p-6 flex flex-col gap-4">
              <h3 className="font-bold text-gray-900 text-lg">{r.name}</h3>
              <p className="text-sm text-gray-500 leading-relaxed flex-1">{r.description}</p>
              <div className="flex flex-col gap-2 mt-auto">
                {r.signals.map(sig => (
                  <span key={sig} className="text-xs font-medium px-3 py-1.5 rounded-md bg-gray-100 text-gray-600 inline-block">{sig}</span>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

function Features() {
  const features = landingData.features;
  return (
    <section id="features" className="relative px-4 sm:px-6 md:px-12 py-16 md:py-24 bg-white">
      <div className="max-w-6xl mx-auto">
        <h2 className="text-2xl sm:text-3xl text-center font-bold mb-4 text-gray-900">
          ...your trades are on the record
        </h2>
        <p className="text-center text-gray-400 max-w-xl mx-auto mb-10 text-sm sm:text-base leading-relaxed">
          Every action Quasar takes is logged, signed, and anchored on-chain. Audit any decision at any time — no dashboards that hide the truth.
        </p>

        <div className="flex flex-col lg:flex-row items-start justify-center gap-8 lg:gap-16">
          {/* Feature list */}
          <div className="w-full lg:flex-1 lg:max-w-md space-y-5 md:space-y-7">
            {features.map((feature: string, index: number) => (
              <div key={index} className="flex items-start space-x-4">
                <div className="w-7 h-7 flex-shrink-0 bg-blue-600 rounded-full flex items-center justify-center mt-0.5">
                  <Check size={15} className="text-white" />
                </div>
                <span className="text-base text-gray-700 leading-snug">{feature}</span>
              </div>
            ))}
          </div>

          {/* Code panel */}
          <div className="w-full lg:flex-1 lg:max-w-md bg-gray-50 rounded-2xl border border-gray-200 overflow-hidden min-w-0">
            <div className="px-4 md:px-5 py-3 border-b border-gray-200 bg-white">
              <span className="text-xs sm:text-sm text-gray-400 font-mono">checkpoints.jsonl</span>
            </div>
            <div className="p-4 md:p-5 font-mono text-xs sm:text-sm space-y-3">
              {[
                { action: "BUY", pair: "BTCUSDT", conf: 0.81, status: "WIN", pnl: "+$22.78", regime: "trending" },
                { action: "HOLD", pair: "ETHUSDT", conf: 0.44, status: "SKIP", pnl: "—", regime: "volatile" },
                { action: "SELL", pair: "BTCUSDT", conf: 0.76, status: "WIN", pnl: "+$11.20", regime: "trending" },
              ].map((r, i) => (
                <div key={i} className="border border-gray-200 rounded-xl p-3 md:p-4 space-y-2 bg-white">
                  <div className="flex justify-between text-sm flex-wrap gap-1">
                    <span className="text-gray-900 font-bold">{r.action}</span>
                    <span className="text-gray-500">{r.pair}</span>
                    <span className="text-gray-500 font-semibold">{r.status}</span>
                  </div>
                  <div className="flex gap-3 text-gray-400 text-xs flex-wrap">
                    <span>regime <span className="text-gray-600 font-semibold">{r.regime}</span></span>
                    <span>conf <span className="text-gray-600 font-semibold">{r.conf}</span></span>
                    <span>pnl <span className="text-gray-700 font-semibold">{r.pnl}</span></span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        <div className="md:w-4/5 mx-auto space-y-8 md:space-y-10 flex flex-col items-center mt-12 md:mt-16">
          <h3 className="text-center text-xl md:text-2xl text-gray-700 px-4 font-medium leading-snug">
            Every decision signed. Every trade verifiable. Every outcome recorded on-chain.
          </h3>
          <a href="/overview"
            className="btn-slide btn-slide-dark bg-black text-white px-8 md:px-10 py-4 rounded-full font-bold text-base transition inline-flex items-center gap-2 active:scale-95">
            <span>Access Dashboard</span>
            <ArrowRight size={18} />
          </a>
        </div>
      </div>
    </section>
  );
}

function RiskManagement() {
  return (
    <section className="relative px-4 sm:px-6 md:px-12 py-16 md:py-24 bg-gray-50">
      <div className="max-w-7xl mx-auto">
        <h2 className="text-2xl sm:text-3xl font-bold text-center mb-4 text-gray-900">Risk Management</h2>
        <p className="text-center text-gray-400 max-w-xl mx-auto mb-12 md:mb-16 text-sm sm:text-base leading-relaxed">
          Quasar enforces strict risk controls at every layer — from position sizing to on-chain smart contract gates — so capital preservation is never optional.
        </p>
        {/* Changed from md:grid-cols-3 to lg:grid-cols-3 — 768px is too tight for 3 dense text columns */}
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4 md:gap-6 lg:gap-8">
          <div className="bg-white rounded-2xl border border-gray-100 p-6 md:p-8">
            <div className="w-10 h-10 bg-blue-600 rounded-full flex items-center justify-center mb-5">
              <TrendingUp size={20} className="text-white" />
            </div>
            <h3 className="text-base md:text-lg font-bold text-gray-900 mb-3">Kelly Criterion Sizing</h3>
            <p className="text-gray-500 text-sm leading-relaxed">
              Each position size is derived from the Kelly formula — balancing expected return against variance to maximise long-run growth without risking ruin. A fractional Kelly is applied for added conservatism.
            </p>
          </div>
          <div className="bg-white rounded-2xl border border-gray-100 p-6 md:p-8">
            <div className="w-10 h-10 bg-blue-600 rounded-full flex items-center justify-center mb-5">
              <Shield size={20} className="text-white" />
            </div>
            <h3 className="text-base md:text-lg font-bold text-gray-900 mb-3">Drawdown Limits</h3>
            <p className="text-gray-500 text-sm leading-relaxed">
              Hard drawdown limits are enforced at the model level and again at the RiskRouter smart contract level. No single bad run can compromise the account — both gates must pass before any trade executes.
            </p>
          </div>
          <div className="bg-white rounded-2xl border border-gray-100 p-6 md:p-8 sm:col-span-2 lg:col-span-1">
            <div className="w-10 h-10 bg-blue-600 rounded-full flex items-center justify-center mb-5">
              <Activity size={20} className="text-white" />
            </div>
            <h3 className="text-base md:text-lg font-bold text-gray-900 mb-3">Trade Frequency Controls</h3>
            <p className="text-gray-500 text-sm leading-relaxed">
              Overtrading is a silent killer. Quasar enforces per-session and per-day frequency limits on-chain, preventing the agent from churning through capital during noisy or low-signal market conditions.
            </p>
          </div>
        </div>
      </div>
    </section>
  );
}

function LSTMSection() {
  return (
    <section className="relative px-4 sm:px-6 md:px-12 py-16 md:py-24 bg-white">
      <div className="max-w-7xl mx-auto">
        <div className="grid md:grid-cols-2 gap-10 lg:gap-16 items-center">
          <div>
            <h2 className="text-2xl sm:text-3xl font-bold text-gray-900 mb-5 leading-snug">An agent that learns from its own history</h2>
            <p className="text-gray-500 text-sm sm:text-base leading-relaxed mb-6">
              After each trading session, Quasar retrains its LSTM model on a combined dataset of its own past decisions, their outcomes, and freshly scraped market data. The result is a model that improves with every iteration — not just on backtests, but on its live performance.
            </p>
            <ul className="space-y-3 md:space-y-4">
              {[
                "Trains on real trade outcomes, not simulated data",
                "Scraped market data enriches each training cycle",
                "LSTM captures temporal patterns across sessions",
                "Confidence scores update as the model evolves",
              ].map((item) => (
                <li key={item} className="flex items-start gap-3">
                  <ChevronRight size={18} className="text-blue-600 flex-shrink-0 mt-0.5" />
                  <span className="text-gray-600 text-sm">{item}</span>
                </li>
              ))}
            </ul>
          </div>

          {/* Training loop panel */}
          <div className="bg-gray-50 rounded-2xl border border-gray-200 p-4 md:p-6 font-mono text-xs sm:text-sm overflow-x-auto">
            <div className="text-gray-400 mb-4 text-xs uppercase tracking-widest">Training loop (simplified)</div>
            <div className="space-y-3 min-w-0">
              {[
                "Load checkpoint history + outcomes",
                "Scrape latest market features",
                "Merge into training dataset",
                "Retrain LSTM on full sequence",
                "Validate on held-out period",
                "Deploy updated model weights",
                "Update confidence thresholds",
              ].map((step, i) => (
                <div key={i} className="flex gap-3 min-w-0">
                  <span className="text-blue-400 flex-shrink-0">{i + 1}</span>
                  <span className="text-gray-600 break-words">{step}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}

function WhyQuasar() {
  const reasons = landingData.whyQuasarReasons;
  return (
    <section className="relative px-4 sm:px-6 md:px-12 py-16 md:py-24 bg-white">
      <div className="max-w-2xl mx-auto">
        <h2 className="text-2xl sm:text-3xl font-bold text-center mb-4 text-gray-900">Why Quasar?</h2>
        <p className="text-center text-gray-400 max-w-xl mx-auto mb-12 md:mb-16 text-sm sm:text-base leading-relaxed">
          Most trading bots are black boxes. Quasar is built from the ground up to be auditable, accountable, and self-correcting.
        </p>
        <div className="space-y-10 md:space-y-14">
          {reasons.map((r: any, i: number) => {
            const Icon = r.icon === "Shield" ? Shield : r.icon === "Zap" ? Zap : Eye;
            return (
              <div key={i} className="flex items-start space-x-5 md:space-x-6">
                <div className="flex-shrink-0 w-11 h-11 md:w-12 md:h-12 bg-blue-600 rounded-full flex items-center justify-center">
                  <Icon size={20} className="text-white" />
                </div>
                <div>
                  <h3 className="text-lg md:text-xl font-bold text-gray-900 mb-2 md:mb-3">{r.title}</h3>
                  <p className="text-sm md:text-base text-gray-500 leading-relaxed">{r.description}</p>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}

function FAQ() {
  const faqs = [
    {
      q: "What is Quasar?",
      a: "Quasar is a trustless on-chain AI trading agent. It analyses market conditions, classifies regimes, and generates signals using EMA for trend-following and Fisher Transform for trend reversals. Trades are governed by smart contract risk controls with every decision signed and logged on-chain.",
    },
    {
      q: "How does Quasar classify market regimes?",
      a: "Quasar analyses a window of real-time market data — including cumulative volume delta, buy aggression, realised volatility, open interest, and liquidation pressure — and scores it across three dimensions: trending, volatile, and ranging. The regime determines which signals the agent acts on: EMA for trend-following in trending markets, Fisher Transform for reversals in ranging markets, and a blended approach when both are present.",
    },
    {
      q: "How does the strategy use EMA and Fisher Transform?",
      a: "EMA signals identify trend-following opportunities — entries aligned with the prevailing direction. Fisher Transform signals identify trend reversal opportunities — entries against an exhausted move. Which signal is trusted depends entirely on the current regime. In ranging markets, reversals dominate. In trending markets, continuation dominates. In volatile markets, both are treated with caution.",
    },
    {
      q: "What is EIP-712 and why does Quasar use it?",
      a: "EIP-712 is an Ethereum standard for typed, structured data signing. Quasar uses it so that every TradeIntent is cryptographically signed by the agent's on-chain identity before any execution occurs — creating an immutable, verifiable record of the decision.",
    },
    {
      q: "How does the LSTM model improve over time?",
      a: "After each session, Quasar retrains its LSTM on its own checkpoint history — the decisions made, signals present, and outcomes realised — combined with freshly scraped market data. This means each training cycle is grounded in real performance, not just backtested scenarios.",
    },
    {
      q: "What stops the agent from taking bad trades?",
      a: "Risk is enforced at two levels. The Kelly criterion controls position sizing at the model level. The RiskRouter smart contract then validates every signed TradeIntent against hard drawdown limits and frequency controls before any execution proceeds on-chain.",
    },
    {
      q: "What is the reputation scoring system?",
      a: "Before every trade, Quasar analyses its last 100 resolved trades and assigns a reputation score between 0.0 and 1.0. The score combines win rate, decision consistency (penalising incorrect high-confidence calls more heavily), and a streak component that rewards sustained performance. This score directly controls how many positions can be open and how aggressively they are sized. Every score is recorded on-chain.",
    },
    {
      q: "Can I audit the agent's past decisions?",
      a: "Yes. Every decision is stored as a checkpoint in a JSONL log and anchored on-chain. You can inspect the regime, signals, confidence score, Kelly-sized position, EIP-712 signature hash, and final PnL for any trade the agent has ever made.",
    },
  ];

  const [open, setOpen] = useState<number | null>(null);

  return (
    <section id="faq" className="relative px-4 sm:px-6 md:px-12 py-16 md:py-24 bg-gray-50">
      <div className="max-w-3xl mx-auto">
        <h2 className="text-2xl sm:text-3xl font-bold text-center mb-4 text-gray-900">Frequently Asked Questions</h2>
        <p className="text-center text-gray-400 max-w-xl mx-auto mb-10 md:mb-14 text-sm sm:text-base leading-relaxed">
          Everything you need to know about how Quasar works.
        </p>
        <div className="space-y-2 md:space-y-3">
          {faqs.map((faq, i) => (
            <div key={i} className="bg-white border border-gray-100 rounded-2xl overflow-hidden">
              <button
                onClick={() => setOpen(open === i ? null : i)}
                className="w-full flex items-center justify-between px-4 sm:px-6 py-4 sm:py-5 text-left hover:bg-gray-50 transition"
              >
                <span className="font-semibold text-gray-900 text-sm sm:text-base pr-4">{faq.q}</span>
                <span className={`flex-shrink-0 transition-transform duration-200 ${open === i ? 'rotate-90' : ''}`}>
                  <ChevronRight size={18} className="text-gray-400" />
                </span>
              </button>
              {open === i && (
                <div className="px-4 sm:px-6 pb-5">
                  <p className="text-gray-500 text-sm leading-relaxed">{faq.a}</p>
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

function CTA() {
  return (
    <section className="relative px-4 sm:px-6 md:px-12 py-16 md:py-24 bg-white">
      <div className="max-w-4xl mx-auto text-center">
        <h2 className="text-3xl sm:text-4xl font-bold text-gray-900 mb-5 md:mb-6 leading-tight">
          Every decision.<br />On the record.
        </h2>
        <p className="text-base md:text-lg text-gray-400 mb-10 md:mb-12 max-w-md mx-auto">
          Access the live dashboard and verify every trade on-chain.
        </p>
        <div className="flex flex-wrap justify-center gap-3 md:gap-4">
          <a href="https://sepolia.etherscan.io/address/0x26691C1e42aB79416FEa3AaAed240e7751bF9f6F" target="_blank" rel="noopener noreferrer"
            className="btn-slide btn-slide-dark bg-black text-white px-7 md:px-8 py-3.5 md:py-4 rounded-full font-bold text-sm md:text-base transition inline-flex items-center gap-2 active:scale-95">
            <span>On-Chain Activity</span>
            <ArrowRight size={18} />
          </a>
          <a href="https://early.surge.xyz/discovery/quasar?ref=rqkM2dQEqKW2puaPZd6ob" target="_blank" rel="noopener noreferrer"
            className="btn-slide btn-slide-border border border-gray-200 text-gray-600 px-7 md:px-8 py-3.5 md:py-4 rounded-full text-sm md:text-base transition">
            View Surge Profile
          </a>
          <a href="https://github.com/basilgoodluck/quasar" target="_blank" rel="noopener noreferrer"
            className="btn-slide btn-slide-border border border-gray-200 text-gray-600 px-7 md:px-8 py-3.5 md:py-4 rounded-full text-sm md:text-base transition">
            View Code
          </a>
        </div>
      </div>
    </section>
  );
}

function Footer() {
  const ref = React.useRef(null);
  const isInView = useInView(ref, { once: true, amount: 0.2 });

  const productLinks = [
    { text: "Dashboard", href: "/overview" },
    { text: "Trades", href: "/trades" },
    { text: "Risk", href: "/risk" },
  ];

  const stack = [
    "FastAPI · asyncpg · Redis",
    "Authlib · Docker · VPS",
    "Kraken CLI · Binance WS",
    "Web3.py · EIP-712 · ERC-8004",
    "LSTM · TypeScript · Next.js",
  ];

  const social = [
    { Icon: FaGithub, label: "GitHub", href: "https://github.com/basilgoodluck/quasar" },
    { Icon: FaLinkedin, label: "LinkedIn", href: "https://www.linkedin.com/in/goodluck-basil" },
    { Icon: FaEnvelope, label: "Email", href: "mailto:basilgoodluck22@gmail.com" },
    { Icon: FiExternalLink, label: "Surge", href: "https://early.surge.xyz/discovery/quasar?ref=rqkM2dQEqKW2puaPZd6ob" },
  ];

  return (
    <footer ref={ref} className="relative py-14 md:py-20 text-gray-500 border-t border-gray-100 bg-white">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex flex-col lg:flex-row gap-10 lg:gap-20">
          <motion.div
            initial={{ opacity: 0, x: -60 }}
            animate={isInView ? { opacity: 1, x: 0 } : {}}
            transition={{ duration: 0.4 }}
            className="flex-shrink-0"
          >
            <div className="flex items-center gap-3 mb-6">
              <div className="w-10 h-10 bg-blue-600 rounded-full flex items-center justify-center">
                <span className="text-white font-bold text-sm">Q</span>
              </div>
              <span className="text-gray-900 font-bold tracking-wide text-2xl">Quasar</span>
            </div>
            <div className="flex gap-5">
              {social.map((s, index) => (
                <a 
                  key={index} 
                  href={s.href} 
                  target="_blank" 
                  rel="noopener noreferrer"
                  className="text-gray-400 hover:text-gray-900 transition-colors"
                  aria-label={s.label}
                >
                  <s.Icon size={22} />
                </a>
              ))}
            </div>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 50 }}
            animate={isInView ? { opacity: 1, y: 0 } : {}}
            transition={{ duration: 0.4, delay: 0.1 }}
            // Changed from sm:flex-row — fires too early at 640px when combined with parent stacking
            className="flex flex-col sm:flex-row gap-8 md:gap-10 lg:gap-16 flex-1"
          >
            <div>
              <div className="text-blue-600 uppercase tracking-widest text-xs font-bold mb-4 md:mb-5">Product</div>
              <ul className="space-y-3">
                {productLinks.map((link) => (
                  <li key={link.text}>
                    <Link href={link.href} className="text-gray-400 hover:text-gray-900 transition-colors text-sm">
                      {link.text}
                    </Link>
                  </li>
                ))}
              </ul>
            </div>

            <div>
              <div className="text-blue-600 uppercase tracking-widest text-xs font-bold mb-4 md:mb-5">Stack</div>
              <div className="space-y-2 text-sm text-gray-400">
                {stack.map((s, i) => (
                  <div key={i}>{s}</div>
                ))}
              </div>
            </div>
          </motion.div>
        </div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={isInView ? { opacity: 1, y: 0 } : {}}
          transition={{ duration: 0.4, delay: 0.5 }}
          className="mt-12 md:mt-16 pt-8 border-t border-gray-100 flex flex-col sm:flex-row justify-between items-center gap-3 text-xs sm:text-sm text-gray-400 text-center sm:text-left"
        >
          <p>© 2026 Quasar. All rights reserved.</p>
          <p>Trading involves risk. Use at your own discretion.</p>
        </motion.div>
      </div>
    </footer>
  );
}

export default function Home() {
  return (
    <>
      <SEO />
      <main className="bg-white text-gray-900 min-h-screen overflow-x-hidden">
        <Header />
        <Hero />
        <HowItWorks />
        <MarketRegimes />
        <Features />
        <LSTMSection />
        <RiskManagement />
        <WhyQuasar />
        <FAQ />
        <CTA />
        <Footer />
      </main>
    </>
  );
}