<div align="center">

# AI-IM-Guard-ML

**面向 IM 私聊风控审核场景的企业级 AI/ML 多证据风险审核框架**

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/API-FastAPI-009688)](https://fastapi.tiangolo.com/)
[![vLLM](https://img.shields.io/badge/Serving-vLLM-7c3aed)](https://github.com/vllm-project/vllm)
[![enterprise-check](https://github.com/NickWilde-AI/AI-IM-Guard-ML/actions/workflows/ci.yml/badge.svg)](https://github.com/NickWilde-AI/AI-IM-Guard-ML/actions/workflows/ci.yml)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

[English](README_EN.md) · [快速开始](#快速开始) · [系统架构](#系统架构) · [训练](#训练) · [企业级验收](#企业级验收) · [文档](#文档)

</div>

---

AI-IM-Guard-ML 是一个面向 IM 私聊安全审核的企业级机器学习工程项目。它把聊天证据、行为信号、LLM Judge 训练、策略路由、审计日志、监控告警、模型治理和部署模板串成一套可运行、可扩展、可接入生产环境的工程系统。

## 为什么做这个项目

很多内容安全系统只做一件事：判断文本是 `safe` 还是 `unsafe`。

真实的 IM 私聊风控要复杂得多。一个可落地的系统需要回答：

- 这段对话是否真的违规；
- 风险严重程度有多高；
- 应该忽略、警告、限流，还是进入封禁复核；
- 聊天语义和行为异常能不能互相印证；
- 这个判断如何审计、监控、回滚和持续改进。

AI-IM-Guard-ML 把这个问题拆成一个结构化、可评审、可复现的工程系统：

```text
IM 审核样本
  -> 聊天证据 + 行为证据
  -> LLM Judge
  -> 结构化风险结论
  -> 后处理保护
  -> 策略路由
  -> 审计 / 指标 / 样本回流
```

这个仓库提供的是一套可以直接启动、继续开发和接入业务数据的 IM 风控审核系统。工程侧已经覆盖数据、训练、评测、API、审计、监控、部署和治理；模型效果侧可以继续接入 GPU 训练环境、私有标注数据和生产 checkpoint。

## 项目亮点

| 能力 | 已实现内容 |
| --- | --- |
| 多证据审核 | 支持聊天文本、场景字段、行为异常和结构化标签 |
| LLM Judge | 支持本地规则基线 Judge，也支持 Transformers/SFT checkpoint 路径 |
| 训练链路 | completion-only SFT、LoRA/PEFT 配置、公开数据字段级 loss mask |
| 数据治理 | XGuard 公开数据接入、保守标签映射、数据拆分和质量审计 |
| 决策安全 | JSON 兜底解析、标签校验、强处置保护、策略路由 |
| API 服务 | FastAPI、request_id、Token/RBAC、CORS、限流、请求大小限制 |
| 审计追踪 | JSONL/SQLite 审计后端、ticket 查询、版本化决策记录 |
| 监控告警 | Prometheus 指标、漂移报告、滑动窗口告警、SLO 文档 |
| 模型治理 | 模型注册表、晋级红线、回滚目标、审批元数据 |
| 交付门禁 | `make enterprise-check`、OpenAPI 契约、preflight、readiness、CI |

## 当前状态

| 阶段 | 状态 | 说明 |
| --- | --- | --- |
| 工程框架 | 已完成 | CLI、API、数据、训练、评测、监控、审计、部署、CI 已串联 |
| 完整训练链路 | 已跑通 | fast-full 配置已跑完整训练集，并在本地保存 checkpoint |
| 中文模型效果 | 待增强 | 需要 GPU 或长时间 MPS 训练，形成 Qwen 效果实验 |
| 生产接入 | 可扩展 | 接入私有数据、训练 checkpoint 和企业基础设施后可进入生产化落地 |

最近一次本地完整训练链路：

| 项目 | 结果 |
| --- | --- |
| 配置 | `configs/local_fast_full_train.yaml` |
| 数据 | `data/train/xguard_splits/train.jsonl` |
| 步数 | `4962 / 4962` |
| 耗时 | 约 20 分钟 |
| 最终 train loss | `10.26` |
| 本地产物 | `outputs/im-audit-judge-fast-full` |

这次 fast-full 训练使用 `sshleifer/tiny-gpt2`，用于证明训练工程链路可执行。它不是中文 IM 风控质量模型。真正的模型效果需要使用 Qwen LoRA/GPU 训练，并报告离线评测指标。

## 系统架构

为了避免 GitHub 上 Mermaid 图出现额外缩放控件，README 使用稳定的文本架构说明。更详细的系统设计见 [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)。

```text
审核请求
  -> 证据构建：聚合聊天、行为、场景信息
  -> Prompt/Feature 渲染：转换成模型可理解的输入
  -> LLM Judge：输出结构化审核 JSON
  -> JSON 解析：提取并修复模型输出
  -> 后处理保护：校验标签、保护强处置
  -> 策略路由：自动关闭、自动警告、策略动作或人审复核
  -> 审计与监控：记录 request_id、版本、指标和告警
  -> 样本回流：把误判和灰区样本用于下一轮训练
```

核心层级：

- **接入层**：请求处理、CLI、schema 校验。关键文件：`api.py`, `cli.py`, `schema.py`
- **证据层**：聊天和行为证据渲染。关键文件：`prompting.py`, `data_audit.py`
- **模型层**：本地规则基线、SFT 训练、checkpoint 推理。关键文件：`inference.py`, `training.py`
- **决策层**：JSON 修复、标签校验、动作路由。关键文件：`parsing.py`, `postprocess.py`
- **治理层**：版本、审计、监控、模型注册。关键文件：`versioning.py`, `audit_store.py`, `monitoring.py`, `model_registry.py`
- **闭环层**：离线评测和 hard case 回流。关键文件：`evaluation.py`, `refinement.py`

## 快速开始

本地快速启动不需要 GPU，也不需要微调 checkpoint。系统会使用确定性的本地规则基线 Judge 跑通完整工程链路，便于开发者立即验证 API、路由、审计、监控和评测流程。

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

启动 API：

```bash
PYTHONPATH=src im-guard --config configs/default.yaml serve --port 8000
```

提交审核请求：

```bash
curl -X POST http://127.0.0.1:8000/judge \
  -H "Content-Type: application/json" \
  -H "X-Request-ID: local-run-1" \
  -d '{
    "ticket_id": "local-run-1",
    "chat_evidence_list": ["加微信稳赚，带你投资。"],
    "behavior_abnormal_list": ["短时间高频私聊。"]
  }'
```

查看服务指标：

```bash
curl http://127.0.0.1:8000/metrics
```

## 输出协议

Judge 输出的是结构化审核结论，而不是单个二分类标签：

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

高影响动作会被视为审核建议，而不是不可逆的最终处置。系统包含后处理保护和策略路由，避免模型输出被无脑执行。

## 训练

安装训练依赖：

```bash
pip install -e ".[train]"
```

训练前检查：

```bash
LC_ALL=en_US.UTF-8 LANG=en_US.UTF-8 \
PYTHONPATH=src im-guard --config configs/default.yaml \
  train-readiness data/train/xguard_splits/train.jsonl \
  --out outputs/training_readiness.json
```

快速跑完整训练链路：

```bash
LC_ALL=en_US.UTF-8 LANG=en_US.UTF-8 \
PYTHONPATH=src im-guard --config configs/local_fast_full_train.yaml \
  train data/train/xguard_splits/train.jsonl
```

Mac MPS 上跑 Qwen LoRA：

```bash
LC_ALL=en_US.UTF-8 LANG=en_US.UTF-8 \
PYTHONPATH=src im-guard --config configs/local_mps_train.yaml \
  train data/train/xguard_splits/train.jsonl
```

GPU 上跑 Qwen 效果训练：

```bash
LC_ALL=en_US.UTF-8 LANG=en_US.UTF-8 \
PYTHONPATH=src im-guard --config configs/default.yaml \
  train data/train/xguard_splits/train.jsonl
```

训练设计：

- completion-only SFT：只对 assistant JSON 输出算 loss，不让模型背用户输入；
- 公开数据字段 mask：公开二分类安全数据不训练 `risk_level` 和 `handling_suggestion`；
- 保守公开标签：公开违规样本最多映射到 `mid_risk / warning`；
- LoRA/PEFT：通过 YAML 配置开启；
- Qwen 风格 prompt：训练和推理使用一致的 prompt 渲染路径。

## 模型效果路线

工程链路已经跑通。下一步重点是模型效果，而不是继续堆功能。

| 步骤 | 目标 |
| --- | --- |
| 准备 GPU | 小模型 LoRA 建议至少 24GB 显存，7B 实验更建议 48GB/80GB |
| 固定验证集 | 保留稳定 `val/test`，避免指标被训练集污染 |
| 训练 Qwen checkpoint | 使用 `Qwen/Qwen2.5-7B-Instruct` 或更小的 Qwen LoRA baseline |
| 严格评测 | 报告 `final_judgment F1`、`risk_level macro-F1`、`handling macro-F1`、`ban_account FPR` |
| 误判分析 | 重点看误封、漏召、强处置误判和 `mid_risk` 灰区 |
| 回灌 hard cases | 把错误样本整理成 refinement 数据，再进入下一轮训练 |

公开 XGuard 数据适合补安全识别覆盖。`limit_account` 和 `ban_account` 这类强处置标签，应该来自人工审核过的 IM 类样本，而不是直接来自公开二分类数据。

## 企业级验收

运行完整本地门禁：

```bash
make enterprise-check
```

门禁覆盖单元测试、源码编译、OpenAPI 契约、生产配置 preflight、模型注册表、交付摘要和 readiness 检查。

最近一次本地结果：

```text
143 passed, 1 warning
```

GitHub Actions 会在 push 和 pull request 时运行同一套企业级门禁。

## 项目结构

```text
.
├── configs/                 # 模型、训练、注册表、灰度配置
├── data/samples/            # 小规模样例审核数据
├── deploy/                  # Docker、vLLM、环境变量和部署示例
├── docs/                    # 架构、运维、训练、治理文档
├── scripts/                 # 数据下载和 API 压测脚本
├── src/im_guard_ml/         # 核心 Python 包
├── tests/                   # 单测、契约、readiness、治理测试
├── Makefile
├── pyproject.toml
└── README.md
```

## 文档

| 需求 | 入口 |
| --- | --- |
| 项目地图 | [docs/PROJECT_INDEX.md](docs/PROJECT_INDEX.md) |
| 架构说明 | [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) |
| 命令手册 | [docs/COMMANDS.md](docs/COMMANDS.md) |
| API 使用 | [docs/API_USAGE.md](docs/API_USAGE.md) |
| 训练与评测 | [docs/TRAINING_AND_EVALUATION.md](docs/TRAINING_AND_EVALUATION.md) |
| 公开数据集 | [docs/PUBLIC_DATASET_XGUARD.md](docs/PUBLIC_DATASET_XGUARD.md) |
| 生产化评审 | [docs/ENTERPRISE_READINESS_REVIEW.md](docs/ENTERPRISE_READINESS_REVIEW.md) |
| 部署与运维 | [docs/DEPLOYMENT_AND_OPERATIONS.md](docs/DEPLOYMENT_AND_OPERATIONS.md) |
| SLO 与告警 | [docs/SLO_AND_ALERTING.md](docs/SLO_AND_ALERTING.md) |
| 模型治理 | [docs/MODEL_GOVERNANCE_PLAYBOOK.md](docs/MODEL_GOVERNANCE_PLAYBOOK.md) |

## 生产接入说明

这个仓库包含公开数据接入、训练代码、API 服务、审计日志、监控、部署模板和治理检查。进入真实业务环境时，通常需要接入或替换：

- 私有 IM 标注数据、申诉数据、人审工单和线上反馈样本；
- 经过正式训练和评测的 Qwen 或同级模型 checkpoint；
- 企业网关、密钥轮换系统、集中审计仓库和人审平台；
- 线上灰度、A/B 实验、回滚和持续监控流程。

推荐对外定位：

> 面向企业级开发的 IM 风控审核系统工程框架，可直接本地启动，也可以接入真实业务数据、训练 checkpoint 和生产基础设施继续落地。

## License

MIT License. See [LICENSE](LICENSE).
