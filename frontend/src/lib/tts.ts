import type { Lang } from "./api";
import { speechLang } from "./i18n";

export type SpeakResult = "ok" | "no-voice" | "unsupported";
export const voiceEnabled = () => (typeof window === "undefined" ? false : localStorage.getItem("kavach_voice") !== "off");
export const setVoiceEnabled = (on: boolean) => localStorage.setItem("kavach_voice", on ? "on" : "off");

function pickVoice(code: string): SpeechSynthesisVoice | undefined {
  const vs = window.speechSynthesis.getVoices();
  return vs.find((v) => v.lang.replace("_", "-").toLowerCase() === code.toLowerCase()) ||
         vs.find((v) => v.lang.toLowerCase().startsWith(code.slice(0, 2).toLowerCase()));
}

/** Browser speech synthesis. Reports honestly when the device has no voice for the language. */
export function speak(text: string, lang: Lang): SpeakResult {
  if (typeof window === "undefined" || !("speechSynthesis" in window)) return "unsupported";
  const code = speechLang(lang);
  const voice = pickVoice(code);
  if (!voice) return "no-voice";
  window.speechSynthesis.cancel();
  const u = new SpeechSynthesisUtterance(text);
  u.voice = voice; u.lang = voice.lang; u.rate = 0.9;
  window.speechSynthesis.speak(u);
  return "ok";
}
