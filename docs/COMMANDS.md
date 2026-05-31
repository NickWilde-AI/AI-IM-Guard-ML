# Commands

This document lists the most common commands for local demos, data checks, evaluation, monitoring, and deployment.

## Local Demo

```bash
PYTHONPATH=src python3 -m im_guard_ml.cli --config configs/default.yaml summary data/samples/sample_cases.jsonl

PYTHONPATH=src python3 -m im_guard_ml.cli --config configs/default.yaml predict data/samples/sample_cases.jsonl \
  --with-route \
  --with-version \
  --audit-log-out outputs/demo_audit_logs.jsonl \
  --out outputs/demo_routed_predictions.jsonl

PYTHONPATH=src python3 -m im_guard_ml.cli --config configs/default.yaml eval outputs/demo_routed_predictions.jsonl
PYTHONPATH=src python3 -m im_guard_ml.cli --config configs/default.yaml monitor outputs/demo_routed_predictions.jsonl
PYTHONPATH=src python3 -m im_guard_ml.cli --config configs/default.yaml alerts outputs/demo_routed_predictions.jsonl
PYTHONPATH=src python3 -m im_guard_ml.cli --config configs/default.yaml audit-data data/samples/sample_cases.jsonl
```

## Makefile Shortcuts

```bash
make summary
make predict
make predict-route
make eval
make monitor
make alerts
make audit-data
make build-demo
make compile
```

## Build Training Data

```bash
PYTHONPATH=src python3 -m im_guard_ml.build_dataset \
  --internal data/raw/history_tickets.jsonl \
  --internal data/raw/synthetic_cases.jsonl \
  --internal data/raw/refinement_cases.jsonl \
  --public data/raw/public_binary_safety.jsonl \
  --out data/train/im_audit_train.jsonl
```

## Train

```bash
pip install -e ".[train]"
im-guard --config configs/default.yaml train data/train/im_audit_train.jsonl
```

Enable LoRA in `configs/default.yaml`:

```yaml
training:
  peft:
    enabled: true
```

## API Service

```bash
pip install -e ".[serve]"
im-guard --config configs/default.yaml serve --port 8000
```

```bash
curl http://127.0.0.1:8000/health
curl http://127.0.0.1:8000/config
curl http://127.0.0.1:8000/metrics
```

## vLLM

```bash
MODEL_PATH=outputs/im-audit-judge \
TP_SIZE=4 \
MAX_MODEL_LEN=8192 \
bash deploy/vllm_serve.sh
```

