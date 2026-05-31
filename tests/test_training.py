"""Tests for training module (field-level loss masking)."""

import pytest

from im_guard_ml.training import _normalize_public_binary_labels, FieldLevelMaskCollator


class TestNormalizePublicBinaryLabels:
    def test_internal_data_unchanged(self):
        case = {
            "task_type": "multi_label",
            "label": {
                "risk_level": "high_risk",
                "final_judgment": "exist_violation",
                "handling_suggestion": "ban_account",
                "topic": "代刷/包榜",
            },
        }
        result = _normalize_public_binary_labels(case)
        assert result["label"]["risk_level"] == "high_risk"
        assert result["label"]["handling_suggestion"] == "ban_account"

    def test_public_violation_capped(self):
        case = {
            "task_type": "public_binary",
            "label": {
                "risk_level": "high_risk",
                "final_judgment": "exist_violation",
                "handling_suggestion": "ban_account",
                "topic": "辱骂攻击",
            },
        }
        result = _normalize_public_binary_labels(case)
        assert result["label"]["risk_level"] == "mid_risk"
        assert result["label"]["handling_suggestion"] == "warning"

    def test_public_safe_normalized(self):
        case = {
            "task_type": "public_binary",
            "label": {
                "risk_level": "mid_risk",
                "final_judgment": "not_exist_violation",
                "handling_suggestion": "warning",
                "topic": "辱骂攻击",
            },
        }
        result = _normalize_public_binary_labels(case)
        assert result["label"]["risk_level"] == "low_risk"
        assert result["label"]["handling_suggestion"] == "ignore"
        assert result["label"]["topic"] == "无主题"

    def test_no_label_unchanged(self):
        case = {"task_type": "public_binary", "label": "not_a_dict"}
        result = _normalize_public_binary_labels(case)
        assert result["label"] == "not_a_dict"

    def test_missing_task_type_unchanged(self):
        case = {
            "label": {
                "risk_level": "high_risk",
                "final_judgment": "exist_violation",
                "handling_suggestion": "ban_account",
            },
        }
        result = _normalize_public_binary_labels(case)
        assert result["label"]["handling_suggestion"] == "ban_account"
