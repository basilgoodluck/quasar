"use client"

import { useState } from "react"
import { Trade } from "@/types"

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
  expectedRR: number
  bestTrade: number
  worstTrade: number
  reputationScore: number
  reputationTrend: "up" | "down" | "flat"
  regimes: Record<string, any>
  activeAgents: string[]
  symbolsTraded: string[]
  currentLeverage: number
  currentRiskPct: number
  latestPositionSize: number
  recentSignals: Trade[]
  recentOutcomes: Trade[]
}

function fmt(n: number, decimals = 2) {
  return n.toLocaleString("en-US", { minimumFractionDigits: decimals, maximumFractionDigits: decimals })
}

const mockData: DashboardData = {
  totalPnl: 2847.65,
  winRate: 68.4,
  currentDrawdown: 6.8,
  maxDrawdown: 14.2,
  activePositions: 3,
  totalEquity: 18740,
  resolvedTrades: 87,
  winCount: 60,
  lossCount: 27,
  avgRR: 1.94,
  expectedRR: 2.0,
  bestTrade: 1240,
  worstTrade: -680,
  reputationScore: 86,
  reputationTrend: "up",
  regimes: {
    BTCUSDT: { state: "trending", direction: "bullish", strength: "strong" },
    ETHUSDT: { state: "ranging", direction: "neutral", strength: "medium" }
  },
  activeAgents: ["momentum", "breakout"],
  symbolsTraded: ["BTCUSDT", "ETHUSDT"],
  currentLeverage: 5.2,
  currentRiskPct: 1.4,
  latestPositionSize: 1240,
  recentSignals: [],
  recentOutcomes: [],
}

export default function DashboardPage() {
  const [data] = useState<DashboardData>(mockData)

  // Simple mock equity curve data
  const equityData = [
    15200, 15410, 15380, 15620, 15890, 15750, 16020, 16340,
    16210, 16580, 16890, 16720, 17050, 17380, 17240, 17610,
    17930, 17820, 18150, 18470, 18390, 18740
  ]

  const maxEquity = Math.max(...equityData)
  const minEquity = Math.min(...equityData)

  return (
    <div className="flex flex-col gap-6">

      <div>
        <div className="text-xs font-mono tracking-[0.08em] text-black uppercase">SYSTEM HEALTH</div>
        <div className="text-3xl font-bold text-black mt-1">
          ${fmt(data.totalPnl)}
          <span className={`ml-3 text-xl ${data.totalPnl >= 0 ? "text-green-600" : "text-red-600"}`}>
            {data.totalPnl >= 0 ? "+" : ""}{((data.totalPnl / (data.totalEquity - data.totalPnl || 1)) * 100).toFixed(1)}%
          </span>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
        <div className="bg-white border border-zinc-200 rounded-2xl p-6">
          <div className="text-xs font-mono tracking-widest text-black uppercase">WIN RATE</div>
          <div className="text-3xl font-bold text-black mt-2">{data.winRate.toFixed(1)}%</div>
        </div>

        <div className="bg-white border border-zinc-200 rounded-2xl p-6">
          <div className="text-xs font-mono tracking-widest text-black uppercase">DRAWDOWN</div>
          <div className="text-3xl font-bold text-red-600 mt-2">{data.currentDrawdown.toFixed(1)}%</div>
        </div>

        <div className="bg-white border border-zinc-200 rounded-2xl p-6">
          <div className="text-xs font-mono tracking-widest text-black uppercase">ACTIVE</div>
          <div className="text-3xl font-bold text-black mt-2">{data.activePositions}</div>
        </div>

        <div className="bg-white border border-zinc-200 rounded-2xl p-6">
          <div className="text-xs font-mono tracking-widest text-black uppercase">EQUITY</div>
          <div className="text-3xl font-bold text-black mt-2">${fmt(data.totalEquity)}</div>
        </div>

        <div className="bg-white border border-zinc-200 rounded-2xl p-6">
          <div className="text-xs font-mono tracking-widest text-black uppercase">REPUTATION</div>
          <div className="text-3xl font-bold text-black mt-2">{data.reputationScore}</div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 bg-white border border-zinc-200 rounded-2xl p-6">
          <div className="text-xs font-mono tracking-widest text-black uppercase mb-4">EQUITY CURVE</div>
          
          <div className="h-64 bg-white relative border border-zinc-100 rounded-xl overflow-hidden">
            <div className="absolute inset-0 flex items-end px-4 pb-4 gap-1">
              {equityData.map((value, i) => {
                const height = ((value - minEquity) / (maxEquity - minEquity)) * 100
                return (
                  <div 
                    key={i}
                    className="flex-1 bg-green-500 rounded-t transition-all"
                    style={{ height: `${height}%` }}
                  />
                )
              })}
            </div>
          </div>
        </div>

        <div className="space-y-4">
          <div className="bg-white border border-zinc-200 rounded-2xl p-6">
            <div className="text-xs font-mono tracking-widest text-black uppercase">AVG R/R</div>
            <div className="text-3xl font-bold text-black mt-2">{data.avgRR.toFixed(2)}</div>
          </div>

          <div className="bg-white border border-zinc-200 rounded-2xl p-6">
            <div className="text-xs font-mono tracking-widest text-black uppercase">BEST / WORST</div>
            <div className="mt-4 space-y-2 text-sm text-black">
              <div>Best: <span className="text-green-600">+${fmt(data.bestTrade)}</span></div>
              <div>Worst: <span className="text-red-600">- ${fmt(Math.abs(data.worstTrade))}</span></div>
            </div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white border border-zinc-200 rounded-2xl p-6">
          <div className="text-xs font-mono tracking-widest text-black uppercase mb-4">CURRENT REGIMES</div>
          <div className="space-y-3 text-base text-black">
            <div>BTCUSDT — trending • bullish • strong</div>
            <div>ETHUSDT — ranging • neutral • medium</div>
          </div>
        </div>

        <div className="bg-white border border-zinc-200 rounded-2xl p-6">
          <div className="text-xs font-mono tracking-widest text-black uppercase mb-4">RISK STATE</div>
          <div className="space-y-3 text-base text-black">
            <div>Leverage: {data.currentLeverage}x</div>
            <div>Risk: {data.currentRiskPct}%</div>
            <div>Size: ${fmt(data.latestPositionSize)}</div>
          </div>
        </div>
      </div>

      <div className="bg-white border border-zinc-200 rounded-2xl p-6">
        <div className="text-xs font-mono tracking-widest text-black uppercase mb-4">RECENT ACTIVITY</div>
        <div className="grid grid-cols-2 gap-8 text-base text-black">
          <div>Last 5 signals</div>
          <div>Last 5 outcomes</div>
        </div>
      </div>

    </div>
  )
}