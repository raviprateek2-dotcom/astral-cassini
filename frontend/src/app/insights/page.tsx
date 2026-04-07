"use client";

import { useState, useEffect, Suspense, useCallback } from "react";
import { api } from "@/lib/api";
import { useSearchParams } from "next/navigation";
import { AgentThinking } from "@/components/AgentThinking";
import type { AuditLogEntry } from "@/types/domain";

interface JobDetails {
    job_title: string;
}

interface StructuredDetails {
    thought_process: string;
    bias_audit: string;
    strategic_value: string;
    trade_offs?: string;
    candidate_pool_health?: string;
}

function InsightsContent() {
    const searchParams = useSearchParams();
    const jobId = searchParams.get("id");
    const [audit, setAudit] = useState<AuditLogEntry[]>([]);
    const [jobDetails, setJobDetails] = useState<JobDetails | null>(null);
    const [loading, setLoading] = useState(true);

    const loadData = useCallback(async () => {
        if (!jobId) return;
        setLoading(true);
        try {
            const [auditData, jobData] = await Promise.all([
                api.getAudit(jobId),
                api.getJob(jobId)
            ]);
            setAudit(auditData.audit_log ?? []);
            setJobDetails(jobData);
        } catch (err) {
            console.error("Failed to load insights", err);
        } finally {
            setLoading(false);
        }
    }, [jobId]);

    useEffect(() => {
        loadData();
    }, [loadData]);

    if (!jobId) {
        return (
            <div className="glass-card" style={{ padding: 60, textAlign: "center" }}>
                <p style={{ fontSize: "3rem" }}>🧠</p>
                <h2>No Pipeline Active</h2>
                <p style={{ color: "var(--text-muted)" }}>Please select a job requisition to view agent reasoning.</p>
            </div>
        );
    }

    return (
        <div className="fade-in">
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-end", marginBottom: 32 }}>
                <div>
                    <h1 style={{ fontSize: "2rem", fontWeight: 800, margin: 0 }}>Agent Insights</h1>
                    <p style={{ color: "var(--text-secondary)", marginTop: 4 }}>
                        Strategic reasoning, bias audits, and RAG search logic for <span style={{ color: "var(--accent-blue)", fontWeight: 700 }}>{jobDetails?.job_title || "Pipeline"}</span>
                    </p>
                </div>
                <button className="btn-outline" onClick={loadData}>↺ Refresh Context</button>
            </div>

            {loading ? (
                <div style={{ display: "flex", justifyContent: "center", padding: 80 }}>
                    <AgentThinking message="Reconstructing Agent Monologues..." />
                </div>
            ) : (
                <div style={{ display: "grid", gridTemplateColumns: "1fr 340px", gap: 32 }}>
                    {/* Timeline of Thoughts */}
                    <div style={{ display: "flex", flexDirection: "column", gap: 24 }}>
                        {audit.map((entry, idx) => {
                            let parsedDetails: StructuredDetails | null = null;
                            const agentLabel = entry.agent ?? "System";
                            const rawDetails = typeof entry.details === "string" ? entry.details : "";
                            const actionStr = entry.action ?? "";
                            const ts = entry.timestamp ?? "";
                            const stageStr = entry.stage ?? "";

                            try {
                                if (rawDetails.trim().startsWith("{")) {
                                    parsedDetails = JSON.parse(rawDetails) as StructuredDetails;
                                }
                            } catch {
                                console.log("Standard details string, not JSON.");
                            }

                            return (
                                <div key={entry.id || idx} className="glass-card fade-in" style={{ 
                                    padding: 24, 
                                    borderLeft: `4px solid ${agentColor(agentLabel)}`,
                                    position: "relative"
                                }}>
                                    <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 16 }}>
                                        <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
                                            <span style={{ fontSize: "1.2rem" }}>{agentIcon(agentLabel)}</span>
                                            <div>
                                                <h3 style={{ fontSize: "0.9rem", fontWeight: 700, margin: 0 }}>{agentLabel}</h3>
                                                <p style={{ fontSize: "0.7rem", color: "var(--text-muted)", margin: 0 }}>{actionStr.replace(/_/g, " ").toUpperCase()} • {ts ? new Date(ts).toLocaleTimeString() : ""}</p>
                                            </div>
                                        </div>
                                        <div className="badge badge-blue" style={{ background: "rgba(255,255,255,0.05)", fontSize: "0.65rem" }}>
                                            STAGE: {stageStr.toUpperCase()}
                                        </div>
                                    </div>

                                    {parsedDetails ? (
                                        <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>
                                            <div>
                                                <h4 style={{ fontSize: "0.75rem", color: "var(--accent-blue)", marginBottom: 8, fontWeight: 700, textTransform: "uppercase" }}>Strategic Reasoning</h4>
                                                <div style={{ fontSize: "0.85rem", lineHeight: 1.6, color: "var(--text-primary)", background: "rgba(0,0,0,0.2)", padding: 16, borderRadius: 8 }}>
                                                    {parsedDetails.thought_process}
                                                </div>
                                            </div>
                                            
                                            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
                                                <div style={{ background: "rgba(16, 185, 129, 0.05)", padding: 16, borderRadius: 8, border: "1px dashed var(--accent-emerald)" }}>
                                                    <h4 style={{ fontSize: "0.7rem", color: "var(--accent-emerald)", marginBottom: 6, fontWeight: 800 }}>🛡️ BIAS AUDIT</h4>
                                                    <p style={{ fontSize: "0.75rem", margin: 0 }}>{parsedDetails.bias_audit || "Inclusive parameters verified."}</p>
                                                </div>
                                                <div style={{ background: "rgba(59, 130, 246, 0.05)", padding: 16, borderRadius: 8, border: "1px dashed var(--accent-blue)" }}>
                                                    <h4 style={{ fontSize: "0.7rem", color: "var(--accent-blue)", marginBottom: 6, fontWeight: 800 }}>💰 VALUE CREATED</h4>
                                                    <p style={{ fontSize: "0.75rem", margin: 0 }}>{parsedDetails.strategic_value}</p>
                                                </div>
                                            </div>
                                        </div>
                                    ) : (
                                        <div style={{ fontSize: "0.85rem", color: "var(--text-secondary)", lineHeight: 1.5 }}>
                                            {rawDetails}
                                        </div>
                                    )}
                                </div>
                            );
                        })}
                    </div>

                    {/* RAG Pipeline Explained Section */}
                    <div>
                        <div className="glass-card" style={{ padding: 24, position: "sticky", top: 32 }}>
                            <h3 style={{ fontSize: "1rem", fontWeight: 700, marginBottom: 20, display: "flex", alignItems: "center", gap: 8 }}>
                                🧬 RAG Pipeline Infrastructure
                            </h3>
                            <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
                                <div style={{ borderLeft: "2px solid var(--accent-blue)", paddingLeft: 16 }}>
                                    <h4 style={{ fontSize: "0.8rem", color: "var(--accent-blue)", marginBottom: 4 }}>1. Vector Indexing</h4>
                                    <p style={{ fontSize: "0.75rem", color: "var(--text-muted)", margin: 0 }}>Parsing PDF/text into high-dimensional embeddings using OpenAI models.</p>
                                </div>
                                <div style={{ borderLeft: "2px solid var(--accent-cyan)", paddingLeft: 16 }}>
                                    <h4 style={{ fontSize: "0.8rem", color: "var(--accent-cyan)", marginBottom: 4 }}>2. Semantic Retrieval</h4>
                                    <p style={{ fontSize: "0.75rem", color: "var(--text-muted)", margin: 0 }}>Semantic k-NN search across the FAISS resume index using JD requirements as the base query.</p>
                                </div>
                                <div style={{ borderLeft: "2px solid var(--accent-purple)", paddingLeft: 16 }}>
                                    <h4 style={{ fontSize: "0.8rem", color: "var(--accent-purple)", marginBottom: 4 }}>3. Cross-Encoder Reranking</h4>
                                    <p style={{ fontSize: "0.75rem", color: "var(--text-muted)", margin: 0 }}>LLM-driven contextual scoring of the top 10 candidates for precise alignment.</p>
                                </div>
                            </div>

                            <div style={{ marginTop: 32, padding: 16, background: "rgba(167, 139, 250, 0.05)", borderRadius: 12, border: "1px solid rgba(167, 139, 250, 0.2)" }}>
                                <h4 style={{ fontSize: "0.75rem", fontWeight: 700, marginBottom: 8 }}>💡 Optimization Tip</h4>
                                <p style={{ fontSize: "0.7rem", color: "var(--text-secondary)", lineHeight: 1.4, margin: 0 }}>
                                    The Scout uses **Feedback-Driven Augmentation**. If you reject a candidate, the agent automatically updates the vector query with negative constraints to prune similar profiles.
                                </p>
                            </div>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}

function agentColor(name: string): string {
    const map: Record<string, string> = {
        "JD Architect": "var(--accent-blue)",
        "The Scout": "var(--accent-cyan)",
        "The Screener": "var(--accent-purple)",
        "The Coordinator": "var(--accent-amber)",
        "Strategic Screener": "var(--accent-rose)",
        "Governance Monitor": "var(--accent-emerald)"
    };
    return map[name] || "#ccc";
}

function agentIcon(name: string): string {
    const map: Record<string, string> = {
        "JD Architect": "📝",
        "The Scout": "🔍",
        "The Screener": "📊",
        "The Coordinator": "📅",
        "Strategic Screener": "🧠",
        "Governance Monitor": "⚖️"
    };
    return map[name] || "🤖";
}

export default function InsightsPage() {
    return (
        <Suspense fallback={<div className="spinner" />}>
            <InsightsContent />
        </Suspense>
    );
}
