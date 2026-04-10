"use client"

import React, { useState, useEffect } from "react"

type Checkpoint = {
  id: string
  timestamp: string
  action: "BUY" | "SELL" | "HOLD"
  symbol: string
  amount: number
  price: number
  confidence: number
  reasoning: string
  signatureValid: boolean
  reasoningHash: string
  txHash?: string
}

export default function CheckpointsPage() {
  const [checkpoints, setCheckpoints] = useState<Checkpoint[]>([])
  const [filter, setFilter] = useState<"all" | "BUY" | "SELL" | "HOLD">("all")
  const [search, setSearch] = useState("")

  useEffect(() => {
    const mockData: Checkpoint[] = [
      {
        id: "cp_001",
        timestamp: "2026-04-10T14:32:18Z",
        action: "BUY",
        symbol: "BTCUSDT",
        amount: 1240,
        price: 82750,
        confidence: 0.87,
        reasoning: "Strong bullish momentum on 15m chart. Price broke above key resistance with high volume. RSI not overbought.",
        signatureValid: true,
        reasoningHash: "0x8f3a9b2c7d1e4f6a8b9c2d1e4f6a8b9c2d1e4f6a",
        txHash: "0x7d8e9f2a1b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f"
      },
      {
        id: "cp_002",
        timestamp: "2026-04-10T13:15:42Z",
        action: "SELL",
        symbol: "ETHUSDT",
        amount: 890,
        price: 1624.75,
        confidence: 0.79,
        reasoning: "Resistance level reached. Bearish divergence on MACD. Taking profit before potential reversal.",
        signatureValid: true,
        reasoningHash: "0x2c4d6e8f0a1b3c5d7e9f1a2b3c4d5e6f7a8b9c0d",
        txHash: "0x1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c"
      },
      {
        id: "cp_003",
        timestamp: "2026-04-10T11:47:09Z",
        action: "HOLD",
        symbol: "SOLUSDT",
        amount: 0,
        price: 142.35,
        confidence: 0.44,
        reasoning: "No clear edge. Market in consolidation phase. Waiting for breakout confirmation.",
        signatureValid: true,
        reasoningHash: "0x9f8e7d6c5b4a3f2e1d0c9b8a7f6e5d4c3b2a1f0e"
      }
    ]
    setCheckpoints(mockData)
  }, [])

  const filteredCheckpoints = checkpoints
    .filter(c => filter === "all" || c.action === filter)
    .filter(c => 
      c.symbol.toLowerCase().includes(search.toLowerCase()) || 
      c.reasoning.toLowerCase().includes(search.toLowerCase())
    )
    .sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime())

  return (
    <div>

      <div style={{ marginBottom: "2rem" }}>
        <div style={{ fontSize: "13px", color: "#6b7280", letterSpacing: ".06em", textTransform: "uppercase" }}>
          ON-CHAIN RECORD
        </div>
        <div style={{ fontSize: "26px", fontWeight: 700, color: "#111827", marginTop: "6px" }}>
          Checkpoints
        </div>
      </div>

      <div style={{ display: "flex", gap: "12px", marginBottom: "1.75rem", flexWrap: "wrap" }}>
        {(["all", "BUY", "SELL", "HOLD"] as const).map(f => (
          <button
            key={f}
            onClick={() => setFilter(f)}
            style={{
              padding: "8px 18px",
              borderRadius: "8px",
              border: "1px solid",
              fontSize: "13px",
              fontWeight: 500,
              cursor: "pointer",
              background: filter === f ? "#2563eb" : "#ffffff",
              color: filter === f ? "#ffffff" : "#374151",
              borderColor: filter === f ? "#2563eb" : "#d1d5db",
            }}
          >
            {f === "all" ? "All" : f}
          </button>
        ))}

        <input
          type="text"
          placeholder="Search symbol or reasoning..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          style={{
            flex: 1,
            minWidth: "260px",
            padding: "9px 16px",
            borderRadius: "8px",
            border: "1px solid #d1d5db",
            fontSize: "14px",
          }}
        />
      </div>

      <div style={{ 
        background: "#ffffff", 
        border: "1px solid #e5e5e5", 
        borderRadius: "12px"
      }}>
        {filteredCheckpoints.length === 0 ? (
          <div style={{ padding: "60px 20px", textAlign: "center", color: "#9ca3af" }}>
            No checkpoints found
          </div>
        ) : (
          filteredCheckpoints.map((cp, i) => (
            <div 
              key={cp.id}
              style={{
                padding: "22px 24px",
                borderBottom: i < filteredCheckpoints.length - 1 ? "1px solid #e5e5e5" : "none"
              }}
            >
              <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "14px" }}>
                <div style={{ display: "flex", alignItems: "center", gap: "14px" }}>
                  <span style={{
                    fontSize: "17px",
                    fontWeight: 700,
                    color: cp.action === "BUY" ? "#22c55e" : cp.action === "SELL" ? "#ef4444" : "#6b7280"
                  }}>
                    {cp.action}
                  </span>
                  <span style={{ fontSize: "17px", fontWeight: 600 }}>{cp.symbol}</span>
                </div>

                <div style={{ textAlign: "right" }}>
                  <div style={{ fontSize: "19px", fontWeight: 700 }}>
                    ${cp.amount.toLocaleString()}
                  </div>
                  <div style={{ fontSize: "13px", color: "#6b7280" }}>
                    @ ${cp.price.toLocaleString()}
                  </div>
                </div>
              </div>

              <div style={{ display: "flex", gap: "32px", marginBottom: "16px" }}>
                <div>
                  <div style={{ fontSize: "12px", color: "#6b7280" }}>CONFIDENCE</div>
                  <div style={{ fontSize: "21px", fontWeight: 600 }}>
                    {(cp.confidence * 100).toFixed(0)}%
                  </div>
                </div>

                <div style={{ flex: 1 }}>
                  <div style={{ fontSize: "12px", color: "#6b7280", marginBottom: "4px" }}>REASONING</div>
                  <div style={{ fontSize: "14.5px", lineHeight: "1.55", color: "#374151" }}>
                    {cp.reasoning}
                  </div>
                </div>
              </div>

              <div style={{ 
                fontSize: "12.5px", 
                color: "#6b7280", 
                display: "flex", 
                flexWrap: "wrap", 
                gap: "18px",
                paddingTop: "12px",
                borderTop: "1px solid #f3f4f6"
              }}>
                <div>
                  Signature: 
                  <span style={{
                    marginLeft: "6px",
                    padding: "2px 9px",
                    borderRadius: "9999px",
                    background: cp.signatureValid ? "#dcfce7" : "#fee2e2",
                    color: cp.signatureValid ? "#166534" : "#991b1b",
                    fontWeight: 500
                  }}>
                    {cp.signatureValid ? "VALID" : "INVALID"}
                  </span>
                </div>

                <div>
                  Hash: <span style={{ fontFamily: "monospace" }}>{cp.reasoningHash.slice(0, 14)}...</span>
                </div>

                {cp.txHash && (
                  <div>
                    Tx: <span style={{ fontFamily: "monospace", color: "#2563eb" }}>{cp.txHash.slice(0, 14)}...</span>
                  </div>
                )}
              </div>

              <div style={{ fontSize: "12.5px", color: "#9ca3af", marginTop: "10px" }}>
                {new Date(cp.timestamp).toLocaleString()}
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  )
}