# API 使用说明

本文档说明 FastAPI 审核服务的接口、鉴权、错误码、审计查询和运维检查方式。它面向生产化展示和接入评审，不替代真实生产网关、密钥系统或集中权限平台。

## 启动

本地 demo：

```bash
PYTHONPATH=src im-guard --config configs/default.yaml serve --port 8000
```

开启 token、审计、请求大小限制和限流：

```bash
export IM_GUARD_API_TOKEN="replace-with-a-secret"
export IM_GUARD_AUDIT_BACKEND=jsonl
export IM_GUARD_AUDIT_LOG_PATH=outputs/api_audit_events.jsonl
export IM_GUARD_CORS_ORIGINS="http://127.0.0.1:8000,http://localhost:8000"
export IM_GUARD_MAX_REQUEST_BYTES=262144
export IM_GUARD_RATE_LIMIT_PER_MINUTE=120
PYTHONPATH=src im-guard --config configs/default.yaml serve --port 8000
```

## 鉴权与角色

默认不设置 `IM_GUARD_API_TOKEN` 或 `IM_GUARD_API_TOKENS` 时，接口保持本地 demo 可访问。设置 token 后，业务接口必须带：

```text
Authorization: Bearer <token>
```

单 token：

```bash
export IM_GUARD_API_TOKEN="replace-with-a-secret"
```

多 token + 最小角色权限：

```bash
export IM_GUARD_API_TOKENS="writer-token:writer,reader-token:reader,audit-token:auditor"
```

| 角色 | 可访问能力 |
| --- | --- |
| `admin` | 全部接口 |
| `writer` | `/judge` |
| `reader` | `/dashboard/data`、`/config`、模拟器配置读取 |
| `auditor` | `/audit/tickets/{ticket_id}` |

## 接口表

| 方法 | 路径 | 鉴权权限 | 说明 |
| --- | --- | --- | --- |
| `GET` | `/health` | 无 | 存活检查 |
| `GET` | `/ready` | 无 | 就绪检查和生产 guard 配置摘要 |
| `GET` | `/config` | `read` | 配置摘要 |
| `POST` | `/judge` | `write` | 提交审核样本 |
| `GET` | `/dashboard/data?window=5m|1h|all` | `read` | 监控大盘数据 |
| `GET` | `/metrics` | 无 | Prometheus 文本指标 |
| `GET` | `/audit/tickets/{ticket_id}` | `audit` | 按 ticket 查询审计事件 |
| `GET` | `/simulator/config` | `config` | 读取模拟器配置 |
| `POST` | `/simulator/speed` | `config` | 设置模拟器速度 |

## 请求 ID

客户端可以传入：

```text
X-Request-ID: req-20260606-0001
```

服务会在响应 header、`/judge` 响应体和审计日志中复用同一个 `request_id`。如果客户端不传，服务自动生成 UUID。

## `/judge` 示例

请求：

```bash
curl -X POST http://127.0.0.1:8000/judge \
  -H "Authorization: Bearer replace-with-a-secret" \
  -H "X-Request-ID: req-demo-1" \
  -H "Content-Type: application/json" \
  -d '{
    "ticket_id": "demo-1",
    "audit_scene": {
      "scene_name": "im_private_chat",
      "behavior_key_summary": {
        "gift_total_value": 8000,
        "chat_frequency_1h": 45
      }
    },
    "chat_evidence_list": [
      "加微信稳赚，带你投资。"
    ],
    "behavior_abnormal_list": [
      "短时间高频私聊。"
    ]
  }'
```

响应字段：

| 字段 | 说明 |
| --- | --- |
| `risk_level` | `low_risk / mid_risk / high_risk` |
| `topic` | 违规主题，如 `诈骗引流` |
| `final_judgment` | `exist_violation / not_exist_violation` |
| `handling_suggestion` | `ignore / warning / limit_account / ban_account` |
| `route` | 策略路由结果 |
| `final_action` | 最终动作建议 |
| `request_id` | 请求追踪 ID |
| `model_version` 等版本字段 | 模型、prompt、rubric、schema、后处理版本 |

## 错误结构

所有生产 guard 和 HTTP 异常使用结构化错误：

```json
{
  "error": {
    "code": "unauthorized",
    "message": "missing or invalid bearer token",
    "request_id": "req-demo-1"
  }
}
```

| HTTP 状态 | `error.code` | 触发条件 |
| --- | --- | --- |
| `401` | `unauthorized` | token 缺失、错误或角色权限不足 |
| `413` | `request_too_large` | 请求体超过 `IM_GUARD_MAX_REQUEST_BYTES` |
| `429` | `rate_limited` | 单 IP 每分钟请求数超过 `IM_GUARD_RATE_LIMIT_PER_MINUTE` |
| `422` | `validation_error` | FastAPI 请求校验失败 |
| 其他 | `http_error` | 通用 HTTP 异常 |

## 审计查询

JSONL 审计：

```bash
export IM_GUARD_AUDIT_BACKEND=jsonl
export IM_GUARD_AUDIT_LOG_PATH=outputs/api_audit_events.jsonl
```

SQLite 审计：

```bash
export IM_GUARD_AUDIT_BACKEND=sqlite
export IM_GUARD_AUDIT_LOG_PATH=outputs/api_audit_events.sqlite
```

查询 ticket：

```bash
curl http://127.0.0.1:8000/audit/tickets/demo-1 \
  -H "Authorization: Bearer replace-with-a-secret"
```

审计事件记录版本、风险结果、route、latency、request_id 和 `input_summary`。`input_summary` 包含 payload hash、证据数量、PII 类型和脱敏样例，不保存完整明文证据列表。

## 监控接口

```bash
curl http://127.0.0.1:8000/dashboard/data?window=5m \
  -H "Authorization: Bearer replace-with-a-secret"

curl http://127.0.0.1:8000/metrics
```

Prometheus 指标包含请求总量、风险等级、主题、处置建议、route、解析异常数和延迟分位数。

## 压测

```bash
python3 scripts/benchmark_api.py \
  --url http://127.0.0.1:8000/judge \
  --requests 100 \
  --token replace-with-a-secret
```

压测脚本用于展示级基准，不替代真实生产压测。生产压测应覆盖多实例、网关、模型队列、长输入、失败重试和审计写入压力。

## 生产接入边界

- Bearer token 是展示级鉴权；真实生产应使用网关、密钥轮换、租户隔离和集中权限。
- SQLite 适合单机展示；多实例生产应使用 PostgreSQL、日志平台或审计平台。
- `/metrics` 提供指标出口；真实告警应接入 Prometheus、日志平台和 on-call 流程。
- `ban_account` 等强处置应经过人审或策略保护，不应只依赖公开训练数据直接自动执行。
