# 部署与运维说明

这份文档用于回答“如果要上线，你怎么部署、怎么配参数、怎么灰度、怎么回滚”。它不要求面试现场真的跑起来，但要体现你知道生产环境里模型服务不是一条 `predict` 命令。

## 1. 服务形态

生产建议拆成两层：

- `vLLM Judge Service`：只负责加载 SFT checkpoint 并生成模型原始输出。
- `Audit API Service`：负责组装 prompt、调用模型、解析 JSON、策略路由、版本追踪、审计日志和监控。

这样拆的好处是模型推理和业务后处理解耦。模型服务可以独立扩容，审核服务可以快速迭代策略和后处理。

## 2. vLLM 推理服务

示例脚本：[deploy/vllm_serve.sh](/Users/chenpeng/WorkSpace/文稿/Tencent/TencentCodeing/AI-IM-Guard-ML/deploy/vllm_serve.sh)

关键参数：

- `MODEL_PATH`：SFT 后的 checkpoint 路径。
- `TP_SIZE`：tensor parallel，一般按 GPU 数和模型大小设置。
- `MAX_MODEL_LEN=8192`：和训练上下文保持一致。
- `--enable-prefix-caching`：rubric、策略表、JSON Schema 是稳定前缀，可降低首 token 延迟。
- `GPU_MEMORY_UTILIZATION`：控制显存使用上限，避免 KV cache 把实例打爆。

示例：

```bash
MODEL_PATH=outputs/im-audit-judge \
TP_SIZE=4 \
MAX_MODEL_LEN=8192 \
bash deploy/vllm_serve.sh
```

## 3. 审核 API 服务

审核 API 负责业务链路，不只是推理。

职责：

- 接收 `audit_scene / chat_evidence_list / behavior_abnormal_list`。
- 根据主题选择 rubric。
- 调用 Judge。
- 解析和校验 JSON。
- 输出 `route / final_action`。
- 写审计日志。
- 暴露健康检查和配置查询。

本仓库提供 FastAPI 入口：

```bash
im-guard serve --model-path outputs/im-audit-judge --port 8000
```

服务同时提供 Prometheus 文本格式指标：

```bash
curl http://127.0.0.1:8000/metrics
```

## 4. 环境变量

示例配置：[deploy/audit_service.env.example](/Users/chenpeng/WorkSpace/文稿/Tencent/TencentCodeing/AI-IM-Guard-ML/deploy/audit_service.env.example)

重要变量：

- `IM_GUARD_MODEL_PATH`：模型路径。
- `IM_GUARD_ENABLE_ROUTE`：是否输出策略路由。
- `IM_GUARD_ENABLE_VERSION`：是否输出版本字段。
- `IM_GUARD_BAN_REQUIRES_HUMAN_REVIEW`：ban 是否强制人审。
- `IM_GUARD_P95_LATENCY_BUDGET_MS`：延迟红线。
- `IM_GUARD_BAN_FPR_REDLINE`：ban 误杀红线。

## 5. 灰度配置

推荐灰度参数：

| 阶段 | 流量 | 模型动作 | 规则引擎 |
| --- | ---: | --- | --- |
| shadow | 1% | 只预测入库 | 主处置 |
| small | 10% | warning/limit 可进入策略，ban 人审 | 兜底 |
| ramp | 50% | 模型主链路 | 强规则兜底 |
| full | 100% | 模型主链路 | 异常兜底 |

每个阶段观察：

- `ban_account_rate`
- `ban_account FPR`
- 人审改判率
- 客诉率
- JSON 解析失败率
- P95/P99 延迟
- 上游行为特征分布

## 6. 回滚策略

必须能快速回滚到上一版本。

触发条件：

- ban FPR 超过红线。
- 客诉率突增。
- 行为特征分布异常。
- JSON 解析失败率升高。
- P95 延迟超预算。
- 人审队列被 ban 样本打爆。

回滚动作：

- 流量切回规则引擎。
- 模型切回上一 checkpoint。
- 禁止 ban 自动流转，只保留人审。
- 固定当前日志和样本，做事故复盘。

## 7. 容量估算

粗略估算思路：

```text
所需实例数 = 峰值 QPS / 单实例稳定 QPS / 安全系数
```

如果单实例稳定 QPS 25-30，线上峰值 80-100 QPS，至少需要 4 个实例，并保留 30%-40% 余量。P99 延迟升高时，优先看 vLLM queue time、输入 token 长度和 KV cache 命中率。

## 8. 面试表达

可以这样讲：

“我会把模型推理和审核业务服务拆开。vLLM 只负责高吞吐生成，审核服务负责 prompt 组装、JSON 校验、策略路由、审计日志和监控。上线不直接全量，先 shadow，再小流量，再放量。ban_account 不直接执行，必须进人审。任何版本都要带 model/prompt/rubric/feature schema/postprocess 版本，线上出问题可以追溯。”
