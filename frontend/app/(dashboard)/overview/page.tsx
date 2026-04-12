"use client"

import { useEffect, useState } from "react"
import { api } from "@/lib/api"
import { Trade } from "@/types"

type RegimeInfo = {
  direction: string
  p_long: number
  p_short: number
  p_neutral: number
}

type DashboardData = {
  totalPnl: number
  winRate: number
  currentDrawdown: number
  maxDrawdown: number
  activePositions: number
  totalEquity: number
  resolvedTrades: number
  winCount: number
  lossCount: number
  avgRR: number
  bestTrade: number
  worstTrade: number
  reputationScore: number
  reputationTrend: "up" | "down" | "flat"
  regimes: Record<string, RegimeInfo>
  symbolsTraded: string[]
  recentOutcomes: Trade[]
}

function fmt(n: number, decimals = 2) {
  return n.toLocaleString("en-US", { 
    minimumFractionDigits: decimals, 
    maximumFractionDigits: decimals 
  })
}

function trendIcon(t: "up" | "down" | "flat") {
  if (t === "up") return <span className="text-emerald-600">↑</span>
  if (t === "down") return <span className="text-red-600">↓</span>
  return <span className="text-zinc-500">→</span>
}

export default function DashboardPage() {
  const [data, setData] = useState<DashboardData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    api.dashboard.overview()
      .then(d => { 
        setData(d); 
        setError(null) 
      })
      .catch(() => setError("Failed to load dashboard"))
      .finally(() => setLoading(false))
  }, [])

  if (loading) return (
    <div className="min-h-screen flex items-center justify-center font-mono text-sm text-zinc-500">
      loading...
    </div>
  )

  if (error || !data) return (
    <div className="min-h-screen flex items-center justify-center font-mono text-sm text-red-600">
      {error ?? "No data available"}
    </div>
  )

  const startEquity = data.totalEquity - data.totalPnl || 1
  const pnlPct = ((data.totalPnl / startEquity) * 100).toFixed(1)

  return (
    <div className="flex flex-col min-h-screen bg-white">

      <div className="flex-1 p-8 lg:p-12">

        {/* Header */}
        <div className="border-b border-zinc-100 pb-12 mb-12">
          <div className="text-[10px] font-mono tracking-[0.125em] text-zinc-500 uppercase mb-2">
            SYSTEM HEALTH
          </div>
          <div className="flex items-baseline gap-4">
            <div className="text-5xl font-semibold text-black tracking-tighter">
              ${fmt(data.totalPnl)}
            </div>
            <div className={`text-2xl font-medium ${data.totalPnl >= 0 ? "text-emerald-600" : "text-red-600"}`}>
              {data.totalPnl >= 0 ? "+" : ""}{pnlPct}%
            </div>
          </div>
        </div>

        {/* KPI Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-6 mb-12">
          {[
            { label: "WIN RATE",     value: `${data.winRate.toFixed(1)}%`,        color: "text-black" },
            { label: "CURRENT DD",   value: `${data.currentDrawdown.toFixed(1)}%`, color: "text-red-600" },
            { label: "ACTIVE POS",   value: data.activePositions.toString(),       color: "text-black" },
            { label: "TOTAL EQUITY", value: `$${fmt(data.totalEquity)}`,           color: "text-black" },
            { 
              label: "REPUTATION", 
              value: `${data.reputationScore.toFixed(2)}`, 
              suffix: trendIcon(data.reputationTrend),
              color: "text-black" 
            },
          ].map((k, i) => (
            <div 
              key={i} 
              className="bg-white border border-zinc-200 rounded-2xl p-8 hover:border-zinc-300 transition-all"
            >
              <div className="text-xs font-mono tracking-widest text-zinc-500 uppercase mb-4">
                {k.label}
              </div>
              <div className={`text-3xl font-semibold tracking-tight ${k.color}`}>
                {k.value}
                {k.suffix && <span className="ml-3 text-2xl align-middle">{k.suffix}</span>}
              </div>
            </div>
          ))}
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 mb-12">
          
          {/* Trade Summary */}
          <div className="bg-white border border-zinc-200 rounded-2xl p-8">
            <div className="text-xs font-mono tracking-widest text-zinc-500 uppercase mb-6">
              TRADE SUMMARY
            </div>
            <div className="space-y-5 text-[15px] text-black">
              <div className="flex justify-between">
                <span className="text-zinc-500">Resolved trades</span>
                <span className="font-medium">{data.resolvedTrades}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-zinc-500">Wins</span>
                <span className="font-medium text-emerald-600">{data.winCount}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-zinc-500">Losses</span>
                <span className="font-medium text-red-600">{data.lossCount}</span>
              </div>
              <div className="flex justify-between pt-4 border-t border-zinc-100">
                <span className="text-zinc-500">Average R:R</span>
                <span className="font-medium">{data.avgRR.toFixed(2)}</span>
              </div>
            </div>
          </div>

          {/* Best / Worst */}
          <div className="bg-white border border-zinc-200 rounded-2xl p-8">
            <div className="text-xs font-mono tracking-widest text-zinc-500 uppercase mb-6">
              BEST &amp; WORST
            </div>
            <div className="space-y-5 text-[15px] text-black">
              <div className="flex justify-between">
                <span className="text-zinc-500">Best trade</span>
                <span className="font-medium text-emerald-600">+${fmt(data.bestTrade)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-zinc-500">Worst trade</span>
                <span className="font-medium text-red-600">-${fmt(Math.abs(data.worstTrade))}</span>
              </div>
              <div className="flex justify-between pt-4 border-t border-zinc-100">
                <span className="text-zinc-500">Maximum drawdown</span>
                <span className="font-medium text-red-600">{data.maxDrawdown.toFixed(1)}%</span>
              </div>
            </div>
          </div>

          {/* Recent Outcomes */}
          <div className="bg-white border border-zinc-200 rounded-2xl p-8">
            <div className="text-xs font-mono tracking-widest text-zinc-500 uppercase mb-6">
              RECENT OUTCOMES
            </div>
            <div className="space-y-3 text-sm font-mono">
              {data.recentOutcomes.length === 0 ? (
                <div className="text-zinc-400 py-6">No recent trades yet</div>
              ) : (
                data.recentOutcomes.map((t) => (
                  <div key={t.id} className="flex justify-between py-1">
                    <span className="text-zinc-500">{t.symbol}</span>
                    <span className={t.pnl >= 0 ? "text-emerald-600" : "text-red-600 font-medium"}>
                      {t.pnl >= 0 ? "+" : ""}{fmt(t.pnl)}
                    </span>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>

        {/* Regimes Section */}
        <div className="bg-white border border-zinc-200 rounded-2xl p-8">
          <div className="text-xs font-mono tracking-widest text-zinc-500 uppercase mb-7">
            CURRENT MARKET REGIMES
          </div>
          
          {Object.keys(data.regimes).length === 0 ? (
            <div className="text-zinc-400 font-mono text-sm py-12 text-center">
              No regime data available
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
              {Object.entries(data.regimes).map(([symbol, r]) => (
                <div 
                  key={symbol} 
                  className="border border-zinc-100 rounded-xl p-6 hover:border-zinc-200 transition-colors"
                >
                  <div className="font-mono font-semibold text-lg text-black mb-5">
                    {symbol}
                  </div>
                  
                  <div className="text-sm font-mono space-y-3 text-zinc-600">
                    <div>
                      Direction: <span className="text-black font-medium">{r.direction ?? "—"}</span>
                    </div>
                    
                    <div className="flex gap-6 pt-2">
                      <div>
                        <span className="text-emerald-600 mr-1">L</span>
                        <span className="font-medium text-black">{(r.p_long * 100).toFixed(0)}%</span>
                      </div>
                      <div>
                        <span className="text-red-600 mr-1">S</span>
                        <span className="font-medium text-black">{(r.p_short * 100).toFixed(0)}%</span>
                      </div>
                      <div>
                        <span className="text-zinc-400 mr-1">N</span>
                        <span className="font-medium text-black">{(r.p_neutral * 100).toFixed(0)}%</span>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

      </div>
    </div>
  )
}