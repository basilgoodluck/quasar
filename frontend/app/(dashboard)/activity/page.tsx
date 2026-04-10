"use client"

import React, { useState, useEffect } from "react"

type ActivityEvent = {
  id: string
  timestamp: string
  type: "TradeIntent" | "RiskApproval" | "RiskRejection" | "VaultAllocation" | "Registration" | "Checkpoint"
  description: string
  txHash?: string
}

export default function ActivityPage() {
  const [activities, setActivities] = useState<ActivityEvent[]>([])
  const [filter, setFilter] = useState<"all" | "TradeIntent" | "RiskApproval" | "RiskRejection" | "VaultAllocation" | "Registration" | "Checkpoint">("all")
  const [search, setSearch] = useState("")

  useEffect(() => {
    const mockData: ActivityEvent[] = [
      {
        id: "act_001",
        timestamp: "2026-04-10T14:32:18Z",
        type: "TradeIntent",
        description: "Submitted BUY intent for 0.015 BTC at market price",
        txHash: "0x7d8e9f2a1b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f"
      },
      {
        id: "act_002",
        timestamp: "2026-04-10T14:32:25Z",
        type: "RiskApproval",
        description: "Risk check passed. Position size approved under current limits",
        txHash: "0x1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c"
      },
      {
        id: "act_003",
        timestamp: "2026-04-10T13:15:42Z",
        type: "Checkpoint",
        description: "Decision signed and checkpoint recorded on-chain",
        txHash: "0x9f8e7d6c5b4a3f2e1d0c9b8a7f6e5d4c3b2a1f0e"
      },
      {
        id: "act_004",
        timestamp: "2026-04-10T11:47:09Z",
        type: "RiskRejection",
        description: "Risk rejected: Proposed leverage exceeds current exposure limit",
      },
      {
        id: "act_005",
        timestamp: "2026-04-10T09:22:14Z",
        type: "VaultAllocation",
        description: "Allocated 2.4% of vault equity to BTC long position",
        txHash: "0x3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e"
      }
    ]
    setActivities(mockData)
  }, [])

  const filteredActivities = activities
    .filter(a => filter === "all" || a.type === filter)
    .filter(a => 
      a.description.toLowerCase().includes(search.toLowerCase()) ||
      a.type.toLowerCase().includes(search.toLowerCase())
    )
    .sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime())

  return (
    <div>

      <div style={{ marginBottom: "2rem" }}>
        <div style={{ fontSize: "13px", color: "#6b7280", letterSpacing: ".06em", textTransform: "uppercase" }}>
          SYSTEM LOG
        </div>
        <div style={{ fontSize: "26px", fontWeight: 700, color: "#111827", marginTop: "6px" }}>
          Activity
        </div>
      </div>

      <div style={{ display: "flex", gap: "12px", marginBottom: "1.75rem", flexWrap: "wrap" }}>
        {(["all", "TradeIntent", "RiskApproval", "RiskRejection", "VaultAllocation", "Registration", "Checkpoint"] as const).map(f => (
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
          placeholder="Search activity or description..."
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
        {filteredActivities.length === 0 ? (
          <div style={{ padding: "60px 20px", textAlign: "center", color: "#9ca3af" }}>
            No activity found
          </div>
        ) : (
          filteredActivities.map((event, i) => (
            <div 
              key={event.id}
              style={{
                padding: "22px 24px",
                borderBottom: i < filteredActivities.length - 1 ? "1px solid #e5e5e5" : "none",
                display: "flex",
                flexDirection: "column",
                gap: "12px"
              }}
            >
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
                <div>
                  <div style={{ 
                    fontSize: "15px", 
                    fontWeight: 600, 
                    color: 
                      event.type === "RiskApproval" || event.type === "VaultAllocation" ? "#22c55e" :
                      event.type === "RiskRejection" ? "#ef4444" : 
                      event.type === "Checkpoint" || event.type === "TradeIntent" ? "#2563eb" : "#374151"
                  }}>
                    {event.type}
                  </div>
                  <div style={{ fontSize: "13.5px", color: "#6b7280", marginTop: "3px" }}>
                    {new Date(event.timestamp).toLocaleString([], { 
                      month: "short", 
                      day: "numeric", 
                      hour: "2-digit", 
                      minute: "2-digit" 
                    })}
                  </div>
                </div>

                {event.txHash && (
                  <div style={{ fontSize: "12.5px", color: "#6b7280", textAlign: "right" }}>
                    Tx: <span style={{ fontFamily: "monospace", color: "#2563eb" }}>{event.txHash.slice(0, 14)}...</span>
                  </div>
                )}
              </div>

              <div style={{ 
                fontSize: "14.5px", 
                lineHeight: "1.55", 
                color: "#374151" 
              }}>
                {event.description}
              </div>
            </div>
          ))
        )}
      </div>

      <div style={{ 
        marginTop: "1.5rem", 
        fontSize: "12.5px", 
        color: "#9ca3af", 
        textAlign: "center" 
      }}>
        Agent lifecycle events • On-chain actions are verifiable
      </div>
    </div>
  )
}