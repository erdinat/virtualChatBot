import { create } from "zustand";
import { persist } from "zustand/middleware";

interface AuthState {
  token:    string | null;
  username: string | null;
  name:     string | null;
  role:     "student" | "teacher" | null;
  setAuth:  (token: string, username: string, name: string, role: string) => void;
  logout:   () => void;
  isAuth:   () => boolean;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      token:    null,
      username: null,
      name:     null,
      role:     null,

      setAuth: (token, username, name, role) => {
        localStorage.setItem("access_token", token);
        set({ token, username, name, role: role as "student" | "teacher" });
      },

      logout: () => {
        localStorage.removeItem("access_token");
        set({ token: null, username: null, name: null, role: null });
      },

      isAuth: () => !!get().token,
    }),
    { name: "sta-auth" }
  )
);
