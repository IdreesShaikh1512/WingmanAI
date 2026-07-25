"use client";

import { create } from "zustand";
import { persist, createJSONStorage } from "zustand/middleware";
import { CurrentUser } from "@/lib/api";

type AuthState = {
  token: string | null;
  user: CurrentUser | null;
  setSession: (token: string, user: CurrentUser) => void;
  clearSession: () => void;
};

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      token: null,
      user: null,
      setSession: (token, user) => set({ token, user }),
      clearSession: () => set({ token: null, user: null }),
    }),
    {
      name: "wingman-auth",
      storage: createJSONStorage(() => localStorage),
    },
  ),
);
