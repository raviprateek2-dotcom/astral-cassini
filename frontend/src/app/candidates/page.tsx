"use client";

import { useState, useEffect } from "react";
import { api } from "@/lib/api";

interface Job {
    job_id: string;
    job_title: string;
    department: string;
}

interface CandidateProfile {
    candidate_id: string;
    candidate_name: string;
    overall_score: number;
    skills_match: number;
    experience_match: number;
    education_match: number;
    cultural_fit: number;
    strengths?: string[];
    gaps?: string[];
    reasoning?: string;
    match_reason?: string;
}

interface RawCandidate {
    name: string;
    skills: string[];
    experience_years: number;
    relevance_score: number;
    match_reason?: string;
}

export default function CandidatesPage() {
    const [jobs, setJobs] = useState<Job[]>([]);
    const [selectedJob, setSelectedJob] = useState<string>("");
    const [candidates, setCandidates] = useState<{
        scored_candidates: CandidateProfile[];
        candidates: RawCandidate[];
    } | null>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        api.listJobs().then(setJobs).catch(() => { }).finally(() => setLoading(false));
    }, []);

    async function loadCandidates(jobId: string) {
        setSelectedJob(jobId);
        setLoading(true);
        try {
            const data = await api.getCandidates(jobId);
            setCandidates(data);
        } catch {
            setCandidates(null);
        } finally {
            setLoading(false);
        }
    }

    const scored = candidates?.scored_candidates || [];
    const matched = candidates?.candidates || [];

    return (
        <div className="fade-in">
            <h1 style={{ fontSize: "2rem", fontWeight: 800, margin: "0 0 4px" }}>Candidate Pipeline</h1>
            <p style={{ color: "var(--text-secondary)", fontSize: "0.9rem", margin: "0 0 32px" }}>
                View matched & scored candidates from Agent 3 (Scout) and Agent 4 (Screener)
            </p>

            {/* Job Selector */}
            <div className="glass-card" style={{ padding: 20, marginBottom: 24 }}>
                <label style={{ fontSize: "0.8rem", color: "var(--text-muted)", display: "block", marginBottom: 8 }}>
                    Select Pipeline
                </label>
                <select
                    className="input"
                    value={selectedJob}
                    onChange={(e) => loadCandidates(e.target.value)}
                    style={{ maxWidth: 400 }}
                >
                    <option value="">Choose a job...</option>
                    {jobs.map((j) => (
                        <option key={j.job_id} value={j.job_id}>
                            {j.job_title} — {j.department}
                        </option>
                    ))}
                </select>
            </div>

            {loading && selectedJob && (
                <div style={{ display: "flex", justifyContent: "center", padding: 60 }}>
                    <div className="spinner" />
                </div>
            )}

            {/* Scored Candidates */}
            {scored.length > 0 && (
                <div className="glass-card" style={{ padding: 24, marginBottom: 24 }}>
                    <h2 style={{ fontSize: "1.1rem", fontWeight: 700, margin: "0 0 20px" }}>
                        📊 Scored Candidates ({scored.length})
                    </h2>
                    <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
                        {scored.map((c: CandidateProfile, i: number) => (
                            <div
                                key={i}
                                style={{
                                    padding: 20,
                                    borderRadius: 12,
                                    border: "1px solid var(--border-glass)",
                                    background: "rgba(15, 23, 42, 0.4)",
                                }}
                            >
                                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
                                    <div>
                                        <h3 style={{ margin: 0, fontSize: "1rem", fontWeight: 600 }}>{c.candidate_name}</h3>
                                        <p style={{ fontSize: "0.8rem", color: "var(--text-muted)", margin: "4px 0 0" }}>
                                            ID: {c.candidate_id}
                                        </p>
                                    </div>
                                    <div style={{ textAlign: "right" }}>
                                        <span
                                            style={{
                                                fontSize: "1.8rem",
                                                fontWeight: 800,
                                                color:
                                                    c.overall_score >= 80
                                                        ? "var(--accent-emerald)"
                                                        : c.overall_score >= 60
                                                            ? "var(--accent-amber)"
                                                            : "var(--accent-rose)",
                                            }}
                                        >
                                            {Math.round(c.overall_score)}
                                        </span>
                                        <span style={{ fontSize: "0.8rem", color: "var(--text-muted)" }}>/100</span>
                                    </div>
                                </div>

                                {/* Score Bars */}
                                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12, marginTop: 16 }}>
                                    {[
                                        { label: "Skills", value: c.skills_match, max: 25 },
                                        { label: "Experience", value: c.experience_match, max: 25 },
                                        { label: "Education", value: c.education_match, max: 25 },
                                        { label: "Cultural Fit", value: c.cultural_fit, max: 25 },
                                    ].map((dim) => (
                                        <div key={dim.label}>
                                            <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 4 }}>
                                                <span style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>{dim.label}</span>
                                                <span style={{ fontSize: "0.75rem", fontWeight: 600 }}>
                                                    {dim.value}/{dim.max}
                                                </span>
                                            </div>
                                            <div className="score-bar">
                                                <div
                                                    className="score-bar-fill"
                                                    style={{
                                                        width: `${(dim.value / dim.max) * 100}%`,
                                                        background:
                                                            dim.value / dim.max >= 0.8
                                                                ? "var(--accent-emerald)"
                                                                : dim.value / dim.max >= 0.6
                                                                    ? "var(--accent-amber)"
                                                                    : "var(--accent-rose)",
                                                    }}
                                                />
                                            </div>
                                        </div>
                                    ))}
                                </div>

                                {/* Strengths & Gaps */}
                                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16, marginTop: 16 }}>
                                    <div>
                                        <p style={{ fontSize: "0.75rem", color: "var(--accent-emerald)", fontWeight: 600, margin: "0 0 6px" }}>
                                            Strengths
                                        </p>
                                        {(c.strengths || []).map((s: string, j: number) => (
                                            <p key={j} style={{ fontSize: "0.8rem", color: "var(--text-secondary)", margin: "2px 0" }}>
                                                ✓ {s}
                                            </p>
                                        ))}
                                    </div>
                                    <div>
                                        <p style={{ fontSize: "0.75rem", color: "var(--accent-rose)", fontWeight: 600, margin: "0 0 6px" }}>
                                            Gaps
                                        </p>
                                        {(c.gaps || []).map((g: string, j: number) => (
                                            <p key={j} style={{ fontSize: "0.8rem", color: "var(--text-secondary)", margin: "2px 0" }}>
                                                △ {g}
                                            </p>
                                        ))}
                                    </div>
                                </div>

                                {c.reasoning && (
                                    <p style={{ fontSize: "0.8rem", color: "var(--text-secondary)", marginTop: 12, padding: "8px 12px", background: "rgba(59, 130, 246, 0.05)", borderRadius: 8, borderLeft: "3px solid var(--accent-blue)" }}>
                                        <span style={{ marginRight: 6 }}>💡</span>
                                        <strong>Recruitment Reason:</strong> {c.reasoning}
                                    </p>
                                )}
                                {c.match_reason && !c.reasoning && (
                                    <p style={{ fontSize: "0.8rem", color: "var(--text-secondary)", marginTop: 12, padding: "8px 12px", background: "rgba(59, 130, 246, 0.05)", borderRadius: 8, borderLeft: "3px solid var(--accent-blue)" }}>
                                        <span style={{ marginRight: 6 }}>💡</span>
                                        <strong>Match Reason:</strong> {c.match_reason}
                                    </p>
                                )}
                            </div>
                        ))}
                    </div>
                </div>
            )}

            {/* Matched Candidates (raw) */}
            {matched.length > 0 && scored.length === 0 && (
                <div className="glass-card" style={{ padding: 24 }}>
                    <h2 style={{ fontSize: "1.1rem", fontWeight: 700, margin: "0 0 20px" }}>
                        🔍 Matched Candidates ({matched.length})
                    </h2>
                    <table className="data-table">
                        <thead>
                            <tr>
                                <th>Name</th>
                                <th>Skills</th>
                                <th>Experience</th>
                                <th>Relevance</th>
                            </tr>
                        </thead>
                        <tbody>
                            {matched.map((c: RawCandidate, i: number) => (
                                <tr key={i}>
                                    <td style={{ fontWeight: 600 }}>{c.name}</td>
                                    <td>
                                        <div style={{ display: "flex", flexWrap: "wrap", gap: 4 }}>
                                            {(c.skills || []).slice(0, 4).map((s: string, j: number) => (
                                                <span key={j} className="badge badge-blue" style={{ fontSize: "0.65rem" }}>
                                                    {s}
                                                </span>
                                            ))}
                                        </div>
                                    </td>
                                    <td>{c.experience_years} yrs</td>
                                    <td>
                                        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                                            <span
                                                style={{
                                                    fontWeight: 700,
                                                    color:
                                                        c.relevance_score >= 0.8
                                                            ? "var(--accent-emerald)"
                                                            : "var(--accent-amber)",
                                                }}
                                            >
                                                {(c.relevance_score * 100).toFixed(0)}%
                                            </span>
                                            {c.match_reason && (
                                                <span title={c.match_reason} style={{ cursor: "help", opacity: 0.7 }}>💡</span>
                                            )}
                                        </div>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            )}

            {selectedJob && !loading && !scored.length && !matched.length && (
                <div className="glass-card" style={{ padding: 40, textAlign: "center" }}>
                    <p style={{ fontSize: "2rem", margin: "0 0 12px" }}>🔍</p>
                    <p style={{ color: "var(--text-muted)" }}>
                        No candidates yet. The pipeline needs to reach the sourcing stage first.
                    </p>
                </div>
            )}
        </div>
    );
}
