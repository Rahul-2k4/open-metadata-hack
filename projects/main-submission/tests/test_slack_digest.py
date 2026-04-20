"""Tests for POST /slack/digest — daily summary endpoint."""
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


def _save(store, incident_id, signal, policy="allowed"):
    store.save_brief(
        brief={
            "incident_id": incident_id,
            "policy_state": policy,
            "what_failed": {"text": "x", "evidence_refs": [f"rca:{signal}"]},
            "what_is_impacted": {"text": "", "evidence_refs": []},
            "who_acts_first": {"text": "", "evidence_refs": []},
            "what_to_do_next": {"text": "", "evidence_refs": []},
        },
        delivery_status="rendered",
        primary_output="local_mirror",
    )


def test_digest_returns_400_when_slack_not_configured():
    app = create_app(_make_config(), retry_interval_seconds=0)
    client = TestClient(app)
    resp = client.post("/slack/digest")
    assert resp.status_code == 400
    assert "not_configured" in resp.json()["status"]


def test_digest_returns_summary_and_sends_when_configured(monkeypatch, tmp_path):
    db = str(tmp_path / "test.db")
    sent_payloads = []

    def fake_sender(payload):
        sent_payloads.append(payload)
        return True

    monkeypatch.setattr("incident_copilot.app.build_slack_sender", lambda: fake_sender)

    cfg = _make_config(db_path=db, slack_webhook_url="https://hooks.slack.com/test")
    app = create_app(cfg, retry_interval_seconds=0)
    client = TestClient(app)

    store = IncidentStore(db)
    _save(store, "inc-1", "null_ratio_exceeded", policy="approval_required")
    _save(store, "inc-2", "volume_drop")

    resp = client.post("/slack/digest")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "sent"
    assert body["total_incidents"] == 2
    assert body["signal_types"] == 2
    assert len(sent_payloads) == 1
    assert "Daily Digest" in sent_payloads[0]["text"]


def test_digest_falls_back_when_send_fails(monkeypatch, tmp_path):
    db = str(tmp_path / "test.db")

    def failing_sender(payload):
        return False

    monkeypatch.setattr("incident_copilot.app.build_slack_sender", lambda: failing_sender)

    cfg = _make_config(db_path=db, slack_webhook_url="https://hooks.slack.com/test")
    app = create_app(cfg, retry_interval_seconds=0)
    client = TestClient(app)

    resp = client.post("/slack/digest")
    assert resp.status_code == 200
    assert resp.json()["status"] == "fallback"


def test_digest_text_includes_signal_types(monkeypatch, tmp_path):
    db = str(tmp_path / "test.db")

    def fake_sender(payload):
        return True

    monkeypatch.setattr("incident_copilot.app.build_slack_sender", lambda: fake_sender)

    cfg = _make_config(db_path=db, slack_webhook_url="https://hooks.slack.com/test")
    app = create_app(cfg, retry_interval_seconds=0)
    client = TestClient(app)

    store = IncidentStore(db)
    _save(store, "inc-1", "null_ratio_exceeded")
    _save(store, "inc-2", "referential_break", policy="approval_required")

    resp = client.post("/slack/digest")
    body = resp.json()
    assert "Null Ratio Exceeded" in body["text"] or "null_ratio_exceeded" in body["text"].lower()
