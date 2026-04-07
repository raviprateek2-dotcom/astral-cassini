import React from 'react';
import { Check, Circle, Loader2 } from 'lucide-react';

const STAGES = [
    { key: "intake", label: "Intake" },
    { key: "jd_drafting", label: "Drafting JD" },
    { key: "jd_review", label: "JD Review" },
    { key: "sourcing", label: "Sourcing" },
    { key: "screening", label: "Screening" },
    { key: "shortlist_review", label: "Shortlist" },
    { key: "interviewing", label: "Interviews" },
    { key: "decision", label: "Decision" },
    { key: "offer", label: "Offer" },
    { key: "completed", label: "Completed" },
];

interface PipelineStepsProps {
    currentStage: string;
}

export function PipelineSteps({ currentStage }: PipelineStepsProps) {
    // Find index of current stage
    let currentIndex = STAGES.findIndex(s => s.key === currentStage);
    
    // If not found in standard map (e.g. outreach or engagement which might be aliases or omitted), fallback gracefully
    if (currentIndex === -1) {
        if (currentStage === "hire_review") currentIndex = 7; 
        else currentIndex = 0;
    }

    return (
        <div className="glass-card" style={{ padding: "24px", marginBottom: "24px", overflowX: "auto" }}>
            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", minWidth: "800px" }}>
                {STAGES.map((stage, idx) => {
                    const isCompleted = idx < currentIndex;
                    const isActive = idx === currentIndex;
                    const isPending = idx > currentIndex;

                    return (
                        <div key={stage.key} style={{ display: "flex", alignItems: "center", flex: 1 }}>
                            {/* Node */}
                            <div style={{ display: "flex", flexDirection: "column", alignItems: "center", position: "relative", zIndex: 1 }}>
                                <div style={{
                                    width: 36, height: 36, borderRadius: "50%",
                                    display: "flex", alignItems: "center", justifyContent: "center",
                                    background: isCompleted ? "var(--accent-emerald)" : isActive ? "var(--accent-blue)" : "rgba(255,255,255,0.05)",
                                    border: `2px solid ${isCompleted ? "var(--accent-emerald)" : isActive ? "var(--accent-blue)" : "var(--border-glass)"}`,
                                    color: isCompleted ? "#fff" : isActive ? "#fff" : "var(--text-muted)",
                                    transition: "all 0.3s ease",
                                    boxShadow: isActive ? "0 0 15px rgba(59, 130, 246, 0.5)" : "none"
                                }}>
                                    {isCompleted ? <Check size={18} /> : isActive ? <Loader2 size={18} className="spin" /> : <Circle size={14} />}
                                </div>
                                <span style={{
                                    marginTop: 8, fontSize: "0.75rem", fontWeight: isActive ? 700 : 500,
                                    color: isActive ? "var(--text-primary)" : "var(--text-muted)",
                                    whiteSpace: "nowrap",
                                    position: "absolute",
                                    top: 40
                                }}>
                                    {stage.label}
                                </span>
                            </div>

                            {/* Connector Line */}
                            {idx < STAGES.length - 1 && (
                                <div style={{
                                    flex: 1,
                                    height: 3,
                                    background: isCompleted ? "var(--accent-emerald)" : "var(--border-glass)",
                                    margin: "0 12px",
                                    borderRadius: 2,
                                    transition: "all 0.3s ease"
                                }} />
                            )}
                        </div>
                    );
                })}
            </div>
            
            {/* Pad bottom for absolute labels */}
            <div style={{ height: "30px" }} />
        </div>
    );
}
