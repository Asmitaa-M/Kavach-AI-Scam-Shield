#!/usr/bin/env bash
# Starts backend (8000) and frontend (3000). First run: sets up venv, trains model, installs npm deps.
set -e
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT/backend"
[ -d .venv ] || python3 -m venv .venv
. .venv/bin/activate
pip install -q -r requirements.txt
[ -f .env ] || cp ../.env.example .env
[ -f ../ml/datasets/train.jsonl ] || python ../ml/preprocessing/build_dataset.py
[ -f ../ml/datasets/test.jsonl ] || python ../ml/preprocessing/build_testset.py
[ -f ../ml/saved_models/scam_clf.joblib ] || python ../ml/training/train.py
PYTHONPATH=. uvicorn app.main:app --port 8000 &
BE=$!
trap "kill $BE 2>/dev/null" EXIT
cd "$ROOT/frontend"
[ -d node_modules ] || npm install --no-audit --no-fund
npm run dev
