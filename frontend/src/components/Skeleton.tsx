import React from "react";

interface SkeletonProps {
    width?: string | number;
    height?: string | number;
    borderRadius?: string | number;
    className?: string;
    style?: React.CSSProperties;
}

export const Skeleton: React.FC<SkeletonProps> = ({
    width = "100%",
    height = "20px",
    borderRadius = "8px",
    className = "",
    style = {},
}) => {
    return (
        <div
            className={`skeleton ${className}`}
            style={{
                width,
                height,
                borderRadius,
                ...style,
            }}
        />
    );
};

export const CardSkeleton: React.FC = () => {
    return (
        <div className="glass-card" style={{ padding: "24px", minHeight: "200px" }}>
            <div style={{ display: "flex", alignItems: "center", gap: "12px", marginBottom: "20px" }}>
                <Skeleton width={40} height={40} borderRadius="50%" />
                <div style={{ flex: 1 }}>
                    <Skeleton width="60%" height={16} style={{ marginBottom: "8px" }} />
                    <Skeleton width="40%" height={12} />
                </div>
            </div>
            <Skeleton width="100%" height={100} style={{ marginBottom: "16px" }} />
            <div style={{ display: "flex", gap: "8px" }}>
                <Skeleton width={80} height={32} />
                <Skeleton width={80} height={32} />
            </div>
        </div>
    );
};
