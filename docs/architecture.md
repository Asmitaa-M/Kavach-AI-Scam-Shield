# Kavach architecture

```
Browser (Next.js 14, TS, Tailwind)  --/api/*-->  Next rewrite proxy  -->  FastAPI (port 8000)
  speechSynthesis (ta-IN/hi-IN/en-IN)                                       |
                                                                            +-- security: argon2id, JWT, rate limit, upload sniffing, redaction, injection guard
                                                                            +-- Tier 1 (local, in the backend process, works offline)
                                                                            |     rules (EN / Tamil / Tanglish / Hinglish) + TF-IDF char n-gram LogReg + UPI parser
                                                                            +-- Tier 2 (agent): LangGraph classify -> plan -> act(loop) -> fuse -> report
                                                                            |     tools: suspicious_language, upi_id_analyzer, url_lexical_check,
                                                                            |            domain_whois (RDAP), safe_browsing, virustotal, cross_case_correlation
                                                                            |     optional Gemini: writes the explanation only
                                                                            +-- SQLAlchemy -> SQLite (default) / PostgreSQL via DATABASE_URL
```

## Tier 1 vs Tier 2
Tier 1 runs inside the backend process (about 1 ms per message in our evaluation), needs no network and no keys. It is NOT on-device.
Tier 2 is the agent. It runs Tier 1 first, then chooses follow-up tools from what it finds. A URL adds WHOIS, Safe Browsing and VirusTotal; identifiers add a cross-case lookup.

## Evidence honesty contract
Every evidence item carries a provenance: `verified` (external API, database, or direct parse), `heuristic` (rule/ML pattern) or `unavailable` (tool could not run).
Tools never raise and never fabricate: no key or no network gives `unavailable` and adds nothing to the score.
Final score = noisy-OR of tier-1 score and weighted tool findings. A verified high-confidence finding (e.g. Safe Browsing hit) floors the score at 90.
The LLM cannot change the score or verdict.

## Prompt-injection defence
Untrusted text is only (a) pattern-matched by code, (b) wrapped in `<untrusted>` delimiters for the optional LLM, which has no tool authority and whose JSON is schema-validated.
Injection phrases are themselves reported as scam evidence.

## Database
users, guardians, family_contacts (argon2id hash only), verification_attempts (outcome only), scam_cases (redacted input), evidence, guardian_alerts.
Every query is scoped to the authenticated user or an active guardian link.

## Known limitations
- Safe words are low-entropy; a leaked hash could be brute-forced. They are an extra check, not proof of identity.
- Rate limiting is in-memory (single process).
- Audio transcription is not implemented (501). No cloned-voice detection.
- Alerts are in-app only. No SMS/WhatsApp provider is integrated.
- Detailed reasons are shown in English; menus and the spoken verdict are translated (en/ta/hi).
- Browser speech needs an installed voice for the language; the app says so when none exists.
- PostgreSQL is configurable but untested here (needs `pip install "psycopg[binary]"`).
