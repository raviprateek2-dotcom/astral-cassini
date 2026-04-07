import React from 'react';

interface SkeletonProps {
    width?: string | number;
    height?: string | number;
    borderRadius?: string | number;
    style?: React.CSSProperties;
    className?: string;
}

export function Skeleton({ width = "100%", height = "100%", borderRadius = "8px", style, className = "" }: SkeletonProps) {
    return (
        <div 
            className={`skeleton ${className}`}
            style={{
                width: typeof width === 'number' ? `${width}px` : width,
                height: typeof height === 'number' ? `${height}px` : height,
                borderRadius: typeof borderRadius === 'number' ? `${borderRadius}px` : borderRadius,
                ...style
            }}
        />
    );
}

export function CardSkeleton() {
    return (
        <div className="glass-card" style={{ padding: "24px", minHeight: "200px", display: "flex", flexDirection: "column", gap: "16px" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                <Skeleton width="60%" height="24px" />
                <Skeleton width="15%" height="20px" borderRadius="10px" />
            </div>
            <Skeleton width="40%" height="14px" />
            <div style={{ flex: 1, display: "flex", alignItems: "flex-end", gap: "16px" }}>
                <Skeleton width="45%" height="30px" />
                <Skeleton width="45%" height="30px" />
            </div>
        </div>
    );
}

export function TableSkeleton({ rows = 5 }: { rows?: number }) {
    return (
        <div className="glass-card" style={{ padding: "24px" }}>
            <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "24px" }}>
                <Skeleton width="200px" height="28px" />
                <Skeleton width="250px" height="40px" />
            </div>
            <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
                <Skeleton width="100%" height="40px" />
                {Array.from({ length: rows }).map((_, i) => (
                    <Skeleton key={i} width="100%" height="60px" />
                ))}
            </div>
        </div>
    );
}
