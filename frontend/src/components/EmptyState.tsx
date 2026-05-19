import React from "react";

interface EmptyStateProps {
    icon: string;
    title: string;
    description: string;
    action?: {
        label: string;
        onClick: () => void;
    };
}

export function EmptyState({ icon, title, description, action }: EmptyStateProps) {
    return (
        <div className="glass-card stagger-1" style={{ padding: "80px 40px", textAlign: "center", background: "rgba(15, 23, 42, 0.4)" }}>
            <div style={{ fontSize: "3rem", marginBottom: 20 }}>{icon}</div>
            <h2 style={{ fontSize: "1.5rem", fontWeight: 700, marginBottom: 12 }}>{title}</h2>
            <p style={{ color: "var(--text-muted)", maxWidth: "500px", margin: "0 auto", lineHeight: 1.6, marginBottom: action ? 24 : 0 }}>
                {description}
            </p>
            {action && (
                <button className="btn-primary" onClick={action.onClick} style={{ padding: "12px 24px" }}>
                    {action.label}
                </button>
            )}
        </div>
    );
}
