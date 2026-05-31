<div align="center">

# AI-IM-Guard-ML

**面向 IM 私聊风控审核场景的企业级 AI/ML 多证据风险审核框架**

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/API-FastAPI-009688)](https://fastapi.tiangolo.com/)
[![vLLM](https://img.shields.io/badge/Serving-vLLM-7c3aed)](https://github.com/vllm-project/vllm)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

AI-IM-Guard-ML 将聊天语义证据、结构化行为异常、LLM Judge、策略路由、监控告警、版本追踪和审计日志组合成一套完整的机器学习工程链路。

</div>

---

## 项目定位

传统内容安全系统通常只做 `safe / unsafe` 二分类，但在直播、社交、创作者平台和私信安全场景中，业务往往需要更细粒度的判断：

- 风险到底有多严重？
- 是不是已经构成违规？
- 应该忽略、警告、限号，还是进入封禁复核？
- 聊天语义和行为异常之间是否能相互印证？
- 线上如何监控、告警、回滚和样本回流？

AI-IM-Guard-ML 提供的是一套 **可解释、可路由、可监控、可回流** 的 AI 风控审核工程框架，而不是一个简单分类器。

## 核心能力

| 能力 | 说明 |
| --- | --- |
| 多证据融合 | 同时接收审核场景、聊天证据、行为异常证据 |
| LLM Judge | 支持启发式 demo Judge，也支持 Transformers / SFT checkpoint |
| 结构化输出 | 输出风险等级、违规判定、处置建议、关联分析和判定依据 |
| 生产后处理 | JSON 兜底解析、字段校验、冲突修正、策略路由 |
| 数据闭环 | 支持多源数据构造、hard sample refinement、数据质量审计 |
| 评测体系 | 支持 Accuracy、F1、macro-F1、FPR、AUPRC、标注一致性指标 |
| LLMOps | 支持 API 服务、Prometheus 指标、监控摘要、告警规则、版本追踪 |
| 部署模板 | 提供 FastAPI、vLLM、Docker Compose 和环境变量示例 |

## 系统架构

```mermaid
flowchart LR
  A["IM 审核请求"] --> B["行为特征聚合"]
  B --> C["Prompt 渲染"]
  C --> D["LLM / Heuristic Judge"]
  D --> E["JSON 解析"]
  E --> F["生产后处理"]
  F --> G["策略路由"]
  G --> H["审计日志"]
  H --> I["监控告警"]
  I --> J["样本回流"]
```

## 快速开始

本地 demo 不依赖真实微调权重，会使用确定性的启发式 Judge 跑通完整工程链路。

```bash
git clone https://github.com/NickWilde-AI/AI-IM-Guard-ML.git
cd AI-IM-Guard-ML

python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

运行完整示例流程：

```bash
make summary
make predict-route
make eval
make monitor
make alerts
make audit-data
```

你也可以直接使用 CLI：

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

## API 服务

```bash
pip install -e ".[serve]"
im-guard --config configs/default.yaml serve --port 8000
```

接口：

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| `GET` | `/health` | 健康检查 |
| `GET` | `/config` | 当前配置摘要 |
| `POST` | `/judge` | 提交审核样本并返回结构化结论 |
| `GET` | `/metrics` | Prometheus 文本格式指标 |

示例：

```bash
curl http://127.0.0.1:8000/health
curl http://127.0.0.1:8000/metrics
```

## 核心输出结构

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

## 训练与微调

安装训练依赖：

```bash
pip install -e ".[train]"
```

构造训练数据：

```bash
PYTHONPATH=src python3 -m im_guard_ml.build_dataset \
  --internal data/raw/history_tickets.jsonl \
  --internal data/raw/synthetic_cases.jsonl \
  --internal data/raw/refinement_cases.jsonl \
  --public data/raw/public_binary_safety.jsonl \
  --out data/train/im_audit_train.jsonl
```

启动 SFT：

```bash
im-guard --config configs/default.yaml train data/train/im_audit_train.jsonl
```

训练入口支持：

- completion-only SFT
- LoRA / PEFT 配置
- 公开二分类样本保守归一，避免污染重处置标签
- Qwen 风格 chat prompt 渲染

LoRA 可在 `configs/default.yaml` 中开启：

```yaml
training:
  peft:
    enabled: true
    method: lora
    r: 16
    lora_alpha: 32
    lora_dropout: 0.05
```

## vLLM 部署

如果已经有微调后的 checkpoint，可以使用 vLLM 启动模型服务：

```bash
MODEL_PATH=outputs/im-audit-judge \
TP_SIZE=4 \
MAX_MODEL_LEN=8192 \
bash deploy/vllm_serve.sh
```

## 项目结构

```text
.
├── configs/                 # 模型、训练、rubric、告警阈值配置
├── data/samples/            # 示例审核样本
├── deploy/                  # vLLM、Docker Compose、环境变量模板
├── docs/                    # 架构说明与命令手册
├── scripts/                 # 演示脚本
├── src/im_guard_ml/         # 核心 Python 包
├── Makefile
├── pyproject.toml
└── README.md
```

核心模块：

| 模块 | 说明 |
| --- | --- |
| `schema.py` | 标签、枚举、字段一致性校验 |
| `prompting.py` | Prompt 模板和渲染 |
| `training.py` | SFT / LoRA 训练入口 |
| `inference.py` | 启发式 Judge 与 Transformers Judge |
| `parsing.py` | JSON 提取和兜底解析 |
| `postprocess.py` | 生产保护和策略路由 |
| `evaluation.py` | 离线评测指标 |
| `data_audit.py` | 数据质量和泄漏审计 |
| `monitoring.py` | 监控摘要 |
| `alerting.py` | 告警判断 |
| `versioning.py` | 版本追踪和审计日志 |
| `api.py` | FastAPI 服务 |
| `cli.py` | 命令行入口 |

## 生产保护机制

模型输出在本项目中被视为审核建议，而不是不可逆的最终处置。

- JSON 异常会进入兜底解析和策略 fallback。
- `ban_account` 必须满足高风险违规语义。
- 高影响处置会路由到复核链路。
- 每条结果可携带模型、prompt、rubric、特征 schema 和后处理版本。
- 监控和告警用于发现分布漂移、解析异常和处置比例异常。
- 审计日志保留输入摘要和模型决策。

## 文档

- [架构说明](docs/ARCHITECTURE.md)
- [命令手册](docs/COMMANDS.md)
- [部署模板](deploy/)

## 适用场景

- 私信/IM 内容安全审核
- 直播和社交平台风控
- 创作者平台交易和引流治理
- 企业内部 AI 风险审核系统
- LLM Judge 工程化落地

## License

MIT License. See [LICENSE](LICENSE).

