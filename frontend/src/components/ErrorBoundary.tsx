import React, { Component, ErrorInfo, ReactNode } from "react";

interface Props {
  children?: ReactNode;
}

interface State {
  hasError: boolean;
  error?: Error;
}

export class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false
  };

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error("Uncaught error:", error, errorInfo);
  }

  public render() {
    if (this.state.hasError) {
      return (
        <div style={{
          display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center",
          minHeight: "100vh", backgroundColor: "#020617", color: "var(--text-primary)", padding: 40
        }}>
          <div className="glass-card" style={{ padding: "40px", maxWidth: 600, width: "100%", textAlign: "center" }}>
            <h2 style={{ color: "var(--accent-rose)", marginBottom: 16 }}>UI Component Crashed</h2>
            <p style={{ color: "var(--text-muted)", marginBottom: 24 }}>
              An unexpected error occurred in the React tree. The application state may be corrupted.
            </p>
            <div style={{ background: "rgba(0,0,0,0.5)", padding: 16, borderRadius: 8, marginBottom: 24, textAlign: "left", overflowX: "auto", fontFamily: "monospace", fontSize: "0.8rem", color: "var(--accent-rose)" }}>
              {this.state.error?.message}
            </div>
            <button
              className="btn-primary"
              onClick={() => window.location.reload()}
            >
              Reload Page
            </button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
