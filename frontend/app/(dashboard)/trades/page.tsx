"use client"

import { useEffect, useRef, useState, useCallback } from "react"
import {
  createChart,
  createSeriesMarkers,
  IChartApi,
  ISeriesApi,
  ISeriesMarkersPluginApi,
  CandlestickSeries,
  LineSeries,
  UTCTimestamp,
  SeriesMarker,
  Time,
} from "lightweight-charts"
import tradesData from "@/data/trades.json"
import { Trade } from "@/types"

const trades = tradesData as Trade[]
const INTERVAL = "1m"

type Candle = { time: UTCTimestamp; open: number; high: number; low: number; close: number }

function decisionColor(d: string) {
  if (d === "approved") return "#22c55e"
  if (d === "rejected") return "#ef4444"
  return "#f59e0b"
}

function fmt(n: number, decimals = 2) {
  return n.toLocaleString("en-US", { minimumFractionDigits: decimals, maximumFractionDigits: decimals })
}

export default function TradesPage() {
  const chartContainerRef = useRef<HTMLDivElement>(null)
  const chartRef = useRef<IChartApi | null>(null)
  const candleSeriesRef = useRef<ISeriesApi<"Candlestick"> | null>(null)
  const lineSeriesRef = useRef<ISeriesApi<"Line"> | null>(null)
  const markersPluginRef = useRef<ISeriesMarkersPluginApi<Time> | null>(null)
  const wsRef = useRef<WebSocket | null>(null)
  const candleMapRef = useRef<Map<number, Candle>>(new Map())

  const [connected, setConnected] = useState(false)
  const [lastPrice, setLastPrice] = useState<number | null>(null)
  const [selectedSymbol, setSelectedSymbol] = useState("BTCUSDT")
  const [filterDecision, setFilterDecision] = useState("all")

  const filteredTrades = filterDecision === "all" ? trades : trades.filter(t => t.decision === filterDecision)

  const buildMarkers = useCallback((tradeList: Trade[]): SeriesMarker<Time>[] => {
    return tradeList
      .filter(t => t.symbol === selectedSymbol)
      .sort((a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime())
      .map(t => ({
        time: Math.floor(new Date(t.timestamp).getTime() / 1000) as UTCTimestamp,
        position: t.side === "BUY" ? "belowBar" : "aboveBar",
        color: decisionColor(t.decision),
        shape: t.side === "BUY" ? "arrowUp" : "arrowDown",
        text: `${t.side} ${t.pnl >= 0 ? "+" : ""}${fmt(t.pnl, 0)}`,
        id: t.id,
      })) as SeriesMarker<Time>[]
  }, [selectedSymbol])

  useEffect(() => {
    if (!chartContainerRef.current) return

    const chart = createChart(chartContainerRef.current, {
      width: chartContainerRef.current.clientWidth,
      height: 420,
      layout: { background: { color: "#111111" }, textColor: "#71717a", fontSize: 11, fontFamily: "monospace" },
      grid: { vertLines: { color: "#1a1a1a" }, horzLines: { color: "#1a1a1a" } },
      crosshair: { mode: 1 },
      rightPriceScale: { borderColor: "#1f1f1f" },
      timeScale: { borderColor: "#1f1f1f", timeVisible: true, secondsVisible: false },
    })

    const candleSeries = chart.addSeries(CandlestickSeries, {
      upColor: "#22c55e", downColor: "#ef4444",
      borderUpColor: "#22c55e", borderDownColor: "#ef4444",
      wickUpColor: "#22c55e", wickDownColor: "#ef4444",
    })

    const lineSeries = chart.addSeries(LineSeries, {
      color: "transparent", lineWidth: 0, priceLineVisible: false, lastValueVisible: false,
    })

    chartRef.current = chart
    candleSeriesRef.current = candleSeries
    lineSeriesRef.current = lineSeries

    // v5: create markers plugin instance on the candleSeries
    markersPluginRef.current = createSeriesMarkers(candleSeries, [])

    fetch(`https://api.binance.com/api/v3/klines?symbol=${selectedSymbol}&interval=${INTERVAL}&limit=120`)
      .then(r => r.json())
      .then((raw: unknown[][]) => {
        const candles: Candle[] = raw.map(k => ({
          time: Math.floor(Number(k[0]) / 1000) as UTCTimestamp,
          open: parseFloat(k[1] as string),
          high: parseFloat(k[2] as string),
          low: parseFloat(k[3] as string),
          close: parseFloat(k[4] as string),
        }))
        candles.forEach(c => candleMapRef.current.set(c.time as number, c))
        candleSeries.setData(candles)
        lineSeries.setData(candles.map(c => ({ time: c.time, value: c.close })))
        markersPluginRef.current?.setMarkers(buildMarkers(trades))
        chart.timeScale().fitContent()
      })

    const ro = new ResizeObserver(entries => {
      chart.applyOptions({ width: entries[0].contentRect.width })
    })
    ro.observe(chartContainerRef.current)

    return () => {
      ro.disconnect()
      markersPluginRef.current = null
      chart.remove()
    }
  }, [selectedSymbol, buildMarkers])

  useEffect(() => {
    markersPluginRef.current?.setMarkers(buildMarkers(filteredTrades))
  }, [filteredTrades, buildMarkers])

  useEffect(() => {
    const ws = new WebSocket(`wss://stream.binance.com:9443/ws/${selectedSymbol.toLowerCase()}@kline_${INTERVAL}`)
    wsRef.current = ws
    ws.onopen = () => setConnected(true)
    ws.onclose = () => setConnected(false)
    ws.onerror = () => setConnected(false)
    ws.onmessage = (e) => {
      const { k } = JSON.parse(e.data)
      const candle: Candle = {
        time: Math.floor(k.t / 1000) as UTCTimestamp,
        open: parseFloat(k.o), high: parseFloat(k.h),
        low: parseFloat(k.l), close: parseFloat(k.c),
      }
      setLastPrice(candle.close)
      candleMapRef.current.set(candle.time as number, candle)
      candleSeriesRef.current?.update(candle)
      lineSeriesRef.current?.update({ time: candle.time, value: candle.close })
    }
    return () => ws.close()
  }, [selectedSymbol])

  const hourlyVolume = Array.from({ length: 24 }, (_, h) => ({
    hour: h,
    volume: trades.filter(t => t.hour === h).reduce((s, t) => s + t.volume, 0),
  })).filter(h => h.volume > 0)
  const maxVol = Math.max(...hourlyVolume.map(h => h.volume))
  const cell: React.CSSProperties = { padding: "6px 10px", whiteSpace: "nowrap" }

  return (
    <div style={{ padding: "1.25rem", background: "#0a0a0a", minHeight: "100vh" }}>

      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "1.25rem", flexWrap: "wrap", gap: "8px" }}>
        <div>
          <p style={{ fontSize: "11px", fontFamily: "monospace", color: "#52525b", letterSpacing: ".1em", textTransform: "uppercase", marginBottom: "2px" }}>Trade Activity</p>
          <p style={{ fontSize: "20px", fontWeight: 600, color: "#e4e4e7", fontFamily: "monospace" }}>
            {lastPrice ? `$${fmt(lastPrice)}` : "—"}
            <span style={{ fontSize: "12px", color: "#52525b", marginLeft: "8px" }}>{selectedSymbol}</span>
          </p>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: "10px", flexWrap: "wrap" }}>
          <span style={{
            fontSize: "11px", fontFamily: "monospace", padding: "3px 10px", borderRadius: "20px",
            background: connected ? "#14532d" : "#450a0a",
            color: connected ? "#22c55e" : "#ef4444",
          }}>{connected ? "live" : "disconnected"}</span>
          <select value={filterDecision} onChange={e => setFilterDecision(e.target.value)}
            style={{ fontSize: "12px", fontFamily: "monospace", padding: "4px 8px", borderRadius: "6px", border: "0.5px solid #1f1f1f", background: "#111111", color: "#e4e4e7" }}>
            <option value="all">all</option>
            <option value="approved">approved</option>
            <option value="rejected">rejected</option>
            <option value="skipped">skipped</option>
          </select>
        </div>
      </div>

      <div style={{ background: "#111111", border: "0.5px solid #1f1f1f", borderRadius: "10px", padding: "1rem", marginBottom: "1rem" }}>
        <div style={{ display: "flex", gap: "8px", marginBottom: "10px", flexWrap: "wrap" }}>
          {["BTCUSDT", "ETHUSDT", "SOLUSDT", "XRPUSDT", "ADAUSDT"].map(s => (
            <button key={s} onClick={() => setSelectedSymbol(s)} style={{
              fontSize: "11px", fontFamily: "monospace", padding: "3px 10px", borderRadius: "6px",
              border: "0.5px solid", cursor: "pointer",
              borderColor: selectedSymbol === s ? "#3b82f6" : "#1f1f1f",
              background: selectedSymbol === s ? "#1e3a5f" : "transparent",
              color: selectedSymbol === s ? "#93c5fd" : "#71717a",
            }}>{s}</button>
          ))}
        </div>
        <div ref={chartContainerRef} style={{ width: "100%" }} />
        <div style={{ display: "flex", gap: "16px", marginTop: "10px", flexWrap: "wrap" }}>
          {[{ label: "approved", color: "#22c55e" }, { label: "rejected", color: "#ef4444" }, { label: "skipped", color: "#f59e0b" }].map(l => (
            <span key={l.label} style={{ display: "flex", alignItems: "center", gap: "5px", fontSize: "11px", fontFamily: "monospace", color: "#71717a" }}>
              <span style={{ width: "8px", height: "8px", borderRadius: "2px", background: l.color, display: "inline-block" }} />
              {l.label}
            </span>
          ))}
        </div>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))", gap: "1rem", marginBottom: "1rem" }}>
        <div style={{ background: "#111111", border: "0.5px solid #1f1f1f", borderRadius: "10px", padding: "1rem 1.25rem" }}>
          <p style={{ fontSize: "11px", fontFamily: "monospace", color: "#52525b", letterSpacing: ".08em", textTransform: "uppercase", marginBottom: ".75rem" }}>volume / hour</p>
          <div style={{ display: "flex", alignItems: "flex-end", gap: "4px", height: "80px" }}>
            {hourlyVolume.map(h => (
              <div key={h.hour} style={{ flex: 1, display: "flex", flexDirection: "column", alignItems: "center", gap: "3px" }}>
                <div style={{ width: "100%", background: "#1e3a5f", height: `${Math.max(4, (h.volume / maxVol) * 64)}px`, borderRadius: "2px 2px 0 0" }} />
                <span style={{ fontSize: "9px", fontFamily: "monospace", color: "#3f3f46" }}>{h.hour}</span>
              </div>
            ))}
          </div>
        </div>

        <div style={{ background: "#111111", border: "0.5px solid #1f1f1f", borderRadius: "10px", padding: "1rem 1.25rem" }}>
          <p style={{ fontSize: "11px", fontFamily: "monospace", color: "#52525b", letterSpacing: ".08em", textTransform: "uppercase", marginBottom: ".75rem" }}>decision breakdown</p>
          <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
            {(["approved", "rejected", "skipped"] as const).map(d => {
              const count = trades.filter(t => t.decision === d).length
              const pct = Math.round((count / trades.length) * 100)
              return (
                <div key={d} style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                  <span style={{ fontSize: "11px", fontFamily: "monospace", color: "#71717a", width: "56px" }}>{d}</span>
                  <div style={{ flex: 1, height: "5px", background: "#1a1a1a", borderRadius: "3px", overflow: "hidden" }}>
                    <div style={{ height: "100%", width: `${pct}%`, background: decisionColor(d), borderRadius: "3px" }} />
                  </div>
                  <span style={{ fontSize: "11px", fontFamily: "monospace", color: "#52525b", width: "28px", textAlign: "right" }}>{count}</span>
                </div>
              )
            })}
          </div>
        </div>
      </div>

      <div style={{ background: "#111111", border: "0.5px solid #1f1f1f", borderRadius: "10px", padding: "1rem 1.25rem" }}>
        <p style={{ fontSize: "11px", fontFamily: "monospace", color: "#52525b", letterSpacing: ".08em", textTransform: "uppercase", marginBottom: ".75rem" }}>
          recent trades <span style={{ color: "#3f3f46" }}>({filteredTrades.length})</span>
        </p>
        <div style={{ overflowX: "auto" }}>
          <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "12px", fontFamily: "monospace" }}>
            <thead>
              <tr style={{ borderBottom: "0.5px solid #1f1f1f" }}>
                {["time", "symbol", "side", "entry", "exit", "pnl", "conf", "decision"].map(h => (
                  <th key={h} style={{ ...cell, textAlign: "left", color: "#52525b", fontWeight: 500 }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {filteredTrades.slice(0, 20).map(t => (
                <tr key={t.id} style={{ borderBottom: "0.5px solid #141414" }}>
                  <td style={{ ...cell, color: "#71717a" }}>{new Date(t.timestamp).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}</td>
                  <td style={{ ...cell, color: "#a1a1aa" }}>{t.symbol}</td>
                  <td style={{ ...cell, color: t.side === "BUY" ? "#22c55e" : "#ef4444" }}>{t.side}</td>
                  <td style={{ ...cell, color: "#71717a" }}>{fmt(t.entry_price)}</td>
                  <td style={{ ...cell, color: "#71717a" }}>{fmt(t.exit_price)}</td>
                  <td style={{ ...cell, color: t.pnl >= 0 ? "#22c55e" : "#ef4444", fontWeight: 500 }}>{t.pnl >= 0 ? "+" : ""}{fmt(t.pnl)}</td>
                  <td style={{ ...cell, color: "#71717a" }}>{(t.confidence * 100).toFixed(0)}%</td>
                  <td style={{ ...cell }}>
                    <span style={{
                      fontSize: "10px", padding: "2px 8px", borderRadius: "10px",
                      background: t.decision === "approved" ? "#14532d" : t.decision === "rejected" ? "#450a0a" : "#451a03",
                      color: t.decision === "approved" ? "#22c55e" : t.decision === "rejected" ? "#ef4444" : "#f59e0b",
                    }}>{t.decision}</span>
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