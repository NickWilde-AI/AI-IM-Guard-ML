# 项目总索引与复习路线

这份文件是整个仓库的入口。复习时不要从代码开始，先按下面顺序建立项目全貌，再看实现细节。

## 1. 最推荐阅读顺序

1. [PROJECT_FROM_ZERO_TO_ONE.md](/Users/chenpeng/WorkSpace/文稿/Tencent/TencentCodeing/AI-IM-Guard-ML/docs/PROJECT_FROM_ZERO_TO_ONE.md)
   从业务背景、任务拆解、数据、模型、训练、上线完整理解项目。

2. [PRODUCTION_SYSTEM_DESIGN.md](/Users/chenpeng/WorkSpace/文稿/Tencent/TencentCodeing/AI-IM-Guard-ML/docs/PRODUCTION_SYSTEM_DESIGN.md)
   理解真实生产服务怎么拆，后处理、路由、版本、监控怎么接。

3. [RUBRIC_AND_LABELING_GUIDE.md](/Users/chenpeng/WorkSpace/文稿/Tencent/TencentCodeing/AI-IM-Guard-ML/docs/RUBRIC_AND_LABELING_GUIDE.md)
   理解 11 类主题、47 个子主题、low/mid/high 标注逻辑。

4. [MODEL_CARD_AND_EXPERIMENT_REPORT.md](/Users/chenpeng/WorkSpace/文稿/Tencent/TencentCodeing/AI-IM-Guard-ML/docs/MODEL_CARD_AND_EXPERIMENT_REPORT.md)
   记住核心指标、基线、消融和上线红线。

5. [DEPLOYMENT_AND_OPERATIONS.md](/Users/chenpeng/WorkSpace/文稿/Tencent/TencentCodeing/AI-IM-Guard-ML/docs/DEPLOYMENT_AND_OPERATIONS.md)
   准备部署、灰度、回滚、容量估算相关追问。

6. [DATA_QUALITY_AND_AUDIT.md](/Users/chenpeng/WorkSpace/文稿/Tencent/TencentCodeing/AI-IM-Guard-ML/docs/DATA_QUALITY_AND_AUDIT.md)
   准备数据质量、标签冲突、训练/评测泄漏相关追问。

7. [DEEP_DIVE_QA.md](/Users/chenpeng/WorkSpace/文稿/Tencent/TencentCodeing/AI-IM-Guard-ML/docs/DEEP_DIVE_QA.md)
   背高频深挖问题的回答结构。

8. [INTERVIEW_PLAYBOOK.md](/Users/chenpeng/WorkSpace/文稿/Tencent/TencentCodeing/AI-IM-Guard-ML/docs/INTERVIEW_PLAYBOOK.md)
   最后压缩成 30 秒、2 分钟、5 分钟讲法。

9. [FINAL_INTERVIEW_CHECKLIST.md](/Users/chenpeng/WorkSpace/文稿/Tencent/TencentCodeing/AI-IM-Guard-ML/docs/FINAL_INTERVIEW_CHECKLIST.md)
   面试前 30 分钟做最终自检。

10. [RESUME_AND_STORYLINE.md](/Users/chenpeng/WorkSpace/文稿/Tencent/TencentCodeing/AI-IM-Guard-ML/docs/RESUME_AND_STORYLINE.md)
    简历 bullet、STAR 叙事和 1/3/5 分钟讲法。

11. [COMMANDS.md](/Users/chenpeng/WorkSpace/文稿/Tencent/TencentCodeing/AI-IM-Guard-ML/docs/COMMANDS.md)
    常用命令、Makefile 和部署入口。

12. [INCIDENT_RUNBOOK.md](/Users/chenpeng/WorkSpace/文稿/Tencent/TencentCodeing/AI-IM-Guard-ML/docs/INCIDENT_RUNBOOK.md)
    线上事故止血、排查和复盘。

13. [DELIVERY_REPORT.md](/Users/chenpeng/WorkSpace/文稿/Tencent/TencentCodeing/AI-IM-Guard-ML/docs/DELIVERY_REPORT.md)
    当前项目交付总清单。

14. [SOURCE_DOC_COVERAGE.md](/Users/chenpeng/WorkSpace/文稿/Tencent/TencentCodeing/AI-IM-Guard-ML/docs/SOURCE_DOC_COVERAGE.md)
    原始两份文档内容和当前工程的覆盖关系。

## 2. 面试必须讲清的 6 件事

1. **业务痛点**：文本二分类不能融合行为证据，也不能支撑差异化处置。
2. **协议设计**：输出 `risk_level / final_judgment / handling_suggestion` 三层，不做简单映射。
3. **数据闭环**：历史工单 + 合成样本 + 灰区 refinement + 公开文本安全数据。
4. **模型训练**：Qwen3.5-27B completion-only 多任务 SFT。
5. **实验验证**：行为证据和 refinement 的消融收益最大，ban FPR 是上线红线。
6. **生产落地**：vLLM 推理、JSON 后处理、策略路由、人审复核、版本追踪、监控回流。

## 3. 代码模块地图

| 模块 | 作用 |
| --- | --- |
| `schema.py` | 输入输出协议、枚举、标签一致性校验 |
| `prompting.py` | prompt 和 chat template 渲染 |
| `training.py` | TRL completion-only SFT 入口 |
| `inference.py` | 启发式 demo Judge 和 Transformers Judge |
| `parsing.py` | JSON 解析与正则兜底 |
| `postprocess.py` | 生产后处理、冲突修正、策略路由 |
| `evaluation.py` | 分类指标、macro-F1、AUPRC、一致性指标 |
| `refinement.py` | committee hard sample 回灌 |
| `monitoring.py` | 线上预测分布和输入漂移摘要 |
| `data_audit.py` | 训练数据质量和泄漏审计 |
| `versioning.py` | 模型/prompt/rubric/后处理版本追踪 |
| `api.py` | FastAPI 服务 |
| `cli.py` | 命令行入口 |

## 4. 配置与样例

| 文件 | 作用 |
| --- | --- |
| `configs/default.yaml` | 默认模型、训练、标签、rubric、版本配置 |
| `configs/rubrics.yaml` | 11 类主题的 low/mid/high 细则 |
| `configs/experiment_results.yaml` | 机器可读实验结果和模型卡摘要 |
| `data/samples/sample_cases.jsonl` | 可演示样例数据 |
| `deploy/vllm_serve.sh` | vLLM 服务启动示例 |
| `deploy/audit_service.env.example` | 审核服务环境变量示例 |
| `deploy/docker-compose.example.yml` | 部署编排示例 |

## 5. 如果只剩 10 分钟复习

按这个顺序看：

1. `INTERVIEW_PLAYBOOK.md` 的 30 秒和 2 分钟版本。
2. `PROJECT_FROM_ZERO_TO_ONE.md` 的第 2、5、6、8、13、17 节。
3. `MODEL_CARD_AND_EXPERIMENT_REPORT.md` 的核心结果和消融实验。
4. `DEEP_DIVE_QA.md` 的第 3、6、11、14、18、20、25 题。
5. `FINAL_INTERVIEW_CHECKLIST.md` 的最后一段收束话术。
6. `RESUME_AND_STORYLINE.md` 的 1 分钟讲法。

## 6. 一句话收束

这个项目的核心价值是：把 IM 私聊风控从一个文本二分类问题，升级成了一个可解释、可路由、可灰度、可回流的多证据业务审核系统。
