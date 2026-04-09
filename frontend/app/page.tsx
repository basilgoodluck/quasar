"use client";

import React, { useState, useEffect, useRef } from 'react';
import { Menu, X, ArrowRight, Check, Shield, Zap, Eye } from 'lucide-react';
import { motion, useInView } from 'framer-motion';
import Link from 'next/link';
import { BASE_URL } from '@/lib/api';

// ─── HEADER ──────────────────────────────────────────────────────────────────

function Header() {
  const [isMenuOpen, setIsMenuOpen] = useState(false);

  const navLinks = [
    { href: "#how",       label: "How It Works" },
    { href: "#features",  label: "Features"     },
    { href: "#contracts", label: "Contracts"    },
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
        transition={{ duration: 0.6, ease: "easeOut" }}
        className="fixed top-0 left-0 right-0 z-50 px-6 md:px-12 py-6 bg-[#03060a]/80 backdrop-blur-md border-b border-white/5"
      >
        <div className="w-full mx-auto flex items-center justify-between">
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.2, duration: 0.5 }}
            className="flex items-center space-x-2"
          >
            <div className="w-8 h-8 bg-green-400 rounded flex items-center justify-center">
              <span className="text-black font-bold text-xs font-mono">Q</span>
            </div>
            <span className="text-white font-mono font-bold tracking-widest text-sm uppercase">Quasar</span>
          </motion.div>

          <div className="hidden md:flex items-center space-x-16">
            <motion.div
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.3, duration: 0.5 }}
              className="flex items-center space-x-10"
            >
              {navLinks.map((link, i) => (
                <motion.a
                  key={link.label}
                  href={link.href}
                  initial={{ opacity: 0, y: -10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.4 + i * 0.05, duration: 0.3 }}
                  whileHover={{ y: -2 }}
                  className="text-zinc-400 hover:text-green-400 transition font-mono text-xs uppercase tracking-widest"
                >
                  {link.label}
                </motion.a>
              ))}
            </motion.div>
            <motion.a
              href={`${BASE_URL}/auth/google`}
              initial={{ opacity: 0, scale: 0.8 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: 0.6, duration: 0.4 }}
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              className="bg-green-400 text-black px-6 py-2.5 rounded font-mono font-bold text-xs uppercase tracking-widest hover:bg-green-300 transition"
            >
              Launch Agent
            </motion.a>
          </div>

          <button onClick={() => setIsMenuOpen(!isMenuOpen)} className="md:hidden text-white z-50 relative">
            {isMenuOpen ? <X size={24} /> : <Menu size={24} />}
          </button>
        </div>
      </motion.nav>

      <div className={`fixed inset-0 bg-[#03060a] z-40 md:hidden transition-all duration-500 ${isMenuOpen ? 'opacity-100 pointer-events-auto' : 'opacity-0 pointer-events-none'}`}>
        <div className="h-full flex flex-col items-center justify-center space-y-8">
          {navLinks.map((link, i) => (
            <a key={link.label} href={link.href} onClick={() => setIsMenuOpen(false)}
              className={`text-white font-mono text-xl uppercase tracking-widest transition-all duration-300 ${isMenuOpen ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-8'}`}
              style={{ transitionDelay: isMenuOpen ? `${i * 60}ms` : '0ms' }}>
              {link.label}
            </a>
          ))}
          <a href={`${BASE_URL}/auth/google`}
            className="mt-4 bg-green-400 text-black px-8 py-3 rounded font-mono font-bold text-sm uppercase">
            Launch Agent
          </a>
        </div>
      </div>
    </>
  );
}

// ─── HERO ────────────────────────────────────────────────────────────────────

const TERMINAL_LINES = [
  { color: "text-green-400", text: "[03:12:44] AGENT quasar-01 ONLINE" },
  { color: "text-zinc-400",  text: "[03:12:45] regime=BULL  confidence=0.81" },
  { color: "text-amber-400", text: "[03:12:46] signal=BUY  pair=BTCUSDT  rsi=38.2" },
  { color: "text-blue-400",  text: "[03:12:47] intent signed  nonce=412" },
  { color: "text-green-400", text: "[03:12:48] RiskRouter → APPROVED  hash=0x3f9a...c12e" },
  { color: "text-white",     text: "[03:12:49] order FILLED  entry=83,241  size=0.024 BTC" },
  { color: "text-green-400", text: "[03:14:11] outcome=WIN  exit=84,190  pnl=+$22.78" },
];

