"use client";
import { ShieldCheck, ShieldX, Trash2 } from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import { api, errMsg } from "@/lib/api";
import { t } from "@/lib/i18n";
import { Button, Card, Empty, ErrorBox, PageTitle, Spinner, inputCls } from "@/components/ui";
import { useSession } from "@/components/Session";

type Contact = { contact_id: string; name: string; relationship_label: string; locked: boolean };
type Verdict = { status: string; message: string; caveat: string; next_steps?: string[]; guardians_alerted?: number };

function VerifyBox({ c, onChanged }: { c: Contact; onChanged: () => void }) {
  const [phrase, setPhrase] = useState(""); const [busy, setBusy] = useState(false); const [err, setErr] = useState(""); const [v, setV] = useState<Verdict | null>(null);
  async function go() {
    setErr(""); setV(null); setBusy(true);
    try { setV(await api<Verdict>(`/family/contacts/${c.contact_id}/verify`, { method: "POST", body: { phrase, notify_guardians: true } })); setPhrase(""); onChanged(); }
    catch (e) { setErr(errMsg(e)); onChanged(); } finally { setBusy(false); }
  }
  return (
    <div className="mt-3 border-t border-ink-700 pt-3">
      <label className="text-sm" htmlFor={`p-${c.contact_id}`}>What phrase did the caller say?</label>
      <div className="mt-1 flex gap-2">
        <input id={`p-${c.contact_id}`} type="password" autoComplete="off" className={inputCls} value={phrase} onChange={(e) => setPhrase(e.target.value)} placeholder="Type exactly what the caller said" maxLength={80} />
        <Button onClick={go} loading={busy} disabled={!phrase.trim() || c.locked}>Check</Button>
      </div>
      {c.locked && <p className="mt-2 text-sm text-amber">Too many wrong tries. Locked for 15 minutes. Call {c.name} directly.</p>}
      {err && <div className="mt-2"><ErrorBox message={err} /></div>}
      {v && (v.status === "VERIFIED" ? (
        <div className="mt-3 rounded-lg border border-safe/50 bg-safe-soft p-3"><p className="flex items-center gap-2 font-display text-xl font-bold text-safe"><ShieldCheck className="h-5 w-5" aria-hidden /> VERIFIED</p><p className="mt-1 text-sm">{v.message}</p><p className="mt-1 text-xs text-mist-300">{v.caveat}</p></div>
      ) : (
        <div className="mt-3 rounded-lg border-2 border-alarm/60 bg-alarm-soft p-3"><p className="flex items-center gap-2 font-display text-xl font-bold text-alarm"><ShieldX className="h-5 w-5" aria-hidden /> VERIFICATION FAILED</p>
          <p className="mt-1 text-sm">{v.message} Treat this call as a scam.</p>
          <ul className="mt-2 list-disc space-y-1 pl-5 text-sm">{v.next_steps?.map((s) => <li key={s}>{s}</li>)}</ul>
          {!!v.guardians_alerted && <p className="mt-2 text-xs text-amber">Your guardians were alerted. The safe word is never shared.</p>}</div>
      ))}
    </div>
  );
}

export default function SafeWord() {
  const { lang } = useSession();
  const [list, setList] = useState<Contact[] | null>(null); const [err, setErr] = useState("");
  const [f, setF] = useState({ name: "", rel: "", phrase: "" }); const [busy, setBusy] = useState(false); const [open, setOpen] = useState<string | null>(null);
  const load = useCallback(() => { api<Contact[]>("/family/contacts").then(setList).catch((e) => setErr(errMsg(e))); }, []);
  useEffect(load, [load]);

  async function add(e: React.FormEvent) {
    e.preventDefault(); setErr(""); setBusy(true);
    try { await api("/family/contacts", { method: "POST", body: { name: f.name, relationship_label: f.rel || "family", phrase: f.phrase } }); setF({ name: "", rel: "", phrase: "" }); load(); }
    catch (x) { setErr(errMsg(x)); } finally { setBusy(false); }
  }
  async function del(id: string) { try { await api(`/family/contacts/${id}`, { method: "DELETE" }); load(); } catch (x) { setErr(errMsg(x)); } }

  return (
    <>
      <PageTitle title={t("safeword", lang)} sub="Agree a secret phrase with each family member in person. If someone calls in an emergency, ask for it." />
      <Card>
        <h2 className="mb-3 font-display text-lg font-semibold">Add a family member</h2>
        <form onSubmit={add} className="grid gap-3 sm:grid-cols-3">
          <label className="text-sm">Name<input className={`${inputCls} mt-1`} required maxLength={120} value={f.name} onChange={(e) => setF({ ...f, name: e.target.value })} /></label>
          <label className="text-sm">Relation<input className={`${inputCls} mt-1`} maxLength={60} placeholder="son, daughter…" value={f.rel} onChange={(e) => setF({ ...f, rel: e.target.value })} /></label>
          <label className="text-sm">Secret phrase<input className={`${inputCls} mt-1`} type="password" autoComplete="off" required minLength={4} maxLength={80} value={f.phrase} onChange={(e) => setF({ ...f, phrase: e.target.value })} /></label>
          <div className="sm:col-span-3"><Button type="submit" loading={busy}>Save family member</Button>
            <p className="mt-2 text-xs text-mist-500">Use a few unrelated words, like a made-up phrase, not a birthday or pet name. We store only a salted hash, never the phrase. A safe word is one extra check, not proof of identity.</p></div>
        </form>
      </Card>
      {err && <div className="mt-4"><ErrorBox message={err} /></div>}
      <div className="mt-5 space-y-3">
        {!list ? <Spinner /> : list.length === 0 ? <Empty title="No family members yet" hint="Add one above, then tell them the phrase in person." /> : list.map((c) => (
          <Card key={c.contact_id}>
            <div className="flex items-center gap-3">
              <div className="min-w-0 flex-1"><p className="font-semibold">{c.name}</p><p className="text-xs text-mist-500">{c.relationship_label}</p></div>
              <Button variant="ghost" onClick={() => setOpen(open === c.contact_id ? null : c.contact_id)}>{open === c.contact_id ? "Close" : "Verify a caller"}</Button>
              <button aria-label={`Remove ${c.name}`} onClick={() => del(c.contact_id)} className="rounded-lg p-2 text-mist-500 hover:bg-ink-700 hover:text-alarm"><Trash2 className="h-4 w-4" aria-hidden /></button>
            </div>
            {open === c.contact_id && <VerifyBox c={c} onChanged={load} />}
          </Card>
        ))}
      </div>
    </>
  );
}
