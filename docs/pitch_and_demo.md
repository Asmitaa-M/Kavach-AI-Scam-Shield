# 8-10 slide outline (use real numbers only)
1. Problem: AI-voice and UPI collect scams hit parents and shopkeepers (Track 3).
2. Solution: Kavach checks the request before money leaves; tells the user in Tamil/Hindi/English; alerts guardians.
3. How it works: user flow (screenshot/paste -> verdict -> voice warning -> guardian alert).
4. Architecture: Tier 1 (rules + ML) -> Tier 2 LangGraph agent -> evidence chain (see docs/architecture.md).
5. The agent: adaptive tool loop; verified vs heuristic vs unavailable evidence; never invents results.
6. Family safe word: defeats voice-clone calls by protocol, not detection. Salted hash, lockout, honest caveat.
7. Evaluation: show ml/evaluation/results/comparison.png. Hybrid P 0.909 / R 0.870 / F1 0.889 / FPR 5.6% on n=59 hand-written held-out set; ML-only F1 0.898 with FPR 11.1%; rules-only recall 0.609. State: tiny set, synthetic training data, Tamil-script recall weak, LLM-only not run.
8. Security and privacy: argon2id, redaction, upload sniffing, prompt-injection guard, access control, 43 tests.
9. Honest limits + roadmap: no payment blocking, no voice-clone detection, audio STT, SMS via provider, Tamil/Hindi OCR packs, real-world data.
10. Links: GitHub repo, demo video.

# 2-3 minute demo script
1. (0:00) Landing page: the warning card. One sentence on the problem.
2. (0:15) Register as parent; add a guardian (second browser/incognito registered as the guardian first).
3. (0:35) UPI check: click "Sample: Fake refund collect request" -> Check now. Red banner, voice warning, "money goes OUT". Show reasons tagged heuristic/verified.
4. (1:00) Upload a screenshot -> OCR text appears -> verdict.
5. (1:15) Call check: Tanglish sample -> HIGH RISK. Click "Start safe-word check", enter a wrong phrase -> VERIFICATION FAILED + next steps.
6. (1:45) Investigator: "Fake KYC link" -> show the plan, the tool timeline, "not checked" items (no keys), and that the score still works.
7. (2:15) Switch to the guardian account -> Guardian alerts shows the cases; mark read.
8. (2:35) History -> open a case -> evidence report. End on the evaluation chart and the "what Kavach cannot do" line.
