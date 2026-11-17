"use client";
import { Printer } from "lucide-react";
import { useEffect, useState } from "react";
import { api, errMsg, type CaseDetail, type CaseRow, type Level } from "@/lib/api";
import { t } from "@/lib/i18n";
import { Button, Card, Empty, ErrorBox, LevelPill, PageTitle, Spinner } from "@/components/ui";
import { useSession } from "@/components/Session";

export default function History() {
  const { lang } = useSession();
  const [rows, setRows] = useState<CaseRow[] | null>(null); const [err, setErr] = useState(""); const [filter, setFilter] = useState<"ALL" | Level>("ALL");
  const [open, setOpen] = useState<CaseDetail | null>(null); const [loadingId, setLoadingId] = useState("");
  useEffect(() => { api<CaseRow[]>("/cases?limit=200").then(setRows).catch((e) => setErr(errMsg(e))); }, []);
  async function show(id: string) {
    if (open?.case_id === id) { setOpen(null); return; }
    setLoadingId(id); try { setOpen(await api<CaseDetail>(`/cases/${id}`)); } catch (e) { setErr(errMsg(e)); } finally { setLoadingId(""); }
  }
  const list = rows?.filter((r) => filter === "ALL" || r.risk_level === filter);
  return (
    <>
      <PageTitle title={t("history", lang)} sub="Every check you ran. Open a case to see its evidence report." />
      <div className="mb-4 flex flex-wrap gap-2">
        {(["ALL", "HIGH RISK", "SUSPICIOUS", "SAFE"] as const).map((k) => (
          <button key={k} onClick={() => setFilter(k)} aria-pressed={filter === k} className={`rounded-full border px-3 py-1 text-xs ${filter === k ? "border-cyan bg-cyan-soft text-cyan" : "border-ink-600 text-mist-300 hover:bg-ink-700"}`}>{k === "ALL" ? "All" : k}</button>
        ))}
      </div>
      {err && <ErrorBox message={err} />}
      {!list ? <Spinner /> : list.length === 0 ? <Empty title="No cases to show" hint="Run a UPI, call or investigator check and it will appear here." /> : (
        <ul className="space-y-3">
          {list.map((c) => (
            <li key={c.case_id}>
              <Card className="!p-4">
                <button onClick={() => show(c.case_id)} className="flex w-full items-center gap-3 text-left" aria-expanded={open?.case_id === c.case_id}>
                  <LevelPill level={c.risk_level} />
                  <div className="min-w-0 flex-1"><p className="truncate text-sm">{c.summary}</p><p className="text-xs text-mist-500">{c.case_id} · {c.input_type}{c.is_simulated ? " · demo sample" : ""} · {new Date(c.created_at + "Z").toLocaleString()}</p></div>
                  <span className="font-display text-xl tabular-nums">{loadingId === c.case_id ? "…" : c.risk_score}</span>
                </button>
                {open?.case_id === c.case_id && (
                  <div className="mt-4 border-t border-ink-700 pt-4">
                    <div className="mb-3 flex items-center justify-between"><h2 className="font-display text-lg font-semibold">Threat evidence report · {open.case_id}</h2><Button variant="ghost" onClick={() => window.print()}><Printer className="h-4 w-4" aria-hidden /> Print or save as PDF</Button></div>
                    <p className="mb-2 text-sm text-mist-300">Input as stored (OTPs, phone and account numbers are redacted):</p>
                    <p className="mb-4 whitespace-pre-wrap rounded-lg bg-ink-950 p-3 text-sm text-mist-300">{open.redacted_input}</p>
                    <ul className="space-y-2">
                      {open.evidence.map((e, i) => (
                        <li key={i} className="flex items-start gap-3 text-sm"><span className={`mt-0.5 shrink-0 rounded border px-1.5 py-0.5 text-[11px] ${e.provenance === "verified" ? "border-safe/40 text-safe" : e.provenance === "unavailable" ? "border-ink-600 text-mist-500" : "border-amber/40 text-amber"}`}>{e.provenance === "unavailable" ? "not checked" : e.provenance}</span><span>{e.description} <span className="text-mist-500">({e.source})</span></span></li>
                      ))}
                      {open.evidence.length === 0 && <li className="text-sm text-mist-500">No scam tactics were recorded for this case.</li>}
                    </ul>
                  </div>
                )}
              </Card>
            </li>
          ))}
        </ul>
      )}
    </>
  );
}
