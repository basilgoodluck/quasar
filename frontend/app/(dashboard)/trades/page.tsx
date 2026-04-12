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

const INTERVAL = "5m"
const INTERVAL_SECONDS = 5 * 60

type Candle = { time: UTCTimestamp; open: number; high: number; low: number; close: number }
type DecisionFilter = "all" | "approved" | "rejected" | "skipped"
type ChartTheme = "light" | "dark"

const PAGE_SIZE = 10

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

function snapToCandle(tradeTs: number): UTCTimestamp {
  return (Math.floor(tradeTs / INTERVAL_SECONDS) * INTERVAL_SECONDS) as UTCTimestamp
}

export default function TradesPage() {
  const chartContainerRef = useRef<HTMLDivElement>(null)
  const chartRef = useRef<IChartApi | null>(null)
  const candleSeriesRef = useRef<ISeriesApi<"Candlestick"> | null>(null)
  const lineSeriesRef = useRef<ISeriesApi<"Line"> | null>(null)
  const markersPluginRef = useRef<any>(null)
  const candleTimesRef = useRef<Set<number>>(new Set())

  const [lastPrice, setLastPrice] = useState<number | null>(null)
  const [symbols, setSymbols] = useState<string[]>([])
  const [selectedSymbol, setSelectedSymbol] = useState("")
  const [filterDecision, setFilterDecision] = useState<DecisionFilter>("all")
  const [liveTrades, setLiveTrades] = useState<Trade[]>([])
  const [chartTheme, setChartTheme] = useState<ChartTheme>("light")
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [page, setPage] = useState(1)

  // Fetch symbols on mount
  useEffect(() => {
    api.trade.getSymbols()
      .then((data: { symbol: string }[]) => {
        const names = data.map(s => s.symbol)
        setSymbols(names)
        if (names.length > 0) setSelectedSymbol(names[0])
      })
      .catch(() => {})
  }, [])

  const filteredTrades = useMemo(
    () => filterDecision === "all" ? liveTrades : liveTrades.filter(t => t.decision === filterDecision),
    [liveTrades, filterDecision]
  )

  const symbolTrades = useMemo(
    () => filteredTrades.filter(t => t.symbol === selectedSymbol),
    [filteredTrades, selectedSymbol]
  )

  const totalPages = Math.max(1, Math.ceil(filteredTrades.length / PAGE_SIZE))
  const pagedTrades = filteredTrades.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE)

  // Reset page when filter changes
  useEffect(() => { setPage(1) }, [filterDecision])

  const buildMarkers = useCallback((tradeList: Trade[]): SeriesMarker<Time>[] => {
    const candleTimes = candleTimesRef.current
    return tradeList
      .sort((a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime())
      .map(t => {
        const tradeTs = Math.floor(new Date(t.timestamp).getTime() / 1000)
        const snapped = snapToCandle(tradeTs)
        if (candleTimes.size > 0 && !candleTimes.has(snapped)) return null
        return {
          time: snapped,
          position: t.side === "BUY" ? "belowBar" : "aboveBar",
          color: decisionColor(t.decision),
          shape: t.side === "BUY" ? "arrowUp" : "arrowDown",
          text: `${t.side} ${t.pnl >= 0 ? "+" : ""}${fmt(t.pnl, 0)}`,
          id: t.id,
        } as SeriesMarker<Time>
      })
      .filter(Boolean) as SeriesMarker<Time>[]
  }, [])

  // Initial fetch
  useEffect(() => {
    setLoading(true)
    api.dashboard.trades()
      .then(data => { setLiveTrades(data); setError(null) })
      .catch(() => setError("failed to load trades"))
      .finally(() => setLoading(false))
  }, [])

  // Live WS
  useEffect(() => {
    const ws = createTradeWebSocket((msg) => {
      if (msg.type === "initial") setLiveTrades(msg.data)
      else if (msg.type === "new_trade") setLiveTrades(prev => [msg.data, ...prev])
    })
    return () => ws.close()
  }, [])

  const fetchHistoricalData = useCallback(async (symbol: string, candleSeries: ISeriesApi<"Candlestick">, lineSeries: ISeriesApi<"Line">, chart: IChartApi) => {
    if (!symbol) return
    try {
      const raw = await api.binance.klines(symbol, INTERVAL)
      const candles: Candle[] = raw.map(k => ({
        time: Math.floor(Number(k[0]) / 1000) as UTCTimestamp,
        open: parseFloat(k[1] as string),
        high: parseFloat(k[2] as string),
        low: parseFloat(k[3] as string),
        close: parseFloat(k[4] as string),
      }))
      candleTimesRef.current = new Set(candles.map(c => c.time as number))
      candleSeries.setData(candles)
      lineSeries.setData(candles.map(c => ({ time: c.time, value: c.close })))
      const last = candles[candles.length - 1]
      if (last) setLastPrice(last.close)
      chart.timeScale().fitContent()
    } catch (err) {
      console.error(err)
    }
  }, [])

  // Binance live stream
  useEffect(() => {
    if (!selectedSymbol) return
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
      candleTimesRef.current.add(candle.time as number)
      setLastPrice(candle.close)
    })
    return () => ws.close()
  }, [selectedSymbol])

  // Chart init — recreate fully when theme or symbol changes
  useEffect(() => {
    if (!chartContainerRef.current || !selectedSymbol) return

    if (chartRef.current) {
      chartRef.current.remove()
      chartRef.current = null
      candleSeriesRef.current = null
      lineSeriesRef.current = null
      markersPluginRef.current = null
    }

    const isDark = chartTheme === "dark"
    const chart = createChart(chartContainerRef.current, {
      width: chartContainerRef.current.clientWidth,
      height: 420,
      layout: {
        background: { color: isDark ? "#111111" : "#ffffff" },
        textColor: isDark ? "#a1a1aa" : "#52525b",
        fontSize: 11,
        fontFamily: "monospace",
      },
      grid: {
        vertLines: { color: isDark ? "#1f1f1f" : "#f1f1f1" },
        horzLines: { color: isDark ? "#1f1f1f" : "#f1f1f1" },
      },
      crosshair: { mode: 1 },
      rightPriceScale: { borderColor: isDark ? "#1f1f1f" : "#e5e5e5" },
      timeScale: { borderColor: isDark ? "#1f1f1f" : "#e5e5e5", timeVisible: true, secondsVisible: false },
    })

    const candleSeries = chart.addSeries(CandlestickSeries, {
      upColor: "#22c55e", downColor: "#ef4444",
      borderUpColor: "#22c55e", borderDownColor: "#ef4444",
      wickUpColor: "#22c55e", wickDownColor: "#ef4444",
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

    fetchHistoricalData(selectedSymbol, candleSeries, lineSeries, chart)

    const ro = new ResizeObserver(entries => {
      chart.applyOptions({ width: entries[0].contentRect.width })
    })
    ro.observe(chartContainerRef.current)

    return () => {
      ro.disconnect()
      chart.remove()
      chartRef.current = null
      candleSeriesRef.current = null
      lineSeriesRef.current = null
      markersPluginRef.current = null
    }
  }, [chartTheme, selectedSymbol, fetchHistoricalData])

  // Update markers whenever symbol trades change
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
      {/* Header */}
      <div style={{ display: "flex", alignItems: "flex-end", justifyContent: "space-between", flexWrap: "wrap", gap: "12px" }}>
        <div>
          <div style={{ fontSize: "11px", fontFamily: "monospace", color: "#6b7280", letterSpacing: ".08em", textTransform: "uppercase", marginBottom: "4px" }}>
            TRADE ACTIVITY
          </div>
          <div style={{ fontSize: "28px", fontWeight: 700, color: "#111827", margin: 0 }}>
            {lastPrice != null ? `$${fmt(lastPrice)}` : "$0.0000"}
            <span style={{ fontSize: "15px", color: "#6b7280", marginLeft: "10px", fontWeight: 500 }}>{selectedSymbol}</span>
          </div>
        </div>
      </div>

      {/* Chart */}
      <div style={{ background: "#ffffff", border: "1px solid #e5e5e5", borderRadius: "12px", padding: "20px", position: "relative" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "16px", flexWrap: "wrap", gap: "12px" }}>
          {/* Symbol dropdown */}
          <select
            value={selectedSymbol}
            onChange={e => setSelectedSymbol(e.target.value)}
            style={{
              fontSize: "13px", padding: "8px 14px", borderRadius: "8px",
              border: "1px solid #d1d5db", background: "#ffffff",
              color: "#374151", cursor: "pointer", fontFamily: "monospace",
              fontWeight: 600, minWidth: "140px",
            }}
          >
            {symbols.map(s => (
              <option key={s} value={s}>{s}</option>
            ))}
          </select>

          <button
            onClick={() => setChartTheme(chartTheme === "light" ? "dark" : "light")}
            style={{ fontSize: "12px", padding: "6px 14px", borderRadius: "8px", border: "1px solid #d1d5db", background: chartTheme === "dark" ? "#111111" : "#ffffff", color: chartTheme === "dark" ? "#e4e4e7" : "#374151", cursor: "pointer", display: "flex", alignItems: "center", gap: "6px" }}
          >
            {chartTheme === "light" ? "🌙 Dark Chart" : "☀️ Light Chart"}
          </button>
        </div>

        <div ref={chartContainerRef} style={{ width: "100%", height: "420px", borderRadius: "8px", overflow: "hidden" }} />

        <div style={{ display: "flex", gap: "20px", marginTop: "16px", flexWrap: "wrap" }}>
          {[{ label: "approved", color: "#22c55e" }, { label: "rejected", color: "#ef4444" }, { label: "skipped", color: "#f59e0b" }].map(item => (
            <div key={item.label} style={{ display: "flex", alignItems: "center", gap: "6px", fontSize: "12px", color: "#6b7280" }}>
              <span style={{ width: "10px", height: "10px", borderRadius: "3px", background: item.color }} />
              {item.label}
            </div>
          ))}
        </div>
      </div>

      {/* Stats */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))", gap: "1.25rem" }}>
        <div style={{ background: "#ffffff", border: "1px solid #e5e5e5", borderRadius: "12px", padding: "20px" }}>
          <div style={{ fontSize: "11px", fontFamily: "monospace", color: "#6b7280", letterSpacing: ".08em", textTransform: "uppercase", marginBottom: "12px" }}>
            VOLUME / HOUR
          </div>
          {hourlyVolume.length === 0 ? (
            <div style={{ height: "80px", display: "flex", alignItems: "center", justifyContent: "center", color: "#9ca3af", fontSize: "13px", fontFamily: "monospace" }}>
              no data
            </div>
          ) : (
            <div style={{ display: "flex", alignItems: "flex-end", gap: "4px", height: "80px" }}>
              {hourlyVolume.map(h => (
                <div key={h.hour} style={{ flex: 1, display: "flex", flexDirection: "column", alignItems: "center", gap: "4px" }}>
                  <div style={{ width: "100%", background: "#3b82f6", height: `${Math.max(4, (h.volume / maxVol) * 64)}px`, borderRadius: "3px 3px 0 0" }} />
                  <span style={{ fontSize: "10px", fontFamily: "monospace", color: "#9ca3af" }}>{h.hour}</span>
                </div>
              ))}
            </div>
          )}
        </div>

        <div style={{ background: "#ffffff", border: "1px solid #e5e5e5", borderRadius: "12px", padding: "20px" }}>
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

      {/* Trades Table */}
      <div style={{ background: "#ffffff", border: "1px solid #e5e5e5", borderRadius: "12px", padding: "20px" }}>
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", flexWrap: "wrap", gap: "12px", marginBottom: "16px" }}>
          <div style={{ fontSize: "11px", fontFamily: "monospace", color: "#6b7280", letterSpacing: ".08em", textTransform: "uppercase" }}>
            RECENT TRADES <span style={{ color: "#9ca3af" }}>({filteredTrades.length})</span>
          </div>
          <select
            value={filterDecision}
            onChange={e => setFilterDecision(e.target.value as DecisionFilter)}
            style={{ fontSize: "13px", padding: "8px 14px", borderRadius: "8px", border: "1px solid #d1d5db", background: "#ffffff", color: "#374151", cursor: "pointer" }}
          >
            <option value="all">All Decisions</option>
            <option value="approved">Approved</option>
            <option value="rejected">Rejected</option>
            <option value="skipped">Skipped</option>
          </select>
        </div>

        {loading ? (
          <div style={{ padding: "40px", textAlign: "center", color: "#9ca3af", fontSize: "13px", fontFamily: "monospace" }}>
            loading...
          </div>
        ) : error ? (
          <div style={{ padding: "40px", textAlign: "center", color: "#ef4444", fontSize: "13px", fontFamily: "monospace" }}>
            {error}
          </div>
        ) : filteredTrades.length === 0 ? (
          <div style={{ padding: "40px", textAlign: "center", color: "#9ca3af", fontSize: "13px", fontFamily: "monospace" }}>
            no trades yet
          </div>
        ) : (
          <>
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
                  {pagedTrades.map(t => (
                    <tr key={t.id} style={{ borderBottom: "1px solid #f3f4f6" }}>
                      <td style={{ padding: "12px 10px", color: "#6b7280" }}>
                        {new Date(t.timestamp).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                      </td>
                      <td style={{ padding: "12px 10px", color: "#374151" }}>{t.symbol}</td>
                      <td style={{ padding: "12px 10px", color: t.side === "BUY" ? "#22c55e" : "#ef4444", fontWeight: 600 }}>{t.side}</td>
                      <td style={{ padding: "12px 10px", color: "#6b7280" }}>{fmt(t.entry_price)}</td>
                      <td style={{ padding: "12px 10px", color: "#6b7280" }}>{t.exit_price != null ? fmt(t.exit_price) : "0.0000"}</td>
                      <td style={{ padding: "12px 10px", color: t.pnl >= 0 ? "#22c55e" : "#ef4444", fontWeight: 600 }}>
                        {t.pnl >= 0 ? "+" : ""}{fmt(t.pnl)}
                      </td>
                      <td style={{ padding: "12px 10px", color: "#6b7280" }}>{(t.confidence * 100).toFixed(0)}%</td>
                      <td style={{ padding: "12px 10px" }}>
                        <span style={{ fontSize: "11px", padding: "4px 10px", borderRadius: "9999px", background: decisionBg(t.decision), color: decisionColor(t.decision) }}>
                          {t.decision}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Pagination */}
            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginTop: "16px", gap: "12px", flexWrap: "wrap" }}>
              <span style={{ fontSize: "12px", fontFamily: "monospace", color: "#9ca3af" }}>
                page {page} of {totalPages}
              </span>
              <div style={{ display: "flex", gap: "8px" }}>
                <button
                  onClick={() => setPage(p => Math.max(1, p - 1))}
                  disabled={page === 1}
                  style={{
                    fontSize: "12px", padding: "6px 16px", borderRadius: "8px", border: "1px solid #d1d5db",
                    background: page === 1 ? "#f9fafb" : "#ffffff",
                    color: page === 1 ? "#d1d5db" : "#374151",
                    cursor: page === 1 ? "not-allowed" : "pointer",
                  }}
                >
                  ← prev
                </button>
                <button
                  onClick={() => setPage(p => Math.min(totalPages, p + 1))}
                  disabled={page === totalPages}
                  style={{
                    fontSize: "12px", padding: "6px 16px", borderRadius: "8px", border: "1px solid #d1d5db",
                    background: page === totalPages ? "#f9fafb" : "#ffffff",
                    color: page === totalPages ? "#d1d5db" : "#374151",
                    cursor: page === totalPages ? "not-allowed" : "pointer",
                  }}
                >
                  next →
                </button>
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  )
}