/**
 * useWebSocket — React hook for real-time pipeline event subscription.
 * Integrates with useJobStore to provide global state updates.
 */
"use client";

import { useEffect, useRef, useState } from "react";
import { useJobStore } from "@/store/useJobStore";
import { api, type PipelineEvent } from "@/lib/api";

type HeartbeatData = {
    current_stage?: string;
    state?: Record<string, unknown>;
    candidates?: number;
    scored?: number;
    interviews?: number;
};

const WS_PING_MS = 25_000;
const WS_BACKOFF_START_MS = 1_000;
const WS_BACKOFF_MAX_MS = 30_000;

export function useWebSocket(jobId: string | null) {
    const ws = useRef<WebSocket | null>(null);
    const [connected, setConnected] = useState(false);
    const [tokenStream, setTokenStream] = useState<string>("");
    const [events, setEvents] = useState<PipelineEvent[]>([]);
    const [heartbeat, setHeartbeat] = useState<HeartbeatData | null>(null);

    const updateJobStateFromSocket = useJobStore((state) => state.updateJobStateFromSocket);

    useEffect(() => {
        if (!jobId) {
            setTokenStream("");
            setConnected(false);
            setEvents([]);
            setHeartbeat(null);
            return;
        }

        const wsBase = process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:8000";
        let socket: WebSocket | null = null;
        let pingInterval: ReturnType<typeof setInterval> | null = null;
        let reconnectTimer: ReturnType<typeof setTimeout> | null = null;
        let backoffMs = WS_BACKOFF_START_MS;
        let stopped = false;

        const clearPing = () => {
            if (pingInterval !== null) {
                clearInterval(pingInterval);
                pingInterval = null;
            }
        };

        const attachHandlers = (s: WebSocket) => {
            s.onmessage = (msgEvent) => {
                try {
                    const evt: PipelineEvent = JSON.parse(msgEvent.data);

                    if (evt.type === "heartbeat" || evt.type === "pipeline_update") {
                        const d = evt.data as HeartbeatData;
                        setHeartbeat(d);
                        updateJobStateFromSocket({
                            current_stage: d.current_stage,
                            state: d.state,
                        });
                    } else if (evt.type === "stream_token") {
                        const piece = typeof evt.data.token === "string" ? evt.data.token : "";
                        setTokenStream((prev) => prev + piece);
                    }
                    setEvents((prev) => [evt, ...prev].slice(0, 50));
                } catch (err) {
                    console.error("WS Message Error:", err);
                }
            };

            s.onopen = () => {
                backoffMs = WS_BACKOFF_START_MS;
                setConnected(true);
                clearPing();
                pingInterval = setInterval(() => {
                    if (socket?.readyState === WebSocket.OPEN) {
                        socket.send(JSON.stringify({ type: "ping" }));
                    }
                }, WS_PING_MS);
            };

            s.onerror = () => setConnected(false);

            s.onclose = () => {
                setConnected(false);
                clearPing();
                ws.current = null;
                if (stopped) return;
                reconnectTimer = setTimeout(() => {
                    reconnectTimer = null;
                    backoffMs = Math.min(backoffMs * 2, WS_BACKOFF_MAX_MS);
                    void openSocket();
                }, backoffMs);
            };
        };

        const openSocket = async () => {
            if (stopped) return;
            let ticket: string;
            try {
                ({ ticket } = await api.getWsTicket(jobId));
            } catch {
                setConnected(false);
                if (!stopped) {
                    reconnectTimer = setTimeout(() => {
                        reconnectTimer = null;
                        backoffMs = Math.min(backoffMs * 2, WS_BACKOFF_MAX_MS);
                        void openSocket();
                    }, backoffMs);
                }
                return;
            }
            if (stopped) return;
            socket = new WebSocket(`${wsBase}/ws/${jobId}?token=${encodeURIComponent(ticket)}`);
            ws.current = socket;
            attachHandlers(socket);
        };

        void openSocket();

        return () => {
            stopped = true;
            if (reconnectTimer !== null) clearTimeout(reconnectTimer);
            clearPing();
            socket?.close();
            ws.current = null;
        };
    }, [jobId, updateJobStateFromSocket]);

    return { connected, tokenStream, setTokenStream, events, heartbeat };
}
