"use client";
import { Bell, Fingerprint, History, LayoutDashboard, LogOut, PhoneCall, ScanSearch, Settings, ShieldCheck, Wallet } from "lucide-react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { api, setToken, getToken, type User } from "@/lib/api";
import { t } from "@/lib/i18n";
import { SessionCtx } from "./Session";
import { Spinner } from "./ui";

const NAV = [
  { href: "/dashboard", key: "dashboard", Icon: LayoutDashboard },
  { href: "/upi", key: "upi", Icon: Wallet },
  { href: "/call", key: "call", Icon: PhoneCall },
  { href: "/safeword", key: "safeword", Icon: Fingerprint },
  { href: "/investigate", key: "investigate", Icon: ScanSearch },
  { href: "/alerts", key: "alerts", Icon: Bell },
  { href: "/history", key: "history", Icon: History },
  { href: "/settings", key: "settings", Icon: Settings },
];

export default function Shell({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const path = usePathname();
  const [user, setUser] = useState<User | null>(null);

  useEffect(() => {
    if (!getToken()) { router.replace("/auth"); return; }
    api<User>("/auth/me").then(setUser).catch(() => { setToken(null); router.replace("/auth"); });
  }, [router]);

  if (!user) return <div className="p-8"><Spinner label="Opening Kavach" /></div>;
  const signOut = () => { setToken(null); router.replace("/"); };
  const lang = user.preferred_language;

  return (
    <SessionCtx.Provider value={{ user, lang, setUser, signOut }}>
      <div className="min-h-screen md:flex">
        <aside className="hidden w-60 shrink-0 flex-col border-r border-ink-700 bg-ink-900 p-4 md:flex">
          <Link href="/dashboard" className="mb-6 flex items-center gap-2 px-2 font-display text-xl font-bold text-mist-100">
            <ShieldCheck className="h-6 w-6 text-cyan" aria-hidden /> Kavach
          </Link>
          <nav className="flex-1 space-y-1" aria-label="Main">
            {NAV.map(({ href, key, Icon }) => {
              const on = path === href;
              return (
                <Link key={href} href={href} aria-current={on ? "page" : undefined}
                  className={`flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm ${on ? "bg-ink-700 font-semibold text-cyan" : "text-mist-300 hover:bg-ink-800"}`}>
                  <Icon className="h-4 w-4" aria-hidden /> {t(key, lang)}
                </Link>
              );
            })}
          </nav>
          <div className="border-t border-ink-700 pt-3">
            <p className="truncate px-2 text-sm text-mist-100">{user.name}</p>
            <p className="truncate px-2 text-xs text-mist-500">{user.email}</p>
            <button onClick={signOut} className="mt-2 flex w-full items-center gap-2 rounded-lg px-2 py-2 text-sm text-mist-300 hover:bg-ink-800">
              <LogOut className="h-4 w-4" aria-hidden /> {t("signout", lang)}
            </button>
          </div>
        </aside>
        <main className="min-w-0 flex-1 px-4 pb-24 pt-6 sm:px-8 md:pb-10">
          <div className="mx-auto max-w-4xl">{children}</div>
        </main>
        <nav aria-label="Main" className="fixed inset-x-0 bottom-0 z-20 flex overflow-x-auto border-t border-ink-700 bg-ink-900 md:hidden">
          {NAV.map(({ href, key, Icon }) => (
            <Link key={href} href={href} className={`flex min-w-[76px] flex-1 flex-col items-center gap-1 px-2 py-2.5 text-[11px] ${path === href ? "text-cyan" : "text-mist-500"}`}>
              <Icon className="h-5 w-5" aria-hidden /> <span className="max-w-[72px] truncate">{t(key, lang)}</span>
            </Link>
          ))}
        </nav>
      </div>
    </SessionCtx.Provider>
  );
}
