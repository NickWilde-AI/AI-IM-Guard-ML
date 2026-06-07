<div align="center">

# AI-IM-Guard-ML

**面向 IM 私聊风控审核场景的企业级 AI/ML 多证据风险审核框架**

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/API-FastAPI-009688)](https://fastapi.tiangolo.com/)
[![vLLM](https://img.shields.io/badge/Serving-vLLM-7c3aed)](https://github.com/vllm-project/vllm)
[![enterprise-check](https://github.com/NickWilde-AI/AI-IM-Guard-ML/actions/workflows/ci.yml/badge.svg)](https://github.com/NickWilde-AI/AI-IM-Guard-ML/actions/workflows/ci.yml)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

AI-IM-Guard-ML 将聊天语义证据、结构化行为异常、LLM Judge、策略路由、监控告警、版本追踪和审计日志组合成一套完整的机器学习工程链路。

</div>

---

## 这个项目能证明什么

这是一个面向 **LLM 风控审核工程岗位** 的生产化展示项目。它重点证明的不是“我会调一个文本分类模型”，而是：

- 能把模糊的 IM 私聊风控问题拆成可训练、可评测、可上线的多任务审核系统。
- 能设计 `risk_level / final_judgment / handling_suggestion` 三层输出，支撑 warning、limit、ban、人审复核等差异化处置。
- 能把公开安全数据、业务样例、合成样本、hard case 回流接成数据闭环，并避免公开二分类数据污染强处置标签。
- 能把 LLM Judge 接入 API、安全、审计、监控、告警、灰度、回滚和部署模板，而不是停留在 notebook。
- 能清楚说明当前仓库的边界：它是生产化展示工程，不声称包含真实公司私聊数据、真实线上 checkpoint 或真实人审平台。

适合用于：

- LLM 应用工程 / 机器学习平台 / 风控算法工程岗位面试。
- 展示从业务建模、数据治理、SFT、评测到 API 部署的完整工程能力。
- 作为“企业级 AI 审核系统”项目作品集，而不是简单 demo。

## 企业级评审速览

如果你是招聘方或代码评审者，可以先看这张表。它把“项目声称具备的能力”和“仓库里能核验的证据”对应起来，避免只停留在口头描述。

| 评审维度 | 已落地证据 | 入口 |
| --- | --- | --- |
| 数据治理 | XGuard 公开数据接入、标签保守映射、train/val/test 拆分、质量审计 | [PUBLIC_DATASET_XGUARD.md](docs/PUBLIC_DATASET_XGUARD.md)、[DATA_QUALITY_AND_AUDIT.md](docs/DATA_QUALITY_AND_AUDIT.md) |
| 训练评测 | completion-only SFT 入口、离线评测报告、模型卡、实验记录 | [TRAINING_AND_EVALUATION.md](docs/TRAINING_AND_EVALUATION.md)、[MODEL_CARD_AND_EXPERIMENT_REPORT.md](docs/MODEL_CARD_AND_EXPERIMENT_REPORT.md) |
| API 安全 | Bearer Token/RBAC、限流、请求大小限制、CORS、结构化错误 | [API_USAGE.md](docs/API_USAGE.md)、`src/im_guard_ml/api.py` |
| 审计追踪 | request_id、输入摘要、JSONL/SQLite 持久化、ticket 查询 | `src/im_guard_ml/audit_store.py`、[API_USAGE.md](docs/API_USAGE.md) |
| 监控告警 | Prometheus 指标、滑动窗口异常、drift 检测、告警规则 | [SLO_AND_ALERTING.md](docs/SLO_AND_ALERTING.md)、`deploy/prometheus/im_guard_alerts.yaml` |
| 模型治理 | model registry、stable/candidate、审批字段、指标红线、回滚目标 | `configs/model_registry.yaml`、`src/im_guard_ml/model_registry.py` |
| 部署运维 | Docker Compose、K8s 模板、vLLM/API 两条路径、事故 runbook | [DEPLOYMENT_AND_OPERATIONS.md](docs/DEPLOYMENT_AND_OPERATIONS.md)、[INCIDENT_RUNBOOK.md](docs/INCIDENT_RUNBOOK.md) |
| 自动验收 | `enterprise-check`、readiness-check、OpenAPI contract、production preflight | [GitHub Actions](https://github.com/NickWilde-AI/AI-IM-Guard-ML/actions/workflows/ci.yml)、[COMMANDS.md](docs/COMMANDS.md) |

当前 `main` 分支的企业级验收门禁会在 GitHub Actions 中自动运行。它覆盖测试、源码编译、交付物完整性、API 契约、生产配置 preflight 和模型注册表检查。

## 面试官优先看哪里

如果只有 10 分钟评审这个仓库，建议按这个顺序：

1. 先看 [PROJECT_INDEX.md](docs/PROJECT_INDEX.md)，建立项目全貌和复习路线。
2. 再看 [DELIVERY_REPORT.md](docs/DELIVERY_REPORT.md)，确认交付项不是零散堆叠。
3. 运行 `make enterprise-check`，核验测试、契约、preflight 和 readiness。
4. 看 [OFFER_DEMO_SCRIPT.md](docs/OFFER_DEMO_SCRIPT.md)，理解 5 分钟现场演示如何讲。
5. 看 [OFFER_DEFENSE_QA.md](docs/OFFER_DEFENSE_QA.md)，检查项目边界、真实数据和生产落地追问。

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

## 5 分钟演示路线

本地 demo 不依赖 GPU 或真实微调权重，会使用确定性的启发式 Judge 跑通工程闭环。

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev,serve]"

make predict-route
make eval-report
make window-alerts
make drift-report
make readiness-check
```

如果要展示 API：

```bash
PYTHONPATH=src im-guard --config configs/default.yaml serve --port 8000
```

另开一个终端：

```bash
curl -X POST http://127.0.0.1:8000/judge \
  -H "Content-Type: application/json" \
  -H "X-Request-ID: interview-demo-1" \
  -d '{"ticket_id":"interview-demo-1","chat_evidence_list":["加微信稳赚，带你投资。"],"behavior_abnormal_list":["短时间高频私聊。"]}'

curl http://127.0.0.1:8000/metrics
```

完整 API、训练和部署说明见：

- [API_USAGE.md](docs/API_USAGE.md)
- [TRAINING_AND_EVALUATION.md](docs/TRAINING_AND_EVALUATION.md)
- [DEPLOYMENT_AND_OPERATIONS.md](docs/DEPLOYMENT_AND_OPERATIONS.md)
- [ENTERPRISE_READINESS_REVIEW.md](docs/ENTERPRISE_READINESS_REVIEW.md)

GitHub Actions 会在 push 和 pull request 时运行 `make enterprise-check`，覆盖单元测试、源码编译、交付摘要和 readiness-check。公开大数据文件仍只保留在本地忽略目录，不进入 CI 和 git。

## 系统架构

AI-IM-Guard-ML 按照真实生产系统的职责边界拆分为 **接入层、证据层、模型层、决策层、治理层、数据闭环层**。模型只负责给出可解释的审核建议，最终处置会经过规则保护、策略路由、审计记录和监控告警。

| 层级 | 核心职责 | 关键模块 |
| --- | --- | --- |
| 接入层 | 接收 IM 审核请求，统一输入字段和业务场景 | `api.py`、`cli.py`、`schema.py` |
| 证据层 | 聚合聊天语义、用户行为、历史特征和场景信息 | `prompting.py`、`data_audit.py` |
| 模型层 | 使用 LLM Judge 输出结构化风险判断，也支持本地启发式 demo | `inference.py`、`training.py` |
| 决策层 | 解析 JSON、修正冲突字段、执行策略路由和处置保护 | `parsing.py`、`postprocess.py` |
| 治理层 | 记录版本、审计日志、指标摘要、Prometheus 指标和告警结果 | `versioning.py`、`monitoring.py`、`alerting.py` |
| 闭环层 | 将误判、难例、人工复核结果回流到数据集和评测集 | `refinement.py`、`evaluation.py` |

核心链路：

```text
审核请求
  -> 多源证据聚合
  -> Prompt / Feature 组装
  -> LLM Judge 推理
  -> 结构化结果解析
  -> 生产后处理
  -> 策略路由
  -> 审计与监控
  -> 样本回流
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
- [项目总索引](docs/PROJECT_INDEX.md)
- [Offer 面试演示脚本](docs/OFFER_DEMO_SCRIPT.md)
- [Offer 高压答辩 Q&A](docs/OFFER_DEFENSE_QA.md)
- [面试口语实战稿](docs/INTERVIEW_SPEAKING_SCRIPT.md)
- [面试讲解手册](docs/INTERVIEW_PLAYBOOK.md)
- [简历与叙事稿](docs/RESUME_AND_STORYLINE.md)
- [部署模板](deploy/)

## 真实性边界

当前仓库包含公开数据接入、训练入口、服务化 API、审计、监控、部署和文档体系；同时保留启发式 Judge，方便在没有 GPU 和真实 checkpoint 的环境下演示完整链路。

它不包含：

- 真实公司内部 IM 私聊、人审、申诉和客诉数据。
- 真实生产训练出的 Qwen checkpoint。
- 真实企业网关、密钥轮换、集中审计库、模型注册和线上 A/B 平台。

因此，对外建议表述为：**“生产化展示项目 / 企业级工程骨架 / 可接入真实业务数据和 checkpoint 的审核系统”**，而不是“已经真实生产上线的系统”。

## 适用场景

- 私信/IM 内容安全审核
- 直播和社交平台风控
- 创作者平台交易和引流治理
- 企业内部 AI 风险审核系统
- LLM Judge 工程化落地

## License

MIT License. See [LICENSE](LICENSE).
