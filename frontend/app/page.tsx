"use client";
import React, { useState, useEffect, useRef } from 'react';
import { Menu, X, ArrowRight, Check, Shield, Zap, Eye } from 'lucide-react';
import { motion, useInView } from 'framer-motion';
import Link from 'next/link';
import { BASE_URL } from '@/lib/api';
import landingData from '@/data/landing.json';

const NAV_HEIGHT = 74;

function Header() {
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const navLinks = [
    { href: "#how", label: "How It Works" },
    { href: "#features", label: "Features" },
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
          <div className="inline-flex items-center gap-2 bg-blue-50 border border-blue-200 rounded-full px-4 py-1.5 mb-8">
            <span className="w-2 h-2 bg-blue-600 rounded-full animate-pulse" />
            <span className="text-blue-700 text-sm font-semibold tracking-widest uppercase">Live on Sepolia</span>
          </div>
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
            Rule-based trading agent with on-chain identity, EIP-712 signed decisions, and smart contract risk enforcement. Every trade is verifiable. Nothing is a black box.
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
        <h3 className="text-3xl font-bold text-center mb-16 text-gray-900">How It Works</h3>
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
                  <h4 className="text-xl font-semibold text-gray-700">{step.title}</h4>
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

function Features() {
  const features = landingData.features;
  return (
    <section id="features" className="relative px-4 sm:px-6 md:px-12 py-24 bg-white">
      <div className="absolute -bottom-40 -left-40 w-[600px] h-[600px] pointer-events-none">
        <div className="w-full h-full bg-gradient-to-tr from-blue-500/20 via-purple-500/10 to-transparent blur-3xl" />
      </div>
      <div className="max-w-6xl mx-auto relative z-10 space-y-10">
        <h3 className="text-3xl text-center font-bold mb-10 text-gray-900">
          ...your trades are on the record
        </h3>
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
                { action: "BUY", pair: "BTCUSDT", conf: 0.81, status: "WIN", pnl: "+$22.78" },
                { action: "HOLD", pair: "ETHUSDT", conf: 0.44, status: "SKIP", pnl: "—" },
                { action: "SELL", pair: "BTCUSDT", conf: 0.76, status: "WIN", pnl: "+$11.20" },
              ].map((r, i) => (
                <div key={i} className="border border-gray-200 rounded-xl p-4 space-y-2 bg-white">
                  <div className="flex justify-between text-base">
                    <span className={r.action === "BUY" ? "text-blue-600 font-bold" : r.action === "SELL" ? "text-red-500 font-bold" : "text-gray-400 font-bold"}>{r.action}</span>
                    <span className="text-gray-500">{r.pair}</span>
                    <span className={r.status === "WIN" ? "text-blue-600 font-semibold" : "text-gray-400"}>{r.status}</span>
                  </div>
                  <div className="flex gap-4 text-gray-400 text-sm">
                    <span>conf <span className="text-purple-500 font-semibold">{r.conf}</span></span>
                    <span>pnl <span className="text-blue-600 font-semibold">{r.pnl}</span></span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
        <div className="md:w-4/5 mx-auto space-y-10 flex flex-col items-center mt-16">
          <h4 className="text-center text-2xl text-gray-700 px-4 font-medium">
            Every decision signed. Every trade verifiable. Every outcome recorded on-chain.
          </h4>
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

function WhyQuasar() {
  const reasons = landingData.whyQuasarReasons;
  return (
    <section className="relative px-4 sm:px-6 md:px-12 py-24 bg-white">
      <div className="absolute -bottom-40 -right-40 w-[600px] h-[600px] pointer-events-none">
        <div className="w-full h-full bg-gradient-to-tl from-blue-500/10 to-transparent blur-3xl" />
      </div>
      <div className="max-w-2xl mx-auto relative z-10">
        <h3 className="text-3xl font-bold text-center mb-20 text-gray-900">Why Quasar?</h3>
        <div className="space-y-14">
          {reasons.map((r: any, i: number) => {
            const Icon = r.icon === "Shield" ? Shield : r.icon === "Zap" ? Zap : Eye;
            return (
              <div key={i} className="flex items-start space-x-6">
                <div className="flex-shrink-0 w-12 h-12 bg-blue-600 rounded-full flex items-center justify-center">
                  <Icon size={22} className="text-white" />
                </div>
                <div>
                  <h4 className="text-xl font-bold text-gray-900 mb-3">{r.title}</h4>
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

function CTA() {
  return (
    <section className="relative px-4 sm:px-6 md:px-12 py-24 bg-white">
      <div className="max-w-4xl mx-auto text-center relative z-10">
        <h3 className="text-4xl font-bold text-gray-900 mb-6">
          Every decision.<br />On the record.
        </h3>
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
              {["FastAPI · asyncpg · Redis", "Authlib · Docker · AWS EC2", "Kraken API · Binance WS", "Web3.py · EIP-712 · ERC-8004"].map(s => (
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
    <main className="bg-white text-gray-900 min-h-screen overflow-x-hidden">
      <Header />
      <Hero />
      <HowItWorks />
      <Features />
      <WhyQuasar />
      <CTA />
      <Footer />
    </main>
  );
}