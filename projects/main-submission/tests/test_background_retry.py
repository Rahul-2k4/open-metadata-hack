import time
from unittest.mock import MagicMock

from incident_copilot.background_retry import retry_pending_deliveries
from incident_copilot.delivery_queue import DeliveryQueue
from incident_copilot.store import IncidentStore


SAMPLE_BRIEF = {
    "incident_id": "inc-r-1",
    "policy_state": "allowed",
    "what_failed": {"text": "x", "evidence_refs": []},
    "what_is_impacted": {"text": "x", "evidence_refs": []},
    "who_acts_first": {"text": "x", "evidence_refs": []},
    "what_to_do_next": {"text": "x", "evidence_refs": []},
}


def _setup(tmp_path):
    db = str(tmp_path / "db.sqlite")
    store = IncidentStore(db)
    queue = DeliveryQueue(db)
    store.save_brief(SAMPLE_BRIEF, delivery_status="failed", primary_output="local_mirror")
    queue.enqueue("inc-r-1", reason="SLACK_SEND_FAILED")
    return store, queue


def test_retry_success_clears_queue(tmp_path):
    store, queue = _setup(tmp_path)
    sender = MagicMock(return_value=True)
    result = retry_pending_deliveries(store=store, queue=queue, slack_sender=sender)
    assert result["retried"] == 1
    assert result["succeeded"] == 1
    assert result["failed"] == 0
    assert queue.pending() == []
    sender.assert_called_once()


def test_retry_failure_leaves_in_queue(tmp_path):
    store, queue = _setup(tmp_path)
    sender = MagicMock(return_value=False)
    result = retry_pending_deliveries(store=store, queue=queue, slack_sender=sender, backoff_seconds=0)
    assert result["retried"] == 1
    assert result["failed"] == 1
    pending = queue.pending()
    assert len(pending) == 1
    assert pending[0]["attempts"] == 1


def test_retry_no_sender_is_noop(tmp_path):
    store, queue = _setup(tmp_path)
    result = retry_pending_deliveries(store=store, queue=queue, slack_sender=None)
    assert result["retried"] == 0
    assert len(queue.pending()) == 1  # unchanged


def test_retry_missing_brief_drops_entry(tmp_path):
    db = str(tmp_path / "db.sqlite")
    store = IncidentStore(db)
    queue = DeliveryQueue(db)
    queue.enqueue("inc-gone", reason="SLACK_SEND_FAILED")
    sender = MagicMock(return_value=True)
    result = retry_pending_deliveries(store=store, queue=queue, slack_sender=sender)
    assert result["retried"] == 1
    assert result["dropped_missing_brief"] == 1
    sender.assert_not_called()


def test_retry_exception_counts_as_failure(tmp_path):
    store, queue = _setup(tmp_path)
    sender = MagicMock(side_effect=RuntimeError("boom"))
    result = retry_pending_deliveries(store=store, queue=queue, slack_sender=sender, backoff_seconds=0)
    assert result["failed"] == 1
    assert queue.pending()[0]["attempts"] == 1
    assert "boom" in queue.pending()[0]["last_error"]
