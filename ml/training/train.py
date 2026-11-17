"""Train the ML classifier on the SYNTHETIC training set and save it."""
import pathlib, sys, joblib
ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))
from app.services.tier1.classifier import build_pipeline, load_jsonl, MODEL_PATH  # noqa: E402

rows = load_jsonl(ROOT / "ml" / "datasets" / "train.jsonl")
model = build_pipeline().fit([r["text"] for r in rows], [r["label"] for r in rows])
MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
joblib.dump(model, MODEL_PATH)
print(f"trained on {len(rows)} synthetic rows -> {MODEL_PATH}")
