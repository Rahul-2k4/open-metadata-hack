from incident_copilot.policy import evaluate_policy


def test_pii_sensitive_requires_steward_approval():
    assets = [{"classifications": ["PII.Sensitive"]}]
    out = evaluate_policy("inc-1", assets)
    assert out.status == "approval_required"
    assert out.required_approver_role == "data_steward"


def test_no_pii_sensitive_is_allowed():
    assets = [{"classifications": ["Finance.Public"]}]
    out = evaluate_policy("inc-1", assets)
    assert out.status == "allowed"
