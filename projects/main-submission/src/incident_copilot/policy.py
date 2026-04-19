from incident_copilot.contracts import PolicyDecision


def evaluate_policy(incident_id, impacted_assets):
    has_pii_sensitive = any(
        "PII.Sensitive" in (a.get("classifications") or [])
        for a in impacted_assets
    )
    if has_pii_sensitive:
        return PolicyDecision(
            incident_id=incident_id,
            status="approval_required",
            reason_codes=["PII_SENSITIVE_IMPACTED"],
            required_approver_role="data_steward",
        )
    return PolicyDecision(
        incident_id=incident_id,
        status="allowed",
        reason_codes=[],
        required_approver_role=None,
    )
