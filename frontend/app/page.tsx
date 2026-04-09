// app/page.tsx
import { BASE_URL } from "@/lib/api"

export default function Home() {
  return (
    <main style={{
      background: "#080808",
      height: "100vh",
      display: "flex",
      alignItems: "center",
      justifyContent: "center",
    }}>
      <a
        href={`${BASE_URL}/auth/google`}
        style={{
          display: "flex",
          alignItems: "center",
          gap: "12px",
          background: "#fff",
          color: "#111",
          textDecoration: "none",
          padding: "12px 24px",
          borderRadius: "6px",
          fontSize: "15px",
          fontWeight: 600,
        }}
      >
        <img src="https://www.google.com/favicon.ico" width={20} height={20} alt="Google"/>
        Sign in with Google
      </a>
    </main>
  )
}