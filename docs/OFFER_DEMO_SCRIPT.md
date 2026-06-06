# Offer 面试演示脚本

这份脚本用于把项目讲成“高薪岗位能买单的工程能力”，而不是功能堆砌。目标是在 5-8 分钟内让面试官形成三个判断：

1. 你能从业务问题定义 ML/LLM 系统。
2. 你能把模型接进可审计、可监控、可回滚的生产链路。
3. 你知道展示项目和真实上线之间的边界，不夸大。

## 1. 30 秒开场

> 这个项目解决的是 IM 私聊风控审核。传统审核通常只看文本做 safe/unsafe 二分类，但直播/社交场景里很多风险需要结合行为证据，比如打赏、进房、关注、短时间高频私聊。  
> 我把它重新定义成一个多证据 LLM Judge：输入聊天证据和行为异常，输出风险等级、是否违规、处置建议和解释依据；后面接 JSON 后处理、策略路由、人审复核、审计日志、监控告警和灰度部署。

## 2. 讲项目价值，不先讲技术栈

推荐顺序：

1. 原问题：文本二分类无法支撑差异化处置。
2. 任务重构：三段输入、三层输出、解释字段。
3. 数据体系：内部/公开/合成/hard case，公开数据不训练强处置。
4. 模型训练：completion-only 多任务 SFT，支持 LoRA。
5. 工程落地：API、鉴权、审计、监控、部署、回滚。
6. 真实边界：当前仓库是生产化展示，不含内部私有数据和真实 checkpoint。

不要一上来讲 FastAPI、Docker、Prometheus。那会显得像在堆工具。先讲业务闭环，再讲工具为什么存在。

## 3. 5 分钟 live demo

### 3.1 验证工程交付

```bash
LC_ALL=en_US.UTF-8 LANG=en_US.UTF-8 make enterprise-check
```

可讲：

> 这个命令会跑测试、编译、交付摘要和 readiness-check。它不是证明模型效果，而是证明工程交付物完整。

### 3.2 跑离线审核链路

```bash
make predict-route
make eval-report
```

展示：

- `outputs/demo_routed_predictions.jsonl`
- `outputs/offline_eval_report.md`

可讲：

> 预测结果里有三层输出、route、final_action 和版本字段。评测报告会看二分类和多字段指标，不只看 accuracy。

### 3.3 跑监控回放

```bash
make window-alerts
make drift-report
```

可讲：

> window-alerts 看局部批次异常，比如 ban 占比突然升高；drift-report 看当前分布相对 baseline 是否漂移。真实生产会接 Prometheus 和日志平台，这里是离线回放验收。

### 3.4 跑 API

终端 1：

```bash
PYTHONPATH=src im-guard --config configs/default.yaml serve --port 8000
```

终端 2：

```bash
curl -X POST http://127.0.0.1:8000/judge \
  -H "Content-Type: application/json" \
  -H "X-Request-ID: interview-demo-1" \
  -d '{"ticket_id":"interview-demo-1","chat_evidence_list":["加微信稳赚，带你投资。"],"behavior_abnormal_list":["短时间高频私聊。"]}'
```

然后：

```bash
curl http://127.0.0.1:8000/ready
curl http://127.0.0.1:8000/metrics
```

可讲：

> request_id 会进入响应和审计日志。线上排查时可以从请求、模型版本、prompt 版本、后处理版本一路追到审计事件。

## 4. 面试官可能追问的高价值回答

### 为什么不是普通文本审核？

因为 IM 风控很多风险不是显式关键词。比如“今晚老规矩”文本本身不一定违规，但如果同时出现短时间高频私聊和大额打赏，就形成证据链。这个项目把聊天语义和行为证据合并进同一个审核任务。

### 为什么不是直接 prompt 一个大模型？

业务输出不是一句解释，而是多字段结构化结果。`risk_level`、`final_judgment`、`handling_suggestion` 要一致，还要能被策略系统和人审系统消费。只靠 prompt 容易字段冲突、格式不稳、成本高，也不方便做版本化和离线评测。

### 公开数据为什么不能直接训练 ban？

公开安全数据通常只有安全/不安全或宽泛 policy 标签，不代表平台业务处置边界。把公开违规样本直接标成 `ban_account` 会污染强处置策略，所以项目把它统一限制为 `mid_risk / warning`。

### 这个项目离真实上线还差什么？

差真实业务私有数据、真实人审和申诉闭环、生产网关、密钥轮换、集中审计库、模型注册审批和线上 A/B 平台。当前仓库证明的是工程骨架和接入方式，不声称替代真实生产平台。

## 5. 不能说过头的话

不要说：

- “这个已经是真实生产系统。”
- “模型效果已经被真实线上验证。”
- “公开数据足够替代真实业务数据。”
- “Bearer token 和 SQLite 就是生产级安全审计。”

推荐说：

- “这是生产化展示项目，保留了真实上线所需的工程边界。”
- “真实上线需要替换内部数据、checkpoint 和企业平台。”
- “这个项目证明我能把 LLM 从模型输出接到风控业务闭环。”

## 6. 1 分钟收束

> 这个项目最核心的价值不是某个模型分数，而是完整定义了 IM 私聊风控审核系统：从业务 taxonomy、数据构建、completion-only SFT，到结构化输出、策略路由、人审复核、审计、监控和灰度回滚。  
> 我用公开数据和启发式 Judge 保证仓库可演示，用训练入口和部署模板保留真实业务接入点。真实上线时只需要替换内部数据、checkpoint 和企业平台能力。

## 7. 面试前最后检查

```bash
git status --short
LC_ALL=en_US.UTF-8 LANG=en_US.UTF-8 make enterprise-check
du -sh . data data/external data/train outputs .venv 2>/dev/null || true
```

确认：

- 工作区干净。
- `enterprise-check` 通过。
- 大数据文件没有提交到 git。
- 能清楚解释哪些能力是当前仓库可复现，哪些是生产接入预留。
