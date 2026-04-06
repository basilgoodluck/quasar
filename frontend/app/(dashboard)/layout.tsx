"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"

const NAV = [
  { href: "/dashboard", label: "Status" },
  { href: "/trades", label: "Trades" },
  { href: "/positions", label: "Positions" },
  { href: "/regime", label: "Regime" },
  { href: "/risk", label: "Risk" },
  { href: "/reputation", label: "Reputation" },
  { href: "/config", label: "Config" },
]

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname()

  return (
    <div style={{ display: "flex", minHeight: "100vh", background: "#0a0a0a" }}>
      <aside style={{
        width: "180px", flexShrink: 0, borderRight: "0.5px solid #1f1f1f",
        display: "flex", flexDirection: "column", padding: "1.25rem 0",
        position: "sticky", top: 0, height: "100vh", overflowY: "auto",
      }}>
        <div style={{ padding: "0 1.25rem 1.5rem" }}>
          <p style={{ fontSize: "10px", fontFamily: "monospace", color: "#52525b", letterSpacing: ".12em", textTransform: "uppercase" }}>agent</p>
          <p style={{ fontSize: "15px", fontWeight: 600, color: "#e4e4e7", marginTop: "2px", fontFamily: "monospace" }}>monitor</p>
        </div>
        <nav style={{ flex: 1, display: "flex", flexDirection: "column", gap: "1px", padding: "0 .5rem" }}>
          {NAV.map(({ href, label }) => {
            const active = pathname === href
            return (
              <Link key={href} href={href} style={{
                display: "block", padding: "7px 12px", borderRadius: "6px",
                fontSize: "13px", fontFamily: "monospace",
                color: active ? "#e4e4e7" : "#71717a",
                background: active ? "#18181b" : "transparent",
                textDecoration: "none",
              }}>{label}</Link>
            )
          })}
        </nav>
        <div style={{ padding: "1rem 1.25rem 0", borderTop: "0.5px solid #1f1f1f", marginTop: "auto" }}>
          <Link href="/" style={{ fontSize: "11px", fontFamily: "monospace", color: "#52525b", textDecoration: "none" }}>public stats</Link>
        </div>
      </aside>
      <main style={{ flex: 1, minWidth: 0, overflowY: "auto" }}>{children}</main>
    </div>
  )
}