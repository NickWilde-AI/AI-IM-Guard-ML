# 原始文档 Coverage Matrix

这份文档用于回答：原始两份材料 `违规审核模型.md` 和 `违规审核模型_QA.md` 里的内容，当前工程是否已经覆盖。这里不做 86 个 QA 的逐条搬运，而是按面试/工程主题做高层映射。

结论：当前项目的大方向和架构是正确的，核心内容已经覆盖。少数内容属于真实生产资源或高级训练实验，在仓库里以接口、配置、文档方案或预留入口体现，不需要在面试 demo 里真实跑通。

## 1. Coverage 总览

| 原始主题 | 当前覆盖程度 | 当前位置 | 说明 |
| --- | --- | --- | --- |
| 项目背景、业务痛点 | 已覆盖 | `PROJECT_FROM_ZERO_TO_ONE.md`, `INTERVIEW_PLAYBOOK.md`, `RESUME_AND_STORYLINE.md` | 文本二分类不足、行为证据融合、差异化处置都已覆盖。 |
| 个人职责与项目边界 | 已覆盖 | `RESUME_AND_STORYLINE.md`, `DELIVERY_REPORT.md` | 已整理成简历 bullet、STAR 和交付清单。 |
| 11 类主题、47 子主题、rubric | 已覆盖 | `RUBRIC_AND_LABELING_GUIDE.md`, `configs/rubrics.yaml` | 当前用 11 类主题和代表性子主题实现，不逐字展开全部 47 段，但面试足够。 |
| 输入协议 `audit_scene/chat_evidence/behavior_abnormal` | 已覆盖 | `schema.py`, `prompting.py`, `sample_cases.jsonl` | 代码和样例都已体现。 |
| 输出协议 `risk/judgment/handling/analysis/basis` | 已覆盖 | `schema.py`, `prompting.py`, `postprocess.py` | 结构化 JSON、解析、后处理完整。 |
| 历史工单、合成池、灰区样本、公开数据 | 已覆盖 | `build_dataset.py`, `DATA_QUALITY_AND_AUDIT.md`, `PROJECT_FROM_ZERO_TO_ONE.md` | 真实数据不可公开，当前是 schema、构造入口和样例。 |
| 分级案例生成器 | 概念覆盖 | `PROJECT_FROM_ZERO_TO_ONE.md`, `MODEL_CARD_AND_EXPERIMENT_REPORT.md` | 没有真实训练生成器 checkpoint，但机制讲清楚了。 |
| refinement / committee | 已覆盖 | `refinement.py`, `PROJECT_FROM_ZERO_TO_ONE.md`, `DEEP_DIVE_QA.md` | 代码有 committee 回灌抽象。 |
| completion-only SFT | 已覆盖 | `training.py`, `prompting.py`, `README.md` | 真实训练入口已预留。 |
| 公开数据只训二分类 / loss mask | 已覆盖轻量工程版 | `README.md`, `PROJECT_FROM_ZERO_TO_ONE.md`, `training.py` | 公开二分类样本在训练前会被归一成保守标签，避免污染 `limit/ban`；生产级 token 字段 mask 可继续扩展。 |
| 评测指标 Acc/F1/FPR/AUPRC/Macro-F1 | 已覆盖 | `evaluation.py`, `MODEL_CARD_AND_EXPERIMENT_REPORT.md` | 标准库实现，能做 demo。 |
| 标注一致性 Fleiss/Krippendorff/Cohen | 已覆盖 | `evaluation.py`, `RUBRIC_AND_LABELING_GUIDE.md` | Fleiss 和 ordinal alpha 有实现；Cohen 在文档中说明。 |
| 内部测试集、P0/P1、公开 benchmark | 已覆盖 | `MODEL_CARD_AND_EXPERIMENT_REPORT.md`, `configs/experiment_results.yaml` | 指标和用途已沉淀；真实数据不可公开。 |
| Qwen3.5-27B / Qwen3.6-plus / 8B / MoE 对比 | 已覆盖 | `MODEL_CARD_AND_EXPERIMENT_REPORT.md`, `DEEP_DIVE_QA.md` | 面试回答和实验表都有。 |
| JSON 解析失败和 schema 校验 | 已覆盖 | `parsing.py`, `postprocess.py`, `PRODUCTION_SYSTEM_DESIGN.md` | 代码有 JSON 截取、正则兜底、后处理修正。 |
| 风险等级、处置档位、ban 人审 | 已覆盖 | `schema.py`, `postprocess.py`, `PRODUCTION_SYSTEM_DESIGN.md` | ban 不直接执行，进入人审链路。 |
| 行为证据消融最大贡献 | 已覆盖 | `MODEL_CARD_AND_EXPERIMENT_REPORT.md`, `DEEP_DIVE_QA.md` | 消融表和话术已覆盖。 |
| vLLM 部署、P95、prefix caching、吞吐 | 已覆盖 | `DEPLOYMENT_AND_OPERATIONS.md`, `deploy/vllm_serve.sh`, `api.py` | 真实 vLLM 依赖 GPU 和 checkpoint，当前提供部署脚本、参数和 `/metrics` 指标。 |
| INT4/AWQ/GPTQ/蒸馏 | 概念覆盖 | `PRODUCTION_SYSTEM_DESIGN.md`, `MODEL_CARD_AND_EXPERIMENT_REPORT.md` | 成本优化方向已覆盖，不需要真实实现。 |
| RLHF/DPO 未生效 | 概念覆盖 | `DEEP_DIVE_QA.md` | 面试追问层面足够。 |
| 灰度上线、shadow、事故处理 | 已覆盖 | `DEPLOYMENT_AND_OPERATIONS.md`, `INCIDENT_RUNBOOK.md` | 灰度、回滚、事故 runbook 都有。 |
| 训练数据版本管理、泄漏检测 | 已覆盖 | `versioning.py`, `data_audit.py`, `DATA_QUALITY_AND_AUDIT.md` | 版本追踪和数据审计有代码入口。 |
| 线上跑得怎么样、业务结果 | 文档覆盖 | `MODEL_CARD_AND_EXPERIMENT_REPORT.md`, `RESUME_AND_STORYLINE.md` | 真实线上数据不可验证，作为项目叙事和结果表保留。 |

