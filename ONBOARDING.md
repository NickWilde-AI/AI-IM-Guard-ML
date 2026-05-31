# AI-IM-Guard-ML 快速上手指南

> 从零开始理解、运行、修改这个项目所需的一切。

---

## 一句话定位

这是一个**直播平台 IM 私聊违规审核模型**，基于 Qwen3.5-27B 微调，输入聊天证据 + 行为异常信号，一次性输出风险等级、违规判定、处置建议三层结构化结论。

---

## 环境准备

```bash
# 要求 Python >= 3.11（StrEnum 依赖）
python3.11 --version

# 克隆后进入项目
cd AI-IM-Guard-ML

# 安装（开发模式，无需 GPU 依赖即可跑 demo）
pip install -e .
pip install pytest  # 测试用

# 如需训练/推理，额外安装
pip install -e ".[train]"   # torch, transformers, trl, peft, datasets
pip install -e ".[serve]"   # fastapi, uvicorn, pyyaml
```

---

## 项目结构一览

```
AI-IM-Guard-ML/
├── src/im_guard_ml/          # 核心代码（下面逐个说明）
│   ├── schema.py             # 数据模型：风险等级、主题、处置建议枚举 + 验证
│   ├── config.py             # 默认配置（模型、训练、告警阈值）
│   ├── prompting.py          # Prompt 模板渲染（user + assistant）
│   ├── inference.py          # 推理：HeuristicJudge（demo）/ TransformersJudge（生产）
│   ├── parsing.py            # JSON 解析 + 正则 fallback
│   ├── postprocess.py        # 生产纠错 + 策略路由
│   ├── training.py           # SFT 训练 + FieldLevelMaskCollator（token 级 loss mask）
│   ├── evaluation.py         # 指标：binary F1、macro-F1、Fleiss Kappa、Krippendorff α
│   ├── refinement.py         # 难样本筛选逻辑
│   ├── committee.py          # 三方异构 committee 集成（self + flash + 规则引擎）
│   ├── generation.py         # 合成数据生成 pipeline（分级生成器）
│   ├── benchmarks.py         # 公开 benchmark 评测（ToxicChat/HarmBench/XSTest）
│   ├── monitoring.py         # 分布统计 + 质量守卫
│   ├── drift_detection.py    # 统计漂移检测（chi2/KS/PSI）
│   ├── alerting.py           # 阈值告警
│   ├── experiment_tracking.py # 实验追踪 + 报告指标
│   ├── versioning.py         # 版本追踪 + 审计日志
│   ├── data_audit.py         # 数据质量审计 + 泄漏检测
│   ├── build_dataset.py      # 数据集归一化（内部/公开）
│   ├── dataio.py             # JSONL/YAML I/O
│   ├── api.py                # FastAPI 服务
│   └── cli.py                # CLI 入口（8 个子命令）
├── configs/
│   ├── default.yaml          # 主配置
│   └── rubrics.yaml          # 11 主题 × 3 级 rubric 细则
├── data/samples/
│   └── sample_cases.jsonl    # 3 条 demo 样本
├── deploy/                   # vLLM + Docker 部署模板
├── tests/                    # 77 个单元测试
├── docs/                     # 14 篇详细文档
├── Makefile                  # 快捷命令
└── pyproject.toml            # 包配置
```

---

## 5 分钟跑通全流程

以下命令用 demo 数据（3 条样本）+ HeuristicJudge（关键词规则，无需 GPU）跑通完整 pipeline：

```bash
# 1. 数据概览
make summary
# 输出：3 条样本，按 source/topic/label 分布统计

# 2. 批量预测
make predict
# 输出：outputs/demo_predictions.jsonl（每条带 prediction 字段）

# 3. 带路由和版本的预测
make predict-route
# 输出：outputs/demo_routed_predictions.jsonl + outputs/demo_audit_logs.jsonl

# 4. 评测指标
make eval
# 输出：binary F1、risk macro-F1、handling macro-F1、per-topic accuracy

# 5. 监控报告
make monitor
# 输出：预测分布、输入分布、质量守卫指标

# 6. 告警评估
make alerts
# 输出：告警状态（pass/warn/critical）+ 触发的告警列表

# 7. 数据质量审计
make audit-data
# 输出：缺失字段、重复 ID、标签错误、泄漏检测

# 8. 构建训练集
make build-demo
# 输出：outputs/built_train.jsonl（归一化后的训练数据）

# 9. 编译检查
make compile
# 验证所有 .py 文件语法正确

# 10. 单元测试
pytest tests/ -v
# 77 tests passed
```

---

## 核心数据流

