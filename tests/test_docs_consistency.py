from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


STALE_PHRASES = [
    "测试从 77 个扩展到 107 个",
    "测试从77个扩展到107个",
    "107 个并通过 `enterprise-check`",
    "缺生产级压测、契约测试",
]


def test_offer_docs_do_not_contain_known_stale_claims():
    docs = [
        "docs/RESUME_AND_STORYLINE.md",
        "docs/OFFER_DEFENSE_QA.md",
        "docs/INTERVIEW_SPEAKING_SCRIPT.md",
        "docs/INTERVIEW_PLAYBOOK.md",
        "docs/ENTERPRISE_READINESS_REVIEW.md",
    ]
    combined = "\n".join((ROOT / rel).read_text(encoding="utf-8") for rel in docs)

    for phrase in STALE_PHRASES:
        assert phrase not in combined


def test_offer_docs_mention_current_enterprise_gates():
    text = (ROOT / "docs" / "OFFER_DEFENSE_QA.md").read_text(encoding="utf-8")

    assert "OpenAPI 契约门禁" in text
    assert "production preflight" in text
    assert "模型注册表检查" in text
    assert "API 轻量压测脚本" in text
