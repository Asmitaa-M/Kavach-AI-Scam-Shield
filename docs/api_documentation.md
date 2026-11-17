# API (live Swagger at http://localhost:8000/docs). All /api routes except register/login need `Authorization: Bearer <token>`.

| Method | Path | Purpose |
|---|---|---|
| GET | /health | status, whether ML model loaded, which integrations are configured |
| POST | /api/auth/register, /api/auth/login | returns `{token, user}` (password min 8 chars) |
| GET | /api/auth/me | current user |
| PATCH | /api/auth/language | `{preferred_language: en|ta|hi}` |
| POST | /api/analyze/upi | `{text, is_demo_sample}` -> score 0-100, level, indicators, upi facts, recommendations |
| POST | /api/analyze/upi/screenshot | multipart `file` (PNG/JPG/WebP, 5 MB) -> OCR + analysis |
| POST | /api/analyze/call | `{text}` transcript analysis |
| POST | /api/analyze/call/audio | validates file, returns 501 (no speech-to-text configured) |
| GET/POST | /api/family/contacts | list / add `{name, relationship_label, phrase}` (phrase never returned) |
| DELETE | /api/family/contacts/{id} | remove |
| POST | /api/family/contacts/{id}/verify | `{phrase, notify_guardians}` -> VERIFIED / VERIFICATION FAILED; 5 failures lock 15 min |
| GET/POST/DELETE | /api/guardians | manage guardians (by email) |
| GET | /api/alerts, /api/alerts/sent | received / sent alerts; POST /api/alerts/{id}/read |
| POST | /api/investigate | `{text}` agent run -> plan, steps, evidence (verified/heuristic/unavailable), verdict |
| GET | /api/cases, /api/cases/{id} | history; detail includes redacted input and evidence |
| GET | /api/dashboard/stats | totals, distribution, unread alerts, recent cases |

Levels: SAFE (<35), SUSPICIOUS (35-64), HIGH RISK (>=65). HIGH RISK creates in-app alerts for active guardians.
