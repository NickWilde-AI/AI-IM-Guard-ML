# AI-IM-Guard-ML

Enterprise-grade AI/ML risk auditing framework for IM private-chat moderation.

AI-IM-Guard-ML is a production-oriented reference implementation for multi-evidence content-risk auditing. It combines chat semantics, structured user-behavior signals, model judgment, policy routing, monitoring, alerting, and audit logging into one coherent ML engineering workflow.

The project is designed for scenarios such as live-streaming, social networking, creator platforms, and private-message safety systems where a binary safe/unsafe classifier is not enough.

## Highlights

- **Multi-evidence risk judgment**: combines `audit_scene`, `chat_evidence_list`, and `behavior_abnormal_list`.
- **Structured LLM Judge output**: produces `risk_level`, `final_judgment`, `handling_suggestion`, `correlation_analysis`, and `judgment_basis`.
- **Production-safe post-processing**: validates model output, corrects unsafe conflicts, and routes high-impact actions to review.
- **SFT-ready training pipeline**: includes prompt rendering, completion-only SFT entrypoint, LoRA configuration, and public-binary data normalization.
- **Evaluation and data quality**: supports classification metrics, macro-F1, FPR, AUPRC, annotation agreement, data audit, and leakage checks.
- **LLMOps workflow**: includes API service, Prometheus-style metrics, monitoring reports, alert rules, version tracing, and audit logs.
- **Deployment templates**: includes FastAPI service, vLLM serving script, environment example, and Docker Compose example.

## System Overview

```text
Raw IM evidence
  -> behavior aggregation
  -> prompt rendering
  -> LLM / heuristic judge
  -> JSON parsing
  -> post-processing
  -> policy routing
  -> audit logging
  -> monitoring and feedback
```

## Repository Layout

```text
.
├── configs/
│   ├── default.yaml                 # model, training, labels, versions, alert thresholds
│   ├── rubrics.yaml                 # risk taxonomy and rubric definitions
│   └── experiment_results.yaml      # model-card style experiment metadata
├── data/samples/
│   └── sample_cases.jsonl           # demo audit cases
├── deploy/
│   ├── audit_service.env.example    # service environment variables
│   ├── docker-compose.example.yml   # API + vLLM deployment example
│   └── vllm_serve.sh                # vLLM OpenAI-compatible server launcher
├── docs/
│   └── ARCHITECTURE.md              # enterprise architecture and workflow
├── src/im_guard_ml/
│   ├── schema.py                    # labels, schema, validation
│   ├── prompting.py                 # prompt templates
│   ├── training.py                  # SFT / LoRA training entrypoint
│   ├── inference.py                 # heuristic and Transformers judges
│   ├── parsing.py                   # JSON extraction and fallback parsing
│   ├── postprocess.py               # production guardrails and policy routing
│   ├── evaluation.py                # offline evaluation metrics
│   ├── refinement.py                # hard-sample refinement loop
│   ├── data_audit.py                # data quality and leakage audit
│   ├── monitoring.py                # monitoring summaries
│   ├── alerting.py                  # alert threshold evaluation
│   ├── versioning.py                # version metadata and audit logs
│   ├── api.py                       # FastAPI application
│   └── cli.py                       # command-line interface
├── Makefile
├── pyproject.toml
└── README.md
```

## Quick Start

The demo path works without a fine-tuned checkpoint. It uses a deterministic heuristic judge to exercise the full engineering workflow.

```bash
git clone https://github.com/NickWilde-AI/AI-IM-Guard-ML.git
cd AI-IM-Guard-ML

python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

Run the sample workflow:

```bash
make summary
make predict-route
make eval
make monitor
make alerts
make audit-data
```

Equivalent raw commands:

```bash
PYTHONPATH=src python3 -m im_guard_ml.cli --config configs/default.yaml summary data/samples/sample_cases.jsonl

PYTHONPATH=src python3 -m im_guard_ml.cli --config configs/default.yaml predict data/samples/sample_cases.jsonl \
  --with-route \
  --with-version \
  --audit-log-out outputs/demo_audit_logs.jsonl \
  --out outputs/demo_routed_predictions.jsonl

PYTHONPATH=src python3 -m im_guard_ml.cli --config configs/default.yaml monitor outputs/demo_routed_predictions.jsonl
PYTHONPATH=src python3 -m im_guard_ml.cli --config configs/default.yaml alerts outputs/demo_routed_predictions.jsonl
PYTHONPATH=src python3 -m im_guard_ml.cli --config configs/default.yaml audit-data data/samples/sample_cases.jsonl
```

## API Service

Install service dependencies:

```bash
pip install -e ".[serve]"
```

Start the API:

```bash
im-guard --config configs/default.yaml serve --port 8000
```

Endpoints:

- `GET /health`
- `GET /config`
- `POST /judge`
- `GET /metrics`

Example:

```bash
curl http://127.0.0.1:8000/health
curl http://127.0.0.1:8000/metrics
```

## Training

Install training dependencies:

```bash
pip install -e ".[train]"
```

Build a training dataset from internal and public sources:

```bash
PYTHONPATH=src python3 -m im_guard_ml.build_dataset \
  --internal data/raw/history_tickets.jsonl \
  --internal data/raw/synthetic_cases.jsonl \
  --internal data/raw/refinement_cases.jsonl \
  --public data/raw/public_binary_safety.jsonl \
  --out data/train/im_audit_train.jsonl
```

Run SFT:

```bash
im-guard --config configs/default.yaml train data/train/im_audit_train.jsonl
```

The training entrypoint supports:

- completion-only SFT
- LoRA configuration through `configs/default.yaml`
- conservative normalization for public binary-only samples
- Qwen-style chat prompt rendering

## Serving With vLLM

For GPU deployments with a fine-tuned checkpoint:

```bash
MODEL_PATH=outputs/im-audit-judge \
TP_SIZE=4 \
MAX_MODEL_LEN=8192 \
bash deploy/vllm_serve.sh
```

## Core Output Schema

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

## Production Guardrails

The project treats model output as a recommendation, not an irreversible enforcement action.

- invalid JSON falls back to safe parsing and policy fallback
- `ban_account` requires high-risk violation semantics
- high-impact actions are routed to review
- versions are attached to each result
- monitoring and alerting detect distribution shifts
- audit logs retain input summaries and model decisions

## Documentation

- [Architecture](docs/ARCHITECTURE.md)
- [Commands](docs/COMMANDS.md)
- [Deployment Templates](deploy/)

## License

MIT License. See [LICENSE](LICENSE).

