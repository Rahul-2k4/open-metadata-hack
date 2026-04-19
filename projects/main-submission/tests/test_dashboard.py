from incident_copilot.dashboard_renderer import render_dashboard_html


def test_empty_dashboard_shows_guidance():
    html = render_dashboard_html([], total=0, has_openmetadata=False, has_slack=False, has_ai=False)
    assert "No incidents yet" in html or "no incidents" in html.lower()
    assert "<!doctype html>" in html.lower()


def test_dashboard_lists_incidents():
    rows = [
        {
            "incident_id": "inc-1",
            "policy_state": "approval_required",
            "primary_output": "local_mirror",
            "delivery_status": "failed",
            "updated_at": 1713436800.0,
            "brief": {
                "incident_id": "inc-1",
                "what_failed": {"text": "Null ratio exceeded"},
            },
        },
        {
            "incident_id": "inc-2",
            "policy_state": "allowed",
            "primary_output": "slack",
            "delivery_status": "sent",
            "updated_at": 1713436801.0,
            "brief": {"incident_id": "inc-2", "what_failed": {"text": "Volume drop"}},
        },
    ]
    html = render_dashboard_html(rows, total=2, has_openmetadata=True, has_slack=True, has_ai=False)
    assert "inc-1" in html
    assert "inc-2" in html
    assert "Null ratio exceeded" in html
    assert "Volume drop" in html
    assert "approval_required" in html


def test_dashboard_shows_integration_status():
    html = render_dashboard_html([], total=0, has_openmetadata=True, has_slack=False, has_ai=True)
    assert "OpenMetadata" in html
    assert "Slack" in html
    assert "AI" in html


def test_dashboard_links_to_incident_view():
    rows = [{
        "incident_id": "inc-x",
        "policy_state": "allowed",
        "primary_output": "slack",
        "delivery_status": "sent",
        "updated_at": 1713436800.0,
        "brief": {"incident_id": "inc-x", "what_failed": {"text": "x"}},
    }]
    html = render_dashboard_html(rows, total=1, has_openmetadata=True, has_slack=True, has_ai=True)
    assert "/incidents/inc-x/view" in html


def test_dashboard_escapes_html_in_payload():
    rows = [{
        "incident_id": "inc-xss",
        "policy_state": "allowed",
        "primary_output": "slack",
        "delivery_status": "sent",
        "updated_at": 1713436800.0,
        "brief": {"incident_id": "inc-xss", "what_failed": {"text": "<script>alert(1)</script>"}},
    }]
    html = render_dashboard_html(rows, total=1, has_openmetadata=True, has_slack=True, has_ai=True)
    assert "<script>" not in html
    assert "&lt;script&gt;" in html
