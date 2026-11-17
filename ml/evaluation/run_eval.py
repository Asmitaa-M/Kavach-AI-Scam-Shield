"""Evaluate rules-only vs ML-only vs hybrid (and LLM-only if GEMINI_API_KEY is set)
on the HELD-OUT hand-written test set. All numbers are computed, never hardcoded.
Decision threshold is fixed a priori at score >= 50 (not tuned on the test set)."""
import json, pathlib, sys, time, os
ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from app.services.tier1.scoring import analyze_text
from app.services.tier1.classifier import load_jsonl

THRESH = 50
test = load_jsonl(ROOT / "ml" / "datasets" / "test.jsonl")
OUT = pathlib.Path(__file__).parent / "results"; OUT.mkdir(exist_ok=True)


def metrics(y, p):
    tp = sum(1 for a, b in zip(y, p) if a and b); tn = sum(1 for a, b in zip(y, p) if not a and not b)
    fp = sum(1 for a, b in zip(y, p) if not a and b); fn = sum(1 for a, b in zip(y, p) if a and not b)
    div = lambda a, b: round(a / b, 4) if b else 0.0
    prec, rec = div(tp, tp + fp), div(tp, tp + fn)
    return {"accuracy": div(tp + tn, len(y)), "precision": prec, "recall": rec,
            "f1": div(2 * prec * rec, prec + rec) if prec + rec else 0.0,
            "false_positive_rate": div(fp, fp + tn), "confusion": {"tp": tp, "fp": fp, "tn": tn, "fn": fn}}


results, errors = {}, {}
y = [r["label"] for r in test]
for mode in ["rules", "ml", "hybrid"]:
    preds, lat = [], []
    for r in test:
        t0 = time.perf_counter(); res = analyze_text(r["text"], "call", mode); lat.append((time.perf_counter() - t0) * 1000)
        preds.append(int(res.score >= THRESH))
    m = metrics(y, preds); m["latency_ms_mean"] = round(sum(lat) / len(lat), 2); m["latency_ms_p95"] = round(sorted(lat)[int(.95 * len(lat)) - 1], 2)
    results[mode] = m
    errors[mode] = [{"text": r["text"][:90], "label": r["label"], "lang": r["lang"]} for r, p in zip(test, preds) if p != r["label"]]

if os.getenv("GEMINI_API_KEY"):
    results["llm_only"] = {"note": "LLM-only evaluation requires the Gemini service; run with key configured (see docs)."}
else:
    results["llm_only"] = {"note": "NOT RUN - GEMINI_API_KEY not configured. No LLM numbers are reported."}

by_lang = {}
for mode in ["hybrid"]:
    for lang in sorted({r["lang"] for r in test}):
        idx = [i for i, r in enumerate(test) if r["lang"] == lang]
        p = [int(analyze_text(test[i]["text"], "call", mode).score >= THRESH) for i in idx]
        by_lang[lang] = {"n": len(idx), **{k: v for k, v in metrics([y[i] for i in idx], p).items() if k in ("recall", "false_positive_rate", "accuracy")}}

report = {"threshold": THRESH, "n_test": len(test), "n_scam": sum(y), "n_legit": len(y) - sum(y),
          "data_caveat": "Small hand-written synthetic-style test set; optimistic vs real-world traffic.",
          "results": results, "hybrid_by_language": by_lang, "errors": errors}
(OUT / "metrics.json").write_text(json.dumps(report, indent=2, ensure_ascii=False))

modes = [m for m in ["rules", "ml", "hybrid"]]
fig, ax = plt.subplots(figsize=(8, 4.2)); w = .2
for i, k in enumerate(["precision", "recall", "f1", "false_positive_rate"]):
    ax.bar([j + i * w for j in range(3)], [results[m][k] for m in modes], w, label=k)
ax.set_xticks([j + 1.5 * w for j in range(3)]); ax.set_xticklabels(["Rules only", "ML only", "Hybrid"])
ax.set_ylim(0, 1.05); ax.set_title(f"Held-out test (n={len(test)}) threshold={THRESH}"); ax.legend(fontsize=8); fig.tight_layout()
fig.savefig(OUT / "comparison.png", dpi=140)

for m in modes:
    r = results[m]; c = r["confusion"]
    print(f"{m:7} acc={r['accuracy']:.3f} P={r['precision']:.3f} R={r['recall']:.3f} F1={r['f1']:.3f} FPR={r['false_positive_rate']:.3f} "
          f"TP={c['tp']} FP={c['fp']} TN={c['tn']} FN={c['fn']} lat={r['latency_ms_mean']}ms")
for m in modes:
    for e in errors[m]: print(f"  [{m}] label={e['label']} ({e['lang']}): {e['text']}")
print("hybrid by language:", by_lang)
