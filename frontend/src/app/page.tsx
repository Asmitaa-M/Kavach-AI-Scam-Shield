import { BellRing, Fingerprint, ScanSearch, ShieldAlert, ShieldCheck } from "lucide-react";
import Link from "next/link";

export default function Landing() {
  return (
    <div className="min-h-screen">
      <header className="mx-auto flex max-w-5xl items-center justify-between px-5 py-5">
        <span className="flex items-center gap-2 font-display text-xl font-bold"><ShieldCheck className="h-6 w-6 text-cyan" aria-hidden /> Kavach</span>
        <Link href="/auth" className="rounded-lg border border-ink-600 px-4 py-2 text-sm font-semibold hover:bg-ink-700">Sign in</Link>
      </header>

      <main className="mx-auto max-w-5xl px-5 pb-20">
        <section className="grid items-center gap-10 py-10 md:grid-cols-2 md:py-16">
          <div>
            <h1 className="font-display text-4xl font-bold leading-[1.1] tracking-tight sm:text-5xl">Check the request before the money leaves.</h1>
            <p className="mt-5 max-w-md text-lg text-mist-300">Kavach reads a suspicious UPI request or call, tells you in Tamil, Hindi or English if it is a scam, and warns your family.</p>
            <div className="mt-7 flex flex-wrap gap-3">
              <Link href="/auth?mode=register" className="rounded-lg bg-cyan px-5 py-3 font-semibold text-ink-950 hover:bg-[#7BD8F5]">Create a free account</Link>
              <Link href="/auth" className="rounded-lg border border-ink-600 px-5 py-3 font-semibold hover:bg-ink-700">Sign in</Link>
            </div>
          </div>

          {/* The product's key moment: the warning a parent sees. Illustrative example, not live data. */}
          <div aria-label="Example warning screen" className="rounded-2xl border-2 border-alarm/60 bg-alarm-soft p-6">
            <div className="mb-3 rounded-lg bg-ink-950/60 p-3 text-sm text-mist-300">
              <p className="text-xs text-mist-500">Incoming collect request</p>
              <p className="mt-1 font-semibold text-mist-100">Rs 50,000 from refund.help22@okaxis</p>
              <p>“Your son needs money urgently. Approve now.”</p>
            </div>
            <div className="flex items-center gap-3">
              <ShieldAlert className="pulse-alarm h-12 w-12 rounded-full text-alarm" aria-hidden />
              <p className="font-display text-3xl font-bold text-alarm">High risk</p>
            </div>
            <p className="mt-3 text-xl leading-snug">Stop! Approving this request may send money <em className="not-italic underline decoration-alarm decoration-2 underline-offset-4">from</em> your bank account.</p>
            <p className="mt-3 text-sm text-mist-300" lang="ta">நிறுத்துங்கள்! இதை ஏற்றால் உங்கள் கணக்கிலிருந்து பணம் செல்லக்கூடும்.</p>
            <p className="mt-4 text-xs text-mist-500">Example screen for illustration.</p>
          </div>
        </section>

        <section className="grid gap-4 md:grid-cols-3">
          {[
            { Icon: ScanSearch, h: "Reads the whole message", p: "Pulls text from screenshots, spots urgency, secrecy, OTP and PIN requests, and tells a payment request from a payment received." },
            { Icon: Fingerprint, h: "Family safe word", p: "A secret phrase only your family knows. If a caller cannot say it, treat the call as a scam. We store it only as a salted hash." },
            { Icon: BellRing, h: "Guardians get told", p: "When something is high risk, your chosen guardians see an alert with the case and the reason. Never your OTP, PIN or safe word." },
          ].map(({ Icon, h, p }) => (
            <div key={h} className="rounded-xl border border-ink-700 bg-ink-900 p-5">
              <Icon className="h-6 w-6 text-cyan" aria-hidden />
              <h2 className="mt-3 font-display text-lg font-semibold">{h}</h2>
              <p className="mt-1 text-sm text-mist-300">{p}</p>
            </div>
          ))}
        </section>

        <section className="mt-10 rounded-xl border border-ink-700 p-5">
          <h2 className="font-display text-lg font-semibold">What Kavach cannot do</h2>
          <p className="mt-2 max-w-2xl text-sm text-mist-300">Kavach cannot block or reverse a UPI payment, and it cannot tell if a voice is cloned. It checks what was said and written, and helps you verify before you act. If money is already gone, call 1930 straight away.</p>
        </section>
      </main>
    </div>
  );
}
