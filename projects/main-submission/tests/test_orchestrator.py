from incident_copilot.orchestrator import run_pipeline


def test_golden_path_returns_approval_required():
    raw = {
        "incident_id": "inc-1",
        "entity_fqn": "svc.db.customer_profiles",
        "test_case_id": "tc-1",
        "severity": "high",
        "occurred_at": "2026-04-18T00:00:00Z",
        "raw_ref": "evt-1",
    }
    om_data = {
        "failed_test": {"message": "null ratio high"},
        "lineage": [{"fqn": "svc.db.customer_curated", "distance": 1, "business_facing": True, "owner": "dre-oncall"}],
        "owners": {"asset_owner": "dre-oncall"},
        "classifications": {"svc.db.customer_curated": ["PII.Sensitive"]},
    }
    out = run_pipeline(raw, om_data, slack_sender=lambda _b: True)
    assert out["brief"]["policy_state"] == "approval_required"


def test_degraded_path_carries_reason_codes():
    out = run_pipeline(
        {"incident_id": "inc-1"},
        {"failed_test": {}, "lineage": [], "owners": {}, "classifications": {}},
        slack_sender=lambda _b: False,
    )
    assert out["delivery"]["delivery"].primary_output == "local_mirror"
    assert out["fallback_reason_codes"]
