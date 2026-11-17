"use client";
import { ImageUp, Info } from "lucide-react";
import Link from "next/link";
import { useState } from "react";
import { api, errMsg, type Analysis } from "@/lib/api";
import { t } from "@/lib/i18n";
import { Button, Card, ErrorBox, PageTitle, inputCls } from "@/components/ui";
import RiskResult from "@/components/RiskResult";
import { useSession } from "@/components/Session";

const SAMPLES = [
  { name: "Fake refund collect request", text: "Collect request of Rs 49,000 from refund.help22@okaxis. Your son needs money urgently. Approve now to receive your refund. Enter UPI PIN to receive. http://sbi-kyc-update.xyz/login" },
  { name: "Wrong transfer, send it back", text: "Sir I sent Rs 12,000 to your account by mistake. Please send it back immediately, I am in hospital." },
  { name: "Genuine bank credit (should be safe)", text: "HDFC Bank: Rs 2,500 has been credited to your a/c XX1234 on 14-11-26. Ref no 4455. Avl bal Rs 12,000." },
];

export default function UpiPage() {
  const { lang } = useSession();
  const [tab, setTab] = useState<"text" | "image">("text");
  const [text, setText] = useState(""); const [file, setFile] = useState<File | null>(null);
  const [sample, setSample] = useState(false);
  const [busy, setBusy] = useState(false); const [err, setErr] = useState(""); const [res, setRes] = useState<Analysis | null>(null);
  const [ack, setAck] = useState(false); const [simDone, setSimDone] = useState(false);

  async function run() {
    setErr(""); setRes(null); setAck(false); setSimDone(false); setBusy(true);
    try {
      if (tab === "image") {
        if (!file) throw new Error("Choose a screenshot first.");
        const form = new FormData(); form.append("file", file);
        setRes(await api<Analysis>("/analyze/upi/screenshot", { method: "POST", form }));
      } else setRes(await api<Analysis>("/analyze/upi", { method: "POST", body: { text, is_demo_sample: sample } }));
    } catch (e) { setErr(errMsg(e)); } finally { setBusy(false); }
  }
  const moneyOut = res?.upi?.direction === "MONEY_OUT_IF_APPROVED";
  const risky = res && res.level !== "SAFE";

  return (
    <>
      <PageTitle title={t("upi", lang)} sub="Paste the request text or upload a screenshot. Kavach shows whether money would come in or go out, and why it looks risky." />
      <Card>
        <div className="mb-4 flex gap-2" role="tablist">
          {(["text", "image"] as const).map((k) => (
            <button key={k} role="tab" aria-selected={tab === k} onClick={() => setTab(k)}
              className={`rounded-lg px-3 py-1.5 text-sm font-semibold ${tab === k ? "bg-ink-700 text-cyan" : "text-mist-300 hover:bg-ink-800"}`}>{k === "text" ? "Paste text" : "Upload screenshot"}</button>
          ))}
        </div>
        {tab === "text" ? (
          <>
            <label className="text-sm" htmlFor="upi-text">Request or message text</label>
            <textarea id="upi-text" rows={5} className={`${inputCls} mt-1`} maxLength={6000} value={text} onChange={(e) => { setText(e.target.value); setSample(false); }} placeholder="Paste the payment request or SMS here" />
            <div className="mt-3 flex flex-wrap gap-2">
              {SAMPLES.map((s) => <button key={s.name} onClick={() => { setText(s.text); setSample(true); }} className="rounded-full border border-ink-600 px-3 py-1 text-xs text-mist-300 hover:bg-ink-700">Sample: {s.name}</button>)}
            </div>
          </>
        ) : (
          <label className="flex cursor-pointer flex-col items-center gap-2 rounded-lg border border-dashed border-ink-600 p-8 text-center text-sm hover:bg-ink-800">
            <ImageUp className="h-7 w-7 text-cyan" aria-hidden />
            <span>{file ? file.name : "Choose a PNG, JPG or WebP screenshot (max 5 MB)"}</span>
            <input type="file" accept="image/png,image/jpeg,image/webp" className="sr-only" onChange={(e) => setFile(e.target.files?.[0] ?? null)} />
          </label>
        )}
        <div className="mt-4"><Button onClick={run} loading={busy} disabled={tab === "text" ? text.trim().length < 3 : !file}>{t("analyze", lang)}</Button></div>
        <p className="mt-3 flex items-start gap-2 text-xs text-mist-500"><Info className="mt-0.5 h-3.5 w-3.5 shrink-0" aria-hidden /> Never type your UPI PIN or OTP here. Screenshot text is read on the server and stored with numbers redacted.</p>
      </Card>

      {err && <div className="mt-4"><ErrorBox message={err} /></div>}
      {res && (
        <div className="mt-5 space-y-4">
          {res.ocr_text && <Card><h2 className="mb-2 font-display text-base font-semibold">Text read from the screenshot</h2><p className="whitespace-pre-wrap text-sm text-mist-300">{res.ocr_text}</p></Card>}
          {res.upi && (
            <Card className={moneyOut ? "!border-alarm/50" : ""}>
              <h2 className="mb-2 font-display text-lg font-semibold">Which way does the money go?</h2>
              <p className={`text-xl font-semibold ${moneyOut ? "text-alarm" : res.upi.direction === "MONEY_IN" ? "text-safe" : "text-mist-100"}`}>
                {moneyOut ? "Money goes OUT of your account if you approve" : res.upi.direction === "MONEY_IN" ? "Looks like money coming IN" : res.upi.direction === "MONEY_OUT_DONE" ? "Looks like money already left" : "Direction unclear"}
              </p>
              {res.upi.direction_note && <p className="mt-1 text-sm text-mist-300">{res.upi.direction_note}</p>}
              <dl className="mt-3 grid gap-2 text-sm sm:grid-cols-3">
                <div><dt className="text-mist-500">UPI IDs</dt><dd className="break-all">{res.upi.upi_ids.join(", ") || "none found"}</dd></div>
                <div><dt className="text-mist-500">Amounts</dt><dd>{res.upi.amounts.map((a) => `Rs ${a.toLocaleString("en-IN")}`).join(", ") || "none found"}</dd></div>
                <div><dt className="text-mist-500">Links</dt><dd className="break-all">{res.upi.urls.join(", ") || "none found"}</dd></div>
              </dl>
            </Card>
          )}
          <RiskResult caseId={res.case_id} score={res.score} level={res.level} indicators={res.indicators} notes={res.notes}
            recommendations={res.recommendations} guardiansAlerted={res.guardians_alerted} disclaimer={res.disclaimer} upiMoneyOut={moneyOut} />

          {risky && (
            <Card>
              <h2 className="font-display text-lg font-semibold">Practice guard (simulation)</h2>
              <p className="mt-1 text-sm text-mist-300">This shows how Kavach would slow you down in a payment app. It does not touch any real payment.</p>
              <label className="mt-3 flex items-start gap-2 text-sm"><input type="checkbox" className="mt-1" checked={ack} onChange={(e) => setAck(e.target.checked)} /> I called the requester on a number I already had saved and they confirmed this request.</label>
              <div className="mt-3 flex flex-wrap gap-2">
                <Button variant="danger" disabled={!ack} onClick={() => setSimDone(true)}>Approve anyway (simulation)</Button>
                <Link href="/safeword" className="inline-flex items-center rounded-lg border border-ink-600 px-4 py-2.5 text-sm font-semibold hover:bg-ink-700">Verify with family safe word</Link>
              </div>
              {simDone && <p className="mt-3 text-sm text-amber">Simulation only. No payment was made. Kavach cannot control your payment app, so decline the real request yourself.</p>}
            </Card>
          )}
        </div>
      )}
    </>
  );
}
