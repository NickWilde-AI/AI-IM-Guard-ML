# AI-IM-Guard-ML Architecture

AI-IM-Guard-ML is a production-oriented AI/ML auditing framework for private-message risk moderation. It is organized around a clear separation of model judgment, output validation, business routing, observability, and feedback loops.

## Design Goals

- Combine semantic chat evidence and structured behavior evidence.
- Produce machine-readable audit decisions.
- Keep high-impact actions behind production guardrails.
- Support offline evaluation, monitoring, alerting, and audit logs.
- Provide a path from heuristic local demo to fine-tuned checkpoint deployment.

## Data Flow

```text
audit request
  -> schema validation
  -> prompt rendering
  -> judge inference
  -> JSON parsing
  -> post-processing
  -> policy routing
  -> versioned audit log
  -> monitoring / alerting
```

## Main Components

| Component | File | Responsibility |
| --- | --- | --- |
| Schema | `src/im_guard_ml/schema.py` | labels, enum values, consistency checks |
| Prompting | `src/im_guard_ml/prompting.py` | audit prompt and chat template rendering |
| Training | `src/im_guard_ml/training.py` | SFT and LoRA training entrypoint |
| Inference | `src/im_guard_ml/inference.py` | heuristic demo judge and Transformers judge |
| Parsing | `src/im_guard_ml/parsing.py` | JSON extraction and fallback parsing |
| Postprocess | `src/im_guard_ml/postprocess.py` | production guardrails and route selection |
| Evaluation | `src/im_guard_ml/evaluation.py` | classification and agreement metrics |
| Data Audit | `src/im_guard_ml/data_audit.py` | dataset quality and leakage checks |
| Monitoring | `src/im_guard_ml/monitoring.py` | prediction and input distribution reports |
| Alerting | `src/im_guard_ml/alerting.py` | pass/warn/critical alert evaluation |
| Versioning | `src/im_guard_ml/versioning.py` | model/prompt/rubric/postprocess version metadata |
| API | `src/im_guard_ml/api.py` | FastAPI service and Prometheus metrics |

## Training Strategy

The training path is designed for completion-only supervised fine-tuning. Public binary-only safety data is normalized conservatively so that it does not teach heavy business handling labels such as `limit_account` or `ban_account`.

LoRA can be enabled from `configs/default.yaml`:

```yaml
training:
  peft:
    enabled: true
    method: lora
    r: 16
    lora_alpha: 32
    lora_dropout: 0.05
```

## Deployment Strategy

The recommended production deployment separates:

- **Judge service**: vLLM-backed model inference.
- **Audit API service**: prompt rendering, parsing, postprocess, routing, logging, metrics.

The repository includes:

- `deploy/vllm_serve.sh`
- `deploy/audit_service.env.example`
- `deploy/docker-compose.example.yml`

## Observability

The API exposes Prometheus-compatible metrics:

```text
im_guard_requests_total
im_guard_ban_total
im_guard_parse_non_ok_total
```

For offline monitoring reports, use:

```bash
im-guard monitor outputs/demo_routed_predictions.jsonl
im-guard alerts outputs/demo_routed_predictions.jsonl
```

## Safety Boundary

The framework intentionally treats the model as a decision-support component. High-impact actions should be reviewed by policy systems or human reviewers before enforcement.

