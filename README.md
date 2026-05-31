# AI-IM-Guard-ML

面向 IM 私聊风控审核场景的企业级 AI/ML 多证据风险审核框架。

AI-IM-Guard-ML 是一个面向生产环境设计的内容风险审核工程，适用于直播、社交、创作者平台、私信安全、风控审核等场景。项目将聊天语义证据、结构化行为异常、LLM Judge、策略路由、监控告警、版本追踪和审计日志组合成一套完整的机器学习工程链路。

它解决的问题不是简单的 safe/unsafe 二分类，而是让系统能够输出可解释、可路由、可监控、可回流的结构化审核结论。

## 核心特性

- **多证据融合审核**：同时使用 `audit_scene`、`chat_evidence_list`、`behavior_abnormal_list`。
- **结构化 LLM Judge 输出**：输出风险等级、违规判定、处置建议、关联分析和判定依据。
- **生产级后处理**：校验模型输出、修正字段冲突，并将高影响处置路由到复核链路。
- **SFT 训练入口**：支持 prompt 渲染、completion-only SFT、LoRA 配置和公开二分类数据保守归一。
- **评测与数据质量**：支持分类指标、macro-F1、FPR、AUPRC、标注一致性、数据审计和泄漏检查。
- **LLMOps 能力**：提供 API 服务、Prometheus 风格指标、监控报告、告警规则、版本追踪和审计日志。
- **部署模板**：提供 FastAPI 服务、vLLM 启动脚本、环境变量示例和 Docker Compose 示例。

## 系统链路

```text
IM 审核请求
  -> 行为特征聚合
  -> Prompt 渲染
  -> LLM / 启发式 Judge
  -> JSON 解析
  -> 生产后处理
  -> 策略路由
  -> 审计日志
  -> 监控告警与样本回流
```

## 目录结构

```text
.
├── configs/
│   ├── default.yaml                 # 模型、训练、标签、版本、告警阈值
│   ├── rubrics.yaml                 # 风险主题和分级规则
│   └── experiment_results.yaml      # 模型卡风格的实验元数据
├── data/samples/
│   └── sample_cases.jsonl           # 示例审核样本
├── deploy/
│   ├── audit_service.env.example    # 服务环境变量示例
│   ├── docker-compose.example.yml   # API + vLLM 部署示例
│   └── vllm_serve.sh                # vLLM 服务启动脚本
├── docs/
│   ├── ARCHITECTURE.md              # 企业级架构说明
│   └── COMMANDS.md                  # 常用命令手册
├── src/im_guard_ml/
│   ├── schema.py                    # 标签、枚举、字段一致性校验
│   ├── prompting.py                 # Prompt 模板
│   ├── training.py                  # SFT / LoRA 训练入口
│   ├── inference.py                 # 启发式 Judge 与 Transformers Judge
│   ├── parsing.py                   # JSON 提取和兜底解析
│   ├── postprocess.py               # 生产保护和策略路由
│   ├── evaluation.py                # 离线评测指标
│   ├── refinement.py                # hard sample 回灌
│   ├── data_audit.py                # 数据质量和泄漏审计
│   ├── monitoring.py                # 监控摘要
│   ├── alerting.py                  # 告警判断
│   ├── versioning.py                # 版本追踪和审计日志
│   ├── api.py                       # FastAPI 服务
│   └── cli.py                       # 命令行入口
├── Makefile
├── pyproject.toml
└── README.md
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

运行示例流程：

```bash
make summary
make predict-route
make eval
make monitor
make alerts
make audit-data
```

等价命令：

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

安装服务依赖：

```bash
pip install -e ".[serve]"
```

启动服务：

```bash
im-guard --config configs/default.yaml serve --port 8000
```

接口：

- `GET /health`
- `GET /config`
- `POST /judge`
- `GET /metrics`

示例：

```bash
curl http://127.0.0.1:8000/health
curl http://127.0.0.1:8000/metrics
```

## 训练

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
- LoRA 配置
- 公开二分类样本保守归一
- Qwen 风格 chat prompt 渲染

## vLLM 部署

如果已经有微调后的 checkpoint，可以使用 vLLM 启动模型服务：

```bash
MODEL_PATH=outputs/im-audit-judge \
TP_SIZE=4 \
MAX_MODEL_LEN=8192 \
bash deploy/vllm_serve.sh
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

## License

MIT License. See [LICENSE](LICENSE).

