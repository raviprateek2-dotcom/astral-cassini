"use client";

import { Inter } from "next/font/google";
import { usePathname } from "next/navigation";
import "./globals.css";
import { AuthProvider } from "@/hooks/useAuth";
import { SidebarAndHeader } from "./SidebarAndHeader";
import { Toaster } from "sonner";
import { ErrorBoundary } from "@/components/ErrorBoundary";

const inter = Inter({ subsets: ["latin"] });

function MainContent({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const isMinimal = pathname === "/" || pathname === "/login";

  return (
    <main
      className="main-content"
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
      <body suppressHydrationWarning className={inter.className} style={{ position: "relative", overflowX: "hidden", minHeight: "100vh", backgroundColor: "#0f172a" }}>
        
        {/* Premium Background */}
        <div className="premium-bg-overlay animate-float" style={{ opacity: 0.6 }} />
        <div className="matrix-bg" />

        <AuthProvider>
          <Toaster richColors position="top-right" />
          <div style={{ display: "flex", minHeight: "100vh" }}>
            <SidebarAndHeader />
            <ErrorBoundary>
              <MainContent>{children}</MainContent>
            </ErrorBoundary>
          </div>
        </AuthProvider>
      </body>
    </html>
  );
}
