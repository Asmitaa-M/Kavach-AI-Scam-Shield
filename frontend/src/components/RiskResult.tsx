"use client";
import { BellRing, CheckCircle2, ShieldAlert, ShieldCheck, Volume2 } from "lucide-react";
import { useEffect, useState } from "react";
import type { Evidence, Indicator, Level } from "@/lib/api";
import { spokenWarning, t } from "@/lib/i18n";
import { speak, voiceEnabled } from "@/lib/tts";
import { Button, Card, levelStyle } from "./ui";
import { useSession } from "./Session";

type Props = {
  caseId: string; score: number; level: Level; recommendations: string[]; guardiansAlerted: boolean; disclaimer: string;
  indicators?: (Indicator | Evidence)[]; notes?: string[]; upiMoneyOut?: boolean; autoSpeak?: boolean;
};

const provTag = (p: string) =>
  p === "verified" ? "border-safe/40 text-safe" : p === "unavailable" ? "border-ink-600 text-mist-500" : "border-amber/40 text-amber";
const provText = (p: string) => (p === "verified" ? "verified" : p === "unavailable" ? "not checked" : "heuristic");

export default function RiskResult(p: Props) {
  const { lang } = useSession();
  const s = levelStyle(p.level);
  const [voiceMsg, setVoiceMsg] = useState("");
  const text = spokenWarning(p.level, lang, !!p.upiMoneyOut);

  const hear = () => {
    const r = speak(text, lang);
    setVoiceMsg(r === "ok" ? "" : r === "no-voice"
      ? "This device has no voice installed for the selected language. Read the warning on screen."
      : "This browser cannot speak warnings. Read the warning on screen.");
  };
  useEffect(() => { if (p.autoSpeak !== false && p.level !== "SAFE" && voiceEnabled()) hear(); /* eslint-disable-next-line */ }, [p.caseId]);

  const Icon = p.level === "HIGH RISK" ? ShieldAlert : p.level === "SAFE" ? ShieldCheck : ShieldAlert;
  return (
    <div className="space-y-4" aria-live="polite">
      <div className={`rounded-xl border-2 ${s.border} ${s.bg} p-5 sm:p-6`}>
        <div className="flex flex-wrap items-start gap-4">
          <Icon className={`h-12 w-12 shrink-0 ${s.text}`} aria-hidden />
          <div className="min-w-0 flex-1">
            <p className={`font-display text-3xl font-bold sm:text-4xl ${s.text}`}>{t(p.level, lang)}</p>
            <p className="mt-2 text-lg leading-snug text-mist-100">{text}</p>
            <p className="mt-2 text-xs text-mist-500">Case {p.caseId}</p>
          </div>
          <div className="text-right">
            <p className={`font-display text-5xl font-bold tabular-nums ${s.text}`}>{p.score}</p>
            <p className="text-xs text-mist-500">risk score out of 100</p>
          </div>
        </div>
        <div className="mt-4 flex flex-wrap items-center gap-3">
          <Button variant="ghost" onClick={hear}><Volume2 className="h-4 w-4" aria-hidden /> {t("hear", lang)}</Button>
          {p.guardiansAlerted && (
            <span className="inline-flex items-center gap-1.5 text-sm text-mist-300"><BellRing className="h-4 w-4 text-amber" aria-hidden /> In-app alert created for your guardians (no SMS is sent)</span>
          )}
        </div>
        {voiceMsg && <p className="mt-3 text-sm text-amber">{voiceMsg}</p>}
      </div>

      {!!p.indicators?.length && (
        <Card>
          <h2 className="mb-3 font-display text-lg font-semibold text-mist-100">Why Kavach says this</h2>
          <ul className="space-y-2">
            {p.indicators.map((i, k) => {
              const prov = i.provenance;
              const label = "label" in i ? i.label : i.description;
              return (
                <li key={k} className="flex items-start gap-3 text-sm">
                  <span className={`mt-0.5 shrink-0 rounded border px-1.5 py-0.5 text-[11px] font-medium ${provTag(prov)}`}>{provText(prov)}</span>
                  <span className="text-mist-100">{label}</span>
                </li>
              );
            })}
          </ul>
          <p className="mt-3 text-xs text-mist-500">“Heuristic” means a pattern match, which is a clue and not proof. “Verified” comes from an external service or a direct reading of the message.</p>
        </Card>
      )}

      {!!p.notes?.length && p.notes.map((n, i) => <p key={i} className="text-sm text-amber">{n}</p>)}

      <Card>
        <h2 className="mb-3 font-display text-lg font-semibold text-mist-100">What to do now</h2>
        <ul className="space-y-2">
          {p.recommendations.map((r, i) => (
            <li key={i} className="flex items-start gap-2 text-sm text-mist-100"><CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-cyan" aria-hidden /> {r}</li>
          ))}
        </ul>
        <p className="mt-4 text-xs text-mist-500">{p.disclaimer}</p>
      </Card>
    </div>
  );
}
