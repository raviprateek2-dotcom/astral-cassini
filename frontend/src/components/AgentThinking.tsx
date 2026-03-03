import React from "react";

interface AgentThinkingProps {
    message?: string;
    size?: "sm" | "md" | "lg";
}

export const AgentThinking: React.FC<AgentThinkingProps> = ({
    message = "Agent is processing...",
    size = "md",
}) => {
    const dotSize = size === "sm" ? 4 : size === "md" ? 6 : 8;
    const fontSize = size === "sm" ? "0.75rem" : size === "md" ? "0.875rem" : "1rem";

    return (
        <div style={{ display: "flex", alignItems: "center", gap: "12px", padding: "8px 12px" }}>
            <div style={{ display: "flex", gap: "4px" }}>
                {[0, 1, 2].map((i) => (
                    <div
                        key={i}
                        className="thinking-dot"
                        style={{
                            width: dotSize,
                            height: dotSize,
                            borderRadius: "50%",
                            backgroundColor: "var(--accent-blue)",
                            animation: `thinking-bounce 1.4s infinite ease-in-out both`,
                            animationDelay: `${i * 0.16}s`,
                        }}
                    />
                ))}
            </div>
            <span style={{ fontSize, color: "var(--text-secondary)", fontWeight: 500, letterSpacing: "0.02em" }}>
                {message}
            </span>
        </div>
    );
};
