# 项目交付总报告

这份报告用于快速确认当前仓库已经交付了什么。它不是新的学习材料，而是最终交付清单。

## 1. 交付目标

把“多证据融合的直播平台 IM 私聊违规审核模型”从文档描述落成一个面试可讲、工程可展示、生产链路完整的项目包。

当前项目覆盖：

- 业务背景和从 0 到 1 架构。
- 输入输出协议和 schema。
- prompt 渲染、训练入口、推理入口。
- JSON 解析、后处理、策略路由。
- 数据构造、数据审计、refinement。
- 训练评测闭环、评测报告、监控、滑动窗口异常检测、drift 检测、告警。
- 版本追踪、审计日志。
- vLLM 部署、Docker、Compose、K8s、服务配置、灰度和事故 runbook。
- API 使用说明、鉴权、最小 RBAC、SQLite 审计、脱敏摘要和 SLO/Prometheus 告警。
- 机器可读 readiness-check，检查交付物、忽略规则和本机公开数据状态。
- GitHub Actions 企业验收门禁，自动运行测试、编译、交付摘要和 readiness-check。
- OpenAPI 契约导出与关键接口缺失检查，防止核心 API 被误删或改名。
- 模型卡、实验报告、rubric、标注规范。
- 简历 bullet、面试叙事、深挖问答、自检清单。

## 2. 代码交付

核心包：`src/im_guard_ml`

| 文件 | 交付内容 |
| --- | --- |
| `schema.py` | 审核输入输出协议、枚举、标签一致性校验 |
| `prompting.py` | prompt 模板、训练/推理渲染 |
| `training.py` | Qwen SFT 训练入口，completion-only loss |
| `inference.py` | 启发式 demo Judge 与 Transformers Judge |
| `parsing.py` | JSON 截取、解析、正则兜底 |
| `postprocess.py` | 生产后处理、冲突修正、策略路由 |
| `evaluation.py` | 二分类、多分类、AUPRC、一致性指标 |
| `refinement.py` | hard sample committee 回灌 |
| `build_dataset.py` | 多源训练数据构造 |
| `data_audit.py` | 数据质量、重复、泄漏审计 |
| `monitoring.py` | 线上预测分布、滑动窗口异常检测和输入漂移报告 |
| `drift_detection.py` | PSI、卡方、KS 漂移检测 |
| `alerting.py` | 告警阈值判定，输出 pass/warn/critical |
| `versioning.py` | model/prompt/rubric/schema/postprocess 版本追踪 |
| `audit_store.py` | JSONL/SQLite 审计持久化 |
| `auth.py` | Bearer token 和最小角色权限 |
| `privacy.py` | 输入摘要和 PII 脱敏 |
| `reporting.py` | 离线评测报告、交付摘要和 readiness-check |
| `api.py` | FastAPI 服务入口 |
| `api_contract.py` | OpenAPI 契约导出和关键接口校验 |
| `cli.py` | 命令行总入口 |

## 3. 配置与样例

| 文件 | 交付内容 |
| --- | --- |
| `configs/default.yaml` | 默认模型、训练、标签、rubric、版本、告警阈值 |
| `configs/rubrics.yaml` | 11 类违规主题 low/mid/high rubric |
| `configs/experiment_results.yaml` | 机器可读模型卡和实验指标 |
| `data/samples/sample_cases.jsonl` | 可演示样例数据 |
| `pyproject.toml` | Python 包与可选依赖配置 |
| `Makefile` | 常用命令快捷入口 |
| `.github/workflows/ci.yml` | GitHub Actions 企业验收门禁 |

## 4. 部署交付

| 文件 | 交付内容 |
| --- | --- |
| `deploy/vllm_serve.sh` | vLLM OpenAI-compatible 服务启动脚本 |
| `deploy/Dockerfile` | API 服务镜像构建 |
| `deploy/audit_service.env.example` | 审核服务环境变量示例 |
| `deploy/audit_service.prod.env.example` | 生产化环境变量示例 |
| `deploy/docker-compose.example.yml` | API 服务和 vLLM 服务编排示例 |
| `deploy/k8s/` | K8s 部署模板 |
| `deploy/prometheus/im_guard_alerts.yaml` | Prometheus 告警规则模板 |

## 5. 文档交付

| 文件 | 用途 |
| --- | --- |
| `PROJECT_INDEX.md` | 项目总入口和复习路线 |
| `PROJECT_FROM_ZERO_TO_ONE.md` | 从业务到上线的完整理解 |
| `PRODUCTION_SYSTEM_DESIGN.md` | 生产系统架构、接口、路由、监控 |
| `RUBRIC_AND_LABELING_GUIDE.md` | 业务 taxonomy、rubric、标注规范 |
| `MODEL_CARD_AND_EXPERIMENT_REPORT.md` | 模型卡、指标、消融、上线红线 |
| `TRAINING_AND_EVALUATION.md` | 数据构建、训练、预测、评测报告和上线前检查 |
| `DEPLOYMENT_AND_OPERATIONS.md` | 部署、灰度、回滚、容量估算 |
| `API_USAGE.md` | API 接口、鉴权、错误码、审计查询和压测 |
| `DATA_QUALITY_AND_AUDIT.md` | 数据质量、标签冲突、泄漏审计 |
| `INCIDENT_RUNBOOK.md` | 线上事故止血、排查和复盘 |
| `COMMANDS.md` | 命令手册 |
| `DEEP_DIVE_QA.md` | 高频深挖问题回答 |
| `INTERVIEW_PLAYBOOK.md` | 30 秒/2 分钟讲法和架构图 |
| `FINAL_INTERVIEW_CHECKLIST.md` | 面试前最终自检 |
| `RESUME_AND_STORYLINE.md` | 简历 bullet、STAR、1/3/5 分钟叙事 |
| `DELIVERY_REPORT.md` | 当前交付清单 |

## 6. 面试主线

推荐主线：

```text
业务痛点
  -> 输入输出协议
  -> 违规 taxonomy 和标注体系
  -> 多源数据构造
  -> Qwen3.5-27B completion-only 多任务 SFT
  -> 消融和核心指标
  -> vLLM 部署与后处理路由
  -> 监控、告警、人审、回流
```

一句话收束：

这个项目不是普通文本分类器，而是把 IM 私聊风控做成了一个可解释、可路由、可灰度、可回流的多证据业务审核系统。

## 7. 当前边界

当前仓库不包含真实公司内部数据、真实 Qwen checkpoint 或线上规则引擎服务。对应位置已经用接口、配置、样例、demo Judge 和部署脚本预留。面试场景下，重点是展示完整工程设计和生产落地能力，而不是现场训练 27B 模型。

## 8. 交付验收命令

```bash
LC_ALL=en_US.UTF-8 LANG=en_US.UTF-8 make enterprise-check
PYTHONPATH=src python3 -m im_guard_ml.cli readiness-check --project-root . --out outputs/readiness_check.json
```

`readiness-check` 输出 JSON，核心交付物缺失为 `fail`，本机未下载公开大数据为 `warn`。大数据目录已在 `.gitignore` 中忽略，不应提交到 git。
