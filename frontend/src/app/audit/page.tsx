"use client";

import { Suspense, useState, useEffect, useMemo } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import { api } from "@/lib/api";
import { EmptyState } from "@/components/EmptyState";
import { useWebSocket } from "@/hooks/useWebSocket";
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
    "Orchestrator": "#f43f5e",
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
    "Orchestrator": "⚡",
};

function AuditPageContent() {
    const searchParams = useSearchParams();
    const [jobs, setJobs] = useState<JobListItem[]>([]);
    const [selectedJob, setSelectedJob] = useState("");
    const [auditLog, setAuditLog] = useState<AuditLogEntry[]>([]);
    const [loading, setLoading] = useState(true);
    const router = useRouter();
    
    // Filtering states
    const [searchQuery, setSearchQuery] = useState("");
    const [agentFilter, setAgentFilter] = useState("All");
    const [stageFilter, setStageFilter] = useState("All");

    // Real-time updates
    const { heartbeat } = useWebSocket(selectedJob || null);

    // Merge heartbeat audit log with existing if new
    useEffect(() => {
        if (heartbeat?.state?.audit_log) {
            const liveLogs = heartbeat.state.audit_log as AuditLogEntry[];
            if (liveLogs.length > auditLog.length) {
                setAuditLog(liveLogs);
            }
        }
    }, [heartbeat, auditLog.length]);

    async function loadAudit(jobId: string) {
        setSelectedJob(jobId);
        setLoading(true);
        try {
            const data = await api.getAudit(jobId);
            setAuditLog(data.audit_log || []);
        } catch { setAuditLog([]); }
        setLoading(false);
    }

    useEffect(() => {
        const selectedFromQuery = (searchParams.get("id") || "").trim();
        api.listJobs()
            .then((list) => {
                setJobs(list);
                if (selectedFromQuery && list.some((j) => j.job_id === selectedFromQuery)) {
                    void loadAudit(selectedFromQuery);
                } else {
                    setLoading(false);
                }
            })
            .catch(() => {
                setLoading(false);
            });
    }, [searchParams]);

    // Unique values for dropdowns
    const uniqueAgents = useMemo(() => Array.from(new Set(auditLog.map(e => e.agent || "System"))).sort(), [auditLog]);
    const uniqueStages = useMemo(() => Array.from(new Set(auditLog.map(e => e.stage).filter(Boolean))).sort(), [auditLog]);

    // Filter logic
    const filteredLog = useMemo(() => {
        return auditLog.filter(entry => {
            const agent = entry.agent || "System";
            if (agentFilter !== "All" && agent !== agentFilter) return false;
            if (stageFilter !== "All" && entry.stage !== stageFilter) return false;
            if (searchQuery) {
                const query = searchQuery.toLowerCase();
                const text = `${agent} ${entry.action} ${entry.stage} ${entry.details}`.toLowerCase();
                if (!text.includes(query)) return false;
            }
            return true;
        });
    }, [auditLog, agentFilter, stageFilter, searchQuery]);

    // CSV Export
    const exportCSV = () => {
        if (!auditLog.length) return;
        const headers = ["Timestamp", "Agent", "Stage", "Action", "Details"];
        const rows = auditLog.map(e => [
            e.timestamp || "",
            e.agent || "System",
            e.stage || "",
            e.action || "",
            (e.details || "").replace(/"/g, '""') // Escape quotes for CSV
        ].map(cell => `"${cell}"`).join(","));
        
        const csvContent = [headers.join(","), ...rows].join("\\n");
        const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
        const url = URL.createObjectURL(blob);
        const link = document.createElement("a");
        link.setAttribute("href", url);
        link.setAttribute("download", `audit_trail_${selectedJob}.csv`);
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    };

    // Helper to safely parse JSON
    const tryParseJSON = (jsonString: string) => {
        try {
            const o = JSON.parse(jsonString);
            if (o && typeof o === "object") return o;
        } catch (_) { }
        return null;
    };

    // Component for expandable details
    const AuditDetails = ({ details }: { details: string }) => {
        const [expanded, setExpanded] = useState(false);
        if (!details) return null;
        
        const jsonObj = tryParseJSON(details);
        if (jsonObj) {
            return (
                <div style={{ marginTop: 8 }}>
                    <button 
                        onClick={() => setExpanded(!expanded)}
                        style={{ background: "transparent", border: "none", color: "var(--brand)", cursor: "pointer", fontSize: "0.8rem", padding: 0, fontWeight: 600 }}
                    >
                        {expanded ? "▼ Hide Details" : "▶ View Structured Details"}
                    </button>
                    {expanded && (
                        <pre style={{ 
                            background: "rgba(0,0,0,0.3)", 
                            padding: 12, 
                            borderRadius: 8, 
                            fontSize: "0.75rem",
                            overflowX: "auto",
                            marginTop: 8,
                            color: "var(--text-secondary)",
                            border: "1px solid var(--border-glass)"
                        }}>
                            {JSON.stringify(jsonObj, null, 2)}
                        </pre>
                    )}
                </div>
            );
        }
        
        return (
            <p style={{ margin: 0, fontSize: "0.8rem", color: "var(--text-secondary)" }}>
                {details}
            </p>
        );
    };

    return (
        <div className="fade-in">
            <h1 style={{ fontSize: "2rem", fontWeight: 800, margin: "0 0 4px" }}>Audit Trail</h1>
            <p style={{ color: "var(--text-secondary)", fontSize: "0.9rem", margin: "0 0 32px" }}>
                Complete decision trail with timestamps and agent attributions
            </p>

            {jobs.length === 0 && !loading ? (
                <EmptyState 
                    icon="💼" 
                    title="No Pipelines Found" 
                    description="Start by creating an active recruitment requisition in the Intelligence Hub to view audit trails." 
                    action={{ label: "Go to Jobs", onClick: () => router.push("/jobs") }} 
                />
            ) : (
                <div className="glass-card" style={{ padding: 20, marginBottom: 24 }}>
                    <select
                        className="input"
                        title="Select pipeline for audit trail"
                        value={selectedJob}
                        onChange={(e) => loadAudit(e.target.value)}
                        style={{ maxWidth: 400 }}
                    >
                        <option value="">Select pipeline...</option>
                        {jobs.map((j) => (
                            <option key={j.job_id} value={j.job_id}>{j.job_title} — {j.department}</option>
                        ))}
                    </select>
                </div>
            )}

            {loading && selectedJob && (
                <div style={{ display: "flex", justifyContent: "center", padding: 60 }}><div className="spinner" /></div>
            )}

            {auditLog.length > 0 && (
                <div className="glass-card" style={{ padding: 24 }}>
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 24, flexWrap: "wrap", gap: 16 }}>
                        <h2 style={{ fontSize: "1.1rem", fontWeight: 700, margin: 0 }}>
                            Timeline ({filteredLog.length} events)
                        </h2>
                        
                        <div style={{ display: "flex", gap: 12, flexWrap: "wrap" }}>
                            <input 
                                type="text"
                                className="input"
                                placeholder="Search events..."
                                value={searchQuery}
                                onChange={e => setSearchQuery(e.target.value)}
                                style={{ width: 200, padding: "6px 12px", fontSize: "0.85rem" }}
                            />
                            
                            <select 
                                className="input"
                                value={agentFilter}
                                onChange={e => setAgentFilter(e.target.value)}
                                style={{ padding: "6px 12px", fontSize: "0.85rem" }}
                            >
                                <option value="All">All Agents</option>
                                {uniqueAgents.map(a => <option key={a} value={a}>{a}</option>)}
                            </select>

                            <select 
                                className="input"
                                value={stageFilter}
                                onChange={e => setStageFilter(e.target.value)}
                                style={{ padding: "6px 12px", fontSize: "0.85rem" }}
                            >
                                <option value="All">All Stages</option>
                                {uniqueStages.map(s => <option key={s} value={s}>{s}</option>)}
                            </select>

                            <button onClick={exportCSV} className="btn btn-secondary" style={{ padding: "6px 12px", fontSize: "0.85rem" }}>
                                ⬇ Export CSV
                            </button>
                        </div>
                    </div>

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

                        {filteredLog.length === 0 ? (
                            <div style={{ padding: 40, textAlign: "center", color: "var(--text-muted)" }}>
                                No events match your filters.
                            </div>
                        ) : (
                            filteredLog.map((entry, i) => {
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
                                        
                                        <AuditDetails details={entry.details || ""} />
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
                        })
                        )}
                    </div>
                </div>
            )}

            {selectedJob && !loading && auditLog.length === 0 && (
                <div className="glass-card" style={{ padding: 40, textAlign: "center" }}>
                    <p style={{ fontSize: "2rem", margin: "0 0 12px" }}>📜</p>
                    <p style={{ color: "var(--text-muted)" }}>No audit events yet for this pipeline.</p>
                </div>
            )}

            {!selectedJob && !loading && jobs.length > 0 && (
                <EmptyState 
                    icon="📜"
                    title="Select a Pipeline"
                    description="Choose a pipeline to view its complete audit trail and decision timeline."
                />
            )}
        </div>
    );
}

export default function AuditPage() {
    return (
        <Suspense fallback={<div className="fade-in" style={{ padding: 24 }}>Loading audit trail...</div>}>
            <AuditPageContent />
        </Suspense>
    );
}
