"use client"
import { useEffect, useRef, useState, useCallback, useMemo } from "react"
import {
  createChart,
  IChartApi,
  ISeriesApi,
  CandlestickSeries,
  LineSeries,
  UTCTimestamp,
  SeriesMarker,
  Time,
  createSeriesMarkers,
} from "lightweight-charts"
import { api } from "@/lib/api"
import { createTradeWebSocket, createBinanceWebSocket } from "@/lib/ws"
import { Trade } from "@/types"
import { config } from "@/config"

const INTERVAL = "5m"
const SYMBOLS = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "XRPUSDT", "ADAUSDT"]

type Candle = { time: UTCTimestamp; open: number; high: number; low: number; close: number }
type DecisionFilter = "all" | "approved" | "rejected" | "skipped"
type ChartTheme = "light" | "dark"

function decisionColor(d: string) {
  if (d === "approved") return "#22c55e"
  if (d === "rejected") return "#ef4444"
  return "#f59e0b"
}

function decisionBg(d: string) {
  if (d === "approved") return "#14532d"
  if (d === "rejected") return "#450a0a"
  return "#451a03"
}

function fmt(n: number, decimals = 2) {
  return n.toLocaleString("en-US", { minimumFractionDigits: decimals, maximumFractionDigits: decimals })
}

