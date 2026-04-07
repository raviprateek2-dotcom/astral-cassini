import React, { useState } from 'react';
import { Search, ChevronDown, ChevronUp, User } from 'lucide-react';
import type { CandidateLike } from "@/types/domain";

interface CandidateTableProps {
    candidates: CandidateLike[];
    onRowClick: (candidate: CandidateLike) => void;
    stage: string;
}

/** Normalized row after map (score is always a finite number for display). */
type CandidateTableRow = CandidateLike & {
    id?: string;
    name?: unknown;
    score: number;
};

export function CandidateTable({ candidates, onRowClick, stage }: CandidateTableProps) {
    const [searchTerm, setSearchTerm] = useState("");
    const [sortField, setSortField] = useState("overall_score");
    const [sortDesc, setSortDesc] = useState(true);

    if (!candidates || candidates.length === 0) {
        return (
            <div className="glass-card" style={{ padding: "40px", textAlign: "center", color: "var(--text-muted)" }}>
                <p>No candidates available in the current stage.</p>
            </div>
        );
    }

    // Filter & Sort
    let processed: CandidateTableRow[] = [...candidates].map((c) => {
        const raw =
            c.overall_weighted_score ?? c.overall_score ?? c.relevance_score ?? 0;
        const score = typeof raw === "number" && Number.isFinite(raw) ? raw : Number(raw) || 0;
        return {
            ...c,
            id: c.candidate_id || c.id,
            name: c.candidate_name || c.name,
            score,
        };
    });

    if (searchTerm) {
        const term = searchTerm.toLowerCase();
        processed = processed.filter((c) => {
            const name = typeof c.name === "string" ? c.name.toLowerCase() : "";
            const skills = Array.isArray(c.skills) ? c.skills : [];
            return (
                name.includes(term) ||
                skills.some((s) => typeof s === "string" && s.toLowerCase().includes(term))
            );
        });
    }

    const sortable = (v: unknown): number | string => {
        if (typeof v === "number" && Number.isFinite(v)) return v;
        if (typeof v === "string") return v.toLowerCase();
        const n = Number(v);
        if (Number.isFinite(n)) return n;
        return "";
    };
    const compare = (x: number | string, y: number | string): number => {
        if (typeof x === "number" && typeof y === "number") return x - y;
        return String(x).localeCompare(String(y));
    };
    processed.sort((a, b) => {
        const valA = sortable(a[sortField as keyof CandidateTableRow] ?? a.score);
        const valB = sortable(b[sortField as keyof CandidateTableRow] ?? b.score);
        const diff = compare(valA, valB);
        if (diff < 0) return sortDesc ? 1 : -1;
        if (diff > 0) return sortDesc ? -1 : 1;
        return 0;
    });

    const handleSort = (field: string) => {
        if (sortField === field) setSortDesc(!sortDesc);
        else {
            setSortField(field);
            setSortDesc(true);
        }
    };

    return (
        <div className="glass-card fade-in" style={{ padding: "24px" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "20px" }}>
                <h2 style={{ fontSize: "1.2rem", fontWeight: 700, margin: 0 }}>Candidate Deep-Dive</h2>
                
                <div style={{ display: "flex", gap: "12px" }}>
                    <div style={{ position: "relative" }}>
                        <Search size={16} style={{ position: "absolute", left: 12, top: 10, color: "var(--text-muted)" }} />
                        <input 
                            className="input" 
                            placeholder="Search names or skills..." 
                            value={searchTerm}
                            onChange={(e) => setSearchTerm(e.target.value)}
                            style={{ paddingLeft: 36, width: 250 }}
                        />
                    </div>
                </div>
            </div>

            <div style={{ overflowX: "auto" }}>
                <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "0.9rem" }}>
                    <thead>
                        <tr style={{ borderBottom: "1px solid var(--border-glass)", textAlign: "left", color: "var(--text-muted)" }}>
                            <th style={{ padding: "12px 16px", cursor: "pointer" }} onClick={() => handleSort("name")}>
                                Candidate {sortField === "name" && (sortDesc ? <ChevronDown size={14} /> : <ChevronUp size={14} />)}
                            </th>
                            <th style={{ padding: "12px 16px" }}>Experience</th>
                            <th style={{ padding: "12px 16px" }}>Core Competency</th>
                            <th style={{ padding: "12px 16px", cursor: "pointer" }} onClick={() => handleSort("score")}>
                                Overall Score {sortField === "score" && (sortDesc ? <ChevronDown size={14} /> : <ChevronUp size={14} />)}
                            </th>
                            {stage === "hire_review" && (
                                <th style={{ padding: "12px 16px" }}>Decision</th>
                            )}
                        </tr>
                    </thead>
                    <tbody>
                        {processed.map((c, i) => (
                            <tr key={i} 
                                onClick={() => onRowClick(c)}
                                style={{ 
                                    borderBottom: "1px solid rgba(255,255,255,0.02)", 
                                    cursor: "pointer",
                                    transition: "background 0.2s ease"
                                }}
                                onMouseEnter={(e) => e.currentTarget.style.background = "rgba(255,255,255,0.03)"}
                                onMouseLeave={(e) => e.currentTarget.style.background = "transparent"}
                            >
                                <td style={{ padding: "16px" }}>
                                    <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
                                        <div style={{ width: 36, height: 36, borderRadius: "50%", background: "var(--border-glass)", display: "flex", alignItems: "center", justifyContent: "center" }}>
                                            <User size={18} />
                                        </div>
                                        <div>
                                            <div style={{ fontWeight: 600 }}>{typeof c.name === "string" ? c.name : String(c.name ?? "—")}</div>
                                            <div style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>{c.id}</div>
                                        </div>
                                    </div>
                                </td>
                                
                                <td style={{ padding: "16px", color: "var(--text-secondary)" }}>
                                    {(() => {
                                        const y = Number(c.experience_years);
                                        return Number.isFinite(y) && y > 0 ? `${y} Years` : "—";
                                    })()}
                                </td>
                                
                                <td style={{ padding: "16px" }}>
                                    <div style={{ display: "flex", flexWrap: "wrap", gap: 4 }}>
                                        {(() => {
                                            const raw = c.skills ?? c.strengths;
                                            const arr = Array.isArray(raw) ? raw : [];
                                            return arr.slice(0, 3).map((s, j: number) => (
                                            <span key={j} style={{ background: "rgba(59, 130, 246, 0.1)", color: "var(--accent-blue)", padding: "2px 8px", borderRadius: 4, fontSize: "0.75rem" }}>
                                                {typeof s === "string" ? s : String(s)}
                                            </span>
                                            ));
                                        })()}
                                    </div>
                                </td>
                                
                                <td style={{ padding: "16px", width: 200 }}>
                                    <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
                                        <div style={{ width: "100%", height: 6, background: "rgba(255,255,255,0.1)", borderRadius: 3, overflow: "hidden" }}>
                                            <div style={{ 
                                                height: "100%", 
                                                width: `${c.score}%`, 
                                                background: c.score > 80 ? "var(--accent-emerald)" : c.score > 60 ? "var(--accent-amber)" : "var(--accent-rose)",
                                                transition: "width 1s ease-in-out" 
                                            }} />
                                        </div>
                                        <span style={{ fontWeight: 700, fontSize: "0.85rem" }}>{c.score > 10 ? c.score : (c.score * 100).toFixed(0)}</span>
                                    </div>
                                </td>

                                {stage === "hire_review" && (
                                    <td style={{ padding: "16px" }}>
                                        <span className={`badge ${c.decision === "hire" ? "badge-emerald" : "badge-rose"}`}>
                                            {typeof c.decision === "string"
                                                ? c.decision.toUpperCase()
                                                : "UNKNOWN"}
                                        </span>
                                    </td>
                                )}
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </div>
    );
}
