<div align="center">

# AI-IM-Guard-ML

**Enterprise-grade AI/ML framework for IM private-message risk review**

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/API-FastAPI-009688)](https://fastapi.tiangolo.com/)
[![vLLM](https://img.shields.io/badge/Serving-vLLM-7c3aed)](https://github.com/vllm-project/vllm)
[![enterprise-check](https://github.com/NickWilde-AI/AI-IM-Guard-ML/actions/workflows/ci.yml/badge.svg)](https://github.com/NickWilde-AI/AI-IM-Guard-ML/actions/workflows/ci.yml)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

AI-IM-Guard-ML is a production-oriented showcase project for IM safety review. It combines chat evidence, behavioral signals, LLM Judge training, policy routing, audit trails, monitoring, model governance, and deployment templates into one reproducible ML engineering system.

[中文](README.md) · [Quick Start](#quick-start) · [Architecture](#architecture) · [Training](#training) · [Enterprise Checks](#enterprise-checks) · [Docs](#documentation)

</div>

---

## Why This Exists

Most content-safety demos stop at a text classifier: `safe` or `unsafe`.

Real IM risk review is messier. A production system needs to decide:

- whether the conversation is actually violating policy;
- how severe the risk is;
- whether the right action is ignore, warning, limit, or ban review;
- whether chat evidence and behavior evidence support each other;
- how the decision is audited, monitored, rolled back, and improved.

AI-IM-Guard-ML turns that problem into a structured, reviewable engineering system:

```text
IM case
  -> chat evidence + behavior evidence
  -> LLM Judge
  -> structured risk output
  -> postprocess guardrails
  -> policy route
  -> audit / metrics / feedback loop
```

The goal is not to pretend this repository contains real company data or an online production checkpoint. The goal is to demonstrate how an enterprise-grade IM risk model project should be designed, trained, evaluated, served, monitored, and explained.

## Highlights

| Area | What is implemented |
| --- | --- |
| Multi-evidence review | Chat messages, scenario fields, behavior abnormalities, and structured labels |
| LLM Judge | Heuristic demo Judge plus Transformers/SFT checkpoint path |
| Training pipeline | Completion-only SFT, LoRA/PEFT config, public-data field loss masking |
| Data governance | XGuard public dataset ingestion, conservative label mapping, split/audit checks |
| Decision safety | JSON parsing fallback, label validation, strong-action guardrails, policy routing |
| API service | FastAPI, request ID, token/RBAC auth, CORS, rate limits, request-size limits |
| Auditability | JSONL/SQLite audit backends, ticket lookup, versioned decisions |
| Monitoring | Prometheus metrics, drift reports, sliding-window alerts, SLO documentation |
| Model governance | Model registry, promotion guardrails, rollback target, approval metadata |
| Delivery gates | `make enterprise-check`, OpenAPI contract, preflight, readiness checks, CI |

## Current Status

| Stage | Status | Notes |
| --- | --- | --- |
| Engineering framework | Complete | CLI, API, data, training, evaluation, monitoring, audit, deployment, CI |
| Full training pipeline | Complete | Full-data fast training run finished and checkpoint saved locally |
| Chinese model quality | In progress | Requires GPU or long MPS training for Qwen-based quality experiments |
| Real production launch | Not claimed | No real company IM data, no online checkpoint, no real human-review platform |

Latest local full-pipeline training run:

| Item | Result |
| --- | --- |
| Config | `configs/local_fast_full_train.yaml` |
| Dataset | `data/train/xguard_splits/train.jsonl` |
| Steps | `4962 / 4962` |
| Runtime | about 20 minutes |
| Final train loss | `10.26` |
| Local output | `outputs/im-audit-judge-fast-full` |

This fast-full run uses `sshleifer/tiny-gpt2`. It proves the training engineering path is executable. It is not a Chinese IM risk-quality model. For model quality, use Qwen LoRA/GPU training and report offline evaluation metrics.

## Architecture

Stable text pipeline:

```text
IM review request
  -> evidence builder
  -> prompt / feature rendering
  -> LLM Judge
  -> JSON parsing
  -> postprocess guardrails
  -> policy routing
  -> audit store + metrics + feedback loop
```

| Layer | Responsibility | Key files |
| --- | --- | --- |
| Access | Request handling, CLI, schema validation | `api.py`, `cli.py`, `schema.py` |
| Evidence | Chat and behavior evidence rendering | `prompting.py`, `data_audit.py` |
| Model | Heuristic demo, SFT training, checkpoint inference | `inference.py`, `training.py` |
| Decision | JSON recovery, validation, action routing | `parsing.py`, `postprocess.py` |
| Governance | Versioning, audit, monitoring, registry | `versioning.py`, `audit_store.py`, `monitoring.py`, `model_registry.py` |
| Feedback | Evaluation and hard-case refinement | `evaluation.py`, `refinement.py` |

## Quick Start

Local demo does not require a GPU or a real fine-tuned checkpoint. It uses a deterministic heuristic Judge to run the full engineering loop.

```bash
git clone https://github.com/NickWilde-AI/AI-IM-Guard-ML.git
cd AI-IM-Guard-ML

python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev,serve]"

make predict-route
make eval-report
make window-alerts
make drift-report
make readiness-check
```

Run the API:

```bash
PYTHONPATH=src im-guard --config configs/default.yaml serve --port 8000
```

Submit a review request:

```bash
curl -X POST http://127.0.0.1:8000/judge \
  -H "Content-Type: application/json" \
  -H "X-Request-ID: interview-demo-1" \
  -d '{
    "ticket_id": "interview-demo-1",
    "chat_evidence_list": ["加微信稳赚，带你投资。"],
    "behavior_abnormal_list": ["短时间高频私聊。"]
  }'
```

Check service metrics:

```bash
curl http://127.0.0.1:8000/metrics
```

## Output Contract

The Judge returns a structured review result instead of a single binary label:

```json
{
  "risk_level": "low_risk | mid_risk | high_risk",
  "topic": "business risk topic",
  "correlation_analysis": "semantic-behavior evidence correlation",
  "final_judgment": "exist_violation | not_exist_violation",
  "judgment_basis": "decision basis with evidence references",
  "handling_suggestion": "ignore | warning | limit_account | ban_account",
  "route": "auto_close | auto_action | policy_action | human_review_required",
  "final_action": "ignore | send_warning | limit_account_candidate | review_before_ban"
}
```

High-impact actions are treated as review recommendations. The system includes postprocess guardrails and routing logic so model output is not blindly treated as irreversible enforcement.

## Training

Install training dependencies:

```bash
pip install -e ".[train]"
```

Run training readiness:

```bash
LC_ALL=en_US.UTF-8 LANG=en_US.UTF-8 \
PYTHONPATH=src im-guard --config configs/default.yaml \
  train-readiness data/train/xguard_splits/train.jsonl \
  --out outputs/training_readiness.json
```

Run the fast full-pipeline training check:

```bash
LC_ALL=en_US.UTF-8 LANG=en_US.UTF-8 \
PYTHONPATH=src im-guard --config configs/local_fast_full_train.yaml \
  train data/train/xguard_splits/train.jsonl
```

Run local Qwen LoRA training on Mac MPS:

```bash
LC_ALL=en_US.UTF-8 LANG=en_US.UTF-8 \
PYTHONPATH=src im-guard --config configs/local_mps_train.yaml \
  train data/train/xguard_splits/train.jsonl
```

Run GPU-oriented Qwen training:

```bash
LC_ALL=en_US.UTF-8 LANG=en_US.UTF-8 \
PYTHONPATH=src im-guard --config configs/default.yaml \
  train data/train/xguard_splits/train.jsonl
```

Training design:

- completion-only SFT: loss is applied to the assistant JSON output, not the user prompt;
- public-data field masking: public binary safety data does not teach `risk_level` or `handling_suggestion`;
- conservative public labels: public violations are capped at `mid_risk / warning`;
- LoRA/PEFT support: configured from YAML;
- Qwen-style prompt rendering: aligned with the inference path.

## Model-Effect Roadmap

The engineering loop is now working. The next step is model quality, not more feature stacking.

| Step | Goal |
| --- | --- |
| Rent GPU capacity | Use at least 24GB VRAM for small LoRA runs; prefer 48GB/80GB for 7B experiments |
| Fix validation data | Keep stable `val/test` splits so metrics are not inflated |
| Train Qwen checkpoint | Use `Qwen/Qwen2.5-7B-Instruct` or a smaller Qwen LoRA baseline |
| Evaluate rigorously | Report `final_judgment F1`, `risk_level macro-F1`, `handling macro-F1`, `ban_account FPR` |
| Analyze errors | Focus on false bans, missed violations, strong-action mistakes, and `mid_risk` gray cases |
| Feed back hard cases | Convert mistakes into refinement samples and rerun training |

Public XGuard data is useful for safety-recognition coverage. Strong actions such as `limit_account` and `ban_account` should come from reviewed IM-like samples, not raw public binary safety data.

## Enterprise Checks

Run the full local gate:

```bash
make enterprise-check
```

The gate covers unit tests, source compilation, OpenAPI contract validation, production preflight, model registry checks, delivery summary, and readiness checks.

Latest local result:

```text
143 passed, 1 warning
```

GitHub Actions runs the same enterprise gate on push and pull request.

## Repository Layout

```text
.
├── configs/                 # model, training, registry, rollout configs
├── data/samples/            # small demo review cases
├── deploy/                  # Docker, vLLM, env templates, deployment examples
├── docs/                    # architecture, operations, training, interview docs
├── scripts/                 # dataset download and API benchmark scripts
├── src/im_guard_ml/         # core Python package
├── tests/                   # unit, contract, readiness, and governance tests
├── Makefile
├── pyproject.toml
└── README.md
```

## Documentation

| Need | Start here |
| --- | --- |
| Project map | [docs/PROJECT_INDEX.md](docs/PROJECT_INDEX.md) |
| Architecture | [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) |
| Commands | [docs/COMMANDS.md](docs/COMMANDS.md) |
| API usage | [docs/API_USAGE.md](docs/API_USAGE.md) |
| Training and evaluation | [docs/TRAINING_AND_EVALUATION.md](docs/TRAINING_AND_EVALUATION.md) |
| Public dataset | [docs/PUBLIC_DATASET_XGUARD.md](docs/PUBLIC_DATASET_XGUARD.md) |
| Production readiness | [docs/ENTERPRISE_READINESS_REVIEW.md](docs/ENTERPRISE_READINESS_REVIEW.md) |
| Deployment and operations | [docs/DEPLOYMENT_AND_OPERATIONS.md](docs/DEPLOYMENT_AND_OPERATIONS.md) |
| SLO and alerting | [docs/SLO_AND_ALERTING.md](docs/SLO_AND_ALERTING.md) |
| Interview demo | [docs/OFFER_DEMO_SCRIPT.md](docs/OFFER_DEMO_SCRIPT.md) |
| Defense Q&A | [docs/OFFER_DEFENSE_QA.md](docs/OFFER_DEFENSE_QA.md) |

## Production Boundary

This repository includes public-data ingestion, training code, API serving, audit logs, monitoring, deployment templates, and governance checks. It intentionally does not include:

- real company IM private messages, appeals, review tickets, or user data;
- a real production Qwen checkpoint;
- a real enterprise gateway, secret rotation system, centralized audit warehouse, or human-review platform;
- a claim that the model is already live in production.

Recommended positioning:

> Production-oriented showcase project, enterprise ML engineering framework, and a review system ready to connect with real business data and a trained checkpoint.

## License

MIT License. See [LICENSE](LICENSE).
