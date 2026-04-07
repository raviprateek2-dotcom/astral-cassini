"use client";

import { Inter } from "next/font/google";
import { usePathname } from "next/navigation";
import "./globals.css";
import { AuthProvider } from "@/hooks/useAuth";
import { SidebarAndHeader } from "./SidebarAndHeader";
import { Toaster } from "sonner";

const inter = Inter({ subsets: ["latin"] });

function MainContent({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const isMinimal = pathname === "/" || pathname === "/login";

  return (
    <main
      style={{
        flex: 1,
        marginLeft: isMinimal ? 0 : "var(--sidebar-width)",
        padding: isMinimal ? 0 : "32px 40px",
        minHeight: "100vh",
        position: "relative",
        zIndex: 1
      }}
    >
      {children}
    </main>
  );
}

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <head>
        <title>PRO HR — Autonomous Recruitment Ecosystem</title>
        <meta name="description" content="Multi-agent recruitment platform with a deterministic orchestrator, human-in-the-loop gates, and FAISS-backed semantic resume search." />
      </head>
      <body className={inter.className} style={{ position: "relative", overflowX: "hidden", minHeight: "100vh", backgroundColor: "#0f172a" }}>

        {/* Agent Matrix Animated Background */}
        <div style={{
          position: "fixed",
          inset: 0,
          zIndex: -1,
          opacity: 0.4,
          background: `
            radial-gradient(circle at 15% 50%, rgba(59, 130, 246, 0.15), transparent 25%),
            radial-gradient(circle at 85% 30%, rgba(167, 139, 250, 0.1), transparent 25%)
          `
        }} />
        <div className="matrix-bg" />

        <AuthProvider>
          <Toaster richColors position="top-right" />
          <div style={{ display: "flex", minHeight: "100vh" }}>
            <SidebarAndHeader />
            <MainContent>{children}</MainContent>
          </div>
        </AuthProvider>
      </body>
    </html>
  );
}
