# 模型卡与实验报告

这份文档模拟真实公司里模型交付时会写的 model card / experiment report。面试里它可以支撑你回答：模型是什么、训练数据是什么、怎么评测、和谁比、哪些模块真正有效、上线红线是什么。

## 1. 模型概览

| 项目 | 内容 |
| --- | --- |
| 模型名称 | `im-audit-judge-qwen35-27b-sft` |
| 基座模型 | Qwen3.5-27B |
| 任务类型 | IM 私聊多证据违规审核 |
| 输入 | `audit_scene + chat_evidence_list + behavior_abnormal_list` |
| 输出 | `risk_level + topic + correlation_analysis + final_judgment + judgment_basis + handling_suggestion` |
| 训练方式 | completion-only SFT |
| 部署方式 | vLLM，贪心解码，JSON 后处理 |

模型定位：业务审核 Judge，不是通用文本 moderation。它的目标是融合聊天语义和行为异常，并给出可路由、可复核、可解释的审核结论。

## 2. 训练数据

| 数据来源 | 数量 | 作用 |
| --- | ---: | --- |
| 历史审核工单 | 24,498 | 主体真实分布，含脱敏工单和人审结论 |
| 分级案例生成器 | 11,615 | 补长尾主题和 low/mid/high 边界 |
| 灰区强化样本 | 2,629 | 回灌上一轮模型误判 hard cases |
| 公开安全数据 | 12,700 | 补通用中英文文本安全能力 |
| 合计 | 51,442 | 多任务训练集 |

内部样本带 `topic / risk_level / final_judgment / handling_suggestion` 标签；公开样本只用于 `final_judgment` 二分类辅助。

## 3. 评测集

| 评测集 | 数量 | 目的 |
| --- | ---: | --- |
| 自构 IM 审核测试集 | 1,024 | 核心离线评测，覆盖三层输出 |
| P0/P1 工单回流 | 312 | 真实线上高风险压力测试 |
| ToxicChat | 约 2.85K | 通用文本审核能力 |
| HarmBench | 约 0.4K | 对抗式安全能力 |
| XSTest | 约 0.45K | 误杀率监控 |

标注质量用 Fleiss Kappa、ordinal Krippendorff alpha、Cohen's Kappa 监控。risk_level 是有序变量，因此必须看 ordinal alpha。

## 4. 核心结果

### 4.1 自构 IM 测试集

| 指标 | 结果 |
| --- | ---: |
| final_judgment Acc | 82.1 |
| risk_level macro-F1 | 75.6 |
| handling_suggestion macro-F1 | 73.2 |
| ban_account FPR | 2.6 |

解读：模型不仅二分类更准，更关键是处置建议 macro-F1 和 ban FPR 达到业务上线红线。ban 误杀是业务最敏感指标，所以单独报告。

### 4.2 P0/P1 回流测试集

| 指标 | 结果 |
| --- | ---: |
| final_judgment Acc | 87.5 |
| risk_level macro-F1 | 77.3 |
| handling_suggestion macro-F1 | 75.1 |

解读：P0/P1 更接近真实线上高风险事故复盘，能证明模型不是只在平衡测试集上好看。

## 5. 与基线对比

| 模型 | final_judgment Acc | risk macro-F1 | handling macro-F1 |
| --- | ---: | ---: | ---: |
| 线上规则引擎 | 67.4 | 56.1 | 58.7 |
| Qwen3.6-plus zero-shot | 78.9 | 58.4 | 66.5 |
| 单任务 risk-only SFT | - | 66.4 | - |
| 单任务 handling-only SFT | - | - | 68.4 |
| 本方案多任务 SFT | 82.1 | 75.6 | 73.2 |

面试讲法：收益最大的是 mid_risk 灰区段，不是 high_risk 强关键词段。规则引擎在强证据链上也能做一些，但对语义弱、行为强的组合不稳定。

## 6. 消融实验

| 配置 | final_judgment Acc | risk macro-F1 | handling macro-F1 | 结论 |
| --- | ---: | ---: | ---: | --- |
| 完整方案 | 82.1 | 75.6 | 73.2 | 最优 |
| 去掉 refinement | 78.4 | 70.2 | 69.1 | hard sample 回灌有效 |
| 去掉行为证据 | 76.5 | 67.8 | 66.4 | 行为证据是最大单点贡献 |
| 去掉公开数据 | 80.6 | 74.1 | 71.9 | 公开数据主要补泛化 |
| 换 35B-A3B MoE | 80.7 | 73.9 | 71.5 | 成本优化候选 |
| 换 8B | 75.8 | 67.2 | 65.0 | 容量不足，灰区掉点明显 |

最关键的消融是“去掉行为证据”。这证明项目不是普通文本分类器，而是多证据融合带来的提升。

## 7. 上线红线

上线前必须满足：

- 自构测试集核心指标不低于上一版本。
- P0/P1 回流测试集不低于业务红线。
- `ban_account FPR <= 3%`。
- JSON 解析失败率处于低位，并有 fallback。
- P95 推理延迟低于业务要求。
- shadow 阶段未发现输入分布或上游特征异常。

如果 `ban_account FPR` 超线，即使 overall accuracy 高，也不能进入全量。

## 7.1 模型注册与审批

本仓库提供最小模型注册表：[configs/model_registry.yaml](../configs/model_registry.yaml)

注册表记录：

- `current_stable`：当前稳定版本。
- `candidate`：候选版本。
- `prompt_version / rubric_version / feature_schema_version / postprocess_version`。
- `train_data_version / eval_data_version`。
- `approved_by / approved_at`。
- `rollback_to`。
- 核心指标和 promotion guardrails。

校验命令：

```bash
PYTHONPATH=src python3 -m im_guard_ml.cli --config configs/default.yaml model-registry-check \
  --registry configs/model_registry.yaml \
  --out outputs/model_registry_check.json
```

这个检查会确保稳定版本有审批元数据，候选版本有回滚目标，指标满足上线红线。真实生产中它应替换为企业模型注册和审批平台；当前仓库保留的是可运行的最小治理接口。

## 8. 已知限制

- 对上游行为特征质量敏感，特征污染会影响处置强度。
- mid_risk 天然存在标注分歧，不能期待 100% 一致。
- 合成数据可能带来表达模板化，需要用真实测试集约束。
- 解释字段可能出现 hallucination，生产上主要用于辅助复核。
- 公开 benchmark 只能证明文本侧能力，不能替代业务测试集。

## 9. 后续优化

- AWQ INT4：降低推理成本，重点监控 risk macro-F1 跌幅。
- MoE 路线：如果 35B-A3B 效果接近，可作为性价比版本。
- 分层路由：明显安全或明显规则命中的样本不走大模型。
- 检索式历史上下文：只取相关历史消息，避免 32K 长上下文拖慢推理。
- 更细的解释质量评测：区分结论错误和解释错误。

## 10. 面试总结句

“这个模型卡里最重要的信息不是某一个分数，而是我能证明每个模块为什么存在：行为证据是最大单点贡献，refinement 解决灰区，公开数据补泛化，多任务学习保证三层输出一致，后处理和人审复核控制生产风险。”
