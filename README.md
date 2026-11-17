# Kavach - AI-Powered Family Scam Shield (VibeX Codes, Track 3: Cyber Safety)

Check a suspicious UPI request or call *before* money leaves the account. Warns in English, Tamil or Hindi, and alerts family guardians.
**Kavach cannot block or reverse UPI payments and cannot detect cloned voices.** It analyses what was said/written and helps you verify.

## Run it
Requirements: Python 3.10+, Node 18+, Tesseract (`sudo apt install tesseract-ocr`; add `tesseract-ocr-tam tesseract-ocr-hin` for Tamil/Hindi screenshots).
```bash
./scripts/dev.sh          # sets up everything, backend :8000, frontend :3000
```
Open http://localhost:3000. API docs: http://localhost:8000/docs.
Manual: see `scripts/dev.sh`. Tests: `cd backend && PYTHONPATH=. pytest -q` (43 tests). Evaluation: `cd backend && python ../ml/evaluation/run_eval.py`.
Optional keys in `backend/.env`: `GEMINI_API_KEY`, `SAFE_BROWSING_API_KEY`, `VIRUSTOTAL_API_KEY`. Without them the app runs fully; those checks show "not checked".

## What works (verified by running it)
- Auth, UPI check (text + screenshot OCR), call-transcript check (English/Tamil/Tanglish/Hindi), money-direction analysis
- Family safe word (argon2id, lockout, never returned), guardians + in-app alert centre, history + printable evidence report, dashboard
- LangGraph agent with adaptive tool loop and verified/heuristic/unavailable evidence
- Spoken warnings via browser speech synthesis (en/ta/hi), when the device has a voice
- 43 backend tests; Next.js production build type-checks; full flow exercised through the frontend proxy

## What is NOT done / not verified
- Not tested in a real browser (no browser available in the build environment): visual QA, mobile layout and Tamil/Hindi voices are unchecked. Please click through it once before demo day.
- Audio upload -> 501 (no speech-to-text). Paste transcripts instead.
- WHOIS/Safe Browsing/VirusTotal/Gemini coded and tested with mocks only, never against the live services.
- No SMS/WhatsApp; PostgreSQL untested; in-memory rate limiter; detailed reasons are English-only.

## Evaluation (computed; held-out hand-written set, n=59, threshold 50)
| | Precision | Recall | F1 | False-positive rate |
|---|---|---|---|---|
| Rules only | 0.824 | 0.609 | 0.700 | 8.3% |
| ML only | 0.846 | 0.957 | 0.898 | 11.1% |
| Hybrid | 0.909 | 0.870 | 0.889 | 5.6% |

Caveats: tiny author-written test set (optimistic vs real traffic); classifier trained only on SYNTHETIC data; Tamil-script recall weak (n=5); LLM-only comparison not run. Raw numbers: `ml/evaluation/results/metrics.json`.

## Layout
`backend/` FastAPI + agent + tests - `frontend/` Next.js app - `ml/` datasets, training, evaluation - `docs/` architecture, API, pitch & demo script
