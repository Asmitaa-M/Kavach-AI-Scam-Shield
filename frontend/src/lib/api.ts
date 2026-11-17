export type Lang = "en" | "ta" | "hi";
export type Level = "SAFE" | "SUSPICIOUS" | "HIGH RISK";
export type User = { user_id: string; name: string; email: string; preferred_language: Lang };
export type Indicator = { id: string; label: string; weight: number; provenance: string; matched: string };
export type Analysis = {
  case_id: string; score: number; level: Level; indicators: Indicator[]; recommendations: string[]; notes: string[];
  upi?: { upi_ids: string[]; amounts: number[]; urls: string[]; direction: string; direction_note: string } | null;
  disclaimer: string; guardians_alerted: boolean; ocr_text?: string; ocr_languages?: string;
};
export type Step = { tool: string; arg: string; status: string; provenance: string; summary: string; ms: number };
export type Evidence = { type: string; description: string; source: string; confidence: number; provenance: string };
export type Investigation = {
  case_id: string; score: number; level: Level; scam_type: string; plan_initial: string[]; steps: Step[]; evidence: Evidence[];
  recommendations: string[]; unavailable_checks: string[]; llm_status: string;
  llm_explanation: { explanation: string; key_points: string[] } | null; disclaimer: string; guardians_alerted: boolean;
};
export type CaseRow = { case_id: string; input_type: string; risk_score: number; risk_level: Level; summary: string; status: string; is_simulated: boolean; created_at: string };
export type CaseDetail = CaseRow & { redacted_input: string; evidence: Evidence[] };

const TOKEN = "kavach_token";
export const getToken = () => (typeof window === "undefined" ? null : localStorage.getItem(TOKEN));
export const setToken = (t: string | null) => { if (t) localStorage.setItem(TOKEN, t); else localStorage.removeItem(TOKEN); };

export class ApiError extends Error {
  status: number;
  constructor(message: string, status: number) { super(message); this.status = status; }
}

export async function api<T>(path: string, opts: { method?: string; body?: unknown; form?: FormData } = {}): Promise<T> {
  const headers: Record<string, string> = {};
  const t = getToken();
  if (t) headers.Authorization = `Bearer ${t}`;
  let body: BodyInit | undefined;
  if (opts.form) body = opts.form;
  else if (opts.body !== undefined) { headers["content-type"] = "application/json"; body = JSON.stringify(opts.body); }
  let res: Response;
  try { res = await fetch(`/api${path}`, { method: opts.method ?? "GET", headers, body }); }
  catch { throw new ApiError("Cannot reach the Kavach server. Make sure the backend is running on port 8000.", 0); }
  if (res.status === 204) return undefined as T;
  const data = await res.json().catch(() => null);
  if (!res.ok) {
    const d = data?.detail;
    const msg = typeof d === "string" ? d : Array.isArray(d) ? d.map((x: { msg: string }) => x.msg).join("; ") : "Something went wrong. Try again.";
    throw new ApiError(msg, res.status);
  }
  return data as T;
}
export const errMsg = (e: unknown) => (e instanceof Error ? e.message : "Something went wrong.");
