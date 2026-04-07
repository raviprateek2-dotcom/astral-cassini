import React, { useState } from 'react';
import { Play, RotateCcw, FastForward, Loader2 } from 'lucide-react';
import { useJobStore } from '@/store/useJobStore';

export function ControlPanel() {
    const { currentJob, forceRunAgent, loading } = useJobStore();
    const [actionLoading, setActionLoading] = useState<string | null>(null);

    const handleAction = async (action: string, updates: any = {}) => {
        setActionLoading(action);
        await forceRunAgent(action, updates);
        setActionLoading(null);
    };

    if (!currentJob) return null;

    const isActive = !["completed"].includes(currentJob.current_stage);

    return (
        <div className="glass-card fade-in" style={{ padding: "20px", display: "flex", alignItems: "center", gap: "16px", flexWrap: "wrap", marginBottom: "24px", background: "rgba(15, 23, 42, 0.8)", border: "1px solid var(--border-glass)" }}>
            <h3 style={{ fontSize: "0.9rem", fontWeight: 700, margin: 0, color: "var(--text-secondary)", marginRight: "8px", textTransform: "uppercase", letterSpacing: "0.05em" }}>
                System Controls
            </h3>

            <div style={{ display: "flex", gap: "12px", flexWrap: "wrap" }}>
                {/* Reset System: Drops state and goes back to jd_drafting */}
                <button 
                    className="btn-outline" 
                    onClick={() => handleAction("reset_pipeline")}
                    disabled={loading || actionLoading !== null}
                    style={{ fontSize: "0.85rem", padding: "8px 16px", display: "flex", alignItems: "center", gap: 6, borderColor: "var(--accent-rose)", color: "var(--accent-rose)" }}
                >
                    {actionLoading === "reset_pipeline" ? <Loader2 size={14} className="spin" /> : <RotateCcw size={14} />}
                    Hard Reset Pipeline
                </button>

                {/* Re-run current active agent or skip a stage */}
                <button 
                    className="btn-outline" 
                    onClick={() => handleAction("rerun_current_stage")}
                    disabled={loading || actionLoading !== null || !isActive}
                    style={{ fontSize: "0.85rem", padding: "8px 16px", display: "flex", alignItems: "center", gap: 6 }}
                >
                    {actionLoading === "rerun_current_stage" ? <Loader2 size={14} className="spin" /> : <Play size={14} />}
                    Re-run Stage
                </button>

                {/* Run entire pipeline bypassing hits (simulated by fast-forwarding state) 
                    For safety we'll assume the backend action 'force_resume' triggers progression. */}
                <button 
                    className="btn-primary" 
                    onClick={() => handleAction("force_resume")}
                    disabled={loading || actionLoading !== null || !isActive}
                    style={{ fontSize: "0.85rem", padding: "8px 16px", display: "flex", alignItems: "center", gap: 6 }}
                >
                    {actionLoading === "force_resume" ? <Loader2 size={14} className="spin" /> : <FastForward size={14} />}
                    Force Advance Pipeline
                </button>
            </div>
        </div>
    );
}
