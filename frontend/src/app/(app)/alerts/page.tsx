"use client";
import { Bell, Trash2, UserPlus } from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import { api, errMsg } from "@/lib/api";
import { t } from "@/lib/i18n";
import { Button, Card, Empty, ErrorBox, PageTitle, Spinner, inputCls } from "@/components/ui";
import { useSession } from "@/components/Session";

type Alert = { alert_id: string; case_id: string; incident_type: string; risk_score: number; summary: string; status: string; delivery: string; created_at: string; guardian_name?: string };
type Guardian = { guardian_id: string; name: string; email: string; linked_account: boolean };
const when = (s: string) => new Date(s + "Z").toLocaleString();

export default function AlertsPage() {
  const { lang } = useSession();
  const [recv, setRecv] = useState<Alert[] | null>(null); const [sent, setSent] = useState<Alert[] | null>(null); const [gs, setGs] = useState<Guardian[] | null>(null);
  const [err, setErr] = useState(""); const [f, setF] = useState({ name: "", email: "" }); const [busy, setBusy] = useState(false);
  const load = useCallback(() => {
    Promise.all([api<Alert[]>("/alerts"), api<Alert[]>("/alerts/sent"), api<Guardian[]>("/guardians")])
      .then(([a, b, c]) => { setRecv(a); setSent(b); setGs(c); }).catch((e) => setErr(errMsg(e)));
  }, []);
  useEffect(load, [load]);

  async function addG(e: React.FormEvent) {
    e.preventDefault(); setErr(""); setBusy(true);
    try { await api("/guardians", { method: "POST", body: f }); setF({ name: "", email: "" }); load(); } catch (x) { setErr(errMsg(x)); } finally { setBusy(false); }
  }
  async function act(p: () => Promise<unknown>) { try { await p(); load(); } catch (x) { setErr(errMsg(x)); } }

  return (
    <>
      <PageTitle title={t("alerts", lang)} sub="Guardians are people you trust. They get an in-app alert when something looks high risk, with the case number and reason." />
      {err && <div className="mb-4"><ErrorBox message={err} /></div>}
      <Card>
        <h2 className="mb-3 font-display text-lg font-semibold">Your guardians</h2>
        <form onSubmit={addG} className="grid gap-3 sm:grid-cols-[1fr_1fr_auto] sm:items-end">
          <label className="text-sm">Name<input className={`${inputCls} mt-1`} required maxLength={120} value={f.name} onChange={(e) => setF({ ...f, name: e.target.value })} /></label>
          <label className="text-sm">Their Kavach email<input type="email" className={`${inputCls} mt-1`} required value={f.email} onChange={(e) => setF({ ...f, email: e.target.value })} /></label>
          <Button type="submit" loading={busy}><UserPlus className="h-4 w-4" aria-hidden /> Add guardian</Button>
        </form>
        <ul className="mt-4 divide-y divide-ink-700">
          {gs?.map((g) => (
            <li key={g.guardian_id} className="flex items-center gap-3 py-2.5 text-sm">
              <div className="min-w-0 flex-1"><p className="font-medium">{g.name}</p><p className="truncate text-xs text-mist-500">{g.email} · {g.linked_account ? "has a Kavach account and will see alerts" : "no Kavach account yet; alerts appear once they register with this email"}</p></div>
              <button aria-label={`Remove ${g.name}`} onClick={() => act(() => api(`/guardians/${g.guardian_id}`, { method: "DELETE" }))} className="rounded-lg p-2 text-mist-500 hover:bg-ink-700 hover:text-alarm"><Trash2 className="h-4 w-4" aria-hidden /></button>
            </li>
          ))}
        </ul>
        {gs && gs.length === 0 && <p className="mt-3 text-sm text-mist-500">No guardians yet. Add someone so high-risk cases are not faced alone.</p>}
      </Card>

      <Card className="mt-4">
        <h2 className="mb-3 font-display text-lg font-semibold">Alerts for people you protect</h2>
        {!recv ? <Spinner /> : recv.length === 0 ? <Empty title="No alerts" hint="When someone who named you as a guardian hits a high-risk case, it shows up here." /> : (
          <ul className="space-y-2">
            {recv.map((a) => (
              <li key={a.alert_id} className={`rounded-lg border p-3 text-sm ${a.status === "unread" ? "border-amber/50 bg-amber-soft" : "border-ink-700"}`}>
                <div className="flex items-start gap-3"><Bell className="mt-0.5 h-4 w-4 shrink-0 text-amber" aria-hidden />
                  <div className="min-w-0 flex-1"><p>{a.summary}</p><p className="mt-1 text-xs text-mist-500">{a.case_id} · {a.incident_type} · risk {a.risk_score} · {when(a.created_at)}</p></div>
                  {a.status === "unread" && <Button variant="ghost" onClick={() => act(() => api(`/alerts/${a.alert_id}/read`, { method: "POST" }))}>Mark read</Button>}
                </div>
              </li>
            ))}
          </ul>
        )}
      </Card>

      <Card className="mt-4">
        <h2 className="mb-3 font-display text-lg font-semibold">Alerts sent about you</h2>
        {!sent ? <Spinner /> : sent.length === 0 ? <Empty title="Nothing sent" hint="High-risk checks automatically alert your guardians." /> : (
          <ul className="divide-y divide-ink-700">{sent.map((a) => <li key={a.alert_id} className="py-2.5 text-sm"><p>To {a.guardian_name}: case {a.case_id}, risk {a.risk_score}</p><p className="text-xs text-mist-500">{when(a.created_at)} · delivered in-app only</p></li>)}</ul>
        )}
      </Card>
    </>
  );
}
