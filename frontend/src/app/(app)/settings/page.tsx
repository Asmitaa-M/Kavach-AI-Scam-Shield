"use client";
import { Volume2 } from "lucide-react";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { api, errMsg, type Lang, type User } from "@/lib/api";
import { LANGS, spokenWarning, t } from "@/lib/i18n";
import { setVoiceEnabled, speak, voiceEnabled } from "@/lib/tts";
import { Button, Card, ErrorBox, PageTitle, inputCls } from "@/components/ui";
import { useSession } from "@/components/Session";

export default function Settings() {
  const { user, lang, setUser, signOut } = useSession();
  const router = useRouter();
  const [voice, setVoice] = useState(true); const [msg, setMsg] = useState(""); const [err, setErr] = useState("");
  useEffect(() => setVoice(voiceEnabled()), []);

  async function changeLang(l: Lang) {
    setErr(""); try { setUser(await api<User>("/auth/language", { method: "PATCH", body: { preferred_language: l } })); } catch (e) { setErr(errMsg(e)); }
  }
  const test = () => {
    const r = speak(spokenWarning("HIGH RISK", lang, true), lang);
    setMsg(r === "ok" ? "" : r === "no-voice" ? `This device has no ${LANGS.find((x) => x.code === lang)!.label} voice. Install one in your phone or computer's speech settings.` : "This browser cannot speak.");
  };
  return (
    <>
      <PageTitle title={t("settings", lang)} />
      {err && <div className="mb-4"><ErrorBox message={err} /></div>}
      <Card>
        <h2 className="mb-3 font-display text-lg font-semibold">Language and voice</h2>
        <label className="block text-sm">Language for menus and spoken warnings
          <select className={`${inputCls} mt-1 max-w-xs`} value={lang} onChange={(e) => changeLang(e.target.value as Lang)}>{LANGS.map((l) => <option key={l.code} value={l.code}>{l.label}</option>)}</select>
        </label>
        <p className="mt-2 text-xs text-mist-500">The spoken verdict and menus are translated. The detailed reasons on screen are in English for now.</p>
        <label className="mt-4 flex items-center gap-2 text-sm"><input type="checkbox" checked={voice} onChange={(e) => { setVoice(e.target.checked); setVoiceEnabled(e.target.checked); }} /> Speak warnings aloud automatically</label>
        <div className="mt-3"><Button variant="ghost" onClick={test}><Volume2 className="h-4 w-4" aria-hidden /> Test the voice</Button></div>
        {msg && <p className="mt-2 text-sm text-amber">{msg}</p>}
      </Card>
      <Card className="mt-4">
        <h2 className="mb-2 font-display text-lg font-semibold">Privacy</h2>
        <ul className="list-disc space-y-1.5 pl-5 text-sm text-mist-300">
          <li>Kavach never asks for your UPI PIN, OTP or bank password. Do not type them anywhere.</li>
          <li>Text you check is stored with OTPs, phone numbers and card or account numbers replaced by markers.</li>
          <li>Family safe words are stored only as salted hashes. They are never shown, logged, or sent to guardians.</li>
          <li>Guardians see the case number, risk level and a short reason. Not your messages.</li>
          <li>Alerts are in-app only. No SMS or WhatsApp message is sent.</li>
          <li>Kavach cannot block or reverse payments. If money was lost, call 1930 and report at cybercrime.gov.in.</li>
        </ul>
      </Card>
      <div className="mt-4"><Button variant="ghost" onClick={() => { signOut(); router.replace("/"); }}>{t("signout", lang)}</Button></div>
    </>
  );
}
