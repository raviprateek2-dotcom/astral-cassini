"use client";

import { useState, useEffect, Suspense, useCallback } from "react";
import { api } from "@/lib/api";
import { useRouter, useSearchParams } from "next/navigation";
import { AgentThinking } from "@/components/AgentThinking";
import type { AuditLogEntry, DecisionTraceRow } from "@/types/domain";

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

interface DecisionTrace {
    candidate_id: string;
    candidate_name: string;
    screening_score: number;
    interview_score_scaled: number;
    concerns_count: number;
    weighted_score: number;
    decision: string;
    rule_applied: string;
}

function InsightsContent() {
    const router = useRouter();
    const searchParams = useSearchParams();
    const jobId = searchParams.get("id");
    const [audit, setAudit] = useState<AuditLogEntry[]>([]);
    const [jobDetails, setJobDetails] = useState<JobDetails | null>(null);
    const [decisionTraces, setDecisionTraces] = useState<DecisionTrace[]>([]);
    const [observability, setObservability] = useState<Record<string, number>>({});
    const [loading, setLoading] = useState(true);

    const loadData = useCallback(async () => {
        if (!jobId) {
            try {
                const jobs = await api.listJobs();
                if (jobs.length > 0) {
                    router.replace(`/insights?id=${jobs[0].job_id}`);
                }
            } catch (err) {
                console.error("Failed to resolve default job for insights", err);
            } finally {
                setLoading(false);
            }
            return;
        }
        setLoading(true);
        try {
            const [auditData, jobData, recommendationsData, healthData] = await Promise.all([
                api.getAudit(jobId),
                api.getJob(jobId),
                api.getRecommendations(jobId),
                api.health(),
            ]);
            setAudit(auditData.audit_log ?? []);
            setJobDetails(jobData);
            setDecisionTraces((recommendationsData.decision_traces ?? []).map((trace: DecisionTraceRow) => ({
                candidate_id: String(trace.candidate_id ?? ""),
                candidate_name: String(trace.candidate_name ?? "Unknown"),
                screening_score: Number(trace.screening_score ?? 0),
                interview_score_scaled: Number(trace.interview_score_scaled ?? 0),
                concerns_count: Number(trace.concerns_count ?? 0),
                weighted_score: Number(trace.weighted_score ?? 0),
                decision: String(trace.decision ?? "no_hire"),
                rule_applied: String(trace.rule_applied ?? ""),
            })));
            setObservability(healthData.observability ?? {});
        } catch (err) {
            console.error("Failed to load insights", err);
        } finally {
            setLoading(false);
        }
    }, [jobId, router]);

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
            ) : audit.length === 0 ? (
                <div className="glass-card" style={{ padding: 40, textAlign: "center" }}>
                    <p style={{ fontSize: "2rem", marginBottom: 8 }}>🧠</p>
                    <h3 style={{ margin: 0 }}>No insights yet for this job</h3>
                    <p style={{ color: "var(--text-muted)", marginTop: 8 }}>
                        Progress the pipeline through at least one stage to populate audit reasoning entries.
                    </p>
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

                            <div style={{ marginTop: 24, padding: 16, background: "rgba(59,130,246,0.06)", borderRadius: 12, border: "1px solid rgba(59,130,246,0.2)" }}>
                                <h4 style={{ fontSize: "0.8rem", fontWeight: 700, marginBottom: 10 }}>📈 Agent Reliability (SLI)</h4>
                                <p style={{ fontSize: "0.72rem", color: "var(--text-muted)", marginTop: 0 }}>
                                    Live in-memory counters from backend observability.
                                </p>
                                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8 }}>
                                    <Metric label="Runs Success" value={observability.agent_runs_success ?? 0} />
                                    <Metric label="Runs Failed" value={observability.agent_runs_failed ?? 0} />
                                    <Metric label="Avg Duration (ms)" value={avgDuration(observability)} />
                                    <Metric label="Total WS Connect OK" value={observability.ws_connect_success ?? 0} />
                                </div>
                            </div>

                            <div style={{ marginTop: 24 }}>
                                <h4 style={{ fontSize: "0.8rem", fontWeight: 700, marginBottom: 10 }}>🧾 Decision Transparency</h4>
                                {decisionTraces.length === 0 ? (
                                    <p style={{ fontSize: "0.74rem", color: "var(--text-muted)", margin: 0 }}>
                                        No decision traces yet. Complete screening and decision stages.
                                    </p>
                                ) : (
                                    <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
                                        {decisionTraces.slice(0, 5).map((trace) => (
                                            <div
                                                key={trace.candidate_id}
                                                style={{
                                                    border: "1px solid rgba(255,255,255,0.08)",
                                                    borderRadius: 10,
                                                    padding: 10,
                                                    background: "rgba(255,255,255,0.02)",
                                                }}
                                            >
                                                <div style={{ display: "flex", justifyContent: "space-between", gap: 8 }}>
                                                    <strong style={{ fontSize: "0.76rem" }}>{trace.candidate_name}</strong>
                                                    <span className="badge badge-blue" style={{ fontSize: "0.62rem" }}>
                                                        {trace.decision.toUpperCase()}
                                                    </span>
                                                </div>
                                                <p style={{ fontSize: "0.68rem", color: "var(--text-muted)", margin: "6px 0 0" }}>
                                                    Score={trace.weighted_score} | Screen={trace.screening_score} | Interview={trace.interview_score_scaled} | Concerns={trace.concerns_count}
                                                </p>
                                            </div>
                                        ))}
                                    </div>
                                )}
                            </div>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}

function avgDuration(metrics: Record<string, number>): string {
    const sum = metrics.agent_duration_ms_sum ?? 0;
    const count = metrics.agent_duration_ms_count ?? 0;
    if (!count) {
        return "0";
    }
    return (sum / count).toFixed(1);
}

function Metric({ label, value }: { label: string; value: number | string }) {
    return (
        <div style={{ padding: 8, borderRadius: 8, background: "rgba(0,0,0,0.2)" }}>
            <p style={{ fontSize: "0.64rem", color: "var(--text-muted)", margin: "0 0 4px" }}>{label}</p>
            <p style={{ fontSize: "0.82rem", fontWeight: 700, margin: 0 }}>{value}</p>
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
