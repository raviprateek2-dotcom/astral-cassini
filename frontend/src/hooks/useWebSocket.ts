/**
 * useWebSocket — React hook for real-time pipeline event subscription.
 */
"use client";

import { useEffect, useRef, useState, useCallback } from "react";

export interface PipelineEvent {
    type: string;
    job_id: string;
    data: Record<string, any>;
}

export function useWebSocket(jobId: string | null) {
    const ws = useRef<WebSocket | null>(null);
    const [connected, setConnected] = useState(false);
    const [events, setEvents] = useState<PipelineEvent[]>([]);
    const [heartbeat, setHeartbeat] = useState<Record<string, any> | null>(null);
    const [tokenStream, setTokenStream] = useState<string>("");

    const addEvent = useCallback((evt: PipelineEvent) => {
        setEvents((prev) => [evt, ...prev].slice(0, 50)); // keep last 50
    }, []);

    useEffect(() => {
        if (!jobId) {
            setTokenStream(""); // reset on job change
            return;
        }

        const socket = new WebSocket(`ws://localhost:8000/ws/${jobId}`);
        ws.current = socket;

        socket.onopen = () => setConnected(true);
        socket.onclose = () => setConnected(false);
        socket.onerror = () => setConnected(false);

        socket.onmessage = (msgEvent) => {
            try {
                const evt: PipelineEvent = JSON.parse(msgEvent.data);
                if (evt.type === "heartbeat") {
                    setHeartbeat(evt.data);
                } else if (evt.type === "stream_token") {
                    setTokenStream((prev) => prev + evt.data.token);
                } else {
                    addEvent(evt);
                }
            } catch { }
        };

        // Ping every 25s to keep connection alive
        const ping = setInterval(() => {
            if (socket.readyState === WebSocket.OPEN) {
                socket.send(JSON.stringify({ type: "ping" }));
            }
        }, 25_000);

        return () => {
            clearInterval(ping);
            socket.close();
        };
    }, [jobId, addEvent]);

    return { connected, events, heartbeat, tokenStream, setTokenStream };
}
