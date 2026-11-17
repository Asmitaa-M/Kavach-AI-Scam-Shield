"use client";
import { AlertTriangle, Loader2 } from "lucide-react";
import type { ButtonHTMLAttributes, ReactNode } from "react";

export function Button({ variant = "primary", loading, className = "", children, ...p }:
  ButtonHTMLAttributes<HTMLButtonElement> & { variant?: "primary" | "ghost" | "danger"; loading?: boolean }) {
  const v = {
    primary: "bg-cyan text-ink-950 hover:bg-[#7BD8F5]",
    ghost: "border border-ink-600 text-mist-100 hover:bg-ink-700",
    danger: "bg-alarm text-ink-950 hover:bg-[#FF7885]",
  }[variant];
  return (
    <button {...p} disabled={p.disabled || loading}
      className={`inline-flex items-center justify-center gap-2 rounded-lg px-4 py-2.5 text-sm font-semibold transition-colors disabled:cursor-not-allowed disabled:opacity-50 ${v} ${className}`}>
      {loading && <Loader2 className="h-4 w-4 animate-spin" aria-hidden />}
      {children}
    </button>
  );
}

export const Card = ({ children, className = "" }: { children: ReactNode; className?: string }) => (
  <section className={`rounded-xl border border-ink-700 bg-ink-900 p-5 ${className}`}>{children}</section>
);

export const PageTitle = ({ title, sub }: { title: string; sub?: string }) => (
  <header className="mb-6">
    <h1 className="font-display text-2xl font-semibold tracking-tight text-mist-100 sm:text-3xl">{title}</h1>
    {sub && <p className="mt-1 max-w-2xl text-sm text-mist-300">{sub}</p>}
  </header>
);

export const ErrorBox = ({ message }: { message: string }) => (
  <div role="alert" className="flex items-start gap-2 rounded-lg border border-alarm/40 bg-alarm-soft p-3 text-sm text-[#FFB3BB]">
    <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" aria-hidden /> <span>{message}</span>
  </div>
);

export const Empty = ({ title, hint }: { title: string; hint: string }) => (
  <div className="rounded-xl border border-dashed border-ink-600 p-8 text-center">
    <p className="font-medium text-mist-100">{title}</p>
    <p className="mt-1 text-sm text-mist-500">{hint}</p>
  </div>
);

export const Spinner = ({ label = "Loading" }: { label?: string }) => (
  <div className="flex items-center gap-2 py-8 text-sm text-mist-500" role="status">
    <Loader2 className="h-4 w-4 animate-spin" aria-hidden /> {label}…
  </div>
);

export const inputCls =
  "w-full rounded-lg border border-ink-600 bg-ink-950 px-3 py-2.5 text-sm text-mist-100 placeholder:text-mist-500 focus:border-cyan focus:outline-none focus:ring-2 focus:ring-cyan/30";

export const levelStyle = (l: string) =>
  l === "HIGH RISK" ? { text: "text-alarm", bg: "bg-alarm-soft", border: "border-alarm/50", solid: "bg-alarm" }
  : l === "SUSPICIOUS" ? { text: "text-amber", bg: "bg-amber-soft", border: "border-amber/50", solid: "bg-amber" }
  : { text: "text-safe", bg: "bg-safe-soft", border: "border-safe/50", solid: "bg-safe" };

export const LevelPill = ({ level }: { level: string }) => {
  const s = levelStyle(level);
  return <span className={`rounded-full border px-2.5 py-0.5 text-xs font-semibold ${s.text} ${s.bg} ${s.border}`}>{level}</span>;
};
