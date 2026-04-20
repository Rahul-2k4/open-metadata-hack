"""Tests for GET /rca-summary — aggregated RCA dashboard endpoint."""
import pytest
from fastapi.testclient import TestClient

from incident_copilot.app import create_app
from incident_copilot.config import AppConfig
from incident_copilot.store import IncidentStore


def _make_config(**overrides) -> AppConfig:
    defaults = dict(
        host="127.0.0.1", port=8080, db_path=":memory:", default_channel="#test",
        openmetadata_base_url=None, openmetadata_jwt_token=None, openmetadata_mcp_url=None,
        slack_webhook_url=None, openrouter_api_key=None, use_om_mcp=False,
        enable_poller=False, poller_interval_seconds=60.0,
    )
    defaults.update(overrides)
    return AppConfig(**defaults)


def _save_brief(store, incident_id, signal, policy="allowed"):
    store.save_brief(
        brief={
            "incident_id": incident_id,
            "policy_state": policy,
            "what_failed": {
                "text": "test",
                "evidence_refs": ["incident_ref", "test_ref", f"rca:{signal}"],
            },
            "what_is_impacted": {"text": "", "evidence_refs": []},
            "who_acts_first": {"text": "", "evidence_refs": []},
            "what_to_do_next": {"text": "", "evidence_refs": []},
        },
        delivery_status="rendered",
        primary_output="local_mirror",
    )


def test_rca_summary_empty_db(tmp_path):
    store = IncidentStore(str(tmp_path / "test.db"))
    result = store.rca_summary()
    assert result["total_incidents"] == 0
    assert result["signal_types"] == []


def test_rca_summary_groups_by_signal(tmp_path):
    store = IncidentStore(str(tmp_path / "test.db"))
    _save_brief(store, "inc-1", "null_ratio_exceeded")
    _save_brief(store, "inc-2", "null_ratio_exceeded")
    _save_brief(store, "inc-3", "volume_drop")
    result = store.rca_summary()
    assert result["total_incidents"] == 3
    by_signal = {b["signal_type"]: b for b in result["signal_types"]}
    assert by_signal["null_ratio_exceeded"]["count"] == 2
    assert by_signal["volume_drop"]["count"] == 1


def test_rca_summary_counts_approval_required(tmp_path):
    store = IncidentStore(str(tmp_path / "test.db"))
    _save_brief(store, "inc-1", "null_ratio_exceeded", policy="approval_required")
    _save_brief(store, "inc-2", "null_ratio_exceeded", policy="allowed")
    result = store.rca_summary()
    bucket = result["signal_types"][0]
    assert bucket["approval_required"] == 1
    assert bucket["count"] == 2


def test_rca_summary_recent_incidents_capped_at_five(tmp_path):
    store = IncidentStore(str(tmp_path / "test.db"))
    for i in range(8):
        _save_brief(store, f"inc-{i}", "volume_drop")
    result = store.rca_summary()
    bucket = result["signal_types"][0]
    assert bucket["count"] == 8
    assert len(bucket["recent_incidents"]) == 5


def test_rca_summary_sorted_by_count_desc(tmp_path):
    store = IncidentStore(str(tmp_path / "test.db"))
    for i in range(3):
        _save_brief(store, f"vol-{i}", "volume_drop")
    _save_brief(store, "null-1", "null_ratio_exceeded")
    result = store.rca_summary()
    assert result["signal_types"][0]["signal_type"] == "volume_drop"


def test_rca_summary_api_endpoint(tmp_path):
    db = str(tmp_path / "test.db")
    app = create_app(_make_config(db_path=db), retry_interval_seconds=0)
    client = TestClient(app)

    store = IncidentStore(db)
    _save_brief(store, "inc-1", "referential_break")
    _save_brief(store, "inc-2", "referential_break", policy="approval_required")

    resp = client.get("/rca-summary")
    assert resp.status_code == 200
    body = resp.json()
    assert body["total_incidents"] == 2
    assert body["signal_types"][0]["signal_type"] == "referential_break"
    assert body["signal_types"][0]["approval_required"] == 1
