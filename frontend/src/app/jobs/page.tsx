"use client";

import { useState, useEffect } from "react";
import { api, CreateJobPayload } from "@/lib/api";
import { AgentThinking } from "@/components/AgentThinking";
import { toast } from "sonner";
import { useWebSocket } from "@/hooks/useWebSocket";

export default function JobsPage() {
    const [showForm, setShowForm] = useState(false);
    const [loading, setLoading] = useState(false);
    const [result, setResult] = useState<any>(null);
    const [error, setError] = useState("");

    const [form, setForm] = useState<CreateJobPayload>({
        job_title: "",
        department: "",
        requirements: [],
        preferred_qualifications: [],
        location: "Remote",
        salary_range: "",
    });
    const [reqInput, setReqInput] = useState("");
    const [prefInput, setPrefInput] = useState("");

    // WebSocket connection active only when we have a result.job_id
    const { connected, events, heartbeat, tokenStream } = useWebSocket(result?.job_id || null);

    async function handleSubmit(e: React.FormEvent) {
        e.preventDefault();
        setLoading(true);
        setError("");
        try {
            const data = await api.createJob(form);
            setResult(data);
            setShowForm(false);
            toast.success("Job Requisition Initialized", {
                description: "Agent 1 (JD Architect) has successfully drafted the requirement."
            });
        } catch (err: any) {
            setError(err.message || "Failed to create job");
            toast.error("Initialization Failed", {
                description: err.message || "Failed to establish agent workflow."
            });
        } finally {
            setLoading(false);
        }
    }

    function addRequirement() {
        if (reqInput.trim()) {
            setForm((f) => ({ ...f, requirements: [...f.requirements, reqInput.trim()] }));
            setReqInput("");
        }
    }

    function addPreferred() {
        if (prefInput.trim()) {
            setForm((f) => ({
                ...f,
                preferred_qualifications: [...(f.preferred_qualifications || []), prefInput.trim()],
            }));
            setPrefInput("");
        }
    }

    // Determine current stage dynamically from WebSocket heartbeat or fallback to initial result
    const currentStage = heartbeat?.current_stage || result?.current_stage || "jd_drafting";

    // Determine the JS to show: either the live streaming tokens, or the final from state.
    const displayJD = tokenStream || result?.state?.job_description || "Agent Architect is typing...";

    return (
        <div className="fade-in">
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 32 }}>
                <div>
                    <h1 style={{ fontSize: "2rem", fontWeight: 800, margin: 0 }}>Job Requisitions</h1>
                    <p style={{ color: "var(--text-secondary)", marginTop: 4, fontSize: "0.9rem" }}>
                        Create new positions & watch Agent 1 draft the JD
                    </p>
                </div>
                <button className="btn-primary" onClick={() => setShowForm(!showForm)}>
                    {showForm ? "✕ Cancel" : "+ New Position"}
                </button>
            </div>

            {error && (
                <div
                    className="glass-card"
                    style={{ padding: 16, marginBottom: 20, borderColor: "var(--accent-rose)" }}
                >
                    <p style={{ color: "var(--accent-rose)", margin: 0, fontSize: "0.9rem" }}>⚠️ {error}</p>
                </div>
            )}

            {/* Create Job Form */}
            {showForm && (
                <div className="glass-card fade-in" style={{ padding: 32, marginBottom: 32 }}>
                    <h2 style={{ fontSize: "1.2rem", fontWeight: 700, margin: "0 0 24px" }}>
                        New Job Requisition
                    </h2>
                    <form onSubmit={handleSubmit}>
                        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 20, marginBottom: 20 }}>
                            <div>
                                <label style={{ fontSize: "0.8rem", color: "var(--text-muted)", display: "block", marginBottom: 6 }}>
                                    Job Title *
                                </label>
                                <input
                                    className="input"
                                    placeholder="e.g. Senior ML Engineer"
                                    value={form.job_title}
                                    onChange={(e) => setForm((f) => ({ ...f, job_title: e.target.value }))}
                                    required
                                />
                            </div>
                            <div>
                                <label style={{ fontSize: "0.8rem", color: "var(--text-muted)", display: "block", marginBottom: 6 }}>
                                    Department *
                                </label>
                                <input
                                    className="input"
                                    placeholder="e.g. Engineering"
                                    value={form.department}
                                    onChange={(e) => setForm((f) => ({ ...f, department: e.target.value }))}
                                    required
                                />
                            </div>
                            <div>
                                <label style={{ fontSize: "0.8rem", color: "var(--text-muted)", display: "block", marginBottom: 6 }}>
                                    Location
                                </label>
                                <input
                                    className="input"
                                    placeholder="e.g. Remote / Bangalore"
                                    value={form.location}
                                    onChange={(e) => setForm((f) => ({ ...f, location: e.target.value }))}
                                />
                            </div>
                            <div>
                                <label style={{ fontSize: "0.8rem", color: "var(--text-muted)", display: "block", marginBottom: 6 }}>
                                    Salary Range
                                </label>
                                <input
                                    className="input"
                                    placeholder="e.g. $120K - $180K"
                                    value={form.salary_range}
                                    onChange={(e) => setForm((f) => ({ ...f, salary_range: e.target.value }))}
                                />
                            </div>
                        </div>

                        {/* Requirements */}
                        <div style={{ marginBottom: 20 }}>
                            <label style={{ fontSize: "0.8rem", color: "var(--text-muted)", display: "block", marginBottom: 6 }}>
                                Required Qualifications
                            </label>
                            <div style={{ display: "flex", gap: 8 }}>
                                <input
                                    className="input"
                                    placeholder="Add a requirement..."
                                    value={reqInput}
                                    onChange={(e) => setReqInput(e.target.value)}
                                    onKeyDown={(e) => e.key === "Enter" && (e.preventDefault(), addRequirement())}
                                />
                                <button type="button" className="btn-outline" onClick={addRequirement}>
                                    Add
                                </button>
                            </div>
                            <div style={{ display: "flex", flexWrap: "wrap", gap: 8, marginTop: 8 }}>
                                {form.requirements.map((r, i) => (
                                    <span
                                        key={i}
                                        className="badge badge-blue"
                                        style={{ cursor: "pointer" }}
                                        onClick={() =>
                                            setForm((f) => ({
                                                ...f,
                                                requirements: f.requirements.filter((_, j) => j !== i),
                                            }))
                                        }
                                    >
                                        {r} ✕
                                    </span>
                                ))}
                            </div>
                        </div>

                        {/* Preferred */}
                        <div style={{ marginBottom: 24 }}>
                            <label style={{ fontSize: "0.8rem", color: "var(--text-muted)", display: "block", marginBottom: 6 }}>
                                Preferred Qualifications
                            </label>
                            <div style={{ display: "flex", gap: 8 }}>
                                <input
                                    className="input"
                                    placeholder="Add a preference..."
                                    value={prefInput}
                                    onChange={(e) => setPrefInput(e.target.value)}
                                    onKeyDown={(e) => e.key === "Enter" && (e.preventDefault(), addPreferred())}
                                />
                                <button type="button" className="btn-outline" onClick={addPreferred}>
                                    Add
                                </button>
                            </div>
                            <div style={{ display: "flex", flexWrap: "wrap", gap: 8, marginTop: 8 }}>
                                {(form.preferred_qualifications || []).map((p, i) => (
                                    <span
                                        key={i}
                                        className="badge badge-purple"
                                        style={{ cursor: "pointer" }}
                                        onClick={() =>
                                            setForm((f) => ({
                                                ...f,
                                                preferred_qualifications: (f.preferred_qualifications || []).filter(
                                                    (_, j) => j !== i
                                                ),
                                            }))
                                        }
                                    >
                                        {p} ✕
                                    </span>
                                ))}
                            </div>
                        </div>

                        <button className="btn-primary" type="submit" disabled={loading || !form.job_title || !form.department} style={{ padding: loading ? "4px 12px" : "10px 24px" }}>
                            {loading ? (
                                <AgentThinking message="Agent 1 is drafting JD..." size="sm" />
                            ) : (
                                "🚀 Create & Start Pipeline"
                            )}
                        </button>
                    </form>
                </div>
            )}

            {/* Result */}
            {result && (
                <div className="glass-card fade-in" style={{ padding: 32 }}>
                    <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 20 }}>
                        <span style={{ fontSize: "1.5rem" }}>
                            {currentStage === "jd_drafting" ? <div className="spinner" style={{ width: 24, height: 24, borderWidth: 2 }} /> : "✅"}
                        </span>
                        <div>
                            <h2 style={{ fontSize: "1.2rem", fontWeight: 700, margin: 0 }}>
                                {currentStage === "jd_drafting" ? "Pipeline Started - Drafting JD..." : "Pipeline Started!"}
                            </h2>
                            <p style={{ color: "var(--text-muted)", fontSize: "0.85rem", margin: "4px 0 0" }}>
                                Job ID: <code style={{ color: "var(--accent-blue)" }}>{result.job_id}</code> •
                                Stage: <span className={`badge ${stageBadge(currentStage)}`}>
                                    {currentStage}
                                </span>
                                {connected && <span style={{ marginLeft: 8, color: "var(--accent-emerald)" }}>• 🟢 Live</span>}
                            </p>
                        </div>
                    </div>

                    <div>
                        <h3 style={{ fontSize: "1rem", fontWeight: 600, margin: "0 0 12px", color: "var(--accent-blue)" }}>
                            📝 Generated Job Description
                        </h3>
                        <div
                            style={{
                                padding: 20,
                                borderRadius: 12,
                                border: "1px solid var(--border-glass)",
                                background: "rgba(15, 23, 42, 0.6)",
                                fontSize: "0.85rem",
                                lineHeight: 1.7,
                                whiteSpace: "pre-wrap",
                                maxHeight: 500,
                                overflowY: "auto",
                                position: "relative"
                            }}
                        >
                            {displayJD}
                            {currentStage === "jd_drafting" && <span className="typing-cursor"></span>}
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}

function stageBadge(stage: string): string {
    const map: Record<string, string> = {
        jd_drafting: "badge-purple",
        jd_review: "badge-amber",
        sourcing: "badge-cyan",
        screening: "badge-blue",
        shortlist_review: "badge-amber",
        completed: "badge-emerald",
    };
    return map[stage] || "badge-blue";
}
