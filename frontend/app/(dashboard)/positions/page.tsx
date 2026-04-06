"use client"

import positionsData from "@/data/positions.json"
import { PositionPoint } from "@/types"

const positions = positionsData as PositionPoint[]

function fmt(n: number, d = 2) {
  return n.toLocaleString("en-US", { minimumFractionDigits: d, maximumFractionDigits: d })
}

function riskColor(r: number) {
  if (r > 2) return "#ef4444"
  if (r > 1.5) return "#f59e0b"
  return "#22c55e"
}

export default function PositionsPage() {
  const maxSize = Math.max(...positions.map(p => p.position_size))
  const avgSize = positions.reduce((s, p) => s + p.position_size, 0) / positions.length
  const avgRisk = positions.reduce((s, p) => s + p.risk_percent, 0) / positions.length
  const avgConf = positions.reduce((s, p) => s + p.confidence, 0) / positions.length

  const confBuckets = [
    { label: "0.6–0.7", min: 0.6, max: 0.7 },
    { label: "0.7–0.8", min: 0.7, max: 0.8 },
    { label: "0.8–0.9", min: 0.8, max: 0.9 },
    { label: "0.9–1.0", min: 0.9, max: 1.01 },
  ].map(b => {
    const pts = positions.filter(p => p.confidence >= b.min && p.confidence < b.max)
    return {
      ...b,
      avgRisk: pts.length ? pts.reduce((s, p) => s + p.risk_percent, 0) / pts.length : 0,
      count: pts.length,
    }
  })

  const maxBucketRisk = Math.max(...confBuckets.map(b => b.avgRisk), 0.01)
  const cell: React.CSSProperties = { padding: "6px 10px", whiteSpace: "nowrap" }

  return (
    <div style={{ padding: "1.25rem", background: "#0a0a0a", minHeight: "100vh" }}>

      <div style={{ marginBottom: "1.25rem" }}>
        <p style={{ fontSize: "11px", fontFamily: "monospace", color: "#52525b", letterSpacing: ".1em", textTransform: "uppercase" }}>Position Sizing</p>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(130px, 1fr))", gap: "10px", marginBottom: "1rem" }}>
        {[
          { label: "avg size", value: `$${fmt(avgSize, 0)}` },
          { label: "avg risk", value: `${fmt(avgRisk)}%` },
          { label: "avg conf", value: `${(avgConf * 100).toFixed(0)}%` },
          { label: "total", value: positions.length },
        ].map(c => (
          <div key={c.label} style={{ background: "#111111", border: "0.5px solid #1f1f1f", borderRadius: "10px", padding: ".85rem 1rem" }}>
            <p style={{ fontSize: "11px", fontFamily: "monospace", color: "#52525b", marginBottom: "4px" }}>{c.label}</p>
            <p style={{ fontSize: "18px", fontWeight: 600, fontFamily: "monospace", color: "#e4e4e7" }}>{c.value}</p>
          </div>
        ))}
      </div>

      <div style={{ background: "#111111", border: "0.5px solid #1f1f1f", borderRadius: "10px", padding: "1rem 1.25rem", marginBottom: "1rem" }}>
        <p style={{ fontSize: "11px", fontFamily: "monospace", color: "#52525b", letterSpacing: ".08em", textTransform: "uppercase", marginBottom: "1rem" }}>position size over time</p>
        <div style={{ overflowX: "auto" }}>
          <div style={{ display: "flex", alignItems: "flex-end", gap: "6px", minWidth: "500px", height: "120px" }}>
            {[...positions].reverse().map((p, i) => {
              const h = Math.max(6, (p.position_size / maxSize) * 96)
              return (
                <div key={i} style={{ flex: 1, display: "flex", flexDirection: "column", alignItems: "center", gap: "4px", minWidth: "24px" }}>
                  <div
                    title={`$${fmt(p.position_size, 0)} | risk ${p.risk_percent}% | conf ${(p.confidence * 100).toFixed(0)}%`}
                    style={{ width: "100%", height: `${h}px`, background: riskColor(p.risk_percent), borderRadius: "2px 2px 0 0", opacity: 0.85 }}
                  />
                  <span style={{ fontSize: "9px", fontFamily: "monospace", color: "#3f3f46" }}>
                    {new Date(p.timestamp).getHours()}h
                  </span>
                </div>
              )
            })}
          </div>
        </div>
        <div style={{ display: "flex", gap: "16px", marginTop: "10px", flexWrap: "wrap" }}>
          {[{ label: "risk > 2%", color: "#ef4444" }, { label: "1.5–2%", color: "#f59e0b" }, { label: "< 1.5%", color: "#22c55e" }].map(l => (
            <span key={l.label} style={{ display: "flex", alignItems: "center", gap: "5px", fontSize: "11px", fontFamily: "monospace", color: "#71717a" }}>
              <span style={{ width: "8px", height: "8px", borderRadius: "2px", background: l.color, display: "inline-block" }} />
              {l.label}
            </span>
          ))}
        </div>
      </div>

      <div style={{ background: "#111111", border: "0.5px solid #1f1f1f", borderRadius: "10px", padding: "1rem 1.25rem", marginBottom: "1rem" }}>
        <p style={{ fontSize: "11px", fontFamily: "monospace", color: "#52525b", letterSpacing: ".08em", textTransform: "uppercase", marginBottom: "1rem" }}>risk % by confidence band</p>
        <div style={{ display: "flex", alignItems: "flex-end", gap: "12px", height: "100px" }}>
          {confBuckets.map(b => (
            <div key={b.label} style={{ flex: 1, display: "flex", flexDirection: "column", alignItems: "center", gap: "6px" }}>
              <span style={{ fontSize: "10px", fontFamily: "monospace", color: "#71717a" }}>{fmt(b.avgRisk)}%</span>
              <div style={{
                width: "100%",
                height: `${Math.max(4, (b.avgRisk / maxBucketRisk) * 60)}px`,
                background: riskColor(b.avgRisk),
                borderRadius: "2px 2px 0 0",
                opacity: 0.85,
              }} />
              <span style={{ fontSize: "10px", fontFamily: "monospace", color: "#52525b" }}>{b.label}</span>
            </div>
          ))}
        </div>
      </div>

      <div style={{ background: "#111111", border: "0.5px solid #1f1f1f", borderRadius: "10px", padding: "1rem 1.25rem" }}>
        <p style={{ fontSize: "11px", fontFamily: "monospace", color: "#52525b", letterSpacing: ".08em", textTransform: "uppercase", marginBottom: ".75rem" }}>all positions</p>
        <div style={{ overflowX: "auto" }}>
          <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "12px", fontFamily: "monospace" }}>
            <thead>
              <tr style={{ borderBottom: "0.5px solid #1f1f1f" }}>
                {["time", "size", "risk %", "confidence", "risk bar"].map(h => (
                  <th key={h} style={{ ...cell, textAlign: "left", color: "#52525b", fontWeight: 500 }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {[...positions].reverse().map((p, i) => (
                <tr key={i} style={{ borderBottom: "0.5px solid #141414" }}>
                  <td style={{ ...cell, color: "#71717a" }}>{new Date(p.timestamp).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}</td>
                  <td style={{ ...cell, color: "#e4e4e7" }}>${fmt(p.position_size, 0)}</td>
                  <td style={{ ...cell, color: riskColor(p.risk_percent), fontWeight: 500 }}>{p.risk_percent}%</td>
                  <td style={{ ...cell, color: "#a1a1aa" }}>{(p.confidence * 100).toFixed(0)}%</td>
                  <td style={{ ...cell, minWidth: "100px" }}>
                    <div style={{ height: "4px", background: "#1f1f1f", borderRadius: "2px", overflow: "hidden" }}>
                      <div style={{ height: "100%", width: `${(p.risk_percent / 3) * 100}%`, background: riskColor(p.risk_percent), borderRadius: "2px" }} />
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}