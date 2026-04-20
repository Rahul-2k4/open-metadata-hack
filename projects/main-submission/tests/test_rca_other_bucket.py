"""Tests for RCA 'other' bucket — Claude classifies novel signals."""
import pytest
from incident_copilot.rca_engine import build_rca, _claude_classify_signal


def test_unknown_signal_uses_template_when_ai_unavailable(monkeypatch):
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    result = build_rca(
        failed_test={"message": "some exotic failure we've never seen"},
        entity_fqn="svc.db.table",
        use_ai=True,
    )
    assert result.signal_type == "unknown"
    assert result.narrative_source == "template"
    assert "unclassified" in result.cause_tree


def test_unknown_signal_calls_claude_classify_when_ai_available(monkeypatch):
    classified = {
        "signal_type": "data_duplication",
        "cause_tree": ["duplicate_ingestion", "missing_dedup_key"],
        "narrative": "Duplicate rows detected — likely caused by missing dedup logic in the pipeline.",
    }
    monkeypatch.setattr("incident_copilot.rca_engine._claude_classify_signal", lambda ft, fqn: classified)
    monkeypatch.setattr("incident_copilot.rca_engine.is_available", lambda: True)

    result = build_rca(
        failed_test={"message": "duplicate rows in output"},
        entity_fqn="svc.db.table",
        use_ai=True,
    )
    assert result.signal_type == "data_duplication"
    assert result.cause_tree == ["duplicate_ingestion", "missing_dedup_key"]
    assert result.narrative_source == "claude"


def test_unknown_signal_falls_back_to_template_when_classify_raises(monkeypatch):
    def raise_exc(ft, fqn):
        raise RuntimeError("Claude timeout")

    monkeypatch.setattr("incident_copilot.rca_engine._claude_classify_signal", raise_exc)
    monkeypatch.setattr("incident_copilot.rca_engine.is_available", lambda: True)
    monkeypatch.setattr("incident_copilot.rca_engine._claude_narrative", lambda *a, **kw: (_ for _ in ()).throw(RuntimeError()))

    result = build_rca(
        failed_test={"message": "exotic failure"},
        entity_fqn="svc.db.table",
        use_ai=True,
    )
    assert result.signal_type == "unknown"
    assert "Unclassified" in result.narrative


def test_known_signal_does_not_call_classify(monkeypatch):
    calls = []

    def should_not_be_called(ft, fqn):
        calls.append(1)
        return {}

    monkeypatch.setattr("incident_copilot.rca_engine._claude_classify_signal", should_not_be_called)
    monkeypatch.setattr("incident_copilot.rca_engine.is_available", lambda: True)
    monkeypatch.setattr("incident_copilot.rca_engine._claude_narrative", lambda *a, **kw: "narrative text")

    result = build_rca(
        failed_test={"message": "null ratio 0.5 exceeded threshold"},
        entity_fqn="svc.db.table",
        use_ai=True,
    )
    assert calls == []
    assert result.signal_type == "null_ratio_exceeded"
