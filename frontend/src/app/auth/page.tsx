"use client";
import { ShieldCheck } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Suspense, useState } from "react";
import { api, errMsg, setToken, type Lang, type User } from "@/lib/api";
import { LANGS } from "@/lib/i18n";
import { Button, ErrorBox, inputCls } from "@/components/ui";

function AuthForm() {
  const router = useRouter();
  const [mode, setMode] = useState<"login" | "register">(
    typeof window !== "undefined" && new URLSearchParams(window.location.search).get("mode") === "register" ? "register" : "login");
  const [f, setF] = useState({ name: "", email: "", password: "", lang: "en" as Lang });
  const [err, setErr] = useState(""); const [busy, setBusy] = useState(false);

  async function submit(e: React.FormEvent) {
    e.preventDefault(); setErr(""); setBusy(true);
    try {
      const body = mode === "register" ? { name: f.name, email: f.email, password: f.password, preferred_language: f.lang } : { email: f.email, password: f.password };
      const r = await api<{ token: string; user: User }>(`/auth/${mode}`, { method: "POST", body });
      setToken(r.token); router.replace("/dashboard");
    } catch (x) { setErr(errMsg(x)); } finally { setBusy(false); }
  }
  return (
    <form onSubmit={submit} className="w-full max-w-sm space-y-4 rounded-2xl border border-ink-700 bg-ink-900 p-6">
      <div className="flex rounded-lg bg-ink-950 p-1" role="tablist">
        {(["login", "register"] as const).map((m) => (
          <button type="button" role="tab" aria-selected={mode === m} key={m} onClick={() => { setMode(m); setErr(""); }}
            className={`flex-1 rounded-md py-2 text-sm font-semibold ${mode === m ? "bg-ink-700 text-cyan" : "text-mist-500"}`}>
            {m === "login" ? "Sign in" : "Create account"}
          </button>
        ))}
      </div>
      {mode === "register" && (
        <label className="block text-sm">Your name
          <input className={`${inputCls} mt-1`} required maxLength={120} value={f.name} onChange={(e) => setF({ ...f, name: e.target.value })} autoComplete="name" />
        </label>
      )}
      <label className="block text-sm">Email
        <input className={`${inputCls} mt-1`} type="email" required value={f.email} onChange={(e) => setF({ ...f, email: e.target.value })} autoComplete="email" />
      </label>
      <label className="block text-sm">Password {mode === "register" && <span className="text-mist-500">(8 or more characters)</span>}
        <input className={`${inputCls} mt-1`} type="password" required minLength={mode === "register" ? 8 : 1} value={f.password}
          onChange={(e) => setF({ ...f, password: e.target.value })} autoComplete={mode === "login" ? "current-password" : "new-password"} />
      </label>
      {mode === "register" && (
        <label className="block text-sm">Language for warnings
          <select className={`${inputCls} mt-1`} value={f.lang} onChange={(e) => setF({ ...f, lang: e.target.value as Lang })}>
            {LANGS.map((l) => <option key={l.code} value={l.code}>{l.label}</option>)}
          </select>
        </label>
      )}
      {err && <ErrorBox message={err} />}
      <Button type="submit" loading={busy} className="w-full">{mode === "login" ? "Sign in" : "Create account"}</Button>
      <p className="text-xs text-mist-500">Kavach never asks for your UPI PIN, OTP or bank password.</p>
    </form>
  );
}

export default function AuthPage() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center gap-6 px-4">
      <Link href="/" className="flex items-center gap-2 font-display text-2xl font-bold"><ShieldCheck className="h-7 w-7 text-cyan" aria-hidden /> Kavach</Link>
      <Suspense><AuthForm /></Suspense>
    </div>
  );
}
