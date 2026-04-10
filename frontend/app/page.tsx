"use client";
import React, { useState, useEffect } from 'react';
import { Menu, X, ArrowRight, Check, Shield, Zap, Eye } from 'lucide-react';
import { motion, useInView } from 'framer-motion';
import Link from 'next/link';
import { BASE_URL } from '@/lib/api';
import landingData from '@/data/landing.json';

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
        className="fixed top-0 left-0 right-0 z-50 px-6 md:px-12 py-6 bg-white/80 backdrop-blur-md border-b border-gray-200"
      >
        <div className="w-full mx-auto flex items-center justify-between">
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.05, duration: 0.25 }}
            className="flex items-center space-x-2"
          >
            <div className="w-8 h-8 bg-blue-600 rounded-full flex items-center justify-center">
              <span className="text-white font-bold text-xs">Q</span>
            </div>
            <span className="text-gray-900 font-bold tracking-wide text-sm">Quasar</span>
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
                  className="text-gray-600 hover:text-blue-600 transition text-sm"
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
              className="bg-black text-white px-6 py-2.5 rounded-full font-bold text-sm hover:bg-gray-900 transition"
            >
              Launch Agent
            </motion.a>
          </div>
          <button onClick={() => setIsMenuOpen(!isMenuOpen)} className="md:hidden text-gray-900 z-50 relative">
            {isMenuOpen ? <X size={24} /> : <Menu size={24} />}
          </button>
        </div>
      </motion.nav>
      <div className={`fixed inset-0 bg-white z-40 md:hidden transition-all duration-300 ${isMenuOpen ? 'opacity-100 pointer-events-auto' : 'opacity-0 pointer-events-none'}`}>
        <div className="h-full flex flex-col items-center justify-center space-y-8">
          {navLinks.map((link, i) => (
            <a key={link.label} href={link.href} onClick={() => setIsMenuOpen(false)}
              className={`text-gray-900 font-bold text-lg transition-all duration-200 ${isMenuOpen ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-8'}`}
              style={{ transitionDelay: isMenuOpen ? `${i * 30}ms` : '0ms' }}>
              {link.label}
            </a>
          ))}
          <a href={`${BASE_URL}/auth/google`}
            className="mt-4 bg-black text-white px-8 py-3 rounded-full font-bold text-sm">
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
  const longestWord = words.reduce((a, b) => a.length > b.length ? a : b, '');

  useEffect(() => {
    const interval = setInterval(() => setCurrentIndex(p => (p + 1) % words.length), 3000);
    return () => clearInterval(interval);
  }, []);

  return (
    <section className="relative px-4 sm:px-6 md:px-12 pt-32 pb-20 bg-white">
      <div className="pointer-events-none absolute inset-0 bg-[linear-gradient(rgba(59,130,246,0.03)_1px,transparent_1px),linear-gradient(90deg,rgba(59,130,246,0.03)_1px,transparent_1px)] bg-[size:60px_60px]" />
      <div className="max-w-4xl mx-auto relative z-10">
        <div className="text-center">
          <h1 className="text-xl sm:text-2xl md:text-3xl font-bold mb-3">
            <span className="text-blue-600">On-Chain</span> <span className="text-gray-900">AI Trading</span>
          </h1>
          <h2 className="text-2xl sm:text-3xl md:text-3xl font-black mb-6 text-gray-900 relative inline-block h-[1.2em] overflow-hidden mx-auto">
            <span className="invisible">{longestWord}</span>
            <span key={currentIndex} className="absolute inset-0 flex items-center justify-center animate-slideUp">
              <span className="relative inline-block">
                {words[currentIndex]}
                <span className="absolute -bottom-1 left-0 w-full h-1 bg-blue-600 transform -skew-x-12" />
              </span>
            </span>
          </h2>
          <p className="text-sm text-gray-500 max-w-xl mb-8 leading-relaxed mx-auto">
            Rule-based trading agent with on-chain identity, EIP-712 signed decisions, and smart contract risk enforcement. Every trade is verifiable. Nothing is a black box.
          </p>
          <div className="flex flex-wrap gap-3 justify-center">
            <a href={`${BASE_URL}/auth/google`}
              className="bg-black text-white px-6 py-3 rounded-full font-bold text-sm hover:bg-gray-900 transition active:scale-95">
              View Live Agent →
            </a>
            <a href="#contracts"
              className="border border-gray-200 text-gray-600 px-6 py-3 rounded-full text-sm hover:border-blue-300 hover:text-blue-600 transition">
              On-Chain Activity
            </a>
          </div>
          <div className="flex gap-8 mt-10 pt-8 border-t border-gray-100 justify-center">
            {landingData.heroStats.map((s: any) => (
              <div key={s.label}>
                <div className="text-sm text-blue-600 font-bold">{s.value}</div>
                <div className="text-xs text-gray-400 mt-0.5">{s.label}</div>
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
      `}</style>
    </section>
  );
}

function HowItWorks() {
  const steps = landingData.howItWorksSteps;
  return (
    <section id="how" className="relative px-4 sm:px-6 md:px-12 py-16 bg-white">
      <div className="max-w-7xl mx-auto">
        <h3 className="text-xl font-bold text-center mb-12 text-gray-900">How It Works</h3>
        <div className="grid md:grid-cols-2 gap-8 md:gap-16 items-start">
          <div className="relative flex justify-center order-2 md:order-1">
            <div className="w-full bg-gray-50 rounded-2xl border border-gray-200 p-6 text-xs font-mono">
              {["TradeDecision", "TradeIntent", "EIP-712 Signature", "RiskRouter Validation", "Execution", "Checkpoint"].map((s, i, arr) => (
                <div key={s}>
                  <div className="flex items-center gap-3 py-3">
                    <div className="w-6 h-6 rounded-full border border-blue-200 bg-blue-50 flex items-center justify-center text-blue-600 text-[10px] font-bold flex-shrink-0">
                      {String(i + 1).padStart(2, '0')}
                    </div>
                    <span className="text-gray-700">{s}</span>
                  </div>
                  {i < arr.length - 1 && <div className="ml-3 text-blue-300">↓</div>}
                </div>
              ))}
            </div>
          </div>
          <div className="flex flex-col space-y-8 order-1 md:order-2">
            {steps.map((step: any, index: number) => (
              <div key={index} className="flex gap-5 flex-col">
                <div className="flex items-baseline gap-4 text-lg text-gray-300 leading-none">
                  {step.number}.
                  <h4 className="text-base font-medium text-gray-600">{step.title}</h4>
                </div>
                <div className="pl-10">
                  <p className="text-sm text-gray-400 leading-relaxed">{step.description}</p>
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
    <section id="features" className="relative px-4 sm:px-6 md:px-12 py-16 bg-white">
      <div className="absolute -bottom-40 -left-40 w-[600px] h-[600px] pointer-events-none">
        <div className="w-full h-full bg-gradient-to-tr from-blue-500/20 via-purple-500/10 to-transparent blur-3xl" />
      </div>
      <div className="max-w-6xl mx-auto relative z-10 space-y-8">
        <h3 className="text-xl text-center font-bold mb-8 text-gray-900">
          ...your trades are on the record
        </h3>
        <div className="flex flex-col lg:flex-row items-center justify-center gap-8 lg:gap-12">
          <div className="flex-1 w-full max-w-md space-y-6">
            {features.map((feature: string, index: number) => (
              <div key={index} className="flex items-center space-x-4">
                <div className="w-6 h-6 flex-shrink-0 bg-blue-600 rounded-full flex items-center justify-center">
                  <Check size={14} className="text-white" />
                </div>
                <span className="text-base text-gray-700">{feature}</span>
              </div>
            ))}
          </div>
          <div className="flex-1 w-full max-w-md bg-gray-50 rounded-2xl border border-gray-200 overflow-hidden">
            <div className="px-4 py-2 border-b border-gray-200 bg-white">
              <span className="text-xs text-gray-400 font-mono">checkpoints.jsonl</span>
            </div>
            <div className="p-4 font-mono text-xs space-y-3">
              {[
                { action: "BUY", pair: "BTCUSDT", conf: 0.81, status: "WIN", pnl: "+$22.78" },
                { action: "HOLD", pair: "ETHUSDT", conf: 0.44, status: "SKIP", pnl: "—" },
                { action: "SELL", pair: "BTCUSDT", conf: 0.76, status: "WIN", pnl: "+$11.20" },
              ].map((r, i) => (
                <div key={i} className="border border-gray-200 rounded-xl p-3 space-y-1 bg-white">
                  <div className="flex justify-between">
                    <span className={r.action === "BUY" ? "text-blue-600" : r.action === "SELL" ? "text-red-500" : "text-gray-400"}>{r.action}</span>
                    <span className="text-gray-500">{r.pair}</span>
                    <span className={r.status === "WIN" ? "text-blue-600" : "text-gray-400"}>{r.status}</span>
                  </div>
                  <div className="flex gap-4 text-gray-400">
                    <span>conf <span className="text-purple-500">{r.conf}</span></span>
                    <span>pnl <span className="text-blue-600">{r.pnl}</span></span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
        <div className="md:w-4/5 mx-auto space-y-10 flex flex-col items-center mt-12">
          <h4 className="text-center text-lg text-gray-700 px-4">
            Every decision signed. Every trade verifiable. Every outcome recorded on-chain.
          </h4>
          <a href={`${BASE_URL}/auth/google`}
            className="bg-black text-white px-8 py-3 rounded-full font-bold text-sm hover:bg-gray-900 transition inline-flex items-center gap-2 active:scale-95">
            <span>Access Dashboard</span>
            <ArrowRight size={16} />
          </a>
        </div>
      </div>
    </section>
  );
}

function WhyQuasar() {
  const reasons = landingData.whyQuasarReasons;
  return (
    <section className="relative px-4 sm:px-6 md:px-12 py-16 bg-white">
      <div className="absolute -bottom-40 -right-40 w-[600px] h-[600px] pointer-events-none">
        <div className="w-full h-full bg-gradient-to-tl from-blue-500/10 to-transparent blur-3xl" />
      </div>
      <div className="max-w-2xl mx-auto relative z-10">
        <h3 className="text-xl font-bold text-center mb-16 text-gray-900">Why Quasar?</h3>
        <div className="space-y-12">
          {reasons.map((r: any, i: number) => {
            const Icon = r.icon === "Shield" ? Shield : r.icon === "Zap" ? Zap : Eye;
            return (
              <div key={i} className="flex items-start space-x-6">
                <div className="flex-shrink-0 w-10 h-10 bg-blue-600 rounded-full flex items-center justify-center">
                  <Icon size={20} className="text-white" />
                </div>
                <div>
                  <h4 className="text-lg font-bold text-gray-900 mb-2">{r.title}</h4>
                  <p className="text-sm text-gray-500 leading-relaxed">{r.description}</p>
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
    <section className="relative px-4 sm:px-6 md:px-12 py-16 bg-white">
      <div className="max-w-4xl mx-auto text-center relative z-10">
        <h3 className="text-xl font-bold text-gray-900 mb-4">
          Every decision.<br />On the record.
        </h3>
        <p className="text-sm text-gray-400 mb-10">
          Access the live dashboard, inspect checkpoints, and verify every trade on-chain.
        </p>
        <div className="flex flex-wrap justify-center gap-4">
          <a href={`${BASE_URL}/auth/google`}
            className="bg-black text-white px-8 py-3 rounded-full font-bold text-sm hover:bg-gray-900 transition inline-flex items-center gap-2 active:scale-95">
            <span>View Checkpoints</span>
            <ArrowRight size={16} />
          </a>
          <a href="https://sepolia.etherscan.io/address/0xd6A6952545FF6E6E6681c2d15C59f9EB8F40FdBC" target="_blank" rel="noopener noreferrer"
            className="border border-gray-200 text-gray-600 px-8 py-3 rounded-full text-sm hover:border-blue-300 hover:text-blue-600 transition">
            View Contract
          </a>
          <a href="https://github.com" target="_blank" rel="noopener noreferrer"
            className="border border-gray-200 text-gray-600 px-8 py-3 rounded-full text-sm hover:border-blue-300 hover:text-blue-600 transition">
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
    <footer id="contracts" ref={ref} className="relative py-20 text-gray-500 overflow-hidden border-t border-gray-100 bg-white">
      <div className="relative z-10 max-w-7xl mx-auto px-6 lg:px-8">
        <div className="flex flex-col lg:flex-row lg:justify-between gap-12 lg:gap-20">
          <motion.div
            initial={{ opacity: 0, x: -60 }}
            animate={isInView ? { opacity: 1, x: 0 } : {}}
            transition={{ duration: 0.4 }}
            className="flex items-center gap-3 flex-shrink-0"
          >
            <div className="w-8 h-8 bg-blue-600 rounded-full flex items-center justify-center">
              <span className="text-white font-bold text-xs">Q</span>
            </div>
            <span className="text-gray-900 font-bold tracking-wide text-sm">Quasar</span>
          </motion.div>
          <motion.div
            initial={{ opacity: 0, y: 50 }}
            animate={isInView ? { opacity: 1, y: 0 } : {}}
            transition={{ duration: 0.4, delay: 0.1 }}
            className="flex flex-col sm:flex-row gap-16 lg:gap-24"
          >
            <ul className="space-y-3 text-xs">
              {productLinks.map((link: any, i: number) => (
                <motion.li key={link.text}
                  initial={{ opacity: 0, x: -30 }}
                  animate={isInView ? { opacity: 1, x: 0 } : {}}
                  transition={{ duration: 0.35, delay: 0.15 + i * 0.05 }}>
                  <Link href={link.href} className="hover:text-gray-900 transition-colors">{link.text}</Link>
                </motion.li>
              ))}
            </ul>
            <div className="text-xs">
              <div className="text-blue-600 uppercase tracking-widest text-[10px] mb-4">Contracts · Sepolia</div>
              <div className="space-y-2">
                {CONTRACTS.map((c: any, i: number) => (
                  <motion.div key={c.label}
                    initial={{ opacity: 0, x: -30 }}
                    animate={isInView ? { opacity: 1, x: 0 } : {}}
                    transition={{ duration: 0.35, delay: 0.2 + i * 0.05 }}
                    className="flex justify-between gap-8">
                    <a href={c.href} target="_blank" rel="noopener noreferrer" className="text-gray-400 hover:text-gray-900 transition-colors">{c.label}</a>
                    <span className="text-gray-300">{c.address}</span>
                  </motion.div>
                ))}
              </div>
            </div>
            <div className="text-xs space-y-2">
              <div className="text-blue-600 uppercase tracking-widest text-[10px] mb-4">Stack</div>
              {["FastAPI · asyncpg · Redis", "Authlib · Docker · AWS EC2", "Kraken API · Binance WS", "Web3.py · EIP-712 · ERC-8004"].map(s => (
                <div key={s} className="text-gray-400">{s}</div>
              ))}
            </div>
          </motion.div>
        </div>
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={isInView ? { opacity: 1, y: 0 } : {}}
          transition={{ duration: 0.4, delay: 0.5 }}
          className="mt-16 pt-8 border-t border-gray-100 flex flex-col md:flex-row justify-between items-center gap-4"
        >
          <p className="text-gray-300 text-xs">© 2025 Quasar. All rights reserved.</p>
          <p className="text-gray-300 text-xs">Trading involves risk. Use at your own discretion.</p>
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