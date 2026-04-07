"use client";

import { useState, useEffect } from "react";
import { api } from "@/lib/api";
import type { AuditLogEntry, JobListItem } from "@/types/domain";

const agentColors: Record<string, string> = {
    "System": "var(--text-muted)",
    "JD Architect": "#3b82f6",
    "The Liaison": "#f59e0b",
    "The Scout": "#06b6d4",
    "The Screener": "#8b5cf6",
    "The Coordinator": "#10b981",
    "The Interviewer": "#ec4899",
    "The Decider": "#f43f5e",
    "Human Reviewer": "#f59e0b",
};

const agentIcons: Record<string, string> = {
    "System": "⚙️",
    "JD Architect": "📝",
    "The Liaison": "🤝",
    "The Scout": "🔍",
    "The Screener": "📊",
    "The Coordinator": "📅",
    "The Interviewer": "🎙️",
    "The Decider": "⚖️",
    "Human Reviewer": "👤",
};

export default function AuditPage() {
    const [jobs, setJobs] = useState<JobListItem[]>([]);
    const [selectedJob, setSelectedJob] = useState("");
    const [auditLog, setAuditLog] = useState<AuditLogEntry[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        api.listJobs().then(setJobs).catch(() => { }).finally(() => setLoading(false));
    }, []);

    async function loadAudit(jobId: string) {
        setSelectedJob(jobId);
        setLoading(true);
        try {
            const data = await api.getAudit(jobId);
            setAuditLog(data.audit_log || []);
        } catch { setAuditLog([]); }
        setLoading(false);
    }

    return (
        <div className="fade-in">
            <h1 style={{ fontSize: "2rem", fontWeight: 800, margin: "0 0 4px" }}>Audit Trail</h1>
            <p style={{ color: "var(--text-secondary)", fontSize: "0.9rem", margin: "0 0 32px" }}>
                Complete decision trail with timestamps and agent attributions
            </p>

            <div className="glass-card" style={{ padding: 20, marginBottom: 24 }}>
                <select className="input" value={selectedJob} onChange={(e) => loadAudit(e.target.value)} style={{ maxWidth: 400 }}>
                    <option value="">Select pipeline...</option>
                    {jobs.map((j) => (
                        <option key={j.job_id} value={j.job_id}>{j.job_title} — {j.department}</option>
                    ))}
                </select>
            </div>

            {loading && selectedJob && (
                <div style={{ display: "flex", justifyContent: "center", padding: 60 }}><div className="spinner" /></div>
            )}

            {auditLog.length > 0 && (
                <div className="glass-card" style={{ padding: 24 }}>
                    <h2 style={{ fontSize: "1.1rem", fontWeight: 700, margin: "0 0 24px" }}>
                        Timeline ({auditLog.length} events)
                    </h2>

                    <div style={{ position: "relative", paddingLeft: 32 }}>
                        {/* Timeline line */}
                        <div
                            style={{
                                position: "absolute",
                                left: 11,
                                top: 0,
                                bottom: 0,
                                width: 2,
                                background: "var(--border-glass)",
                            }}
                        />

                        {auditLog.map((entry, i) => {
                            const agentLabel = entry.agent ?? "System";
                            return (
                            <div
                                key={i}
                                className="fade-in"
                                style={{
                                    position: "relative",
                                    paddingBottom: 24,
                                    paddingLeft: 24,
                                }}
                            >
                                {/* Timeline dot */}
                                <div
                                    style={{
                                        position: "absolute",
                                        left: -26,
                                        top: 4,
                                        width: 24,
                                        height: 24,
                                        borderRadius: "50%",
                                        display: "flex",
                                        alignItems: "center",
                                        justifyContent: "center",
                                        fontSize: "0.75rem",
                                        background: `${agentColors[agentLabel] || "var(--text-muted)"}20`,
                                        border: `2px solid ${agentColors[agentLabel] || "var(--text-muted)"}`,
                                    }}
                                >
                                    {agentIcons[agentLabel] || "•"}
                                </div>

                                {/* Content */}
                                <div
                                    style={{
                                        padding: 16,
                                        borderRadius: 12,
                                        border: "1px solid var(--border-glass)",
                                        background: "rgba(15, 23, 42, 0.3)",
                                    }}
                                >
                                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 6 }}>
                                        <span
                                            style={{
                                                fontWeight: 600,
                                                fontSize: "0.85rem",
                                                color: agentColors[agentLabel] || "var(--text-primary)",
                                            }}
                                        >
                                            {agentLabel}
                                        </span>
                                        <span style={{ fontSize: "0.7rem", color: "var(--text-muted)" }}>
                                            {entry.timestamp ? new Date(entry.timestamp).toLocaleString("en-IN", {
                                                day: "numeric", month: "short", hour: "2-digit", minute: "2-digit", second: "2-digit",
                                            }) : ""}
                                        </span>
                                    </div>
                                    <p style={{ margin: "0 0 4px", fontSize: "0.85rem", fontWeight: 500 }}>
                                        {entry.action?.replace(/_/g, " ")}
                                    </p>
                                    {entry.details && (
                                        <p style={{ margin: 0, fontSize: "0.8rem", color: "var(--text-secondary)" }}>
                                            {entry.details}
                                        </p>
                                    )}
                                    {entry.stage && (
                                        <span
                                            className="badge badge-blue"
                                            style={{ marginTop: 8, display: "inline-block", fontSize: "0.65rem" }}
                                        >
                                            {entry.stage}
                                        </span>
                                    )}
                                </div>
                            </div>
                            );
                        })}
                    </div>
                </div>
            )}

            {selectedJob && !loading && auditLog.length === 0 && (
                <div className="glass-card" style={{ padding: 40, textAlign: "center" }}>
                    <p style={{ fontSize: "2rem", margin: "0 0 12px" }}>📜</p>
                    <p style={{ color: "var(--text-muted)" }}>No audit events yet for this pipeline.</p>
                </div>
            )}
        </div>
    );
}
