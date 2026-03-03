"use client";

import React, { createContext, useContext, useEffect, useState } from "react";
import { useRouter, usePathname } from "next/navigation";
import { api } from "@/lib/api";

type User = {
    id: number;
    email: string;
    full_name: string;
    role: string;
};

type AuthContextType = {
    user: User | null;
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
    const [user, setUser] = useState<User | null>(null);
    const [loading, setLoading] = useState(true);
    const router = useRouter();
    const pathname = usePathname();

    useEffect(() => {
        // Check for token on mount
        const token = typeof window !== "undefined" ? localStorage.getItem("token") : null;
        const storedUser = typeof window !== "undefined" ? localStorage.getItem("user") : null;

        if (token && storedUser) {
            api.setToken(token);
            setUser(JSON.parse(storedUser));
        } else if (pathname !== "/login" && pathname !== "/") {
            router.push("/login");
        }

        setLoading(false);
    }, [pathname, router]);

    const logout = () => {
        localStorage.removeItem("token");
        localStorage.removeItem("user");
        api.setToken("");
        setUser(null);
        router.push("/login");
    };

    return (
        <AuthContext.Provider value={{ user, loading, logout }}>
            {children}
        </AuthContext.Provider>
    );
}
