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
  return n.toLocaleString("en-US", { minimumFractionDigits: decimals, maximumFractionDigits: decimals })
}

function trendIcon(t: "up" | "down" | "flat") {
  if (t === "up") return <span style={{ color: "#22c55e" }}>↑</span>
  if (t === "down") return <span style={{ color: "#ef4444" }}>↓</span>
  return <span style={{ color: "#9ca3af" }}>→</span>
}

export default function DashboardPage() {
  const [data, setData] = useState<DashboardData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    api.dashboard.overview()
      .then(d => { setData(d); setError(null) })
      .catch(() => setError("failed to load dashboard"))
      .finally(() => setLoading(false))
  }, [])

  if (loading) return (
    <div style={{ padding: "60px", textAlign: "center", fontFamily: "monospace", color: "#9ca3af" }}>loading...</div>
  )

  if (error || !data) return (
    <div style={{ padding: "60px", textAlign: "center", fontFamily: "monospace", color: "#ef4444" }}>{error ?? "no data"}</div>
  )

  const startEquity = data.totalEquity - data.totalPnl || 1
  const pnlPct = ((data.totalPnl / startEquity) * 100).toFixed(1)

  return (
    <div className="flex flex-col gap-6">

      {/* Header */}
      <div>
        <div className="text-xs font-mono tracking-[0.08em] text-black uppercase">SYSTEM HEALTH</div>
        <div className="text-3xl font-bold text-black mt-1">
          ${fmt(data.totalPnl)}
          <span className={`ml-3 text-xl ${data.totalPnl >= 0 ? "text-green-600" : "text-red-600"}`}>
            {data.totalPnl >= 0 ? "+" : ""}{pnlPct}%
          </span>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
        {[
          { label: "WIN RATE",   value: `${data.winRate.toFixed(1)}%`,        color: "" },
          { label: "DRAWDOWN",   value: `${data.currentDrawdown.toFixed(1)}%`, color: "text-red-600" },
          { label: "ACTIVE",     value: `${data.activePositions}`,             color: "" },
          { label: "EQUITY",     value: `$${fmt(data.totalEquity)}`,           color: "" },
          { label: "REPUTATION", value: `${data.reputationScore.toFixed(2)} ${trendIcon(data.reputationTrend) as any}`, color: "" },
        ].map(k => (
          <div key={k.label} className="bg-white border border-zinc-200 rounded-2xl p-6">
            <div className="text-xs font-mono tracking-widest text-black uppercase">{k.label}</div>
            <div className={`text-3xl font-bold mt-2 ${k.color || "text-black"}`}>{k.value}</div>
          </div>
        ))}
      </div>

      {/* Stats row */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Win/Loss */}
        <div className="bg-white border border-zinc-200 rounded-2xl p-6">
          <div className="text-xs font-mono tracking-widest text-black uppercase mb-4">TRADE SUMMARY</div>
          <div className="space-y-3 text-base text-black">
            <div>Resolved: <span className="font-bold">{data.resolvedTrades}</span></div>
            <div>Wins: <span className="text-green-600 font-bold">{data.winCount}</span></div>
            <div>Losses: <span className="text-red-600 font-bold">{data.lossCount}</span></div>
            <div>Avg R/R: <span className="font-bold">{data.avgRR.toFixed(2)}</span></div>
          </div>
        </div>

        {/* Best / Worst */}
        <div className="bg-white border border-zinc-200 rounded-2xl p-6">
          <div className="text-xs font-mono tracking-widest text-black uppercase mb-4">BEST / WORST</div>
          <div className="space-y-3 text-base text-black">
            <div>Best: <span className="text-green-600 font-bold">+${fmt(data.bestTrade)}</span></div>
            <div>Worst: <span className="text-red-600 font-bold">-${fmt(Math.abs(data.worstTrade))}</span></div>
            <div>Max DD: <span className="text-red-600 font-bold">{data.maxDrawdown.toFixed(1)}%</span></div>
          </div>
        </div>

        {/* Recent outcomes */}
        <div className="bg-white border border-zinc-200 rounded-2xl p-6">
          <div className="text-xs font-mono tracking-widest text-black uppercase mb-4">RECENT OUTCOMES</div>
          <div className="space-y-2">
            {data.recentOutcomes.length === 0 ? (
              <div className="text-sm text-zinc-400 font-mono">no outcomes yet</div>
            ) : data.recentOutcomes.map(t => (
              <div key={t.id} className="flex justify-between text-sm font-mono">
                <span className="text-zinc-500">{t.symbol}</span>
                <span className={t.pnl >= 0 ? "text-green-600" : "text-red-600"}>
                  {t.pnl >= 0 ? "+" : ""}{fmt(t.pnl)}
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Regimes */}
      <div className="bg-white border border-zinc-200 rounded-2xl p-6">
        <div className="text-xs font-mono tracking-widest text-black uppercase mb-4">CURRENT REGIMES</div>
        {Object.keys(data.regimes).length === 0 ? (
          <div className="text-sm text-zinc-400 font-mono">no regime data</div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {Object.entries(data.regimes).map(([symbol, r]) => (
              <div key={symbol} className="border border-zinc-100 rounded-xl p-4">
                <div className="text-sm font-mono font-bold text-black mb-2">{symbol}</div>
                <div className="text-xs font-mono text-zinc-500 space-y-1">
                  <div>direction: <span className="text-black">{r.direction ?? "—"}</span></div>
                  <div className="flex gap-3 mt-2">
                    <span className="text-green-600">L {(r.p_long * 100).toFixed(0)}%</span>
                    <span className="text-red-500">S {(r.p_short * 100).toFixed(0)}%</span>
                    <span className="text-zinc-400">N {(r.p_neutral * 100).toFixed(0)}%</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

    </div>
  )
}