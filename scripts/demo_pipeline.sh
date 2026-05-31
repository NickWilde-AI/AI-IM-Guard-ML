#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

python3 -m im_guard_ml.cli --config configs/default.yaml summary data/samples/sample_cases.jsonl
python3 -m im_guard_ml.cli --config configs/default.yaml predict data/samples/sample_cases.jsonl --out outputs/demo_predictions.jsonl
python3 -m im_guard_ml.cli --config configs/default.yaml eval outputs/demo_predictions.jsonl

