from im_guard_ml.data_audit import audit_dataset, detect_pii_types


def test_detect_pii_types_finds_email_phone_and_id_card():
    row = {
        "ticket_id": "pii-1",
        "audit_scene": {},
        "chat_evidence_list": [{"original_content": "邮箱 a@example.com 手机 13800138000 身份证 110101199003077771"}],
        "behavior_abnormal_list": [],
        "label": {
            "risk_level": "low_risk",
            "topic": "无主题",
            "final_judgment": "not_exist_violation",
            "handling_suggestion": "ignore",
        },
    }

    assert set(detect_pii_types(row)) == {"email", "phone_cn", "id_card_cn"}
    report = audit_dataset([row])
    assert report["pii_risk_count"] == 3
    assert report["pii_risk_by_type"]["email"] == 1
