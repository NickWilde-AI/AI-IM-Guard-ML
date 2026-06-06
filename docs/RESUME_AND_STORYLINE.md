# 简历与面试叙事稿

这份文档用于把项目压缩成招聘方最容易听懂的表达：简历 bullet、STAR 故事、1 分钟/3 分钟/5 分钟讲法。

## 1. 简历 Bullet

**多证据融合的直播平台 IM 私聊违规审核模型**

- 面向直播/社交 IM 私聊风控，将原“文本二分类审核”升级为融合聊天语义、异地登录、关注、进房、打赏冲榜等行为信号的多任务审核 Judge，统一输出 `risk_level / final_judgment / handling_suggestion` 与可解释依据，支撑 warning、limit、ban 差异化处置。
- 设计 11 类违规主题、47 个子主题及 low/mid/high 分级 rubric；构建 51.4K 多源训练集，包含 24.5K 脱敏历史工单、11.6K 分级合成样本、2.6K 灰区 hard sample 与 12.7K 公开安全数据。
- 基于 Qwen3.5-27B 进行 completion-only 多任务 SFT，并通过 self + Qwen-flash + 规则引擎 committee 迭代回灌灰区样本；在 1024 条人审测试集上取得 final_judgment Acc 82.1、risk macro-F1 75.6、handling macro-F1 73.2，ban FPR 控制到 2.6%。
- 参与 vLLM 推理上线方案设计，补齐 JSON Schema 校验、策略路由、人审复核、版本追踪和监控回流机制；单实例 P95 延迟控制在 1.2s 内，支持生产灰度和规则兜底。

如果面试官看的是当前 GitHub 仓库，需要主动补一句边界：

> GitHub 版本是生产化展示工程，保留公开数据接入、训练入口、API、安全、审计、监控、部署和文档体系；真实公司内部数据、线上 checkpoint、人审平台和网关能力不能公开，所以用公开 XGuard 数据和启发式 Judge 跑通可复现链路。

## 1.1 简历使用建议

如果你有真实工作经历能支撑内部数据和线上指标，可以使用上面的完整 bullet。  
如果你把这个项目作为个人作品集，推荐改成更稳妥的表述：

- 设计并开源 IM 私聊风控审核生产化展示项目，将文本二分类审核升级为语义证据 + 行为证据融合的多任务 LLM Judge，统一输出 `risk_level / final_judgment / handling_suggestion` 与解释依据。
- 接入 Apache-2.0 的 XGuard 公开中文安全数据，设计到 IM 风控标签体系的保守映射，转换为项目 JSONL 训练格式，并补齐去重、train/val/test 拆分、标签合法性、泄漏和 PII 风险审计。
- 实现 FastAPI 审核服务，支持 Bearer Token/RBAC、请求 ID、请求大小限制、基础限流、结构化错误、JSONL/SQLite 审计持久化、按 ticket 查询和脱敏输入摘要。
- 补齐 Prometheus 指标、滑动窗口异常检测、drift 检测、离线评测报告、Docker/Compose/K8s 部署模板和企业级成熟度评审文档；测试从 77 个扩展到 107 个并通过 `enterprise-check`。

这版更适合 GitHub 作品集，不会把展示项目说成真实公司上线项目。

## 2. STAR 叙事

Situation：

公司直播/社交业务里，IM 私聊是黑灰产高发场景。原审核系统主要依赖规则引擎和文本二分类模型，只能判断“有没有违规”，不能融合行为信号，也不能支撑警告、限号、封号等差异化处置。

Task：

我的目标是设计一个能在生产链路落地的统一审核模型，既要看懂聊天语义，也要结合异地登录、进房、关注、打赏等行为证据，并输出风险等级、违规判定、处置建议和解释依据。

Action：

我先和业务运营对齐违规 taxonomy，把 11 类主题拆成 47 个子主题，并写 low/mid/high rubric。数据上，我把历史工单脱敏重采样，训练分级案例生成器补长尾，再用上一轮模型误判样本做 refinement，最后叠加公开安全数据补文本泛化。模型上，我用 Qwen3.5-27B 做 completion-only 多任务 SFT，让单模型同时学习 risk、judgment、handling 和解释字段。工程上，我设计 JSON 输出协议、后处理校验、策略路由、人审复核和线上监控。

