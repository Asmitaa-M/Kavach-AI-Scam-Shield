"use client";
import { createContext, useContext } from "react";
import type { Lang, User } from "@/lib/api";

type Ctx = { user: User; lang: Lang; setUser: (u: User) => void; signOut: () => void };
export const SessionCtx = createContext<Ctx | null>(null);
export function useSession() {
  const c = useContext(SessionCtx);
  if (!c) throw new Error("useSession outside provider");
  return c;
}
