# 数据质量与审计

这份文档回答“训练前怎么保证数据可靠”。真实项目里，模型效果很多时候不是被算法限制，而是被脏数据、重复样本、标签冲突、测试集泄漏拖垮。

## 1. 数据审计目标

训练前至少检查：

- 必填字段是否完整。
- `label` 枚举是否合法。
- `final_judgment / risk_level / handling_suggestion` 是否逻辑一致。
- `ticket_id` 是否重复。
- 输入证据和标签是否完全重复。
- 公开二分类数据是否误注入重处置标签。
- 训练集和评测集是否存在 ID 或 payload 泄漏。

## 2. 仓库实现

对应代码：[src/im_guard_ml/data_audit.py](/Users/chenpeng/WorkSpace/文稿/Tencent/TencentCodeing/AI-IM-Guard-ML/src/im_guard_ml/data_audit.py)

CLI：

```bash
PYTHONPATH=src python3 -m im_guard_ml.cli \
  --config configs/default.yaml \
  audit-data data/samples/sample_cases.jsonl
```

如果要检查训练集和评测集泄漏：

```bash
PYTHONPATH=src python3 -m im_guard_ml.cli \
  --config configs/default.yaml \
  audit-data data/train/im_audit_train.jsonl \
  --eval-jsonl data/eval/internal_test.jsonl
```

## 3. 质量红线

建议红线：

- 必填字段缺失：0。
- 标签枚举错误：0。
- `not_exist_violation + ban_account`：0。
- 训练/评测 `ticket_id` 重合：0。
- 训练/评测 payload 完全重复：0。
- 公开二分类数据进入 `limit_account / ban_account`：0。

## 4. 面试表达

可以这样讲：

“我会在训练前做数据审计，不会直接把多源数据拼起来就训。审计包括 schema 完整性、标签逻辑一致性、重复样本、公开数据是否污染处置标签，以及训练/评测泄漏。尤其是这个项目里公开数据只有二分类标签，如果误参与 handling 训练，会污染业务处置边界。”

