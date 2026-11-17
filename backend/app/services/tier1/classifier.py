"""Lightweight ML scam classifier: char n-gram TF-IDF + logistic regression.
Char n-grams work across Tamil script, Tanglish and Hindi without a language tokenizer.
Trained ONLY on synthetic data (see ml/preprocessing/build_dataset.py)."""
import json
import pathlib
import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline

ROOT = pathlib.Path(__file__).resolve().parents[4]
MODEL_PATH = ROOT / "ml" / "saved_models" / "scam_clf.joblib"
_model = None


def build_pipeline() -> Pipeline:
    return Pipeline([
        ("tfidf", TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 5), min_df=2,
                                  sublinear_tf=True, lowercase=True)),
        ("lr", LogisticRegression(C=4.0, max_iter=1000, class_weight="balanced")),
    ])


def load_jsonl(path) -> list[dict]:
    return [json.loads(l) for l in pathlib.Path(path).read_text(encoding="utf-8").splitlines() if l.strip()]


def get_model():
    global _model
    if _model is None and MODEL_PATH.exists():
        _model = joblib.load(MODEL_PATH)
    return _model


def predict_proba(text: str) -> float | None:
    """Return P(scam) or None if no trained model is available (graceful degradation)."""
    m = get_model()
    if m is None:
        return None
    return float(m.predict_proba([text])[0][1])
