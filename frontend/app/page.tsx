"use client";
import React, { useState, useEffect, useRef } from 'react';
import { Menu, X, ArrowRight, Check, Shield, Zap, Eye, Brain, TrendingUp, Lock, Activity, ChevronRight } from 'lucide-react';
import { motion, useInView } from 'framer-motion';
import Link from 'next/link';
import Head from 'next/head';
import { BASE_URL } from '@/lib/api';
import landingData from '@/data/landing.json';

const NAV_HEIGHT = 74;

function SEO() {
  return (
    <Head>
      <title>Quasar – On-Chain AI Trading Agent | Verifiable, Transparent, Self-Improving</title>
      <meta name="description" content="Quasar is a trustless on-chain AI trading agent. It classifies market regimes, uses EMA and Fisher Transform signals, trains an LSTM model on its own decisions, enforces risk via smart contracts, and uses a reputation scoring system to dynamically control exposure. Every action is EIP-712 signed and verifiable on Sepolia." />
      <meta name="keywords" content="on-chain trading agent, AI trading bot, EIP-712, smart contract trading, LSTM trading model, Kelly criterion, reputation scoring, verifiable trading, DeFi agent, Sepolia testnet, transparent trading" />
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
    { href: "#contracts", label: "Contracts" },
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
        className="fixed top-0 left-0 right-0 z-50 px-6 md:px-12 bg-white/80 backdrop-blur-md border-b border-gray-200 flex items-center"
      >
        <div className="w-full mx-auto flex items-center justify-between">
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
          <div className="hidden md:flex items-center space-x-16">
            <motion.div
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.08, duration: 0.25 }}
              className="flex items-center space-x-10"
            >
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
            </motion.div>
            <motion.a
              href={`${BASE_URL}/auth/google`}
              initial={{ opacity: 0, scale: 0.8 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: 0.18, duration: 0.25 }}
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              className="btn-slide btn-slide-dark bg-black text-white px-7 py-3 rounded-full font-bold text-base transition"
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
          <a href={`${BASE_URL}/auth/google`}
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
      className="relative px-4 sm:px-6 md:px-12 flex flex-col justify-center overflow-hidden"
      style={{ minHeight: `calc(100vh - ${NAV_HEIGHT}px)`, marginTop: NAV_HEIGHT, background: '#0a0a0f' }}
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

      <div className="max-w-4xl mx-auto relative z-10 w-full">
        <div className="text-center">
          <h1 className="text-3xl sm:text-4xl font-bold mb-4">
            <span className="text-blue-600">On-Chain</span> <span className="text-white">AI Trading</span>
          </h1>
          <h2 className="text-4xl font-black mb-8 text-white relative inline-block h-[1.2em] overflow-hidden mx-auto">
            <span className="invisible">{longestWord}</span>
            <span key={currentIndex} className="absolute inset-0 flex items-center justify-center animate-slideUp">
              <span className="relative inline-block">
                {words[currentIndex]}
                <span className="absolute -bottom-1 left-0 w-full h-1 bg-blue-600 transform -skew-x-12" />
              </span>
            </span>
          </h2>
          <p className="text-lg text-gray-400 max-w-2xl mb-10 leading-relaxed mx-auto">
            A trustless trading agent that classifies market regimes, learns from its own decisions via LSTM, and enforces every trade through EIP-712 signed smart contract risk controls. Every decision is verifiable. Nothing is a black box.
          </p>
          <div className="flex flex-wrap gap-4 justify-center">
            <a href={`${BASE_URL}/auth/google`}
              className="btn-slide btn-slide-dark bg-white text-black px-8 py-4 rounded-full font-bold text-base transition active:scale-95">
              View Live Agent →
            </a>
            <a href="#contracts"
              className="btn-slide btn-slide-border border border-gray-700 text-gray-400 px-8 py-4 rounded-full text-base transition">
              On-Chain Activity
            </a>
          </div>
          <div className="flex gap-10 mt-14 pt-10 border-t border-gray-800 justify-center">
            {landingData.heroStats.map((s: any) => (
              <div key={s.label}>
                <div className="text-xl text-blue-400 font-bold">{s.value}</div>
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
    <section id="how" className="relative px-4 sm:px-6 md:px-12 py-24 bg-white">
      <div className="max-w-7xl mx-auto">
        <h2 className="text-3xl font-bold text-center mb-4 text-gray-900">How It Works</h2>
        <p className="text-center text-gray-400 max-w-xl mx-auto mb-16 text-base leading-relaxed">
          Quasar operates a fully auditable decision pipeline — from raw market data to an on-chain checkpoint — with no human intervention required.
        </p>
        <div className="grid md:grid-cols-2 gap-8 md:gap-16 items-start">
          <div className="relative flex justify-center order-2 md:order-1">
            <div className="w-full bg-gray-50 rounded-2xl border border-gray-200 p-6 text-sm font-mono">
              {["TradeDecision", "TradeIntent", "EIP-712 Signature", "RiskRouter Validation", "Execution", "Checkpoint"].map((s, i, arr) => (
                <div key={s}>
                  <div className="flex items-center gap-3 py-3">
                    <div className="w-7 h-7 rounded-full border border-blue-200 bg-blue-50 flex items-center justify-center text-blue-600 text-xs font-bold flex-shrink-0">
                      {String(i + 1).padStart(2, '0')}
                    </div>
                    <span className="text-gray-700 text-base">{s}</span>
                  </div>
                  {i < arr.length - 1 && <div className="ml-3 text-blue-300 text-lg">↓</div>}
                </div>
              ))}
            </div>
          </div>
          <div className="flex flex-col space-y-10 order-1 md:order-2">
            {steps.map((step: any, index: number) => (
              <div key={index} className="flex gap-5 flex-col">
                <div className="flex items-baseline gap-4 text-2xl text-gray-200 leading-none font-black">
                  {step.number}.
                  <h3 className="text-xl font-semibold text-gray-700">{step.title}</h3>
                </div>
                <div className="pl-10">
                  <p className="text-base text-gray-400 leading-relaxed">{step.description}</p>
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
      description: "Strong directional momentum. Quasar increases conviction on EMA continuation signals and sizes positions more aggressively within Kelly limits.",
      signals: ["EMA crossover confirmed", "ADX > 25", "Low mean-reversion probability"],
      color: "blue",
    },
    {
      name: "Volatile",
      description: "High price variance with no clear direction. Position sizes are reduced and frequency controls tighten. The agent waits for confirmation before acting.",
      signals: ["ATR spike detected", "Fisher Transform neutral", "Drawdown guard active"],
      color: "yellow",
    },
    {
      name: "Trending Volatile",
      description: "Momentum exists but with elevated noise. EMA signals are weighted lower. Fisher Transform reversals are monitored closely for early exit triggers.",
      signals: ["EMA signal present", "ATR elevated", "Hybrid risk model active"],
      color: "purple",
    },
    {
      name: "Ranging",
      description: "Sideways price action. Trend signals are ignored. The agent focuses on mean-reversion opportunities and reduces trade frequency significantly.",
      signals: ["ADX < 20", "Price within Bollinger bands", "Minimal EMA divergence"],
      color: "gray",
    },
  ];

  return (
    <section className="relative px-4 sm:px-6 md:px-12 py-24 bg-gray-50">
      <div className="max-w-7xl mx-auto">
        <h2 className="text-3xl font-bold text-center mb-4 text-gray-900">Market Regime Classification</h2>
        <p className="text-center text-gray-400 max-w-xl mx-auto mb-16 text-base leading-relaxed">
          Before evaluating any signal, Quasar classifies the current market into one of four regimes and adapts its entire strategy accordingly.
        </p>
        <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-6">
          {regimes.map((r) => (
            <div key={r.name} className="bg-white rounded-2xl border border-gray-100 p-6 flex flex-col gap-4">
              <h3 className="font-bold text-gray-900 text-base">{r.name}</h3>
              <p className="text-sm text-gray-500 leading-relaxed flex-1">{r.description}</p>
              <div className="flex flex-col gap-2">
                {r.signals.map(sig => (
                  <span key={sig} className="text-xs font-medium px-2 py-1 rounded-md bg-gray-100 text-gray-600">{sig}</span>
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
    <section id="features" className="relative px-4 sm:px-6 md:px-12 py-24 bg-white">
      <div className="max-w-6xl mx-auto relative z-10 space-y-10">
        <h2 className="text-3xl text-center font-bold mb-4 text-gray-900">
          ...your trades are on the record
        </h2>
        <p className="text-center text-gray-400 max-w-xl mx-auto mb-10 text-base leading-relaxed">
          Every action Quasar takes is logged, signed, and anchored on-chain. Audit any decision at any time — no dashboards that hide the truth.
        </p>
        <div className="flex flex-col lg:flex-row items-center justify-center gap-10 lg:gap-16">
          <div className="flex-1 w-full max-w-md space-y-7">
            {features.map((feature: string, index: number) => (
              <div key={index} className="flex items-center space-x-4">
                <div className="w-7 h-7 flex-shrink-0 bg-blue-600 rounded-full flex items-center justify-center">
                  <Check size={15} className="text-white" />
                </div>
                <span className="text-lg text-gray-700">{feature}</span>
              </div>
            ))}
          </div>
          <div className="flex-1 w-full max-w-md bg-gray-50 rounded-2xl border border-gray-200 overflow-hidden">
            <div className="px-5 py-3 border-b border-gray-200 bg-white">
              <span className="text-sm text-gray-400 font-mono">checkpoints.jsonl</span>
            </div>
            <div className="p-5 font-mono text-sm space-y-3">
              {[
                { action: "BUY", pair: "BTCUSDT", conf: 0.81, status: "WIN", pnl: "+$22.78", regime: "trending" },
                { action: "HOLD", pair: "ETHUSDT", conf: 0.44, status: "SKIP", pnl: "—", regime: "volatile" },
                { action: "SELL", pair: "BTCUSDT", conf: 0.76, status: "WIN", pnl: "+$11.20", regime: "trending" },
              ].map((r, i) => (
                <div key={i} className="border border-gray-200 rounded-xl p-4 space-y-2 bg-white">
                  <div className="flex justify-between text-base">
                    <span className="text-gray-900 font-bold">{r.action}</span>
                    <span className="text-gray-500">{r.pair}</span>
                    <span className="text-gray-500 font-semibold">{r.status}</span>
                  </div>
                  <div className="flex gap-4 text-gray-400 text-sm flex-wrap">
                    <span>regime <span className="text-gray-600 font-semibold">{r.regime}</span></span>
                    <span>conf <span className="text-gray-600 font-semibold">{r.conf}</span></span>
                    <span>pnl <span className="text-gray-700 font-semibold">{r.pnl}</span></span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
        <div className="md:w-4/5 mx-auto space-y-10 flex flex-col items-center mt-16">
          <h3 className="text-center text-2xl text-gray-700 px-4 font-medium">
            Every decision signed. Every trade verifiable. Every outcome recorded on-chain.
          </h3>
          <a href={`${BASE_URL}/auth/google`}
            className="btn-slide btn-slide-dark bg-black text-white px-10 py-4 rounded-full font-bold text-base transition inline-flex items-center gap-2 active:scale-95">
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
    <section className="relative px-4 sm:px-6 md:px-12 py-24 bg-gray-50">
      <div className="max-w-7xl mx-auto">
        <h2 className="text-3xl font-bold text-center mb-4 text-gray-900">Risk Management</h2>
        <p className="text-center text-gray-400 max-w-xl mx-auto mb-16 text-base leading-relaxed">
          Quasar enforces strict risk controls at every layer — from position sizing to on-chain smart contract gates — so capital preservation is never optional.
        </p>
        <div className="grid md:grid-cols-3 gap-8">
          <div className="bg-white rounded-2xl border border-gray-100 p-8">
            <div className="w-10 h-10 bg-blue-600 rounded-full flex items-center justify-center mb-5">
              <TrendingUp size={20} className="text-white" />
            </div>
            <h3 className="text-lg font-bold text-gray-900 mb-3">Kelly Criterion Sizing</h3>
            <p className="text-gray-500 text-sm leading-relaxed">
              Each position size is derived from the Kelly formula — balancing expected return against variance to maximise long-run growth without risking ruin. A fractional Kelly is applied for added conservatism.
            </p>
          </div>
          <div className="bg-white rounded-2xl border border-gray-100 p-8">
            <div className="w-10 h-10 bg-blue-600 rounded-full flex items-center justify-center mb-5">
              <Shield size={20} className="text-white" />
            </div>
            <h3 className="text-lg font-bold text-gray-900 mb-3">Drawdown Limits</h3>
            <p className="text-gray-500 text-sm leading-relaxed">
              Hard drawdown limits are enforced at the model level and again at the RiskRouter smart contract level. No single bad run can compromise the account — both gates must pass before any trade executes.
            </p>
          </div>
          <div className="bg-white rounded-2xl border border-gray-100 p-8">
            <div className="w-10 h-10 bg-blue-600 rounded-full flex items-center justify-center mb-5">
              <Activity size={20} className="text-white" />
            </div>
            <h3 className="text-lg font-bold text-gray-900 mb-3">Trade Frequency Controls</h3>
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
    <section className="relative px-4 sm:px-6 md:px-12 py-24 bg-white">
      <div className="max-w-7xl mx-auto">
        <div className="grid md:grid-cols-2 gap-16 items-center">
          <div>
            <h2 className="text-3xl font-bold text-gray-900 mb-5">An agent that learns from its own history</h2>
            <p className="text-gray-500 text-base leading-relaxed mb-6">
              After each trading session, Quasar retrains its LSTM model on a combined dataset of its own past decisions, their outcomes, and freshly scraped market data. The result is a model that improves with every iteration — not just on backtests, but on its live performance.
            </p>
            <ul className="space-y-4">
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
          <div className="bg-gray-50 rounded-2xl border border-gray-200 p-6 font-mono text-sm">
            <div className="text-gray-400 mb-4 text-xs uppercase tracking-widest">Training loop (simplified)</div>
            <div className="space-y-3">
              <div className="flex gap-3">
                <span className="text-blue-400">1</span>
                <span className="text-gray-600">Load checkpoint history + outcomes</span>
              </div>
              <div className="flex gap-3">
                <span className="text-blue-400">2</span>
                <span className="text-gray-600">Scrape latest market features</span>
              </div>
              <div className="flex gap-3">
                <span className="text-blue-400">3</span>
                <span className="text-gray-600">Merge into training dataset</span>
              </div>
              <div className="flex gap-3">
                <span className="text-blue-400">4</span>
                <span className="text-gray-600">Retrain LSTM on full sequence</span>
              </div>
              <div className="flex gap-3">
                <span className="text-blue-400">5</span>
                <span className="text-gray-600">Validate on held-out period</span>
              </div>
              <div className="flex gap-3">
                <span className="text-blue-400">6</span>
                <span className="text-gray-600">Deploy updated model weights</span>
              </div>
              <div className="flex gap-3">
                <span className="text-blue-400">7</span>
                <span className="text-gray-600">Update confidence thresholds</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}

function ReputationScore() {
  const components = [
    {
      label: "Win Rate",
      weight: "40%",
      description: "Overall accuracy across the last 100 resolved trades. The baseline signal of whether the agent's decisions are profitable.",
      bar: 78,
    },
    {
      label: "Decision Consistency",
      weight: "40%",
      description: "Measures reliability when operating with high confidence. Incorrect high-confidence calls are penalised more heavily than low-confidence misses.",
      bar: 64,
    },
    {
      label: "Streak Component",
      weight: "20%",
      description: "Rewards sustained performance over time. A winning streak boosts the score; a losing streak reduces it, encouraging stable execution over erratic bursts.",
      bar: 55,
    },
  ];

  return (
    <section className="relative px-4 sm:px-6 md:px-12 py-24 bg-gray-50">
      <div className="max-w-7xl mx-auto">
        <div className="grid md:grid-cols-2 gap-16 items-start">
          <div>
            <h2 className="text-3xl font-bold text-gray-900 mb-5">Performance earns trust. Trust earns exposure.</h2>
            <p className="text-gray-500 text-base leading-relaxed mb-8">
              Before every trade, Quasar evaluates its own recent performance and assigns a reputation score between 0.0 and 1.0. This score directly controls how aggressively the agent is allowed to participate — low reputation reduces exposure, high reputation unlocks it.
            </p>
            <div className="space-y-6">
              {components.map((c) => (
                <div key={c.label}>
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm font-semibold text-gray-800">{c.label}</span>
                    <span className="text-xs text-gray-400 font-mono">{c.weight} weight</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-1.5 mb-2">
                    <div className="bg-gray-700 h-1.5 rounded-full" style={{ width: `${c.bar}%` }} />
                  </div>
                  <p className="text-xs text-gray-400 leading-relaxed">{c.description}</p>
                </div>
              ))}
            </div>
          </div>
          <div className="flex flex-col gap-5">
            <div className="bg-white rounded-2xl border border-gray-200 p-6">
              <div className="text-xs text-gray-400 uppercase tracking-widest font-semibold mb-4">Current reputation score</div>
              <div className="flex items-end gap-4 mb-4">
                <span className="text-5xl font-black text-gray-900">0.74</span>
                <span className="text-sm text-gray-400 mb-2">/ 1.0</span>
              </div>
              <div className="w-full bg-gray-100 rounded-full h-2 mb-4">
                <div className="bg-gray-700 h-2 rounded-full" style={{ width: '74%' }} />
              </div>
              <div className="grid grid-cols-3 gap-3 text-center">
                <div className="bg-gray-50 rounded-xl p-3">
                  <div className="text-sm font-bold text-gray-900">78%</div>
                  <div className="text-xs text-gray-400 mt-0.5">Win rate</div>
                </div>
                <div className="bg-gray-50 rounded-xl p-3">
                  <div className="text-sm font-bold text-gray-900">0.81</div>
                  <div className="text-xs text-gray-400 mt-0.5">Consistency</div>
                </div>
                <div className="bg-gray-50 rounded-xl p-3">
                  <div className="text-sm font-bold text-gray-900">+6</div>
                  <div className="text-xs text-gray-400 mt-0.5">Win streak</div>
                </div>
              </div>
            </div>
            <div className="bg-white rounded-2xl border border-gray-200 p-6">
              <div className="text-xs text-gray-400 uppercase tracking-widest font-semibold mb-5">How score controls behaviour</div>
              <div className="space-y-4">
                {[
                  { range: "0.0 – 0.4", label: "Restricted", desc: "Minimal exposure. 1 concurrent position max. Smallest Kelly fraction." },
                  { range: "0.4 – 0.7", label: "Moderate", desc: "Standard participation. 2–3 positions. Normal Kelly sizing." },
                  { range: "0.7 – 1.0", label: "Full access", desc: "Unrestricted positions. Scaled Kelly. Aggressive participation allowed." },
                ].map((tier) => (
                  <div key={tier.range} className="flex items-start gap-3">
                    <span className="text-xs font-bold px-2 py-1 rounded-md flex-shrink-0 bg-gray-100 text-gray-600">{tier.range}</span>
                    <div>
                      <div className="text-sm font-semibold text-gray-800">{tier.label}</div>
                      <div className="text-xs text-gray-400 mt-0.5">{tier.desc}</div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
            <div className="bg-white rounded-2xl border border-gray-200 p-5 flex items-start gap-3">
              <Lock size={16} className="text-blue-600 flex-shrink-0 mt-0.5" />
              <p className="text-sm text-gray-500 leading-relaxed">
                Each score is recorded locally and submitted on-chain, creating a verifiable performance history. The system stays inactive until a minimum trade count is reached — ensuring all metrics are based on sufficient data.
              </p>
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
    <section className="relative px-4 sm:px-6 md:px-12 py-24 bg-white">
      <div className="max-w-2xl mx-auto relative z-10">
        <h2 className="text-3xl font-bold text-center mb-4 text-gray-900">Why Quasar?</h2>
        <p className="text-center text-gray-400 max-w-xl mx-auto mb-16 text-base leading-relaxed">
          Most trading bots are black boxes. Quasar is built from the ground up to be auditable, accountable, and self-correcting.
        </p>
        <div className="space-y-14">
          {reasons.map((r: any, i: number) => {
            const Icon = r.icon === "Shield" ? Shield : r.icon === "Zap" ? Zap : Eye;
            return (
              <div key={i} className="flex items-start space-x-6">
                <div className="flex-shrink-0 w-12 h-12 bg-blue-600 rounded-full flex items-center justify-center">
                  <Icon size={22} className="text-white" />
                </div>
                <div>
                  <h3 className="text-xl font-bold text-gray-900 mb-3">{r.title}</h3>
                  <p className="text-base text-gray-500 leading-relaxed">{r.description}</p>
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
      a: "Quasar is a trustless on-chain AI trading agent. It analyses market conditions, classifies regimes, generates signals using EMA and Fisher Transform, and executes trades governed by smart contract risk controls — with every decision signed and logged on-chain.",
    },
    {
      q: "How does Quasar classify market regimes?",
      a: "Quasar uses a combination of ADX, ATR, and EMA divergence to categorise each market window as trending, volatile, trending-volatile, or ranging. The regime determines which signals are trusted, how positions are sized, and how aggressively the agent trades.",
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
      a: "Before every trade, Quasar analyses its last 100 resolved trades and assigns a reputation score between 0.0 and 1.0. The score combines win rate, decision consistency (penalising incorrect high-confidence calls more heavily), and a streak component that rewards sustained performance. This score directly controls how many positions can be open concurrently and how aggressively positions are sized. Low reputation enforces restricted activity; high reputation unlocks full participation. Every score is recorded on-chain.",
    },
    {
      q: "Is Quasar live on mainnet?",
      a: "Quasar is currently live on the Sepolia testnet. You can view all contract activity and signed checkpoints on Sepolia Etherscan. Mainnet deployment is planned following an extended testnet validation period.",
    },
    {
      q: "Can I audit the agent's past decisions?",
      a: "Yes. Every decision is stored as a checkpoint in a JSONL log and anchored on-chain. You can inspect the regime, signals, confidence score, Kelly-sized position, EIP-712 signature hash, and final PnL for any trade the agent has ever made.",
    },
  ];

  const [open, setOpen] = useState<number | null>(null);

  return (
    <section id="faq" className="relative px-4 sm:px-6 md:px-12 py-24 bg-gray-50">
      <div className="max-w-3xl mx-auto">
        <h2 className="text-3xl font-bold text-center mb-4 text-gray-900">Frequently Asked Questions</h2>
        <p className="text-center text-gray-400 max-w-xl mx-auto mb-14 text-base leading-relaxed">
          Everything you need to know about how Quasar works.
        </p>
        <div className="space-y-3">
          {faqs.map((faq, i) => (
            <div key={i} className="bg-white border border-gray-100 rounded-2xl overflow-hidden">
              <button
                onClick={() => setOpen(open === i ? null : i)}
                className="w-full flex items-center justify-between px-6 py-5 text-left"
              >
                <span className="font-semibold text-gray-900 text-base">{faq.q}</span>
                <span className={`ml-4 flex-shrink-0 transition-transform duration-200 ${open === i ? 'rotate-90' : ''}`}>
                  <ChevronRight size={18} className="text-gray-400" />
                </span>
              </button>
              {open === i && (
                <div className="px-6 pb-5">
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
    <section className="relative px-4 sm:px-6 md:px-12 py-24 bg-white">
      <div className="max-w-4xl mx-auto text-center relative z-10">
        <h2 className="text-4xl font-bold text-gray-900 mb-6">
          Every decision.<br />On the record.
        </h2>
        <p className="text-lg text-gray-400 mb-12">
          Access the live dashboard, inspect checkpoints, and verify every trade on-chain.
        </p>
        <div className="flex flex-wrap justify-center gap-4">
          <a href={`${BASE_URL}/auth/google`}
            className="btn-slide btn-slide-dark bg-black text-white px-10 py-4 rounded-full font-bold text-base transition inline-flex items-center gap-2 active:scale-95">
            <span>View Checkpoints</span>
            <ArrowRight size={18} />
          </a>
          <a href="https://sepolia.etherscan.io/address/0xd6A6952545FF6E6E6681c2d15C59f9EB8F40FdBC" target="_blank" rel="noopener noreferrer"
            className="btn-slide btn-slide-border border border-gray-200 text-gray-600 px-10 py-4 rounded-full text-base transition">
            View Contract
          </a>
          <a href="https://github.com" target="_blank" rel="noopener noreferrer"
            className="btn-slide btn-slide-border border border-gray-200 text-gray-600 px-10 py-4 rounded-full text-base transition">
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
  const productLinks = landingData.productLinks;
  const CONTRACTS = landingData.contracts;
  return (
    <footer id="contracts" ref={ref} className="relative py-24 text-gray-500 overflow-hidden border-t border-gray-100 bg-white">
      <div className="relative z-10 max-w-7xl mx-auto px-6 lg:px-8">
        <div className="flex flex-col lg:flex-row lg:justify-between gap-14 lg:gap-20">
          <motion.div
            initial={{ opacity: 0, x: -60 }}
            animate={isInView ? { opacity: 1, x: 0 } : {}}
            transition={{ duration: 0.4 }}
            className="flex items-center gap-3 flex-shrink-0"
          >
            <div className="w-10 h-10 bg-blue-600 rounded-full flex items-center justify-center">
              <span className="text-white font-bold text-sm">Q</span>
            </div>
            <span className="text-gray-900 font-bold tracking-wide text-xl">Quasar</span>
          </motion.div>
          <motion.div
            initial={{ opacity: 0, y: 50 }}
            animate={isInView ? { opacity: 1, y: 0 } : {}}
            transition={{ duration: 0.4, delay: 0.1 }}
            className="flex flex-col sm:flex-row gap-16 lg:gap-24"
          >
            <ul className="space-y-4 text-sm">
              {productLinks.map((link: any, i: number) => (
                <motion.li key={link.text}
                  initial={{ opacity: 0, x: -30 }}
                  animate={isInView ? { opacity: 1, x: 0 } : {}}
                  transition={{ duration: 0.35, delay: 0.15 + i * 0.05 }}>
                  <Link href={link.href} className="hover:text-gray-900 transition-colors text-base">{link.text}</Link>
                </motion.li>
              ))}
            </ul>
            <div className="text-sm">
              <div className="text-blue-600 uppercase tracking-widest text-xs font-bold mb-5">Contracts · Sepolia</div>
              <div className="space-y-3">
                {CONTRACTS.map((c: any, i: number) => (
                  <motion.div key={c.label}
                    initial={{ opacity: 0, x: -30 }}
                    animate={isInView ? { opacity: 1, x: 0 } : {}}
                    transition={{ duration: 0.35, delay: 0.2 + i * 0.05 }}
                    className="flex justify-between gap-10">
                    <a href={c.href} target="_blank" rel="noopener noreferrer" className="text-gray-400 hover:text-gray-900 transition-colors text-base">{c.label}</a>
                    <span className="text-gray-300 text-base">{c.address}</span>
                  </motion.div>
                ))}
              </div>
            </div>
            <div className="text-sm space-y-3">
              <div className="text-blue-600 uppercase tracking-widest text-xs font-bold mb-5">Stack</div>
              {["FastAPI · asyncpg · Redis", "Authlib · Docker · AWS EC2", "Kraken API · Binance WS", "Web3.py · EIP-712 · ERC-8004", "PyTorch · LSTM · scikit-learn"].map(s => (
                <div key={s} className="text-gray-400 text-base">{s}</div>
              ))}
            </div>
          </motion.div>
        </div>
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={isInView ? { opacity: 1, y: 0 } : {}}
          transition={{ duration: 0.4, delay: 0.5 }}
          className="mt-20 pt-8 border-t border-gray-100 flex flex-col md:flex-row justify-between items-center gap-4"
        >
          <p className="text-gray-300 text-sm">© 2025 Quasar. All rights reserved.</p>
          <p className="text-gray-300 text-sm">Trading involves risk. Use at your own discretion.</p>
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
        <ReputationScore />
        <WhyQuasar />
        <FAQ />
        <CTA />
        <Footer />
      </main>
    </>
  );
}