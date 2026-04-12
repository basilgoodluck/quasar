"use client"

import { ReactNode } from "react"
import Link from "next/link"
import { usePathname } from "next/navigation"
import { BASE_URL } from "@/lib/api"

const NAV = [
  { href: "/overview", label: "overview", icon: "▦" },
  { href: "/trades", label: "trades", icon: "⇅" }
]

function Sidebar({ pathname }: { pathname: string }) {
  return (
    <aside style={{
      position: "fixed",
      left: 0,
      top: 0,
      bottom: 0,
      width: "220px",
      background: "#ffffff",
      borderRight: "1px solid #e5e5e5",
      display: "flex",
      flexDirection: "column",
      padding: "1.5rem 0",
      zIndex: 10,
      overflowY: "auto",
    }}>
      <Link href="/" style={{ 
        display: "flex", 
        alignItems: "center", 
        gap: "10px", 
        textDecoration: "none", 
        padding: "0 1.5rem", 
        marginBottom: "2.5rem" 
      }}>
        <div style={{
          width: "32px", 
          height: "32px", 
          borderRadius: "50%",
          background: "#2563eb", 
          display: "flex", 
          alignItems: "center", 
          justifyContent: "center", 
        }}>
          <span style={{ color: "#fff", fontWeight: 700, fontSize: "13px" }}>Q</span>
        </div>
        <span style={{ 
          color: "#111827", 
          fontWeight: 700, 
          fontSize: "15px" 
        }}>
          Quasar
        </span>
      </Link>

      <nav style={{ 
        display: "flex", 
        flexDirection: "column", 
        gap: "4px", 
        flex: 1, 
        padding: "0 1rem" 
      }}>
        {NAV.map(link => {
          const active = pathname === link.href || (link.href !== "/trades" && pathname.startsWith(link.href))
          return (
            <Link
              key={link.href}
              href={link.href}
              style={{
                display: "flex",
                alignItems: "center",
                gap: "12px",
                padding: "10px 14px",
                borderRadius: "8px",
                textDecoration: "none",
                fontSize: "13.5px",
                fontWeight: 500,
                color: active ? "#111827" : "#6b7280",
                background: active ? "#f8fafc" : "transparent",
              }}
            >
              <span style={{ fontSize: "15px", opacity: active ? 1 : 0.6, width: "18px", textAlign: "center" }}>
                {link.icon}
              </span>
              <span style={{ textTransform: "capitalize" }}>{link.label}</span>
              {active && (
                <span style={{ marginLeft: "auto", width: "5px", height: "5px", borderRadius: "50%", background: "#2563eb" }} />
              )}
            </Link>
          )
        })}
      </nav>

      <div style={{ padding: "1rem", marginTop: "auto" }}>
        <a
          href={`${BASE_URL}/auth/google`}
          style={{
            display: "block",
            textAlign: "center",
            fontSize: "12.5px",
            padding: "9px 0",
            borderRadius: "8px",
            border: "1px solid #e5e5e5",
            color: "#6b7280",
            textDecoration: "none",
          }}
          onMouseEnter={e => { 
            e.currentTarget.style.borderColor = "#2563eb"; 
            e.currentTarget.style.color = "#1e40af" 
          }}
          onMouseLeave={e => { 
            e.currentTarget.style.borderColor = "#e5e5e5"; 
            e.currentTarget.style.color = "#6b7280" 
          }}
        >
          Sign out
        </a>
      </div>
    </aside>
  )
}

function Topbar({ pathname }: { pathname: string }) {
  const crumbs = pathname.replace("/trades", "").split("/").filter(Boolean)

  return (
    <header style={{
      position: "fixed",
      top: 0,
      left: "220px",
      right: 0,
      height: "64px",
      borderBottom: "1px solid #e5e5e5",
      background: "#ffffff",
      display: "flex",
      alignItems: "center",
      justifyContent: "space-between",
      padding: "0 2rem",
      zIndex: 10,
    }}>
      <div style={{ 
        display: "flex", 
        alignItems: "center", 
        gap: "8px", 
        fontSize: "13px", 
        color: "#6b7280",
        fontWeight: 500
      }}>
        <span>Trades</span>
        {crumbs.map((crumb, i) => (
          <span key={crumb} style={{ display: "flex", alignItems: "center", gap: "8px" }}>
            <span style={{ color: "#d1d5db" }}>/</span>
            <span style={{ 
              color: i === crumbs.length - 1 ? "#111827" : "#6b7280",
              textTransform: "capitalize"
            }}>
              {crumb}
            </span>
          </span>
        ))}
      </div>

      <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
        <span style={{ 
          width: "8px", 
          height: "8px", 
          borderRadius: "50%", 
          background: "#22c55e" 
        }} />
        <span style={{ fontSize: "13px", color: "#6b7280" }}>Live</span>
      </div>
    </header>
  )
}

export default function DashboardLayout({ children }: { children: ReactNode }) {
  const pathname = usePathname()

  return (
    <div style={{ display: "flex", minHeight: "100vh", background: "#f9fafb" }}>
      <Sidebar pathname={pathname} />
      
      <div style={{ 
        marginLeft: "220px", 
        width: "calc(100% - 220px)",
        display: "flex",
        flexDirection: "column",
        minHeight: "100vh"
      }}>
        <Topbar pathname={pathname} />
        
        <main style={{ 
          flex: 1, 
          padding: "2rem", 
          marginTop: "64px",   
          overflowY: "auto",
          background: "#ffffff"
        }}>
          {children}
        </main>
      </div>
    </div>
  )
}