function Hero() {
  const words = ['Verifiable', 'On-Chain', 'Auditable', 'Deterministic'];
  const [currentIndex, setCurrentIndex] = useState(0);
  const [lines, setLines] = useState<typeof TERMINAL_LINES>([]);
  const longestWord = words.reduce((a, b) => a.length > b.length ? a : b, '');

  useEffect(() => {
    const interval = setInterval(() => setCurrentIndex(p => (p + 1) % words.length), 3000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    TERMINAL_LINES.forEach((l, i) => {
      setTimeout(() => setLines(p => [...p, l]), 400 + i * 500);
    });
  }, []);

  return (
    <section className="relative px-4 sm:px-6 md:px-12 py-12 md:py-20 pt-32">
      <div className="pointer-events-none absolute inset-0 bg-[linear-gradient(rgba(0,255,135,0.03)_1px,transparent_1px),linear-gradient(90deg,rgba(0,255,135,0.03)_1px,transparent_1px)] bg-[size:60px_60px]" />
      <div className="max-w-7xl mx-auto relative z-10">
        <div className="grid md:grid-cols-2 gap-8 md:gap-12 items-start">

          <div className="text-center md:text-left">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded border border-green-400/20 bg-green-400/5 mb-6">
              <span className="w-1.5 h-1.5 rounded-full bg-green-400 animate-pulse" />
              <span className="font-mono text-xs text-green-400 uppercase tracking-widest">Agent Online · agentId #7</span>
            </div>

            <h1 className="text-4xl sm:text-5xl md:text-6xl font-bold mb-3 font-mono">
              <span className="text-green-400">On-Chain</span> <span className="text-white">AI Trading</span>
            </h1>
            <h2 className="text-5xl sm:text-6xl md:text-7xl font-black mb-6 text-white relative inline-block h-[1.2em] overflow-hidden font-mono">
              <span className="invisible">{longestWord}</span>
              <span key={currentIndex} className="absolute inset-0 flex items-center justify-center md:justify-start animate-slideUp">
                <span className="relative inline-block">
                  {words[currentIndex]}
                  <span className="absolute -bottom-1 left-0 w-full h-1 bg-green-400 transform -skew-x-12" />
                </span>
              </span>
            </h2>

            <p className="text-base sm:text-lg text-zinc-400 max-w-xl mb-8 leading-relaxed mx-auto md:mx-0">
              Rule-based trading agent with on-chain identity, EIP-712 signed decisions, and smart contract risk enforcement. Every trade is verifiable. Nothing is a black box.
            </p>

            <div className="flex flex-wrap gap-3 justify-center md:justify-start">
              <a href={`${BASE_URL}/auth/google`}
                className="bg-green-400 text-black px-6 py-3 rounded font-mono font-bold text-sm uppercase tracking-widest hover:bg-green-300 transition active:scale-95">
                View Live Agent →
              </a>
              <a href="#contracts"
                className="border border-white/10 text-white px-6 py-3 rounded font-mono text-sm uppercase tracking-widest hover:border-green-400/30 hover:text-green-400 transition">
                On-Chain Activity
              </a>
            </div>

            <div className="flex gap-8 mt-10 pt-8 border-t border-white/5 justify-center md:justify-start">
              {[{ v: "ERC-8004", l: "Identity" }, { v: "EIP-712", l: "Signatures" }, { v: "100%", l: "Auditable" }].map(s => (
                <div key={s.l}>
                  <div className="font-mono text-lg text-green-400 font-bold">{s.v}</div>
                  <div className="text-xs text-zinc-600 mt-0.5 font-mono">{s.l}</div>
                </div>
              ))}
            </div>
          </div>

          <div className="relative mt-8 md:mt-0">
            <div className="bg-[#070d14] rounded-lg border border-white/8 overflow-hidden">
              <div className="flex items-center gap-2 px-4 py-3 border-b border-white/5 bg-[#050b10]">
                <span className="w-2.5 h-2.5 rounded-full bg-red-500/70" />
                <span className="w-2.5 h-2.5 rounded-full bg-amber-400/70" />
                <span className="w-2.5 h-2.5 rounded-full bg-green-400/70" />
                <span className="ml-4 font-mono text-xs text-zinc-600">quasar-agent · live</span>
                <span className="ml-auto flex items-center gap-1.5">
                  <span className="w-1.5 h-1.5 rounded-full bg-green-400 animate-pulse" />
                  <span className="font-mono text-xs text-green-400">LIVE</span>
                </span>
              </div>
              <div className="p-4 h-64 overflow-y-auto space-y-2">
                {lines.map((l, i) => (
                  <div key={i} className={`font-mono text-xs leading-relaxed ${l.color}`}>{l.text}</div>
                ))}
                <span className="inline-block w-2 h-3 bg-green-400 animate-pulse" />
              </div>
            </div>

            <div className="mt-3 bg-[#070d14] rounded-lg border border-white/8 p-4 font-mono text-xs">
              <div className="text-zinc-600 mb-2 uppercase tracking-widest text-[10px]">Latest Checkpoint</div>
              <div className="space-y-1">
                {[
                  ["agentId",    "7",              "text-white"    ],
                  ["action",     "BUY · BTCUSDT",  "text-green-400"],
                  ["confidence", "0.81",           "text-amber-400"],
                  ["signature",  "0x3f9a...c12e",  "text-zinc-400" ],
                  ["status",     "APPROVED ✓",     "text-green-400"],
                ].map(([k, v, c]) => (
                  <div key={k} className="flex justify-between">
                    <span className="text-zinc-600">{k}</span>
                    <span className={c}>{v}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>

      <style jsx>{`
        @keyframes slideUp {
          0%   { opacity: 0; transform: translateY(100%); }
          100% { opacity: 1; transform: translateY(0);    }
        }
        .animate-slideUp { animation: slideUp 0.5s ease-in-out forwards; }
      `}</style>
    </section>
  );
}

// ─── HOW IT WORKS ────────────────────────────────────────────────────────────

function HowItWorks() {
  const steps = [
    { number: "01", title: "Register Agent",       description: "Mint ERC-721 via AgentRegistry to receive a persistent agentId as on-chain identity." },
    { number: "02", title: "Strategy Runs",        description: "Rule-based engine reads live market data, computes RSI / Stoch RSI, emits a TradeDecision." },
    { number: "03", title: "Sign Intent",          description: "TradeIntent structured and signed by agentWallet using EIP-712 before any action." },
    { number: "04", title: "On-Chain Validation",  description: "RiskRouter smart contract verifies position size, drawdown limits, and frequency constraints." },
    { number: "05", title: "Execute & Record",     description: "Kraken CLI executes only on APPROVED. Checkpoint written on-chain with full audit trail." },
  ];

  return (
    <section id="how" className="relative px-4 sm:px-6 md:px-12 py-16 md:py-20">
      <div className="max-w-7xl mx-auto">
        <h3 className="text-3xl md:text-4xl font-bold text-center mb-12 text-white font-mono">How It Works</h3>
        <div className="grid md:grid-cols-2 gap-8 md:gap-16 items-start">

          <div className="relative flex justify-center order-2 md:order-1">
            <div className="w-full bg-[#070d14] rounded-lg border border-white/8 p-6 font-mono text-xs">
              {["TradeDecision", "TradeIntent", "EIP-712 Signature", "RiskRouter Validation", "Execution", "Checkpoint"].map((s, i, arr) => (
                <div key={s}>
                  <div className="flex items-center gap-3 py-3">
                    <div className="w-6 h-6 rounded border border-green-400/30 bg-green-400/5 flex items-center justify-center text-green-400 text-[10px] font-bold flex-shrink-0">
                      {String(i + 1).padStart(2, '0')}
                    </div>
                    <span className="text-zinc-300">{s}</span>
                  </div>
                  {i < arr.length - 1 && <div className="ml-3 text-green-400/30">↓</div>}
                </div>
              ))}
            </div>
          </div>

          <div className="flex flex-col space-y-8 order-1 md:order-2">
            {steps.map((step, index) => (
              <div key={index} className="flex gap-5 flex-col">
                <div className="flex items-baseline gap-4 text-2xl md:text-3xl text-white/20 leading-none font-mono">
                  {step.number}.
                  <h4 className="text-base md:text-lg font-medium text-white/70">{step.title}</h4>
                </div>
                <div className="pl-10">
                  <p className="text-zinc-500 text-sm md:text-base leading-relaxed">{step.description}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}

// ─── FEATURES ────────────────────────────────────────────────────────────────

function Features() {
  const features = [
    "ERC-8004 On-Chain Identity",
    "EIP-712 Signed Decisions",
    "RiskRouter Enforcement",
    "Cryptographic Audit Trail",
    "Regime Filtering",
    "Explainability Layer",
  ];

  return (
    <section id="features" className="relative px-4 sm:px-6 md:px-12 py-16 md:py-20">
      <div className="absolute -bottom-40 -left-40 w-[600px] h-[600px] pointer-events-none">
        <div className="w-full h-full bg-gradient-to-tr from-green-500/10 via-emerald-500/5 to-transparent blur-3xl" />
      </div>

      <div className="max-w-6xl mx-auto relative z-10 space-y-8">
        <h3 className="text-3xl sm:text-4xl md:text-5xl text-center font-bold mb-8 text-white font-mono">
          ...your trades are on the record
        </h3>
        <div className="flex flex-col lg:flex-row items-center justify-center gap-8 lg:gap-12">
          <div className="flex-1 w-full max-w-md space-y-6">
            {features.map((feature, index) => (
              <div key={index} className="flex items-center space-x-4">
                <div className="w-6 h-6 flex-shrink-0 bg-green-400 rounded flex items-center justify-center">
                  <Check size={14} className="text-black" />
                </div>
                <span className="text-base text-zinc-300 font-mono">{feature}</span>
              </div>
            ))}
          </div>

          <div className="flex-1 w-full max-w-md bg-[#070d14] rounded-lg border border-white/8 overflow-hidden">
            <div className="px-4 py-2 border-b border-white/5 bg-[#050b10]">
              <span className="font-mono text-xs text-zinc-600">checkpoints.jsonl</span>
            </div>
            <div className="p-4 font-mono text-xs space-y-3">
              {[
                { action: "BUY",  pair: "BTCUSDT", conf: 0.81, status: "WIN",  pnl: "+$22.78" },
                { action: "HOLD", pair: "ETHUSDT", conf: 0.44, status: "SKIP", pnl: "—"       },
                { action: "SELL", pair: "BTCUSDT", conf: 0.76, status: "WIN",  pnl: "+$11.20" },
              ].map((r, i) => (
                <div key={i} className="border border-white/5 rounded p-3 space-y-1">
                  <div className="flex justify-between">
                    <span className={r.action === "BUY" ? "text-green-400" : r.action === "SELL" ? "text-red-400" : "text-zinc-500"}>{r.action}</span>
                    <span className="text-zinc-400">{r.pair}</span>
                    <span className={r.status === "WIN" ? "text-green-400" : "text-zinc-600"}>{r.status}</span>
                  </div>
                  <div className="flex gap-4 text-zinc-600">
                    <span>conf <span className="text-amber-400">{r.conf}</span></span>
                    <span>pnl <span className="text-green-400">{r.pnl}</span></span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        <div className="md:w-4/5 mx-auto space-y-10 flex flex-col items-center mt-12">
          <h4 className="text-center text-xl sm:text-2xl text-white/80 px-4 font-mono">
            Every decision signed. Every trade verifiable. Every outcome recorded on-chain.
          </h4>
          <a href={`${BASE_URL}/auth/google`}
            className="bg-green-400 text-black px-8 py-3 rounded font-mono font-bold text-sm uppercase tracking-widest hover:bg-green-300 transition inline-flex items-center gap-2">
            <span>Access Dashboard</span>
            <ArrowRight size={16} />
          </a>
        </div>
      </div>
    </section>
  );
}

// ─── WHY QUASAR ──────────────────────────────────────────────────────────────

function WhyQuasar() {
  const reasons = [
    { icon: Shield, title: "Verifiable Identity",  description: "Agent registered via ERC-8004. Persistent agentId as NFT. Every action is attributable — no anonymous bots." },
    { icon: Zap,    title: "Enforced Risk",        description: "RiskRouter smart contract is the final gate. Position size, drawdown, and frequency validated on-chain before execution." },
    { icon: Eye,    title: "Full Explainability",  description: "Every decision includes regime state, indicator values, confidence score, and reasoning. Nothing is hidden." },
  ];

  return (
    <section className="relative px-4 sm:px-6 md:px-12 py-16 md:py-24">
      <div className="absolute -bottom-40 -right-40 w-[600px] h-[600px] pointer-events-none">
        <div className="w-full h-full bg-gradient-to-tl from-green-500/8 to-transparent blur-3xl" />
      </div>
      <div className="max-w-2xl mx-auto relative z-10">
        <h3 className="text-3xl md:text-4xl font-bold text-center mb-16 text-white font-mono">Why Quasar?</h3>
        <div className="space-y-12">
          {reasons.map((r, i) => {
            const Icon = r.icon;
            return (
              <div key={i} className="flex items-start space-x-6">
                <div className="flex-shrink-0 w-10 h-10 bg-green-400 rounded flex items-center justify-center">
                  <Icon size={20} className="text-black" />
                </div>
                <div>
                  <h4 className="text-xl font-bold text-white mb-2 font-mono">{r.title}</h4>
                  <p className="text-zinc-500 leading-relaxed">{r.description}</p>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}

// ─── CTA ─────────────────────────────────────────────────────────────────────

function CTA() {
  return (
    <section className="relative px-4 sm:px-6 md:px-12 py-16 md:py-20">
      <div className="max-w-4xl mx-auto text-center relative z-10">
        <h3 className="text-3xl md:text-5xl font-bold text-white font-mono mb-4">
          Every decision.<br />On the record.
        </h3>
        <p className="text-zinc-500 mb-10 text-sm">
          Access the live dashboard, inspect checkpoints, and verify every trade on-chain.
        </p>
        <div className="flex flex-wrap justify-center gap-4">
          <a href={`${BASE_URL}/auth/google`}
            className="bg-green-400 text-black px-8 py-3 rounded font-mono font-bold text-sm uppercase hover:bg-green-300 transition inline-flex items-center gap-2 active:scale-95">
            <span>View Checkpoints</span>
            <ArrowRight size={16} />
          </a>
          <a href="https://sepolia.etherscan.io/address/0xd6A6952545FF6E6E6681c2d15C59f9EB8F40FdBC" target="_blank" rel="noopener noreferrer"
            className="border border-white/10 text-white px-8 py-3 rounded font-mono text-sm uppercase hover:border-green-400/30 hover:text-green-400 transition">
            View Contract
          </a>
          <a href="https://github.com" target="_blank" rel="noopener noreferrer"
            className="border border-white/10 text-white px-8 py-3 rounded font-mono text-sm uppercase hover:border-green-400/30 hover:text-green-400 transition">
            View Code
          </a>
        </div>
      </div>
    </section>
  );
}

// ─── FOOTER ──────────────────────────────────────────────────────────────────

const CONTRACTS = [
  { label: "AgentRegistry",  address: "0x97b07dD...32d0ca3", href: "https://sepolia.etherscan.io/address/0x97b07dDc405B0c28B17559aFFE63BdB3632d0ca3" },
  { label: "RiskRouter",     address: "0xd6A695...40FdBC",   href: "https://sepolia.etherscan.io/address/0xd6A6952545FF6E6E6681c2d15C59f9EB8F40FdBC" },
  { label: "HackathonVault", address: "0x0E7CD8...45fC90",   href: "https://sepolia.etherscan.io/address/0x0E7CD8ef9743FEcf94f9103033a044caBD45fC90" },
  { label: "Validation",     address: "0x92bF63...87F1",     href: "https://sepolia.etherscan.io/address/0x92bF63E5C7Ac6980f237a7164Ab413BE226187F1" },
];

function Footer() {
  const ref = useRef(null);
  const isInView = useInView(ref, { once: true, amount: 0.2 });

  const productLinks = [
    { text: 'Dashboard',   href: '/dashboard'   },
    { text: 'Checkpoints', href: '/checkpoints' },
    { text: 'Trades',      href: '/trades'      },
    { text: 'Risk',        href: '/risk'         },
  ];

  return (
    <footer id="contracts" ref={ref} className="relative py-20 text-zinc-400 overflow-hidden border-t border-white/5">
      <div className="relative z-10 max-w-7xl mx-auto px-6 lg:px-8">
        <div className="flex flex-col lg:flex-row lg:justify-between gap-12 lg:gap-20">

          <motion.div
            initial={{ opacity: 0, x: -60 }}
            animate={isInView ? { opacity: 1, x: 0 } : {}}
            transition={{ duration: 0.8 }}
            className="flex items-center gap-3 flex-shrink-0"
          >
            <div className="w-8 h-8 bg-green-400 rounded flex items-center justify-center">
              <span className="text-black font-bold text-xs font-mono">Q</span>
            </div>
            <span className="text-white font-mono font-bold tracking-widest text-sm uppercase">Quasar</span>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 50 }}
            animate={isInView ? { opacity: 1, y: 0 } : {}}
            transition={{ duration: 0.8, delay: 0.2 }}
            className="flex flex-col sm:flex-row gap-16 lg:gap-24"
          >
            <ul className="space-y-3 font-mono text-xs">
              {productLinks.map((link, i) => (
                <motion.li key={link.text}
                  initial={{ opacity: 0, x: -30 }}
                  animate={isInView ? { opacity: 1, x: 0 } : {}}
                  transition={{ duration: 0.5, delay: 0.4 + i * 0.08 }}>
                  <Link href={link.href} className="hover:text-white transition-colors uppercase tracking-widest">{link.text}</Link>
                </motion.li>
              ))}
            </ul>

            <div className="font-mono text-xs">
              <div className="text-green-400 uppercase tracking-widest text-[10px] mb-4">Contracts · Sepolia</div>
              <div className="space-y-2">
                {CONTRACTS.map((c, i) => (
                  <motion.div key={c.label}
                    initial={{ opacity: 0, x: -30 }}
                    animate={isInView ? { opacity: 1, x: 0 } : {}}
                    transition={{ duration: 0.5, delay: 0.6 + i * 0.08 }}
                    className="flex justify-between gap-8">
                    <a href={c.href} target="_blank" rel="noopener noreferrer" className="text-zinc-500 hover:text-white transition-colors">{c.label}</a>
                    <span className="text-zinc-700">{c.address}</span>
                  </motion.div>
                ))}
              </div>
            </div>

            <div className="font-mono text-xs space-y-2">
              <div className="text-green-400 uppercase tracking-widest text-[10px] mb-4">Stack</div>
              {["FastAPI · asyncpg · Redis", "Authlib · Docker · AWS EC2", "Kraken API · Binance WS", "Web3.py · EIP-712 · ERC-8004"].map(s => (
                <div key={s} className="text-zinc-600">{s}</div>
              ))}
            </div>
          </motion.div>
        </div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={isInView ? { opacity: 1, y: 0 } : {}}
          transition={{ duration: 0.8, delay: 1.0 }}
          className="mt-16 pt-8 border-t border-white/5 flex flex-col md:flex-row justify-between items-center gap-4"
        >
          <p className="text-zinc-700 text-xs font-mono">© 2025 Quasar. All rights reserved.</p>
          <p className="text-zinc-800 text-xs font-mono">Trading involves risk. Use at your own discretion.</p>
        </motion.div>
      </div>
    </footer>
  );
}

// ─── PAGE ────────────────────────────────────────────────────────────────────

export default function Home() {
  return (
    <main className="bg-[#03060a] text-[#c8dde8] min-h-screen overflow-x-hidden">
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