Result：

最终模型在自构 1024 条人审测试集上 final_judgment Acc 达到 82.1，risk macro-F1 75.6，handling macro-F1 73.2，ban_account FPR 控到 2.6%。消融显示行为证据是最大单点贡献，去掉后 risk macro-F1 明显下降。方案上线时采用 shadow、小流量、全量灰度，并保留规则引擎兜底。

## 3. 1 分钟讲法

“我做的是直播/社交 IM 私聊违规审核模型。原系统只看聊天文本做 safe/unsafe 二分类，没法利用打赏、进房、关注、异地登录这些行为信号，也不能直接支持 warning、limit、ban 这种处置。我把业务违规拆成 11 类主题和 47 个子主题，设计 low/mid/high rubric，然后构建历史工单、合成样本、灰区 hard sample 和公开安全数据组成的训练集，在 Qwen3.5-27B 上做 completion-only 多任务 SFT。模型一次输出风险等级、违规判定、处置建议和解释依据。最终在 1024 条人审测试集上 Acc 82.1，risk macro-F1 75.6，handling macro-F1 73.2，ban FPR 2.6%。这个项目的核心不是单纯调模型，而是把业务审核做成了可解释、可路由、可灰度上线的数据闭环系统。”

## 4. 3 分钟讲法

“这个项目的背景是 IM 私聊风控。直播和社交场景里，很多违规不是文本一眼能看出来的，比如代刷包榜经常用‘今晚老规矩’这种暗语，必须结合短时间大额打赏、进房、关注等行为才能判断。原系统是规则引擎加文本二分类，规则维护成本高，二分类也无法支持差异化处置。

我做的第一步是重新定义任务。输入不是单条文本，而是 `audit_scene / chat_evidence_list / behavior_abnormal_list` 三段证据；输出也不是 safe/unsafe，而是 `risk_level / final_judgment / handling_suggestion`，再加关联分析和判定依据。

第二步是数据。我把历史审核工单脱敏后按主题和处置档位重采样，得到 24.5K；然后按 low/mid/high 分别训练案例生成器，补长尾和边界样本，得到 11.6K；再用上一轮模型误判样本做 refinement，通过 self、Qwen-flash 和规则引擎 committee 过滤，回灌 2.6K hard sample；最后用公开安全数据补通用文本能力。

第三步是模型。我选 Qwen3.5-27B 做 completion-only 多任务 SFT，只对 assistant 的 JSON 输出算 loss。多任务的原因是风险等级、违规判定、处置建议不是独立问题，单模型能共享证据理解，也能避免多个模型输出冲突。

结果上，自构测试集 final_judgment Acc 82.1，risk macro-F1 75.6，handling macro-F1 73.2，ban FPR 2.6%。消融里去掉行为证据掉点最大，说明这个项目的核心收益确实来自语义和行为融合。上线设计上，我用 vLLM 部署，后面接 JSON 校验、策略路由、人审复核和监控回流，ban 不直接执行，必须人审。”

## 5. 5 分钟讲法结构

1. 业务背景：IM 私聊黑灰产、文本二分类不足、行为证据重要。
2. 任务定义：三段输入、三层输出、解释字段。
3. 违规体系：11 类主题、47 个子主题、low/mid/high rubric。
4. 数据构造：历史工单、合成池、refinement、公开安全数据。
5. 模型训练：Qwen3.5-27B、completion-only、多任务 SFT。
6. 评测结果：核心指标、P0/P1、公开 benchmark、ban FPR。
7. 消融结论：行为证据、refinement、多任务、模型尺寸。
8. 生产落地：vLLM、JSON 后处理、策略路由、人审、监控、回流。
9. 风险控制：数据泄漏、合成偏移、上游特征污染、重处罚误杀。
10. 总结价值：不是分类器，是业务审核系统。

## 6. 面试官听完应该留下的印象

- 你能从业务问题出发，而不是一上来讲模型。
- 你知道标签体系和 rubric 是模型效果的前提。
- 你理解多源数据和 hard sample 闭环。
- 你能用消融证明模块贡献。
- 你知道模型上线需要后处理、灰度、监控、人审和回滚。
- 你能把 LLM 训练、风控业务和生产工程连起来。
