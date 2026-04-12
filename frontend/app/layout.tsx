import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Quasar - On-Chain AI Trading Agent",
  description: "Rule-based AI trading agent with on-chain identity, EIP-712 signed decisions, and verifiable smart contract execution.",
  icons: {
    icon: "/favicon.ico",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="h-full">
      <body className="min-h-full bg-white text-gray-900"
      suppressHydrationWarning={true}>
        {children}
      </body>
    </html>
  );
}