export default function TradesPage() {
  const chartContainerRef = useRef<HTMLDivElement>(null)
  const chartRef = useRef<IChartApi | null>(null)
  const candleSeriesRef = useRef<ISeriesApi<"Candlestick"> | null>(null)
  const lineSeriesRef = useRef<ISeriesApi<"Line"> | null>(null)
  const markersPluginRef = useRef<any>(null)
  const [lastPrice, setLastPrice] = useState<number | null>(null)
  const [selectedSymbol, setSelectedSymbol] = useState("BTCUSDT")
  const [filterDecision, setFilterDecision] = useState<DecisionFilter>("all")
  const [liveTrades, setLiveTrades] = useState<Trade[]>([])
  const [chartTheme, setChartTheme] = useState<ChartTheme>("light")

  const filteredTrades = useMemo(
    () => filterDecision === "all" ? liveTrades : liveTrades.filter(t => t.decision === filterDecision),
    [liveTrades, filterDecision]
  )

  const symbolTrades = useMemo(
    () => filteredTrades.filter(t => t.symbol === selectedSymbol),
    [filteredTrades, selectedSymbol]
  )

  const buildMarkers = useCallback((tradeList: Trade[]): SeriesMarker<Time>[] => {
    return tradeList
      .sort((a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime())
      .map(t => ({
        time: Math.floor(new Date(t.timestamp).getTime() / 1000) as UTCTimestamp,
        position: t.side === "BUY" ? "belowBar" : "aboveBar",
        color: decisionColor(t.decision),
        shape: t.side === "BUY" ? "arrowUp" : "arrowDown",
        text: `${t.side} ${t.pnl >= 0 ? "+" : ""}${fmt(t.pnl, 0)}`,
        id: t.id,
      }))
  }, [])

  useEffect(() => {
    api.dashboard.trades()
      .then(setLiveTrades)
      .catch(() => {
        import("@/data/trades.json").then(mod => setLiveTrades(mod.default as Trade[]))
      })
  }, [])

  useEffect(() => {
    const ws = createTradeWebSocket((msg) => {
      if (msg.type === "initial") setLiveTrades(msg.data)
      else if (msg.type === "new_trade") setLiveTrades(prev => [msg.data, ...prev])
    })
    return () => ws.close()
  }, [])

  const fetchHistoricalData = useCallback(async (symbol: string) => {
    try {
      const raw = await api.binance.klines(symbol, INTERVAL)
      const candles: Candle[] = raw.map(k => ({
        time: Math.floor(Number(k[0]) / 1000) as UTCTimestamp,
        open: parseFloat(k[1] as string),
        high: parseFloat(k[2] as string),
        low: parseFloat(k[3] as string),
        close: parseFloat(k[4] as string),
      }))
      candleSeriesRef.current?.setData(candles)
      lineSeriesRef.current?.setData(candles.map(c => ({ time: c.time, value: c.close })))
      const last = candles[candles.length - 1]
      if (last) setLastPrice(last.close)
      markersPluginRef.current?.setMarkers(buildMarkers(symbolTrades))
      chartRef.current?.timeScale().fitContent()
    } catch (err) {
      console.error(err)
    }
  }, [buildMarkers, symbolTrades])

  useEffect(() => {
    const ws = createBinanceWebSocket(selectedSymbol, INTERVAL, (msg) => {
      const k = msg.k
      if (!k) return
      const candle: Candle = {
        time: Math.floor(k.t / 1000) as UTCTimestamp,
        open: parseFloat(k.o), high: parseFloat(k.h),
        low: parseFloat(k.l), close: parseFloat(k.c),
      }
      candleSeriesRef.current?.update(candle)
      lineSeriesRef.current?.update({ time: candle.time, value: candle.close })
      setLastPrice(candle.close)
    })
    return () => ws.close()
  }, [selectedSymbol])

  useEffect(() => {
    if (!chartContainerRef.current) return
    const isDark = chartTheme === "dark"
    const chart = createChart(chartContainerRef.current, {
      width: chartContainerRef.current.clientWidth,
      height: 420,
      layout: {
        background: { color: isDark ? "#111111" : "#ffffff" },
        textColor: isDark ? "#a1a1aa" : "#52525b",
        fontSize: 11,
        fontFamily: "monospace"
      },
      grid: {
        vertLines: { color: isDark ? "#1f1f1f" : "#f1f1f1" },
        horzLines: { color: isDark ? "#1f1f1f" : "#f1f1f1" }
      },
      crosshair: { mode: 1 },
      rightPriceScale: { borderColor: isDark ? "#1f1f1f" : "#e5e5e5" },
      timeScale: { borderColor: isDark ? "#1f1f1f" : "#e5e5e5", timeVisible: true, secondsVisible: false },
    })
    const candleSeries = chart.addSeries(CandlestickSeries, {
      upColor: "#22c55e",
      downColor: "#ef4444",
      borderUpColor: "#22c55e",
      borderDownColor: "#ef4444",
      wickUpColor: "#22c55e",
      wickDownColor: "#ef4444",
    })
    const lineSeries = chart.addSeries(LineSeries, {
      color: isDark ? "#60a5fa" : "#3b82f6",
      lineWidth: 2,
    })
    const markersPlugin = createSeriesMarkers(candleSeries)
    chartRef.current = chart
    candleSeriesRef.current = candleSeries
    lineSeriesRef.current = lineSeries
    markersPluginRef.current = markersPlugin
    fetchHistoricalData(selectedSymbol)
    const ro = new ResizeObserver(entries => {
      chart.applyOptions({ width: entries[0].contentRect.width })
    })
    ro.observe(chartContainerRef.current)
    return () => { ro.disconnect(); chart.remove() }
  }, [chartTheme, selectedSymbol, fetchHistoricalData])

  useEffect(() => {
    markersPluginRef.current?.setMarkers(buildMarkers(symbolTrades))
  }, [symbolTrades, buildMarkers])

  const hourlyVolume = Array.from({ length: 24 }, (_, h) => ({
    hour: h,
    volume: liveTrades.filter(t => t.hour === h).reduce((s, t) => s + t.volume, 0),
  })).filter(h => h.volume > 0)

  const maxVol = hourlyVolume.length ? Math.max(...hourlyVolume.map(h => h.volume)) : 0

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "1.5rem" }}>
      <div style={{ display: "flex", alignItems: "flex-end", justifyContent: "space-between", flexWrap: "wrap", gap: "12px" }}>
        <div>
          <div style={{ fontSize: "11px", fontFamily: "monospace", color: "#6b7280", letterSpacing: ".08em", textTransform: "uppercase", marginBottom: "4px" }}>
            TRADE ACTIVITY
          </div>
          <div style={{ fontSize: "28px", fontWeight: 700, color: "#111827", margin: 0 }}>
            {lastPrice ? `$${fmt(lastPrice)}` : "0.0000"}
            <span style={{ fontSize: "15px", color: "#6b7280", marginLeft: "10px", fontWeight: 500 }}>{selectedSymbol}</span>
          </div>
        </div>
        <select
          value={filterDecision}
          onChange={e => setFilterDecision(e.target.value as DecisionFilter)}
          style={{
            fontSize: "13px",
            padding: "8px 14px",
            borderRadius: "8px",
            border: "1px solid #d1d5db",
            background: "#ffffff",
            color: "#374151",
            cursor: "pointer",
          }}
        >
          <option value="all">All Decisions</option>
          <option value="approved">Approved</option>
          <option value="rejected">Rejected</option>
          <option value="skipped">Skipped</option>
        </select>
      </div>

      <div style={{
        background: "#ffffff",
        border: "1px solid #e5e5e5",
        borderRadius: "12px",
        padding: "20px",
        position: "relative"
      }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "16px", flexWrap: "wrap", gap: "12px" }}>
          <div style={{ display: "flex", gap: "8px", flexWrap: "wrap" }}>
            {SYMBOLS.map(s => (
              <button
                key={s}
                onClick={() => setSelectedSymbol(s)}
                style={{
                  fontSize: "12px",
                  padding: "6px 14px",
                  borderRadius: "8px",
                  border: "1px solid",
                  cursor: "pointer",
                  borderColor: selectedSymbol === s ? "#2563eb" : "#d1d5db",
                  background: selectedSymbol === s ? "#eff6ff" : "#ffffff",
                  color: selectedSymbol === s ? "#1e40af" : "#6b7280",
                  fontWeight: selectedSymbol === s ? 600 : 400,
                }}
              >
                {s}
              </button>
            ))}
          </div>
          <button
            onClick={() => setChartTheme(chartTheme === "light" ? "dark" : "light")}
            style={{
              fontSize: "12px",
              padding: "6px 14px",
              borderRadius: "8px",
              border: "1px solid #d1d5db",
              background: chartTheme === "dark" ? "#111111" : "#ffffff",
              color: chartTheme === "dark" ? "#e4e4e7" : "#374151",
              cursor: "pointer",
              display: "flex",
              alignItems: "center",
              gap: "6px",
            }}
          >
            {chartTheme === "light" ? "🌙 Dark Chart" : "☀️ Light Chart"}
          </button>
        </div>
        <div
          ref={chartContainerRef}
          style={{
            width: "100%",
            height: "420px",
            borderRadius: "8px",
            overflow: "hidden"
          }}
        />
        <div style={{ display: "flex", gap: "20px", marginTop: "16px", flexWrap: "wrap" }}>
          {[
            { label: "approved", color: "#22c55e" },
            { label: "rejected", color: "#ef4444" },
            { label: "skipped", color: "#f59e0b" },
          ].map(item => (
            <div key={item.label} style={{ display: "flex", alignItems: "center", gap: "6px", fontSize: "12px", color: "#6b7280" }}>
              <span style={{ width: "10px", height: "10px", borderRadius: "3px", background: item.color }} />
              {item.label}
            </div>
          ))}
        </div>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))", gap: "1.25rem" }}>
        <div style={{
          background: "#ffffff",
          border: "1px solid #e5e5e5",
          borderRadius: "12px",
          padding: "20px"
        }}>
          <div style={{ fontSize: "11px", fontFamily: "monospace", color: "#6b7280", letterSpacing: ".08em", textTransform: "uppercase", marginBottom: "12px" }}>
            VOLUME / HOUR
          </div>
          <div style={{ display: "flex", alignItems: "flex-end", gap: "4px", height: "80px" }}>
            {hourlyVolume.map(h => (
              <div key={h.hour} style={{ flex: 1, display: "flex", flexDirection: "column", alignItems: "center", gap: "4px" }}>
                <div style={{
                  width: "100%",
                  background: "#3b82f6",
                  height: `${Math.max(4, (h.volume / maxVol) * 64)}px`,
                  borderRadius: "3px 3px 0 0",
                }} />
                <span style={{ fontSize: "10px", fontFamily: "monospace", color: "#9ca3af" }}>{h.hour}</span>
              </div>
            ))}
          </div>
        </div>

        <div style={{
          background: "#ffffff",
          border: "1px solid #e5e5e5",
          borderRadius: "12px",
          padding: "20px"
        }}>
          <div style={{ fontSize: "11px", fontFamily: "monospace", color: "#6b7280", letterSpacing: ".08em", textTransform: "uppercase", marginBottom: "14px" }}>
            DECISION BREAKDOWN
          </div>
          <div style={{ display: "flex", flexDirection: "column", gap: "14px" }}>
            {(["approved", "rejected", "skipped"] as const).map(d => {
              const count = liveTrades.filter(t => t.decision === d).length
              const pct = liveTrades.length ? Math.round((count / liveTrades.length) * 100) : 0
              return (
                <div key={d} style={{ display: "flex", alignItems: "center", gap: "12px" }}>
                  <span style={{ fontSize: "13px", color: "#374151", width: "70px", textTransform: "capitalize" }}>{d}</span>
                  <div style={{ flex: 1, height: "6px", background: "#f3f4f6", borderRadius: "9999px", overflow: "hidden" }}>
                    <div style={{ height: "100%", width: `${pct}%`, background: decisionColor(d), borderRadius: "9999px" }} />
                  </div>
                  <span style={{ fontSize: "13px", color: "#6b7280", width: "30px", textAlign: "right", fontWeight: 500 }}>{count}</span>
                </div>
              )
            })}
          </div>
        </div>
      </div>

      <div style={{
        background: "#ffffff",
        border: "1px solid #e5e5e5",
        borderRadius: "12px",
        padding: "20px"
      }}>
        <div style={{ fontSize: "11px", fontFamily: "monospace", color: "#6b7280", letterSpacing: ".08em", textTransform: "uppercase", marginBottom: "12px" }}>
          RECENT TRADES <span style={{ color: "#9ca3af" }}>({filteredTrades.length})</span>
        </div>
        <div style={{ overflowX: "auto" }}>
          <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "13px", fontFamily: "monospace" }}>
            <thead>
              <tr style={{ borderBottom: "1px solid #e5e5e5" }}>
                {["time", "symbol", "side", "entry", "exit", "pnl", "conf", "decision"].map(h => (
                  <th key={h} style={{ padding: "12px 10px", textAlign: "left", color: "#6b7280", fontWeight: 500 }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {filteredTrades.slice(0, 20).map(t => (
                <tr key={t.id} style={{ borderBottom: "1px solid #f3f4f6" }}>
                  <td style={{ padding: "12px 10px", color: "#6b7280" }}>
                    {new Date(t.timestamp).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                  </td>
                  <td style={{ padding: "12px 10px", color: "#374151" }}>{t.symbol}</td>
                  <td style={{ padding: "12px 10px", color: t.side === "BUY" ? "#22c55e" : "#ef4444", fontWeight: 600 }}>{t.side}</td>
                  <td style={{ padding: "12px 10px", color: "#6b7280" }}>{fmt(t.entry_price)}</td>
                  <td style={{ padding: "12px 10px", color: "#6b7280" }}>{fmt(t.exit_price)}</td>
                  <td style={{ padding: "12px 10px", color: t.pnl >= 0 ? "#22c55e" : "#ef4444", fontWeight: 600 }}>
                    {t.pnl >= 0 ? "+" : ""}{fmt(t.pnl)}
                  </td>
                  <td style={{ padding: "12px 10px", color: "#6b7280" }}>{(t.confidence * 100).toFixed(0)}%</td>
                  <td style={{ padding: "12px 10px" }}>
                    <span style={{
                      fontSize: "11px",
                      padding: "4px 10px",
                      borderRadius: "9999px",
                      background: decisionBg(t.decision),
                      color: decisionColor(t.decision),
                    }}>
                      {t.decision}
                    </span>
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