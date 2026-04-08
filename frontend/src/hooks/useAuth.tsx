"use client";

import React, { createContext, useContext, useEffect, useState } from "react";
import { useRouter, usePathname } from "next/navigation";
import { api, type MeResponse } from "@/lib/api";

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
        api.logout().catch(() => null);
        localStorage.removeItem("user");
        sessionStorage.removeItem("ws_token");
        setUser(null);
        router.replace("/");
    };

    return (
        <AuthContext.Provider value={{ user, loading, logout }}>
            {children}
        </AuthContext.Provider>
    );
}
