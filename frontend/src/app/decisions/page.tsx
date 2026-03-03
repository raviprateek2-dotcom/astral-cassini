"use client";

import { useState, useEffect } from "react";
import { api } from "@/lib/api";

export default function DecisionsPage() {
    const [jobs, setJobs] = useState<any[]>([]);
    const [selectedJob, setSelectedJob] = useState("");
    const [recs, setRecs] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        api.listJobs().then(setJobs).catch(() => { }).finally(() => setLoading(false));
    }, []);

    async function loadRecs(jobId: string) {
        setSelectedJob(jobId);
        setLoading(true);
        try {
            const data = await api.getRecommendations(jobId);
            setRecs(data.final_recommendations || []);
        } catch { setRecs([]); }
        setLoading(false);
    }

    return (
        <div className="fade-in">
            <h1 style={{ fontSize: "2rem", fontWeight: 800, margin: "0 0 4px" }}>Final Decisions</h1>
            <p style={{ color: "var(--text-secondary)", fontSize: "0.9rem", margin: "0 0 32px" }}>
                Hire / No-Hire recommendations from Agent 7 (The Decider)
            </p>

            <div className="glass-card" style={{ padding: 20, marginBottom: 24 }}>
                <select className="input" value={selectedJob} onChange={(e) => loadRecs(e.target.value)} style={{ maxWidth: 400 }}>
                    <option value="">Select pipeline...</option>
                    {jobs.map((j) => (
                        <option key={j.job_id} value={j.job_id}>{j.job_title} — {j.department}</option>
                    ))}
                </select>
            </div>

            {loading && selectedJob && (
                <div style={{ display: "flex", justifyContent: "center", padding: 60 }}><div className="spinner" /></div>
            )}

            {recs.length > 0 && (
                <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>
                    {recs.map((r, i) => (
                        <div key={i} className="glass-card fade-in" style={{ padding: 28 }}>
                            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 20 }}>
                                <div>
                                    <h2 style={{ margin: 0, fontSize: "1.2rem", fontWeight: 700 }}>{r.candidate_name}</h2>
                                    <p style={{ fontSize: "0.8rem", color: "var(--text-muted)", margin: "4px 0 0" }}>
                                        ID: {r.candidate_id}
                                    </p>
                                </div>
                                <div style={{ textAlign: "right" }}>
                                    <span className={`badge ${r.decision === "hire" ? "badge-emerald" :
                                            r.decision === "maybe" ? "badge-amber" : "badge-rose"
                                        }`} style={{ fontSize: "0.9rem", padding: "8px 20px" }}>
                                        {r.decision === "hire" ? "✅ HIRE" :
                                            r.decision === "maybe" ? "🤔 MAYBE" : "❌ NO HIRE"}
                                    </span>
                                    <p style={{ fontSize: "0.8rem", color: "var(--text-muted)", margin: "4px 0 0" }}>
                                        Confidence: <strong>{Math.round(r.confidence)}%</strong>
                                    </p>
                                </div>
                            </div>

                            {/* Score Breakdown */}
                            <div style={{
                                display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 16, marginBottom: 20,
                                padding: 16, borderRadius: 12, border: "1px solid var(--border-glass)", background: "rgba(15,23,42,0.4)",
                            }}>
                                <div style={{ textAlign: "center" }}>
                                    <p style={{ fontSize: "0.7rem", color: "var(--text-muted)", margin: "0 0 4px", textTransform: "uppercase" }}>Screening (40%)</p>
                                    <p style={{ fontSize: "1.5rem", fontWeight: 800, margin: 0, color: "var(--accent-blue)" }}>
                                        {Math.round(r.screening_weight || 0)}
                                    </p>
                                </div>
                                <div style={{ textAlign: "center" }}>
                                    <p style={{ fontSize: "0.7rem", color: "var(--text-muted)", margin: "0 0 4px", textTransform: "uppercase" }}>Interview (60%)</p>
                                    <p style={{ fontSize: "1.5rem", fontWeight: 800, margin: 0, color: "var(--accent-purple)" }}>
                                        {Math.round(r.interview_weight || 0)}
                                    </p>
                                </div>
                                <div style={{ textAlign: "center" }}>
                                    <p style={{ fontSize: "0.7rem", color: "var(--text-muted)", margin: "0 0 4px", textTransform: "uppercase" }}>Weighted Total</p>
                                    <p style={{ fontSize: "1.5rem", fontWeight: 800, margin: 0, color: "var(--accent-emerald)" }}>
                                        {Math.round(r.overall_weighted_score || 0)}
                                    </p>
                                </div>
                            </div>

                            {/* Reasoning */}
                            <div style={{ marginBottom: 16 }}>
                                <h3 style={{ fontSize: "0.85rem", fontWeight: 600, color: "var(--accent-cyan)", margin: "0 0 8px" }}>
                                    💡 Reasoning
                                </h3>
                                <p style={{ fontSize: "0.85rem", lineHeight: 1.7, color: "var(--text-secondary)", margin: 0 }}>
                                    {r.reasoning}
                                </p>
                            </div>

                            {/* Risk Factors */}
                            {(r.risk_factors || []).length > 0 && (
                                <div>
                                    <h3 style={{ fontSize: "0.85rem", fontWeight: 600, color: "var(--accent-amber)", margin: "0 0 8px" }}>
                                        ⚠️ Risk Factors
                                    </h3>
                                    <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
                                        {r.risk_factors.map((rf: string, j: number) => (
                                            <span key={j} className="badge badge-amber">{rf}</span>
                                        ))}
                                    </div>
                                </div>
                            )}
                        </div>
                    ))}
                </div>
            )}

            {selectedJob && !loading && recs.length === 0 && (
                <div className="glass-card" style={{ padding: 40, textAlign: "center" }}>
                    <p style={{ fontSize: "2rem", margin: "0 0 12px" }}>⚖️</p>
                    <p style={{ color: "var(--text-muted)" }}>No final decisions yet. Pipeline hasn&apos;t reached the decision stage.</p>
                </div>
            )}
        </div>
    );
}
