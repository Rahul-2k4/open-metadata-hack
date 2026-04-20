"""Incident dashboard — single-page HTML list of recent triage briefs."""
import html as _html
from datetime import datetime, timezone


_CSS = """
* { box-sizing: border-box; margin: 0; padding: 0; }
body {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
  background: #0f1115; color: #e6e8eb; padding: 32px 16px; line-height: 1.5;
}
.container { max-width: 1100px; margin: 0 auto; }
header {
  display: flex; align-items: center; justify-content: space-between;
  padding-bottom: 20px; border-bottom: 1px solid #1f2430; margin-bottom: 24px;
}
h1 { font-size: 22px; font-weight: 600; letter-spacing: -0.01em; }
.subtitle { font-size: 13px; color: #8b93a7; margin-top: 4px; }
.status-row { display: flex; gap: 8px; flex-wrap: wrap; }
.pill {
  display: inline-flex; align-items: center; gap: 6px;
  padding: 5px 10px; border-radius: 999px;
  font-size: 11px; font-weight: 600; letter-spacing: 0.03em; text-transform: uppercase;
  background: #151922; border: 1px solid #1f2430; color: #8b93a7;
}
.pill.on { background: #0f2a1a; border-color: #235a32; color: #8eecae; }
.pill.off { background: #1a0f0f; border-color: #4a2828; color: #cf7c7c; }
.dot { width: 6px; height: 6px; border-radius: 50%; background: currentColor; }
table { width: 100%; border-collapse: collapse; margin-top: 8px; }
th, td {
  text-align: left; padding: 12px 14px; border-bottom: 1px solid #1f2430;
  font-size: 13px; vertical-align: middle;
}
th { font-size: 11px; font-weight: 600; color: #8b93a7; text-transform: uppercase; letter-spacing: 0.08em; }
tr:hover td { background: #12161e; }
td a { color: #9ecdff; text-decoration: none; font-family: ui-monospace, SFMono-Regular, Menlo, monospace; }
td a:hover { text-decoration: underline; }
.badge {
  display: inline-block; padding: 3px 8px; border-radius: 4px;
  font-size: 10px; font-weight: 700; letter-spacing: 0.05em; text-transform: uppercase;
}
.badge.approval_required { background: #3a1b1b; color: #ff9b9b; }
.badge.allowed { background: #1b3a26; color: #8eecae; }
.delivery {
  font-size: 11px; font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
  color: #8b93a7; padding: 2px 6px; background: #0f1115; border: 1px solid #2a3040;
  border-radius: 3px;
}
.delivery.slack { color: #9ecdff; }
.delivery.local_mirror { color: #ffcf8e; }
.truncate { max-width: 360px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; color: #c0c5d1; }
.empty {
  text-align: center; padding: 60px 20px; color: #5a6275;
  border: 1px dashed #1f2430; border-radius: 12px; margin-top: 24px;
}
.empty h2 { font-size: 16px; font-weight: 500; color: #8b93a7; margin-bottom: 8px; }
.empty code {
  display: inline-block; padding: 4px 8px; background: #151922; border-radius: 4px;
  font-size: 12px; color: #9ecdff; font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
}
footer {
  margin-top: 32px; padding-top: 16px; border-top: 1px solid #1f2430;
  font-size: 11px; color: #5a6275; text-align: center;
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
}
"""


def _format_time(ts: float) -> str:
    if not ts:
        return ""
    return datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%d %H:%M UTC")


def _status_pill(label: str, on: bool) -> str:
    cls = "on" if on else "off"
    return f'<span class="pill {cls}"><span class="dot"></span>{_html.escape(label)}</span>'


def render_dashboard_html(
    rows: list[dict],
    total: int,
    has_openmetadata: bool,
    has_slack: bool,
    has_ai: bool,
) -> str:
    pills = (
        _status_pill("OpenMetadata", has_openmetadata)
        + _status_pill("Slack", has_slack)
        + _status_pill("AI narratives", has_ai)
    )

    if not rows:
        body = """
          <div class="empty">
            <h2>No incidents yet</h2>
            <p>Configure an OpenMetadata alert destination to point at:</p>
            <p><code>POST /webhooks/incidents</code></p>
            <p style="margin-top:14px">Or run <code>./scripts/verify.sh</code> to see a sample incident flow.</p>
          </div>
        """
    else:
        body_rows = []
        for r in rows:
            brief = r.get("brief") or {}
            what_failed = (brief.get("what_failed") or {}).get("text", "")
            incident_id = r.get("incident_id", "")
            policy = r.get("policy_state", "allowed")
            primary = r.get("primary_output", "")
            delivery = r.get("delivery_status", "")
            updated = _format_time(r.get("updated_at", 0) or 0)

            body_rows.append(f"""
              <tr>
                <td><a href="/incidents/{_html.escape(incident_id)}/view">{_html.escape(incident_id)}</a></td>
                <td><span class="badge {_html.escape(policy)}">{_html.escape(policy)}</span></td>
                <td class="truncate">{_html.escape(what_failed)}</td>
                <td><span class="delivery {_html.escape(primary)}">{_html.escape(primary)} · {_html.escape(delivery)}</span></td>
                <td>{_html.escape(updated)}</td>
              </tr>""")
        body = f"""
          <table>
            <thead>
              <tr><th>Incident</th><th>Policy</th><th>What failed</th><th>Delivery</th><th>Updated</th></tr>
            </thead>
            <tbody>{"".join(body_rows)}</tbody>
          </table>
        """

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Incident Copilot · Dashboard</title>
<style>{_CSS}</style>
</head>
<body>
<div class="container">
  <header>
    <div>
      <h1>Incident Copilot</h1>
      <div class="subtitle">{total} incident{'s' if total != 1 else ''} · OpenMetadata DQ triage</div>
    </div>
    <div class="status-row">{pills}</div>
  </header>
  {body}
  <footer>evidence-backed · deterministic · reproducible · click an incident ID for the full brief</footer>
</div>
</body>
</html>
"""