## 2. 当前架构是否正确

正确。当前项目的主线和原始文档一致：

```text
业务审核需求
  -> 违规 taxonomy/rubric
  -> 三段输入证据
  -> 多源训练数据
  -> Qwen 多任务 SFT
  -> JSON 结构化输出
  -> 后处理和策略路由
  -> 人审复核、监控、回流
```

面试时如果没思路，可以直接按这个链路回答。

## 3. 需要改正的东西多吗

不多。当前没有明显架构性错误，主要是三个“可选增强”：

1. **生产级 token 字段 loss mask**
   当前已做公开样本保守归一，避免处置标签污染；如果真实训练要精确到 JSON 字段 token mask，可以继续扩展自定义 collator。

2. **QLoRA 量化训练**
   当前已有 LoRA 配置入口；QLoRA 4bit 参数预留在配置中，真实落地还需结合具体 GPU 和 bitsandbytes 环境。

3. **Prometheus 指标扩展**
   当前 API 已有 `/metrics`；后续可继续加入 latency histogram、topic label、route label 等更细指标。

## 4. 面试中怎么解释“没有真实资源”

可以这样说：

“原始项目依赖公司内部工单、行为打点、线上规则引擎和 Qwen3.5-27B 微调 checkpoint，这些不能在个人仓库公开。所以我在仓库里保留了完整 schema、训练入口、数据构造、评测、后处理、部署和监控链路，用样例数据和 demo judge 跑通工程闭环。真实公司环境只需要替换内部数据、SFT checkpoint 和行为特征服务。”

## 5. 最后结论

当前仓库已经足够支撑面试讲解和工程理解。它不是“真实线上模型权重交付”，而是一个完整的 LLM 风控审核系统蓝图加可运行骨架。对你的背景来说，最值得继续补的是基础 ML 概念和轻量微调，而不是再堆更多业务文档。