```
┌─────────────────────────────────────────────────────────────────────┐
│                        审核请求输入                                    │
│  audit_scene (行为摘要) + chat_evidence_list + behavior_abnormal_list │
└───────────────────────────────┬─────────────────────────────────────┘
                                │
                                ▼
┌───────────────────────────────────────────────────────────────────┐
│  Prompt 渲染 (prompting.py)                                        │
│  主题清单 + rubric + 处置策略表 + 三段证据 → 结构化 user prompt     │
└───────────────────────────────┬───────────────────────────────────┘
                                │
                                ▼
┌───────────────────────────────────────────────────────────────────┐
│  模型推理 (inference.py)                                           │
│  HeuristicJudge (demo) 或 TransformersJudge (微调 checkpoint)      │
└───────────────────────────────┬───────────────────────────────────┘
                                │
                                ▼
┌───────────────────────────────────────────────────────────────────┐
│  JSON 解析 (parsing.py)                                            │
│  优先 json.loads → 失败则正则 fallback → 兜底安全默认值             │
└───────────────────────────────┬───────────────────────────────────┘
                                │
                                ▼
┌───────────────────────────────────────────────────────────────────┐
│  后处理 (postprocess.py)                                           │
│  标签验证 → 生产纠错 → 策略路由                                     │
│  ban_account 无行为证据 → 降级 limit_account                       │
│  not_exist_violation → 强制 low_risk + ignore                      │
└───────────────────────────────┬───────────────────────────────────┘
                                │
                                ▼
┌───────────────────────────────────────────────────────────────────┐
│  路由决策                                                          │
│  ignore      → auto_close                                         │
│  warning     → auto_action / send_warning                         │
│  limit       → policy_action / limit_account_candidate            │
│  ban_account → human_review_required / review_before_ban          │
└───────────────────────────────────────────────────────────────────┘
```

---

## 输入输出格式

### 输入（一条审核案例）

```json
{
  "ticket_id": "im-audit-2026-04-24-008721",
  "audit_scene": {
    "chat_type": "IM私聊",
    "user_intimacy": "无",
    "behavior_key_summary": {
      "login_behavior": "异地登录。",
      "search_behavior": "搜索 UID。",
      "follow_behavior": "关注。",
      "enter_room_behavior": "进入对方房间。",
      "mic_interact_behavior": "无互动。",
      "t_bean_consume": "极大额消费。",
      "reward_behavior": "持续高频大额打赏，旨在推高榜单。",
      "gift_total_value": 10000,
      "gift_total_count": 5
    }
  },
  "chat_evidence_list": [
    {
      "occur_time": "2026-04-24 19:00:00",
      "original_content": "帮我代刷一下今晚的周榜，包榜到第一。",
      "risk_point": "明确提及代刷和包榜。"
    }
  ],
  "behavior_abnormal_list": [
    {
      "abnormal_type": "代刷/包榜行为",
      "abnormal_description": "30 分钟内对目标主播突发性大额打赏 1 万元。"
    }
  ]
}
```

### 输出（模型预测 + 路由）

```json
{
  "risk_level": "high_risk",
  "topic": "代刷/包榜",
  "correlation_analysis": "语义中明确约定代刷包榜，行为侧短时间大额打赏完全印证。",
  "final_judgment": "exist_violation",
  "judgment_basis": "明确的代刷约定 + 明确的冲榜行为，证据链完整。",
  "handling_suggestion": "ban_account",
  "route": "human_review_required",
  "final_action": "review_before_ban"
}
```

---

## 训练 Pipeline

### 数据构成（约 51.4K 条）

| 来源 | 数量 | 标签 | 用途 |
|------|------|------|------|
| 历史工单（脱敏重采样） | ~24.5K | 完整四类 | 主训练数据 |
| 分级案例生成器 | ~11.6K | 完整四类 | 补全 risk_level + 长尾主题 |
| 灰区强化样本 | ~2.6K | 完整四类 | 模型盲点回灌 |
| 公开数据集子集 | ~12.7K | 仅 binary | 文本侧辅助（loss mask） |

### 训练命令

```bash
# 完整 SFT（需要 8×A100 80GB）
PYTHONPATH=src python3.11 -m im_guard_ml.cli \
  --config configs/default.yaml \
  train path/to/merged_train.jsonl

# 关键超参：
# - 2 epochs, lr=2e-6, batch=4×4=64 effective
# - completion-only loss（只在 assistant 回复上算 loss）
# - FieldLevelMaskCollator: 公开数据的 risk_level/handling token 被 mask
# - 可选 LoRA (r=16, alpha=32)
```

### 核心设计决策

