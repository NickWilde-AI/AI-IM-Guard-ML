from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from .dataio import read_jsonl, write_jsonl


PUBLIC_TOPIC_MAP = {
    "violence": "违禁品交易",
    "illegal": "违禁品交易",
    "sexual": "色情诱导",
    "harassment": "辱骂攻击",
    "hate": "辱骂攻击",
    "self_harm": "自伤诱导",
    "politics": "政治敏感",
}


def normalize_internal(row: dict[str, Any], source: str) -> dict[str, Any]:
    obj = dict(row)
    obj.setdefault("ticket_id", stable_id(source, row))
    obj.setdefault("source", source)
    obj.setdefault("audit_scene", {})
    obj.setdefault("chat_evidence_list", [])
    obj.setdefault("behavior_abnormal_list", [])
    return obj


def normalize_public(row: dict[str, Any], source: str) -> dict[str, Any]:
    content = row.get("content") or row.get("prompt") or row.get("response") or row.get("text") or ""
    raw_topic = row.get("topic") or row.get("category") or ""
    final = row.get("final_judgment") or row.get("harm_label") or row.get("label")
    final_judgment = "not_exist_violation" if str(final).lower() in {"safe", "0", "false", "not_exist_violation"} else "exist_violation"
    topic = PUBLIC_TOPIC_MAP.get(str(raw_topic).lower(), row.get("topic", "无主题" if final_judgment == "not_exist_violation" else "虚假信息"))
    return {
        "ticket_id": stable_id(source, row),
        "audit_scene": {
            "chat_type": "public_text",
            "user_intimacy": "unknown",
            "behavior_key_summary": {},
        },
        "chat_evidence_list": [{"original_content": content, "risk_point": "公开安全数据文本侧监督样本。"}],
        "behavior_abnormal_list": [],
        "label": {
            "risk_level": "low_risk" if final_judgment == "not_exist_violation" else "mid_risk",
            "topic": topic,
            "correlation_analysis": "",
            "final_judgment": final_judgment,
            "judgment_basis": "公开数据集二分类金标。",
            "handling_suggestion": "ignore" if final_judgment == "not_exist_violation" else "warning",
        },
        "source": source,
        "task_type": "public_binary",
    }


def stable_id(source: str, row: dict[str, Any]) -> str:
    payload = json.dumps(row, ensure_ascii=False, sort_keys=True)
    digest = hashlib.sha1(payload.encode("utf-8")).hexdigest()[:12]
    return f"{source}-{digest}"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m im_guard_ml.build_dataset")
    parser.add_argument("--internal", action="append", default=[], help="Internal JSONL path, can be repeated.")
    parser.add_argument("--public", action="append", default=[], help="Public binary JSONL path, can be repeated.")
    parser.add_argument("--out", required=True)
    args = parser.parse_args(argv)
    rows: list[dict[str, Any]] = []
    for path in args.internal:
        source = Path(path).stem
        rows.extend(normalize_internal(row, source) for row in read_jsonl(path))
    for path in args.public:
        source = Path(path).stem
        rows.extend(normalize_public(row, source) for row in read_jsonl(path))
    write_jsonl(args.out, rows)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

