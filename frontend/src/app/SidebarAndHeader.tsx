"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useAuth } from "@/hooks/useAuth";

const navItems = [
    { href: "/dashboard", label: "Dashboard", icon: "📊" },
    { href: "/analytics", label: "Analytics", icon: "📈" },
    { href: "/kanban", label: "Kanban Board", icon: "🗂️" },
    { href: "/jobs", label: "Jobs", icon: "💼" },
    { href: "/insights", label: "Agent Insights", icon: "🧠" },
    { href: "/candidates", label: "Candidates", icon: "👥" },
    { href: "/approvals", label: "Approvals", icon: "✅" },
    { href: "/interviews", label: "Interviews", icon: "🎙️" },
    { href: "/decisions", label: "Decisions", icon: "⚖️" },
    { href: "/audit", label: "Audit Trail", icon: "📜" },
];

export function SidebarAndHeader() {
    const { user, logout, loading } = useAuth();
    const pathname = usePathname();

    // Hide sidebar/header on landing and login pages
    if (pathname === "/" || pathname === "/login" || loading) return null;

    return (
        <>
            <nav className="sidebar">
                <div className="logo-container" style={{ marginBottom: 40, padding: "24px 20px 0" }}>
                    <span style={{ fontSize: "1.75rem", marginRight: 8 }}>🤖</span>
                    <span style={{ fontWeight: 800, fontSize: "1.25rem", background: "linear-gradient(to right, #60a5fa, #a78bfa)", WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent" }}>
                        PRO HR
                    </span>
                </div>

                <ul style={{ listStyle: "none", padding: 0, margin: 0, display: "flex", flexDirection: "column", gap: 6 }}>
                    {navItems.map((item) => {
                        // Strict match for Dashboard "/", otherwise check if pathname starts with href (e.g., "/jobs/123" matches "/jobs")
                        const isActive = item.href === "/" ? pathname === "/" : pathname.startsWith(item.href);

                        return (
                            <li key={item.href}>
                                <Link
                                    href={item.href}
                                    style={{
                                        display: "flex",
                                        alignItems: "center",
                                        gap: 12,
                                        padding: "10px 14px",
                                        borderRadius: 8,
                                        color: isActive ? "#fff" : "rgba(255, 255, 255, 0.6)",
                                        background: isActive ? "linear-gradient(90deg, rgba(96, 165, 250, 0.15) 0%, transparent 100%)" : "transparent",
                                        borderLeft: isActive ? "3px solid #60a5fa" : "3px solid transparent",
                                        textDecoration: "none",
                                        fontWeight: isActive ? 600 : 500,
                                        transition: "all 0.2s ease"
                                    }}
                                    onMouseOver={(e) => {
                                        if (!isActive) {
                                            e.currentTarget.style.background = "rgba(255, 255, 255, 0.03)";
                                            e.currentTarget.style.color = "#fff";
                                        }
                                    }}
                                    onMouseOut={(e) => {
                                        if (!isActive) {
                                            e.currentTarget.style.background = "transparent";
                                            e.currentTarget.style.color = "rgba(255, 255, 255, 0.6)";
                                        }
                                    }}
                                >
                                    <span style={{ fontSize: "1.1rem", opacity: isActive ? 1 : 0.7 }}>{item.icon}</span>
                                    {item.label}
                                </Link>
                            </li>
                        );
                    })}
                </ul>

                {user && (
                    <div style={{ marginTop: "auto", paddingTop: 20, borderTop: "1px solid rgba(255,255,255,0.08)" }}>
                        <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 16 }}>
                            <div style={{
                                width: 36, height: 36, borderRadius: "50%",
                                background: "linear-gradient(135deg, #60a5fa 0%, #3b82f6 100%)",
                                display: "flex", alignItems: "center", justifyContent: "center",
                                fontWeight: 700, fontSize: "0.9rem", color: "#fff",
                                boxShadow: "0 4px 12px rgba(59, 130, 246, 0.3)"
                            }}>
                                {user.full_name.charAt(0)}
                            </div>
                            <div style={{ flex: 1, minWidth: 0 }}>
                                <p style={{ margin: 0, fontSize: "0.85rem", fontWeight: 600, color: "#fff", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>{user.full_name}</p>
                                <p style={{ margin: 0, fontSize: "0.7rem", color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.5px" }}>{user.role.replace("_", " ")}</p>
                            </div>
                        </div>
                        <button
                            onClick={logout}
                            style={{
                                width: "100%", padding: "8px",
                                background: "rgba(244,63,94,0.1)", color: "var(--accent-rose)",
                                border: "1px solid rgba(244,63,94,0.2)", borderRadius: 8, cursor: "pointer",
                                fontSize: "0.8rem", fontWeight: 500, transition: "all 0.2s"
                            }}
                            onMouseOver={e => {
                                e.currentTarget.style.background = "rgba(244,63,94,0.15)";
                                e.currentTarget.style.borderColor = "rgba(244,63,94,0.4)";
                            }}
                            onMouseOut={e => {
                                e.currentTarget.style.background = "rgba(244,63,94,0.1)";
                                e.currentTarget.style.borderColor = "rgba(244,63,94,0.2)";
                            }}
                        >
                            Sign Out
                        </button>
                    </div>
                )}
            </nav>

            <header className="header">
                <div style={{ display: "flex", justifyContent: "flex-end", width: "100%" }}>
                    <div style={{ display: "flex", alignItems: "center", gap: "1rem" }}>
                        <button className="icon-btn">🔔</button>
                        <button className="icon-btn">⚙️</button>
                    </div>
                </div>
            </header>
        </>
    );
}
