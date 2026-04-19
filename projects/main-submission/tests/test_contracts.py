from incident_copilot.contracts import BriefBlock, PolicyDecision, DeliveryResult


def test_brief_block_requires_evidence_refs():
    block = BriefBlock(text="what failed", evidence_refs=["incident_ref", "test_ref"])
    assert block.evidence_refs == ["incident_ref", "test_ref"]


def test_policy_decision_has_reason_codes_and_approver():
    item = PolicyDecision(
        incident_id="inc-1",
        status="approval_required",
        reason_codes=["PII_SENSITIVE_IMPACTED"],
        required_approver_role="data_steward",
    )
    assert item.required_approver_role == "data_steward"


def test_delivery_result_tracks_primary_output():
    out = DeliveryResult(slack_status="failed", local_status="rendered", primary_output="local_mirror")
    assert out.primary_output == "local_mirror"
