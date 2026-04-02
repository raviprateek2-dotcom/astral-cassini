"use client";

import React, { useEffect } from "react";
import Link from "next/link";
import { useAuth } from "@/hooks/useAuth";
import { useRouter } from "next/navigation";

export default function LandingPage() {
    const { user, loading } = useAuth();
    const router = useRouter();

    useEffect(() => {
        if (!loading && user) {
            router.push("/dashboard");
        }
    }, [user, loading, router]);

    const teamMembers = [
        { 
            name: "Ashish Padhy", 
            role: "AI & Infrastructure", 
            contribution: "Architected the 7-agent orchestration engine and core LangGraph pipeline.",
            avatar: "🧬",
            color: "#3b82f6"
        },
        { 
            name: "Ravi Prateek", 
            role: "Full Stack Architecture", 
            contribution: "Implemented the real-time WebSocket event stream and API security layers.",
            avatar: "🏗️",
            color: "#10b981"
        },
        { 
            name: "Arushi Thakur", 
            role: "UI/UX & Frontend", 
            contribution: "Designed the glassmorphic UI, dynamic animations, and landing experience.",
            avatar: "🎨",
            color: "#f43f5e"
        },
        { 
            name: "Shubham Nimje", 
            role: "RAG & Data Engineering", 
            contribution: "Optimized the FAISS vector index and hybrid-search reranking logic.",
            avatar: "🔍",
            color: "#8b5cf6"
        },
        { 
            name: "Rakesh Sain", 
            role: "Backend Systems", 
            contribution: "Managed the SQLAlchemy database schemas and persistent workflow state.",
            avatar: "🗄️",
            color: "#f59e0b"
        },
        { 
            name: "Gaurav Garg", 
            role: "Agentic Orchestration", 
            contribution: "Refined the agentic instruction set and cross-encoder match reasoning.",
            avatar: "🤖",
            color: "#06b6d4"
        },
        { 
            name: "Kritarth Kudarya", 
            role: "Product Strategy", 
            contribution: "Built the Social-Economic ROI calculator and organizational KPI dashboard.",
            avatar: "📈",
            color: "#ec4899"
        },
        { 
            name: "Sandeep Kumar", 
            role: "Compliance & QA", 
            contribution: "Developed the Ethical Audit Trail and automated governance verification system.",
            avatar: "🛡️",
            color: "#14b8a6"
        },
    ];

    const agents = [
        { id: 1, name: "JD Architect", pro: "Drafting Precision", feature: "Generates high-fidelity JDs from unstructured inputs.", icon: "📝" },
        { id: 2, name: "Scout", pro: "Semantic Sourcing", feature: "Powered by FAISS retrieval and real-time candidate search.", icon: "🔭" },
        { id: 3, name: "Screener", pro: "Explainable Scoring", feature: "Provides match reasoning and competency gaps for every profile.", icon: "📊" },
        { id: 4, name: "Ethics Guardian", pro: "Bias Mitigation", feature: "Explicitly audit logs for demographic data exclusion.", icon: "🛡️" },
        { id: 5, name: "Coordinator", pro: "Interview Intelligence", feature: "Manages automated scheduling and analysis.", icon: "📅" },
        { id: 6, name: "Negotiator", pro: "Strategic Offers", feature: "Benchmarks roles against industry market values.", icon: "🤝" },
        { id: 7, name: "Closer", pro: "Onboarding Flow", feature: "Finalizes contracts and integrates new hires into the org.", icon: "🚀" },
    ];

    const [activeMember, setActiveMember] = React.useState<number | null>(null);

    return (
        <div className="landing-container" style={{
            background: "#0a0e1a",
            color: "var(--text-primary)",
            overflowX: "hidden",
            scrollBehavior: "smooth"
        }}>
            {/* --- SECTION 1: HERO HUB --- */}
            <section style={{
                minHeight: "100vh",
                display: "flex",
                flexDirection: "column",
                alignItems: "center",
                justifyContent: "center",
                padding: "20px",
                position: "relative",
                textAlign: "center"
            }}>
                {/* Background Ambient Glows */}
                <div style={{
                    position: "absolute",
                    top: "20%",
                    left: "10%",
                    width: "50vw",
                    height: "50vw",
                    background: "radial-gradient(circle, rgba(59, 130, 246, 0.05) 0%, transparent 70%)",
                    filter: "blur(80px)",
                    zIndex: 0
                }} />

                <div className="fade-in" style={{ position: "relative", zIndex: 1, maxWidth: "900px" }}>
                    <div style={{
                        display: "inline-flex",
                        alignItems: "center",
                        gap: "12px",
                        marginBottom: "32px",
                        padding: "8px 20px",
                        borderRadius: "100px",
                        background: "rgba(255, 255, 255, 0.03)",
                        border: "1px solid rgba(255, 255, 255, 0.08)",
                        backdropFilter: "blur(10px)"
                    }}>
                        <span style={{ fontSize: "1.2rem" }}>🤖</span>
                        <span style={{ fontSize: "0.85rem", fontWeight: 600, color: "var(--text-secondary)", letterSpacing: "0.1em", textTransform: "uppercase" }}>
                            Enterprise Multi-Agent Ecosystem
                        </span>
                    </div>

                    <h1 style={{
                        fontSize: "clamp(2.5rem, 8vw, 4.5rem)",
                        fontWeight: 900,
                        lineHeight: 1.1,
                        marginBottom: "24px",
                        letterSpacing: "-0.04em",
                        background: "linear-gradient(180deg, #FFFFFF 0%, rgba(255, 255, 255, 0.6) 100%)",
                        WebkitBackgroundClip: "text",
                        WebkitTextFillColor: "transparent"
                    }}>
                        Revolutionize Hiring with <br /> <span className="gradient-text">Autonomous Agents.</span>
                    </h1>

                    <p style={{
                        fontSize: "clamp(1.1rem, 2vw, 1.35rem)",
                        color: "var(--text-secondary)",
                        marginBottom: "48px",
                        lineHeight: 1.6,
                        maxWidth: "700px",
                        marginInline: "auto"
                    }}>
                        PRO HR leverages a consolidated 7-agent architecture to automate the
                        entire recruitment lifecycle—from semantic sourcing to offer generation.
                    </p>

                    <div style={{ display: "flex", gap: "20px", justifyContent: "center", alignItems: "center", flexWrap: "wrap" }}>
                        <Link href="/login">
                            <button className="btn-primary" style={{ padding: "18px 40px", fontSize: "1rem", borderRadius: "14px", boxShadow: "0 15px 30px -5px rgba(59, 130, 246, 0.5)" }}>
                                Launch Control Center
                            </button>
                        </Link>
                        <button
                            className="btn-outline"
                            style={{ padding: "18px 40px", fontSize: "1rem", borderRadius: "14px" }}
                            onClick={() => document.getElementById("submission-hub")?.scrollIntoView({ behavior: "smooth" })}
                        >
                            Explore Ecosystem
                        </button>
                    </div>
                </div>

                {/* Animated Scroll Indicator */}
                <div style={{ position: "absolute", bottom: "40px", opacity: 0.6, animation: "bounce 2s infinite" }}>
                    <span style={{ fontSize: "1.5rem" }}>⌄</span>
                </div>
            </section>

            {/* --- SECTION 2: PROJECT SUBMISSION HUB --- */}
            <section id="submission-hub" style={{
                padding: "100px 20px",
                maxWidth: "1200px",
                margin: "0 auto",
                position: "relative"
            }}>
                <div className="glass-card" style={{ padding: "60px", textAlign: "center", marginBottom: "80px", position: "relative", overflow: "hidden" }}>
                    <div style={{ position: "absolute", top: 0, left: 0, width: "100%", height: "4px", background: "var(--gradient-primary)" }} />
                    
                    <span className="badge badge-blue" style={{ marginBottom: "20px" }}>Project Submission Details</span>
                    <h2 style={{ fontSize: "2.5rem", fontWeight: 800, marginBottom: "40px" }}>Strategic Project Overview</h2>

                    <div style={{
                        display: "grid",
                        gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))",
                        gap: "30px",
                        marginTop: "20px"
                    }}>
                        <div style={{ padding: "30px", background: "rgba(255, 255, 255, 0.02)", borderRadius: "20px", border: "1px solid rgba(255, 255, 255, 0.05)" }}>
                            <div style={{ fontSize: "3.5rem", fontWeight: 900, color: "var(--accent-blue)", marginBottom: "10px" }}>15</div>
                            <div style={{ fontSize: "1.1rem", fontWeight: 600, opacity: 0.8 }}>Project Team</div>
                        </div>
                        <div style={{ padding: "30px", background: "rgba(255, 255, 255, 0.02)", borderRadius: "20px", border: "1px solid rgba(255, 255, 255, 0.05)" }}>
                            <div style={{ fontSize: "3.5rem", fontWeight: 900, color: "var(--accent-emerald)", marginBottom: "10px" }}>08</div>
                            <div style={{ fontSize: "1.1rem", fontWeight: 600, opacity: 0.8 }}>Active Members</div>
                        </div>
                        <div style={{ padding: "30px", background: "rgba(255, 255, 255, 0.02)", borderRadius: "20px", border: "1px solid rgba(255, 255, 255, 0.05)" }}>
                            <div style={{ fontSize: "3.5rem", fontWeight: 900, color: "var(--accent-purple)", marginBottom: "10px" }}>A+</div>
                            <div style={{ fontSize: "1.1rem", fontWeight: 600, opacity: 0.8 }}>Project Rating</div>
                        </div>
                    </div>

                    <p style={{ marginTop: "40px", color: "var(--text-secondary)", fontSize: "1.1rem", maxWidth: "800px", marginInline: "auto" }}>
                        This project represents the cutting edge of autonomous recruitment technology, featuring a multi-layered agentic infrastructure, 
                        FAISS vector retrieval, and human-in-the-loop validation for enterprise-grade MBA submission.
                    </p>
                </div>

                {/* --- SECTION 3: THE 7-AGENT ECOSYSTEM --- */}
                <div id="ecosystem" style={{ marginBottom: "120px" }}>
                    <div style={{ textAlign: "center", marginBottom: "60px" }}>
                        <span className="badge badge-purple" style={{ marginBottom: "16px" }}>Core Technology</span>
                        <h2 style={{ fontSize: "3rem", fontWeight: 900, marginBottom: "16px" }}>7-Agent Strategic Workflow</h2>
                        <p style={{ color: "var(--text-secondary)", fontSize: "1.1rem" }}>A cohesive ecosystem where specialized autonomous agents collaborate in real-time</p>
                    </div>

                    <div style={{
                        display: "grid",
                        gridTemplateColumns: "repeat(auto-fill, minmax(280px, 1fr))",
                        gap: "24px"
                    }}>
                        {agents.map((agent) => (
                            <div key={agent.id} className="glass-card agent-hover shadow-hover" style={{ padding: "32px", position: "relative", overflow: "hidden" }}>
                                <div style={{ fontSize: "2.5rem", marginBottom: "20px" }}>{agent.icon}</div>
                                <h3 style={{ fontSize: "1.2rem", fontWeight: 800, marginBottom: "8px" }}>Agent {agent.id}: {agent.name}</h3>
                                <p style={{ fontSize: "0.8rem", color: "var(--accent-blue)", fontWeight: 700, marginBottom: "12px", textTransform: "uppercase" }}>
                                    {agent.pro}
                                </p>
                                <p style={{ fontSize: "0.9rem", color: "var(--text-secondary)", lineHeight: 1.6 }}>{agent.feature}</p>
                                <div style={{ 
                                    position: "absolute", bottom: -20, right: -10, fontSize: "5rem", opacity: 0.05, fontWeight: 900, pointerEvents: "none" 
                                }}>
                                    0{agent.id}
                                </div>
                            </div>
                        ))}
                    </div>
                </div>

                {/* --- SECTION 4: TRUST & GOVERNANCE --- */}
                <div style={{ marginBottom: "120px" }}>
                    <div style={{ textAlign: "center", marginBottom: "50px" }}>
                        <span className="badge badge-emerald" style={{ marginBottom: "16px" }}>The Trust Layer</span>
                        <h2 style={{ fontSize: "2.5rem", fontWeight: 800, marginBottom: "16px" }}>Pillars of Strategic Governance</h2>
                        <p style={{ color: "var(--text-secondary)", fontSize: "1.1rem" }}>Ensuring precision, transparency, and ethical integrity at scale</p>
                    </div>

                    <div style={{
                        display: "grid",
                        gridTemplateColumns: "repeat(auto-fit, minmax(300px, 1fr))",
                        gap: "24px"
                    }}>
                        {[
                            { 
                                title: "Vector Precision", 
                                desc: "FAISS-powered semantic retrieval ensures we find the 'unfindable' candidates buried in deep resumes.",
                                icon: "🔭",
                                color: "var(--accent-blue)"
                            },
                            { 
                                title: "LLM Reranking", 
                                desc: "Cross-encoder reranking provides contextual 'Match Reasoning' instead of just raw scores.",
                                icon: "🧠",
                                color: "var(--accent-purple)"
                            },
                            { 
                                title: "Bias Mitigation", 
                                desc: "Explicit audit trails verify demographic exclusion, ensuring 100% merit-based recruitment.",
                                icon: "🛡️",
                                color: "var(--accent-emerald)"
                            }
                        ].map((item, i) => (
                            <div key={i} className="glass-card" style={{ padding: "40px", borderTop: `4px solid ${item.color}` }}>
                                <div style={{ fontSize: "2.5rem", marginBottom: "20px" }}>{item.icon}</div>
                                <h3 style={{ fontSize: "1.25rem", fontWeight: 700, marginBottom: "12px" }}>{item.title}</h3>
                                <p style={{ fontSize: "0.95rem", color: "var(--text-secondary)", lineHeight: 1.6 }}>{item.desc}</p>
                            </div>
                        ))}
                    </div>
                </div>

                {/* --- THE DEVELOPMENT TEAM --- */}
                <div style={{ textAlign: "center", marginBottom: "60px" }}>
                    <span className="badge badge-purple" style={{ marginBottom: "16px" }}>The Visionaries</span>
                    <h2 style={{ fontSize: "3rem", fontWeight: 900, marginBottom: "16px" }}>Development Team</h2>
                    <p style={{ color: "var(--text-secondary)", fontSize: "1.1rem" }}>Meet the students behind the PRO HR ecosystem</p>
                </div>

                <div style={{
                    display: "grid",
                    gridTemplateColumns: "repeat(auto-fill, minmax(280px, 1fr))",
                    gap: "24px"
                }}>
                    {teamMembers.map((member, index) => (
                        <div 
                            key={index} 
                            className={`glass-card team-card ${activeMember === index ? "active-member" : ""}`} 
                            style={{ 
                                padding: activeMember === index ? "40px" : "30px", 
                                textAlign: "center", 
                                cursor: "pointer",
                                transition: "all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275)",
                                borderTop: activeMember === index ? `4px solid ${member.color}` : "1px solid var(--border-glass)",
                                background: activeMember === index ? "rgba(255, 255, 255, 0.05)" : ""
                            }}
                            onClick={() => setActiveMember(activeMember === index ? null : index)}
                        >
                            <div style={{
                                width: activeMember === index ? "80px" : "64px",
                                height: activeMember === index ? "80px" : "64px",
                                borderRadius: "50%",
                                background: member.color + "20",
                                color: member.color,
                                display: "flex",
                                alignItems: "center",
                                justifyContent: "center",
                                fontSize: activeMember === index ? "2.5rem" : "1.8rem",
                                fontWeight: "bold",
                                margin: "0 auto 20px",
                                transition: "all 0.4s ease",
                                boxShadow: activeMember === index ? `0 0 20px ${member.color}40` : "none"
                            }}>
                                {member.avatar}
                            </div>
                            <h3 style={{ fontSize: "1.25rem", fontWeight: 700, marginBottom: "4px" }}>{member.name}</h3>
                            <p style={{ fontSize: "0.8rem", color: member.color, fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.05em", marginBottom: "12px" }}>
                                {member.role}
                            </p>
                            
                            {activeMember === index && (
                                <div className="fade-in" style={{ marginTop: "20px", paddingTop: "20px", borderTop: "1px solid rgba(255,255,255,0.05)" }}>
                                    <p style={{ fontSize: "0.9rem", color: "var(--text-secondary)", lineHeight: 1.6, margin: 0 }}>
                                        {member.contribution}
                                    </p>
                                    <div style={{ display: "inline-block", marginTop: "16px", padding: "4px 12px", borderRadius: "100px", background: member.color + "15", color: member.color, fontSize: "0.75rem", fontWeight: 800 }}>
                                        Key Contribution
                                    </div>
                                </div>
                            )}
                            
                            {activeMember !== index && (
                                <p style={{ fontSize: "0.7rem", color: "var(--text-muted)", margin: "10px 0 0" }}>Click to view contribution</p>
                            )}
                        </div>
                    ))}
                </div>
            </section>

            {/* Footer */}
            <footer style={{
                padding: "60px 20px",
                borderTop: "1px solid rgba(255, 255, 255, 0.05)",
                textAlign: "center",
                background: "rgba(10, 14, 26, 0.8)"
            }}>
                <div style={{ marginBottom: "20px", fontSize: "1.5rem", fontWeight: "bold", letterSpacing: "2px" }}>PRO HR</div>
                <div style={{ color: "var(--text-muted)", fontSize: "0.85rem" }}>
                    &copy; 2026 PRO HR Recruitment Systems. Designed for the Autonomous Future.
                </div>
            </footer>

            <style jsx>{`
                @keyframes bounce {
                    0%, 20%, 50%, 80%, 100% { transform: translateY(0); }
                    40% { transform: translateY(-10px); }
                    60% { transform: translateY(-5px); }
                }
            `}</style>
        </div>
    );
}
