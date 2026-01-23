/**
 * Zustand store for authentication state management
 */

import { create } from "zustand";
import { persist } from "zustand/middleware";

interface AuthStore {
    token: string | null;
    user: any | null;
    setToken: (token: string | null) => void;
    setUser: (user: any | null) => void;
    logout: () => void;
}

export const useAuthStore = create<AuthStore>()(
    persist(
        (set) => ({
            token: localStorage.getItem("auth_token"),
            user: null,
            setToken: (token) => {
                if (token) {
                    localStorage.setItem("auth_token", token);
                } else {
                    localStorage.removeItem("auth_token");
                }
                set({ token });
            },
            setUser: (user) => set({ user }),
            logout: () => {
                localStorage.removeItem("auth_token");
                set({ token: null, user: null });
            },
        }),
        {
            name: "auth-storage",
        }
    )
);