1. **为什么单模型多任务？** 三层任务共享可迁移表示，risk+binary 联合比单训 handling 提升 +2.8pp
2. **为什么 completion-only？** Prompt 里有 rubric/策略表等静态文本，不应参与梯度
3. **为什么 token 级 loss mask？** 公开数据没有 risk/handling 真标签，必须屏蔽这两个字段的 loss
4. **为什么迭代 refinement？** 灰区难样本（语义良性但行为违规）是模型最弱的地方，回灌比堆量有效

---

## 评测体系

| 测试集 | 样本数 | 任务 | 定位 |
|--------|--------|------|------|
| 自构 IM 审核测试集 | 1,024 | risk + judgment + handling | 核心内部指标 |
| P0/P1 工单回流 | 312 | risk + judgment + handling | 真实业务验证 |
| ToxicChat | ~2,850 | binary | 通用能力不退化 |
| HarmBench | ~400 | binary | 抗 jailbreak |
| XSTest | ~450 | binary | 监控误杀率 |

### 报告指标

| 指标 | 本方案 | 最强基线 (Qwen3.6-plus) | 提升 |
|------|--------|------------------------|------|
| 违规判定 Acc | 82.1 | 78.9 | +3.2pp |
| 风险等级 macro-F1 | 75.6 | 58.4 | +17.2pp |
| 处置建议 macro-F1 | 73.2 | 66.5 | +6.7pp |
| ban_account FPR | 2.6% | 4.7% | -2.1pp |

---

## 生产部署

```bash
# 1. vLLM 推理服务
bash deploy/vllm_serve.sh
# 默认: TP=4, prefix caching, max_model_len=8192

# 2. FastAPI 审核服务
PYTHONPATH=src python3.11 -m im_guard_ml.cli \
  --config configs/default.yaml \
  serve --model-path ./ckpt/im-audit-judge --port 8000

# 3. Docker Compose（双容器）
docker compose -f deploy/docker-compose.example.yml up
```

### 生产安全护栏

- ban_account → 强制人审复核，模型不直接执行封号
- JSON 解析失败 → 正则兜底 → 安全默认值（not_violation + ignore）
- 行为证据缺失 → ban 自动降级为 limit
- 监控告警 → ban 率 > 12% 触发 critical

---

## 关键模块速查

| 我想... | 看哪个文件 |
|---------|-----------|
| 理解输入输出格式 | `schema.py` |
| 看 Prompt 怎么拼的 | `prompting.py` |
| 看模型怎么推理 | `inference.py` |
| 看 JSON 怎么解析 | `parsing.py` |
| 看后处理和路由逻辑 | `postprocess.py` |
| 看训练怎么跑 | `training.py` |
| 看 loss mask 怎么做 | `training.py` → `FieldLevelMaskCollator` |
| 看难样本怎么筛 | `refinement.py` + `committee.py` |
| 看合成数据怎么生成 | `generation.py` |
| 看评测指标 | `evaluation.py` |
| 看公开 benchmark | `benchmarks.py` |
| 看监控和漂移检测 | `monitoring.py` + `drift_detection.py` |
| 看告警逻辑 | `alerting.py` |
| 看实验结果 | `experiment_tracking.py` → `REPORTED_RESULTS` |
| 看 API 接口 | `api.py` |
| 看 CLI 命令 | `cli.py` |

---

## 面试要点速记

### 30 秒版本

> 我做的是直播 IM 私聊违规审核模型。原来只有文本二分类，我升级成一个 Qwen3.5-27B 多任务 SFT 模型，联合输出风险等级、违规判定、处置建议。核心创新是语义+行为联合判定，加上迭代 refinement 解决灰区难样本。最终违规判定 Acc 82.1，处置建议 macro-F1 73.2，相对最强基线 +6.7pp。

### 高频追问

1. **为什么不用 API？** → Qwen3.6-plus zero-shot 只有 78.9，mid_risk 只有 64.7
2. **行为证据贡献多大？** → 去掉后三个指标分别掉 5.6/7.8/6.8pp，最大单点
3. **公开数据怎么处理？** → 双层防御：label capping + token 级 field loss mask
4. **ban FPR 怎么压到 2.6%？** → rubric 严格 + 显式学习 + 合成"高风险但证据不全"样本
5. **violation 概率能当 risk 用吗？** → 不能，Spearman 只有 0.43，mid 段过度自信

---

## 下一步

- 详细设计文档：`docs/PROJECT_FROM_ZERO_TO_ONE.md`
- 面试 Playbook：`docs/INTERVIEW_PLAYBOOK.md`
- 命令参考：`docs/COMMANDS.md`
- 生产系统设计：`docs/PRODUCTION_SYSTEM_DESIGN.md`
- Rubric 标注指南：`docs/RUBRIC_AND_LABELING_GUIDE.md`
