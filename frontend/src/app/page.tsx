"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { useAuth } from "@/hooks/useAuth";
import { useRouter } from "next/navigation";

export default function LandingPage() {
    const { user, loading } = useAuth();
    const router = useRouter();

    if (!loading && user) {
        router.push("/dashboard");
    }

    return (
        <div className="landing-container" style={{
            minHeight: "100vh",
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            justifyContent: "center",
            padding: "20px",
            background: "radial-gradient(circle at center, rgba(30, 41, 59, 0.7) 0%, #0f172a 100%)",
            position: "fixed",
            inset: 0,
            zIndex: 100,
            overflow: "hidden"
        }}>
            {/* Soft Ambient Glows */}
            <div style={{
                position: "absolute",
                top: "20%",
                left: "30%",
                width: "40vw",
                height: "40vw",
                background: "radial-gradient(circle, rgba(59, 130, 246, 0.08) 0%, transparent 70%)",
                filter: "blur(60px)",
                zIndex: -1
            }} />
            <div style={{
                position: "absolute",
                bottom: "10%",
                right: "20%",
                width: "35vw",
                height: "35vw",
                background: "radial-gradient(circle, rgba(167, 139, 250, 0.05) 0%, transparent 70%)",
                filter: "blur(80px)",
                zIndex: -1
            }} />

            <div className="fade-in" style={{ textAlign: "center", maxWidth: "800px" }}>
                <div style={{
                    display: "inline-flex",
                    alignItems: "center",
                    gap: "12px",
                    marginBottom: "24px",
                    padding: "8px 16px",
                    borderRadius: "100px",
                    background: "rgba(255, 255, 255, 0.03)",
                    border: "1px solid rgba(255, 255, 255, 0.08)",
                    backdropFilter: "blur(10px)"
                }}>
                    <span style={{ fontSize: "1.2rem" }}>🤖</span>
                    <span style={{ fontSize: "0.85rem", fontWeight: 600, color: "var(--text-secondary)", letterSpacing: "0.05em", textTransform: "uppercase" }}>
                        Multi-Agent Recruitment Ecosystem
                    </span>
                </div>

                <h1 style={{
                    fontSize: "clamp(2.5rem, 8vw, 4.5rem)",
                    fontWeight: 900,
                    lineHeight: 1.1,
                    marginBottom: "24px",
                    letterSpacing: "-0.03em",
                    background: "linear-gradient(180deg, #FFFFFF 0%, rgba(255, 255, 255, 0.7) 100%)",
                    WebkitBackgroundClip: "text",
                    WebkitTextFillColor: "transparent"
                }}>
                    Hire Smarter with <br /> Artificial Intelligence.
                </h1>

                <p style={{
                    fontSize: "clamp(1rem, 2vw, 1.25rem)",
                    color: "var(--text-secondary)",
                    marginBottom: "48px",
                    lineHeight: 1.6,
                    maxWidth: "600px",
                    marginInline: "auto"
                }}>
                    PRO HR orchestrates 7 specialized AI agents to automate your entire
                    recruitment pipeline—from JD drafting to final decision.
                </p>

                <div style={{ display: "flex", gap: "16px", justifyContent: "center", alignItems: "center" }}>
                    <Link href="/login">
                        <button className="btn-primary" style={{ padding: "16px 36px", fontSize: "1rem", borderRadius: "12px", boxShadow: "0 10px 25px -5px rgba(59, 130, 246, 0.4)" }}>
                            Launch Control Center
                        </button>
                    </Link>
                    <button
                        className="btn-outline"
                        style={{ padding: "16px 36px", fontSize: "1rem", borderRadius: "12px" }}
                        onClick={() => window.scrollTo({ top: window.innerHeight, behavior: "smooth" })}
                    >
                        Explore Ecosystem
                    </button>
                </div>

                {/* Agent Icons Minimalist Strip */}
                <div style={{
                    marginTop: "80px",
                    display: "flex",
                    gap: "40px",
                    justifyContent: "center",
                    opacity: 0.5,
                    filter: "grayscale(100%) brightness(200%)"
                }}>
                    {["📝", "🤝", "🔍", "📊", "📅", "🎙️", "⚖️"].map((emoji, i) => (
                        <span key={i} style={{ fontSize: "1.5rem" }}>{emoji}</span>
                    ))}
                </div>
            </div>

            {/* Footer Minimalist */}
            <div style={{
                position: "absolute",
                bottom: "40px",
                left: 0,
                right: 0,
                textAlign: "center",
                fontSize: "0.8rem",
                color: "var(--text-muted)",
                letterSpacing: "0.02em"
            }}>
                &copy; 2026 PRO HR. Built for the Next Generation of Talent.
            </div>
        </div>
    );
}
