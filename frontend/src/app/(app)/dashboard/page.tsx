"use client";
import { ArrowRight, Bell, PhoneCall, ScanSearch, Wallet } from "lucide-react";
import Link from "next/link";
import { useEffect, useState } from "react";
import { api, errMsg, type CaseRow } from "@/lib/api";
import { t } from "@/lib/i18n";
import { Card, Empty, ErrorBox, LevelPill, PageTitle, Spinner, levelStyle } from "@/components/ui";
import { useSession } from "@/components/Session";

type Stats = { total_scans: number; high_risk: number; safe: number; distribution: Record<string, number>; unread_alerts: number; recent: CaseRow[] };

export default function Dashboard() {
  const { user, lang } = useSession();
  const [s, setS] = useState<Stats | null>(null); const [err, setErr] = useState("");
  useEffect(() => { api<Stats>("/dashboard/stats").then(setS).catch((e) => setErr(errMsg(e))); }, []);
  if (err) return <ErrorBox message={err} />;
  if (!s) return <Spinner />;
  const total = Math.max(1, s.total_scans);
  const tiles = [
    { label: "Total checks", v: s.total_scans, c: "text-mist-100" },
    { label: "High risk found", v: s.high_risk, c: "text-alarm" },
    { label: "Looked safe", v: s.safe, c: "text-safe" },
    { label: "Unread guardian alerts", v: s.unread_alerts, c: "text-amber" },
  ];
  return (
    <>
      <PageTitle title={`${t("dashboard", lang)}`} sub={`Welcome, ${user.name}. Paste a message or upload a screenshot whenever something feels wrong.`} />
      <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
        {tiles.map((x) => (
          <Card key={x.label} className="!p-4">
            <p className={`font-display text-4xl font-bold tabular-nums ${x.c}`}>{x.v}</p>
            <p className="mt-1 text-xs text-mist-300">{x.label}</p>
          </Card>
        ))}
      </div>

      <div className="mt-4 grid gap-4 md:grid-cols-3">
        <Card className="md:col-span-2">
          <h2 className="mb-3 font-display text-lg font-semibold">Quick checks</h2>
          <div className="grid gap-2 sm:grid-cols-3">
            {[{ h: "/upi", l: "Check a UPI request", I: Wallet }, { h: "/call", l: "Check a call", I: PhoneCall }, { h: "/investigate", l: "Investigate a link", I: ScanSearch }].map(({ h, l, I }) => (
              <Link key={h} href={h} className="flex items-center justify-between gap-2 rounded-lg border border-ink-600 p-3 text-sm font-medium hover:bg-ink-700">
                <span className="flex items-center gap-2"><I className="h-4 w-4 text-cyan" aria-hidden /> {l}</span><ArrowRight className="h-4 w-4 text-mist-500" aria-hidden />
              </Link>
            ))}
          </div>
        </Card>
        <Card>
          <h2 className="mb-3 font-display text-lg font-semibold">Risk mix</h2>
          {s.total_scans === 0 ? <p className="text-sm text-mist-500">No checks yet.</p> : (
            <div className="space-y-2.5">
              {(["HIGH RISK", "SUSPICIOUS", "SAFE"] as const).map((k) => (
                <div key={k} className="text-xs">
                  <div className="mb-1 flex justify-between text-mist-300"><span>{k}</span><span>{s.distribution[k] ?? 0}</span></div>
                  <div className="h-2 rounded bg-ink-800"><div className={`h-2 rounded ${levelStyle(k).solid}`} style={{ width: `${((s.distribution[k] ?? 0) / total) * 100}%` }} /></div>
                </div>
              ))}
            </div>
          )}
        </Card>
      </div>

      <Card className="mt-4">
        <div className="mb-3 flex items-center justify-between">
          <h2 className="font-display text-lg font-semibold">Recent checks</h2>
          <Link href="/history" className="text-sm text-cyan hover:underline">See all</Link>
        </div>
        {s.recent.length === 0 ? <Empty title="Nothing checked yet" hint="Start with a UPI request or a call transcript. Each sample button fills in a realistic example." /> : (
          <ul className="divide-y divide-ink-700">
            {s.recent.map((c) => (
              <li key={c.case_id} className="flex items-center gap-3 py-3">
                <LevelPill level={c.risk_level} />
                <div className="min-w-0 flex-1"><p className="truncate text-sm">{c.summary}</p><p className="text-xs text-mist-500">{c.case_id} · {c.input_type} · {new Date(c.created_at + "Z").toLocaleString()}</p></div>
                <span className="font-display text-lg tabular-nums">{c.risk_score}</span>
              </li>
            ))}
          </ul>
        )}
      </Card>
      {s.unread_alerts > 0 && (
        <Link href="/alerts" className="mt-4 flex items-center gap-2 rounded-lg border border-amber/40 bg-amber-soft p-3 text-sm text-amber"><Bell className="h-4 w-4" aria-hidden /> You have {s.unread_alerts} unread alert{s.unread_alerts > 1 ? "s" : ""} from people you protect.</Link>
      )}
    </>
  );
}
