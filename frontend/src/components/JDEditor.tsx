"use client";

import { useState } from "react";

interface JDEditorProps {
    initialValue: string;
    onChange: (value: string) => void;
}

export default function JDEditor({ initialValue, onChange }: JDEditorProps) {
    const [value, setValue] = useState(initialValue);
    const requiredSections = [
        "Role Summary",
        "Core Responsibilities",
        "Required Qualifications",
        "Preferred Qualifications",
        "Compensation & Benefits",
        "Interview Process",
        "Equal Opportunity Statement",
    ];

    const handleChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
        const newValue = e.target.value;
        setValue(newValue);
        onChange(newValue);
    };

    return (
        <div className="fade-in" style={{ width: "100%" }}>
            <div 
                style={{ 
                    display: "flex", 
                    justifyContent: "space-between", 
                    alignItems: "center",
                    marginBottom: 12 
                }}
            >
                <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                    <span style={{ fontSize: "1.2rem" }}>📝</span>
                    <span style={{ fontSize: "0.85rem", fontWeight: 600, color: "var(--text-secondary)" }}>
                        Collaborative Editor
                    </span>
                </div>
                <span style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>
                    {value.length} characters | Markdown supported
                </span>
            </div>

            <div
                style={{
                    marginBottom: 12,
                    padding: 12,
                    borderRadius: 12,
                    border: "1px dashed var(--border-glass)",
                    background: "rgba(59, 130, 246, 0.06)",
                }}
            >
                <p style={{ margin: "0 0 8px", fontSize: "0.78rem", fontWeight: 700, color: "var(--accent-blue)" }}>
                    Required JD Sections
                </p>
                <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
                    {requiredSections.map((section) => (
                        <span key={section} className="badge badge-blue" style={{ fontSize: "0.68rem" }}>
                            {section}
                        </span>
                    ))}
                </div>
            </div>

            <div 
                style={{ 
                    position: "relative",
                    background: "rgba(15, 23, 42, 0.4)",
                    borderRadius: 16,
                    border: "1px solid var(--border-glass)",
                    padding: 4,
                    transition: "all 0.3s ease",
                }}
                className="editor-container"
            >
                <textarea
                    value={value}
                    onChange={handleChange}
                    spellCheck={false}
                    style={{
                        width: "100%",
                        minHeight: "400px",
                        background: "transparent",
                        border: "none",
                        color: "var(--text-primary)",
                        padding: "20px",
                        fontSize: "0.95rem",
                        lineHeight: "1.6",
                        fontFamily: "var(--font-mono, 'JetBrains Mono', monospace)",
                        outline: "none",
                        resize: "vertical",
                    }}
                    placeholder="Draft your job description here..."
                />
                
                {/* Visual Accent */}
                <div 
                    style={{ 
                        position: "absolute",
                        top: 0,
                        left: 0,
                        width: "4px",
                        height: "100%",
                        background: "linear-gradient(to bottom, var(--accent-blue), transparent)",
                        borderTopLeftRadius: 16,
                        borderBottomLeftRadius: 16,
                    }}
                />
            </div>

            <style jsx>{`
                .editor-container:focus-within {
                    border-color: var(--accent-blue);
                    box-shadow: 0 0 20px rgba(59, 130, 246, 0.15);
                }
            `}</style>
        </div>
    );
}
