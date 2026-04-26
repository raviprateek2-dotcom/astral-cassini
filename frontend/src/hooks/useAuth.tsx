"use client";

import React, { createContext, useContext, useEffect, useState } from "react";
import { useRouter, usePathname } from "next/navigation";
import { api, type MeResponse } from "@/lib/api";
import { isFrontendDemoMode } from "@/lib/demoMode";

function meResponseFromLocalStorage(): MeResponse | null {
    if (typeof window === "undefined") return null;
    const raw = localStorage.getItem("user");
    if (!raw) return null;
    try {
        const parsed = JSON.parse(raw) as Partial<MeResponse> & { full_name?: string; role?: string; email?: string };
        if (!parsed?.email || !parsed?.role) return null;
        return {
            id: typeof parsed.id === "number" ? parsed.id : Number(parsed.id) || 0,
            email: String(parsed.email),
            full_name: String(parsed.full_name ?? "Demo user"),
            role: String(parsed.role),
            department: parsed.department ?? null,
            is_active: parsed.is_active !== false,
        };
    } catch {
        return null;
    }
}

type AuthContextType = {
    user: MeResponse | null;
    loading: boolean;
    logout: () => void;
};

const AuthContext = createContext<AuthContextType>({
    user: null,
    loading: true,
    logout: () => { },
});

export const useAuth = () => useContext(AuthContext);

export function AuthProvider({ children }: { children: React.ReactNode }) {
    const [user, setUser] = useState<MeResponse | null>(null);
    const [loading, setLoading] = useState(true);
    const router = useRouter();
    const pathname = usePathname();

    useEffect(() => {
        const initializeAuth = async () => {
            if (isFrontendDemoMode()) {
                let fromStore = meResponseFromLocalStorage();
                if (!fromStore) {
                    // Auto-provision a demo user — no login needed at all
                    fromStore = {
                        id: 0,
                        email: "admin@prohr.ai",
                        full_name: "Demo Admin",
                        role: "admin",
                        department: "Engineering",
                        is_active: true,
                    };
                    localStorage.setItem("user", JSON.stringify(fromStore));
                }
                setUser(fromStore);
                setLoading(false);
                return;
            }
            try {
                const me = await api.me();
                setUser(me);
                localStorage.setItem("user", JSON.stringify(me));
            } catch {
                setUser(null);
                localStorage.removeItem("user");
                if (pathname !== "/login" && pathname !== "/") {
                    router.push("/");
                }
            } finally {
                setLoading(false);
            }
        };
        initializeAuth();
    }, [pathname, router]);

    const logout = () => {
        if (!isFrontendDemoMode()) {
            api.logout().catch(() => null);
        }
        localStorage.removeItem("user");
        sessionStorage.removeItem("ws_token");
        setUser(null);
        router.replace("/");
    };

    const isPublicRoute = pathname === "/" || pathname === "/login";
    // Block only while `/me` is in flight — not for `user === null` after failure (redirect must run; shell would deadlock).
    const blockProtectedShell = !isPublicRoute && loading;

    return (
        <AuthContext.Provider value={{ user, loading, logout }}>
            {blockProtectedShell ? (
                <div
                    role="status"
                    aria-busy="true"
                    aria-label="Loading session"
                    style={{
                        position: "fixed",
                        inset: 0,
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "center",
                        background: "rgba(15, 23, 42, 0.92)",
                        color: "rgba(226, 232, 240, 0.85)",
                        fontSize: "0.95rem",
                        zIndex: 50,
                    }}
                >
                    Loading session…
                </div>
            ) : (
                children
            )}
        </AuthContext.Provider>
    );
}
