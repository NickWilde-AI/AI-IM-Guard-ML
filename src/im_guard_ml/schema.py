from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class RiskLevel(StrEnum):
    LOW = "low_risk"
    MID = "mid_risk"
    HIGH = "high_risk"


class FinalJudgment(StrEnum):
    NOT_VIOLATION = "not_exist_violation"
    VIOLATION = "exist_violation"


class HandlingSuggestion(StrEnum):
    IGNORE = "ignore"
    WARNING = "warning"
    LIMIT_ACCOUNT = "limit_account"
    BAN_ACCOUNT = "ban_account"


TOPICS = [
    "代刷/包榜",
    "色情诱导",
    "诈骗引流",
    "私下交易",
    "政治敏感",
    "辱骂攻击",
    "未成年保护",
    "版权侵犯",
    "虚假信息",
    "自伤诱导",
    "违禁品交易",
    "无主题",
]


@dataclass(slots=True)
class AuditLabel:
    risk_level: str
    topic: str
    final_judgment: str
    handling_suggestion: str
    correlation_analysis: str = ""
    judgment_basis: str = ""

    @classmethod
    def safe_default(cls) -> "AuditLabel":
        return cls(
            risk_level=RiskLevel.LOW.value,
            topic="无主题",
            final_judgment=FinalJudgment.NOT_VIOLATION.value,
            handling_suggestion=HandlingSuggestion.IGNORE.value,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "risk_level": self.risk_level,
            "topic": self.topic,
            "correlation_analysis": self.correlation_analysis,
            "final_judgment": self.final_judgment,
            "judgment_basis": self.judgment_basis,
            "handling_suggestion": self.handling_suggestion,
        }


@dataclass(slots=True)
class AuditCase:
    ticket_id: str
    audit_scene: dict[str, Any]
    chat_evidence_list: list[dict[str, Any]]
    behavior_abnormal_list: list[dict[str, Any]]
    label: AuditLabel | None = None
    hint_topic: str | None = None
    source: str = ""
    extra: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, obj: dict[str, Any]) -> "AuditCase":
        label_obj = obj.get("label")
        label = None
        if isinstance(label_obj, dict):
            label = AuditLabel(
                risk_level=label_obj.get("risk_level", RiskLevel.LOW.value),
                topic=label_obj.get("topic", "无主题"),
                correlation_analysis=label_obj.get("correlation_analysis", ""),
                final_judgment=label_obj.get("final_judgment", FinalJudgment.NOT_VIOLATION.value),
                judgment_basis=label_obj.get("judgment_basis", ""),
                handling_suggestion=label_obj.get("handling_suggestion", HandlingSuggestion.IGNORE.value),
            )
        known = {
            "ticket_id",
            "audit_scene",
            "chat_evidence_list",
            "behavior_abnormal_list",
            "label",
            "hint_topic",
            "source",
        }
        return cls(
            ticket_id=obj.get("ticket_id", ""),
            audit_scene=obj.get("audit_scene", {}),
            chat_evidence_list=obj.get("chat_evidence_list", []),
            behavior_abnormal_list=obj.get("behavior_abnormal_list", []),
            label=label,
            hint_topic=obj.get("hint_topic"),
            source=obj.get("source", ""),
            extra={k: v for k, v in obj.items() if k not in known},
        )

    def to_dict(self) -> dict[str, Any]:
        obj = {
            "ticket_id": self.ticket_id,
            "audit_scene": self.audit_scene,
            "chat_evidence_list": self.chat_evidence_list,
            "behavior_abnormal_list": self.behavior_abnormal_list,
            "source": self.source,
        }
        if self.hint_topic:
            obj["hint_topic"] = self.hint_topic
        if self.label:
            obj["label"] = self.label.to_dict()
        obj.update(self.extra)
        return obj


def validate_label(label: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if label.get("risk_level") not in {x.value for x in RiskLevel}:
        errors.append("risk_level must be low_risk, mid_risk, or high_risk")
    if label.get("final_judgment") not in {x.value for x in FinalJudgment}:
        errors.append("final_judgment must be exist_violation or not_exist_violation")
    if label.get("handling_suggestion") not in {x.value for x in HandlingSuggestion}:
        errors.append("handling_suggestion must be ignore, warning, limit_account, or ban_account")
    if label.get("topic", "无主题") not in TOPICS:
        errors.append("topic must be one of the configured business topics")
    if label.get("final_judgment") == FinalJudgment.NOT_VIOLATION.value:
        if label.get("handling_suggestion") not in {HandlingSuggestion.IGNORE.value, HandlingSuggestion.WARNING.value}:
            errors.append("not_exist_violation should not route to limit_account or ban_account")
    if label.get("handling_suggestion") == HandlingSuggestion.BAN_ACCOUNT.value:
        if label.get("risk_level") != RiskLevel.HIGH.value or label.get("final_judgment") != FinalJudgment.VIOLATION.value:
            errors.append("ban_account requires high_risk and exist_violation")
    return errors

