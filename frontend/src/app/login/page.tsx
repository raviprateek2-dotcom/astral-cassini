"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";

type LoginStep = "identify" | "authenticate" | "processing" | "success";

export default function LoginPage() {
    const router = useRouter();
    const [step, setStep] = useState<LoginStep>("identify");
    const [email, setEmail] = useState("hr@prohr.ai");
    const [password, setPassword] = useState("hr123");
    const [error, setError] = useState("");
    const [isAuthenticating, setIsAuthenticating] = useState(false);
    const [terminalLines, setTerminalLines] = useState<string[]>([]);

    const addTerminalLine = (line: string, delay: number) => {
        return new Promise(resolve => {
            setTimeout(() => {
                setTerminalLines(prev => [...prev, line]);
                resolve(true);
            }, delay);
        });
    };

    const runLoginPipeline = async (e: React.FormEvent) => {
        e.preventDefault();
        setError("");

        if (step === "identify") {
            if (!email) { setError("Email is required"); return; }
            setStep("authenticate");
            return;
        }

        if (step === "authenticate") {
            if (!password) { setError("Password is required"); return; }
            setIsAuthenticating(true);
            setStep("processing");
            setTerminalLines(["> Initializing Agent Core v4.0..."]);

            try {
                await addTerminalLine("> Establishing secure LangGraph connection...", 400);
                await addTerminalLine("> Verifying RSA-4096 Identity matrix...", 600);
                await addTerminalLine("> Pinging Liaison Agent...", 300);

                const data = await api.login(email, password);

                await addTerminalLine(`> [OK] Access Granted level: ${data.user.role.toUpperCase()}`, 400);
                await addTerminalLine("> Synchronizing local vector stores...", 500);
                await addTerminalLine(`> Hello, ${data.user.full_name.split(' ')[0]}. Booting dashboard...`, 300);

                localStorage.setItem("token", data.access_token);
                localStorage.setItem("user", JSON.stringify(data.user));
                api.setToken(data.access_token);

                setTimeout(() => setStep("success"), 600);
                setTimeout(() => router.push("/dashboard"), 1500);

            } catch (err: any) {
                await addTerminalLine("> [CRITICAL ERROR] Authentication failure.", 100);
                await addTerminalLine("> Details: Access Denied by Hive Guard.", 100);
                setTimeout(() => {
                    setError(err.message || "Security Clearance Denied");
                    setStep("authenticate");
                    setIsAuthenticating(false);
                    setTerminalLines([]);
                }, 1500);
            }
        }
    };

    const steps = [
        { key: "identify", label: "Identity", icon: "👤" },
        { key: "authenticate", label: "Clearance", icon: "🔑" },
        { key: "processing", label: "Extraction", icon: "🧬" },
        { key: "success", label: "Access", icon: "⚡" },
    ];

    const currentStepIndex = steps.findIndex(s => s.key === step);

    return (
        <div style={{
            minHeight: "100vh",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            position: "relative",
            overflow: "hidden",
            backgroundColor: "#020617"
        }}>
            {/* Background Effects */}
            <div className="matrix-bg" style={{ opacity: 0.3 }} />
            <div style={{
                position: "absolute",
                width: 600, height: 600,
                background: "radial-gradient(circle, rgba(59, 130, 246, 0.1) 0%, transparent 70%)",
                top: "50%", left: "50%", transform: "translate(-50%, -50%)",
                pointerEvents: "none", zIndex: 0
            }} />

            <div className="glass-card fade-in" style={{
                position: "relative",
                width: "100%",
                maxWidth: 480,
                padding: "60px 48px",
                zIndex: 10,
                display: "flex",
                flexDirection: "column",
                minHeight: 520,
                border: "1px solid rgba(59,130,246,0.2)",
                boxShadow: "0 0 50px rgba(0,0,0,0.5), 0 0 20px rgba(59,130,246,0.1)"
            }}>
                {/* Brand Header */}
                <div style={{ textAlign: "center", marginBottom: 40 }}>
                    <div className="logo-container" style={{ marginBottom: 16 }}>
                        <span style={{ fontSize: "3rem" }}>🤖</span>
                    </div>
                    <h1 style={{ fontSize: "2rem", fontWeight: 900, letterSpacing: "-1px", margin: 0 }}>
                        AGENT<span style={{ color: "var(--accent-blue)" }}>HIRE</span>
                    </h1>
                    <p style={{ color: "var(--text-muted)", fontSize: "0.85rem", marginTop: 8, letterSpacing: "1px", textTransform: "uppercase" }}>
                        Multi-Agent Recruitment Ecosystem
                    </p>
                </div>

                {/* Pipeline Step Indicator */}
                <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 48, position: "relative" }}>
                    {/* Connecting Line */}
                    <div style={{
                        position: "absolute", top: 18, left: 30, right: 30, height: 2,
                        background: "rgba(255,255,255,0.05)", zIndex: 0
                    }} />
                    <div style={{
                        position: "absolute", top: 18, left: 30, width: `${(currentStepIndex / 3) * 100}%`,
                        height: 2, background: "var(--accent-blue)", zIndex: 0, transition: "all 0.6s cubic-bezier(0.4, 0, 0.2, 1)"
                    }} />

                    {steps.map((s, idx) => {
                        const isActive = s.key === step;
                        const isPast = steps.findIndex(st => st.key === step) > idx || step === "success";
                        return (
                            <div key={s.key} style={{ zIndex: 1, display: "flex", flexDirection: "column", alignItems: "center", gap: 8 }}>
                                <div style={{
                                    width: 36, height: 36, borderRadius: "50%",
                                    background: isPast ? "var(--accent-blue)" : isActive ? "#1e293b" : "#0f172a",
                                    border: `2px solid ${isActive || isPast ? "var(--accent-blue)" : "rgba(255,255,255,0.1)"}`,
                                    display: "flex", alignItems: "center", justifyContent: "center",
                                    fontSize: "1rem", color: isPast ? "white" : isActive ? "var(--accent-blue)" : "rgba(255,255,255,0.2)",
                                    transition: "all 0.4s ease",
                                    boxShadow: isActive ? "0 0 15px rgba(59,130,246,0.3)" : "none"
                                }}>
                                    {isPast && s.key !== "success" ? "✓" : s.icon}
                                </div>
                                <span style={{
                                    fontSize: "0.65rem", fontWeight: 700, textTransform: "uppercase",
                                    color: isActive || isPast ? "var(--text-primary)" : "var(--text-muted)",
                                    opacity: isActive || isPast ? 1 : 0.5,
                                    transition: "all 0.4s ease"
                                }}>
                                    {s.label}
                                </span>
                            </div>
                        );
                    })}
                </div>

                {/* Content Area */}
                <div style={{ flex: 1 }}>
                    {error && (
                        <div className="fade-in" style={{
                            background: "rgba(244, 63, 94, 0.1)", border: "1px solid rgba(244, 63, 94, 0.2)",
                            color: "var(--accent-rose)", padding: "14px", borderRadius: 12,
                            fontSize: "0.8rem", textAlign: "center", marginBottom: 24, fontWeight: 600
                        }}>
                            Security Error: {error}
                        </div>
                    )}

                    {(step === "identify" || step === "authenticate") && (
                        <form onSubmit={runLoginPipeline} className="fade-in">
                            {step === "identify" ? (
                                <div style={{ marginBottom: 24 }}>
                                    <label style={{ display: "block", fontSize: "0.75rem", color: "var(--text-muted)", marginBottom: 10, fontWeight: 600, textTransform: "uppercase" }}>
                                        Establish Identity
                                    </label>
                                    <input
                                        type="email"
                                        className="input"
                                        value={email}
                                        onChange={(e) => setEmail(e.target.value)}
                                        placeholder="agent.name@prohr.ai"
                                        autoFocus
                                        required
                                        style={{ fontSize: "1.1rem", padding: "16px", background: "rgba(0,0,0,0.3)" }}
                                    />
                                </div>
                            ) : (
                                <div style={{ marginBottom: 24 }}>
                                    <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 10 }}>
                                        <label style={{ fontSize: "0.75rem", color: "var(--text-muted)", fontWeight: 600, textTransform: "uppercase" }}>
                                            Clearance Code
                                        </label>
                                        <span onClick={() => setStep("identify")} style={{ fontSize: "0.7rem", color: "var(--accent-blue)", cursor: "pointer", fontWeight: 700 }}>
                                            Change Node
                                        </span>
                                    </div>
                                    <input
                                        type="password"
                                        className="input"
                                        value={password}
                                        onChange={(e) => setPassword(e.target.value)}
                                        placeholder="••••••••"
                                        autoFocus
                                        required
                                        style={{ fontSize: "1.1rem", padding: "16px", letterSpacing: "4px", background: "rgba(0,0,0,0.3)" }}
                                    />
                                </div>
                            )}

                            <button type="submit" className="btn-primary" style={{ width: "100%", padding: "16px", fontSize: "1rem" }}>
                                {step === "identify" ? "Continue Identification" : "Initiate Secure Protocol"}
                            </button>

                            {step === "identify" && (
                                <div style={{ marginTop: 32, textAlign: "center", borderTop: "1px solid rgba(255,255,255,0.05)", paddingTop: 24 }}>
                                    <p style={{ fontSize: "0.7rem", color: "var(--text-muted)", marginBottom: 12, textTransform: "uppercase", letterSpacing: "0.5px" }}>Pre-configured Access Levels</p>
                                    <div style={{ display: "flex", justifyContent: "center", gap: 20 }}>
                                        <button type="button" onClick={() => { setEmail("admin@prohr.ai"); setPassword("admin123"); }} style={{ background: "none", border: "1px solid var(--accent-blue)", color: "var(--accent-blue)", padding: "4px 10px", borderRadius: 6, fontSize: "0.7rem", fontWeight: 700, cursor: "pointer" }}>Admin</button>
                                        <button type="button" onClick={() => { setEmail("hr@prohr.ai"); setPassword("hr123"); }} style={{ background: "none", border: "1px solid var(--accent-amber)", color: "var(--accent-amber)", padding: "4px 10px", borderRadius: 6, fontSize: "0.7rem", fontWeight: 700, cursor: "pointer" }}>HR Manager</button>
                                    </div>
                                </div>
                            )}
                        </form>
                    )}

                    {step === "processing" && (
                        <div className="fade-in" style={{
                            background: "rgba(0,0,0,0.6)",
                            borderRadius: 12,
                            padding: 24,
                            flex: 1,
                            fontFamily: "'Fira Code', monospace",
                            fontSize: "0.8rem",
                            color: "#60a5fa",
                            border: "1px solid rgba(59,130,246,0.2)",
                            boxShadow: "inset 0 0 20px rgba(0,0,0,0.5)",
                            minHeight: 180,
                            overflowY: "auto",
                            display: "flex",
                            flexDirection: "column"
                        }}>
                            {terminalLines.map((line, i) => (
                                <div key={i} style={{ marginBottom: 10, lineHeight: 1.4 }}>
                                    <span style={{ color: "rgba(255,255,255,0.3)", marginRight: 8 }}>[{new Date().toLocaleTimeString([], { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' })}]</span>
                                    {line}
                                </div>
                            ))}
                            <div className="pulse" style={{ width: 8, height: 16, background: "var(--accent-blue)", marginTop: 6, display: "inline-block" }} />
                        </div>
                    )}

                    {step === "success" && (
                        <div className="fade-in" style={{ textAlign: "center", padding: 20 }}>
                            <div className="spinner" style={{ width: 40, height: 40, margin: "0 auto 24px" }} />
                            <h3 style={{ fontSize: "1.25rem", margin: 0 }}>Establishing Dashboard Context...</h3>
                            <p style={{ color: "var(--text-muted)", marginTop: 8 }}>Secure session active.</p>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
