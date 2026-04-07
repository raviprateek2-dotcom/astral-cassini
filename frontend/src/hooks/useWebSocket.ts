/**
 * useWebSocket — React hook for real-time pipeline event subscription.
 * Integrates with useJobStore to provide global state updates.
 */
"use client";

import { useEffect, useRef, useState, useCallback } from "react";
import { useJobStore } from "@/store/useJobStore";

export interface PipelineEvent {
    type: string;
    job_id: string;
    data: any;
}

export function useWebSocket(jobId: string | null) {
    const ws = useRef<WebSocket | null>(null);
    const [connected, setConnected] = useState(false);
    const [tokenStream, setTokenStream] = useState<string>("");
    
    const updateJobStateFromSocket = useJobStore((state) => state.updateJobStateFromSocket);

    useEffect(() => {
        if (!jobId) {
            setTokenStream(""); 
            return;
        }

        const socket = new WebSocket(`ws://localhost:8000/ws/${jobId}`);
        ws.current = socket;

        socket.onopen = () => {
            setConnected(true);
            console.log(`WebSocket connected for job ${jobId}`);
        };
        
        socket.onclose = () => {
            setConnected(false);
            console.log(`WebSocket disconnected for job ${jobId}`);
        };
        
        socket.onerror = () => setConnected(false);

        socket.onmessage = (msgEvent) => {
            try {
                const evt: PipelineEvent = JSON.parse(msgEvent.data);
                
                if (evt.type === "heartbeat") {
                    // Update global store with latest job state
                    updateJobStateFromSocket(evt.data);
                } else if (evt.type === "stream_token") {
                    setTokenStream((prev) => prev + evt.data.token);
                } else {
                    // Other events like audit logs etc could be handled here if needed
                    // updateJobStateFromSocket handles the main state merge
                }
            } catch (err) {
                console.error("WS Message Error:", err);
            }
        };

        const ping = setInterval(() => {
            if (socket.readyState === WebSocket.OPEN) {
                socket.send(JSON.stringify({ type: "ping" }));
            }
        }, 25_000);

        return () => {
            clearInterval(ping);
            socket.close();
        };
    }, [jobId, updateJobStateFromSocket]);

    return { connected, tokenStream, setTokenStream };
}
