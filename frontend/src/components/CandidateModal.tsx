import React from 'react';
import { X, Award, Briefcase, GraduationCap, AlertTriangle, Target } from 'lucide-react';
import type { CandidateLike } from "@/types/domain";

interface CandidateModalProps {
    candidate: CandidateLike | null;
    onClose: () => void;
}

export function CandidateModal({ candidate, onClose }: CandidateModalProps) {
    if (!candidate) return null;

    // Normalize from ScoredCandidate or Recommendation model
    const score = candidate.overall_weighted_score || candidate.overall_score || candidate.relevance_score || 0;
    const rawStrengths = candidate.strengths ?? candidate.skills;
    const strengths = Array.isArray(rawStrengths) ? rawStrengths : [];
    const rawGaps = candidate.gaps ?? candidate.missing_skills;
    const gaps = Array.isArray(rawGaps) ? rawGaps : [];
    const reasoning =
        (typeof candidate.reasoning === "string" && candidate.reasoning) ||
        (typeof candidate.match_reason === "string" && candidate.match_reason) ||
        "No manual insights available.";
    const thought_process =
        (typeof candidate.thought_process === "string" && candidate.thought_process) ||
        "Scoring applied standard criteria.";
    const experienceYearsRaw = Number(candidate.experience_years);
    const experienceYears = Number.isFinite(experienceYearsRaw) ? experienceYearsRaw : 0;
    const educationLabel =
        typeof candidate.education === "string" && candidate.education.length > 0
            ? candidate.education
            : "-";

    return (
        <div style={{
            position: "fixed",
            top: 0, left: 0, width: "100%", height: "100%",
            background: "rgba(10, 14, 26, 0.8)",
            backdropFilter: "blur(4px)",
            zIndex: 1000,
            display: "flex", alignItems: "center", justifyContent: "center"
        }} onClick={onClose}>
            
            <div className="glass-card fade-in" style={{
                width: "90%",
                maxWidth: "800px",
                maxHeight: "90vh",
                overflowY: "auto",
                background: "rgba(15, 23, 42, 0.95)",
                padding: "32px",
                position: "relative"
            }} onClick={e => e.stopPropagation()}>
                
                <button onClick={onClose} style={{
                    position: "absolute", top: 20, right: 20,
                    background: "none", border: "none", color: "var(--text-muted)", cursor: "pointer"
                }}><X size={24} /></button>

                <div style={{ display: "flex", gap: "24px", marginBottom: "32px", alignItems: "flex-start" }}>
                    <div style={{ width: 80, height: 80, borderRadius: "50%", background: "rgba(255,255,255,0.05)", display: "flex", alignItems: "center", justifyContent: "center", fontSize: "2rem" }}>
                        👤
                    </div>
                    <div>
                        <h2 style={{ fontSize: "2rem", margin: "0 0 8px" }}>{candidate.name || candidate.candidate_name}</h2>
                        <div style={{ display: "flex", gap: 12, color: "var(--text-secondary)", fontSize: "0.9rem" }}>
                            <span style={{ display: "flex", alignItems: "center", gap: 4 }}><Briefcase size={14} /> {experienceYears} Years Exp</span>
                            <span style={{ display: "flex", alignItems: "center", gap: 4 }}><GraduationCap size={14} /> {educationLabel}</span>
                        </div>
                    </div>
                    
                    <div style={{ marginLeft: "auto", textAlign: "right" }}>
                        <div style={{ fontSize: "0.8rem", color: "var(--text-muted)", textTransform: "uppercase" }}>Overall Score</div>
                        <div style={{ fontSize: "3rem", fontWeight: 900, color: score > 80 ? 'var(--accent-emerald)' : 'var(--accent-amber)', lineHeight: 1 }}>
                            {score > 10 ? score : (score * 100).toFixed(0)}<span style={{ fontSize: "1.5rem" }}>%</span>
                        </div>
                    </div>
                </div>

                {/* Score Breakdown Bars if available */}
                {typeof candidate.skills_match === "number" && (
                    <div style={{ marginBottom: "32px" }}>
                        <h3 style={{ fontSize: "1.1rem", marginBottom: "16px" }}>Deterministic Evaluation Matrix</h3>
                        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "20px" }}>
                            {[
                                {
                                    label: "Technical Skills",
                                    val: (Number(candidate.skills_match) / 25) * 100,
                                    color: "var(--accent-blue)",
                                },
                                {
                                    label: "Experience Velocity",
                                    val: (Number(candidate.experience_match) / 25) * 100,
                                    color: "var(--accent-purple)",
                                },
                                {
                                    label: "Education Baseline",
                                    val: (Number(candidate.education_match) / 25) * 100,
                                    color: "var(--accent-emerald)",
                                },
                                {
                                    label: "Culture & Alignment",
                                    val: (Number(candidate.cultural_fit) / 25) * 100,
                                    color: "var(--accent-amber)",
                                },
                            ].map((stat, i) => (
                                <div key={i}>
                                    <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "6px", fontSize: "0.85rem", color: "var(--text-secondary)" }}>
                                        <span>{stat.label}</span>
                                        <span style={{ fontWeight: 700 }}>{stat.val.toFixed(0)}%</span>
                                    </div>
                                    <div style={{ height: "6px", background: "rgba(255,255,255,0.05)", borderRadius: "3px" }}>
                                        <div style={{ height: "100%", width: `${stat.val}%`, background: stat.color, borderRadius: "3px" }} />
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>
                )}

                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "24px", marginBottom: "24px" }}>
                    <div style={{ background: "rgba(16, 185, 129, 0.05)", padding: "20px", borderRadius: "12px", border: "1px solid rgba(16, 185, 129, 0.1)" }}>
                        <h4 style={{ display: "flex", alignItems: "center", gap: "8px", margin: "0 0 16px", color: "var(--accent-emerald)" }}><Award size={18} /> Verified Strengths</h4>
                        <ul style={{ margin: 0, paddingLeft: "20px", fontSize: "0.9rem", color: "var(--text-secondary)", lineHeight: 1.6 }}>
                            {strengths
                                .filter((s): s is string => typeof s === "string")
                                .map((s, i) => (
                                    <li key={i} style={{ marginBottom: "8px" }}>{s}</li>
                                ))}
                        </ul>
                    </div>

                    <div style={{ background: "rgba(244, 63, 94, 0.05)", padding: "20px", borderRadius: "12px", border: "1px solid rgba(244, 63, 94, 0.1)" }}>
                        <h4 style={{ display: "flex", alignItems: "center", gap: "8px", margin: "0 0 16px", color: "var(--accent-rose)" }}><AlertTriangle size={18} /> Potential Gaps</h4>
                        <ul style={{ margin: 0, paddingLeft: "20px", fontSize: "0.9rem", color: "var(--text-secondary)", lineHeight: 1.6 }}>
                            {gaps.length > 0
                                ? gaps
                                    .filter((g): g is string => typeof g === "string")
                                    .map((g, i) => <li key={i} style={{ marginBottom: "8px" }}>{g}</li>)
                                : <li>No significant gaps detected.</li>}
                        </ul>
                    </div>
                </div>

                <div style={{ background: "rgba(255,255,255,0.02)", padding: "24px", borderRadius: "12px", border: "1px solid var(--border-glass)" }}>
                    <h4 style={{ display: "flex", alignItems: "center", gap: "8px", margin: "0 0 16px", color: "var(--text-primary)" }}>
                        <Target size={18} color="var(--accent-cyan)" /> Autonomous Logic Trail
                    </h4>
                    <div style={{ fontSize: "0.9rem", color: "var(--text-secondary)", lineHeight: 1.6, marginBottom: 12 }}>
                        <strong>Reasoning:</strong> {reasoning}
                    </div>
                    <div style={{ fontSize: "0.9rem", color: "var(--text-muted)", lineHeight: 1.6 }}>
                        <strong>System Trace:</strong> {thought_process}
                    </div>
                </div>

            </div>
        </div>
    );
}
