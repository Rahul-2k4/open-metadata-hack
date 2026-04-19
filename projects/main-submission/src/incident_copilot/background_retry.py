"""Background retry worker — consumes DeliveryQueue, re-attempts Slack delivery.

Used by the FastAPI app as a periodic asyncio task. Pure-function core so it's
easy to test without a running event loop.
"""
from incident_copilot.delivery_queue import DeliveryQueue
from incident_copilot.store import IncidentStore


def retry_pending_deliveries(
    store: IncidentStore,
    queue: DeliveryQueue,
    slack_sender,
    limit: int = 20,
    backoff_seconds: float = 30.0,
) -> dict:
    """Process up to `limit` pending deliveries. Returns a summary dict.

    `slack_sender` matches the existing signature used throughout the codebase:
    a callable `(payload: dict) -> bool`. If `None`, retry is a no-op.
    """
    summary = {"retried": 0, "succeeded": 0, "failed": 0, "dropped_missing_brief": 0}

    if slack_sender is None:
        return summary

    for entry in queue.pending(limit=limit):
        summary["retried"] += 1
        incident_id = entry["incident_id"]

        row = store.fetch_by_id(incident_id)
        if row is None:
            summary["dropped_missing_brief"] += 1
            queue.mark_success(incident_id)  # drop — nothing to retry against
            continue

        brief = row["brief"]
        payload = {"channel": "slack", "incident_id": incident_id, "brief": brief}

        try:
            ok = bool(slack_sender(payload))
        except Exception as exc:
            queue.mark_failed(incident_id, last_error=str(exc), backoff_seconds=backoff_seconds)
            summary["failed"] += 1
            continue

        if ok:
            store.save_brief(brief, delivery_status="sent", primary_output="slack")
            queue.mark_success(incident_id)
            summary["succeeded"] += 1
        else:
            queue.mark_failed(incident_id, last_error="slack_sender returned False", backoff_seconds=backoff_seconds)
            summary["failed"] += 1

    return summary
