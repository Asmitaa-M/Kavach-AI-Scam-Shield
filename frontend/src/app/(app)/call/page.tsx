"use client";
import { FileAudio } from "lucide-react";
import Link from "next/link";
import { useState } from "react";
import { api, errMsg, type Analysis } from "@/lib/api";
import { t } from "@/lib/i18n";
import { Button, Card, ErrorBox, PageTitle, inputCls } from "@/components/ui";
import RiskResult from "@/components/RiskResult";
import { useSession } from "@/components/Session";

const SAMPLES = [
  { name: "Family emergency (English)", text: "Papa, I am in trouble. I had an accident and the police are here. Send Rs 50,000 right now on this number. Please don't tell mom." },
  { name: "Tanglish", text: "Amma naan unga magan, accident aayiduchu. udane 20000 panam anuppunga, yaarkittayum sollathe." },
  { name: "Tamil", text: "உங்கள் மகன் விபத்தில் சிக்கியுள்ளார். உடனே பணம் அனுப்புங்கள். யாரிடமும் சொல்லாதே." },
  { name: "Fake bank officer", text: "I am calling from SBI KYC department. Your account will be blocked today. Share the OTP you just received to avoid this." },
  { name: "Normal family call", text: "Mom I reached home safely. Will call you after dinner. Please keep some food for me." },
];

export default function CallPage() {
  const { lang } = useSession();
  const [text, setText] = useState(""); const [sample, setSample] = useState(false);
  const [busy, setBusy] = useState(false); const [err, setErr] = useState(""); const [res, setRes] = useState<Analysis | null>(null);
  const [audioMsg, setAudioMsg] = useState("");

  async function run() {
    setErr(""); setRes(null); setBusy(true);
    try { setRes(await api<Analysis>("/analyze/call", { method: "POST", body: { text, is_demo_sample: sample } })); }
    catch (e) { setErr(errMsg(e)); } finally { setBusy(false); }
  }
  async function upload(f: File | null) {
    if (!f) return; setAudioMsg("");
    const form = new FormData(); form.append("file", f);
    try { await api("/analyze/call/audio", { method: "POST", form }); } catch (e) { setAudioMsg(errMsg(e)); }
  }
  return (
    <>
      <PageTitle title={t("call", lang)} sub="Paste what the caller said. Kavach checks the words for scam tactics. It cannot tell whether a voice is cloned." />
      <Card>
        <label className="text-sm" htmlFor="call-text">Call transcript (English, Tamil or mixed)</label>
        <textarea id="call-text" rows={6} className={`${inputCls} mt-1`} maxLength={6000} value={text} onChange={(e) => { setText(e.target.value); setSample(false); }} placeholder="Type or paste what was said on the call" />
        <div className="mt-3 flex flex-wrap gap-2">
          {SAMPLES.map((s) => <button key={s.name} onClick={() => { setText(s.text); setSample(true); }} className="rounded-full border border-ink-600 px-3 py-1 text-xs text-mist-300 hover:bg-ink-700">Sample: {s.name}</button>)}
        </div>
        <div className="mt-4 flex flex-wrap items-center gap-3">
          <Button onClick={run} loading={busy} disabled={text.trim().length < 3}>{t("analyze", lang)}</Button>
          <label className="inline-flex cursor-pointer items-center gap-2 rounded-lg border border-ink-600 px-4 py-2.5 text-sm font-semibold hover:bg-ink-700">
            <FileAudio className="h-4 w-4" aria-hidden /> Upload a recording
            <input type="file" accept="audio/*" className="sr-only" onChange={(e) => { upload(e.target.files?.[0] ?? null); e.target.value = ""; }} />
          </label>
        </div>
        {audioMsg && <div className="mt-3"><ErrorBox message={audioMsg} /></div>}
      </Card>
      {err && <div className="mt-4"><ErrorBox message={err} /></div>}
      {res && (
        <div className="mt-5 space-y-4">
          <RiskResult caseId={res.case_id} score={res.score} level={res.level} indicators={res.indicators} notes={res.notes}
            recommendations={res.recommendations} guardiansAlerted={res.guardians_alerted} disclaimer={res.disclaimer} />
          {res.level !== "SAFE" && (
            <Card>
              <h2 className="font-display text-lg font-semibold">Is it really your family member?</h2>
              <p className="mt-1 text-sm text-mist-300">Ask the caller for your family safe word. If they cannot say it, hang up and call back on a saved number.</p>
              <Link href="/safeword" className="mt-3 inline-flex rounded-lg bg-cyan px-4 py-2.5 text-sm font-semibold text-ink-950 hover:bg-[#7BD8F5]">Start safe-word check</Link>
            </Card>
          )}
        </div>
      )}
    </>
  );
}
