# Task Plan

- [x] Add tests for Slack sender webhook success, failure, and not-configured fallback.
- [x] Add facade test coverage for env-driven Slack send attempts and deterministic payload hashing.
- [x] Implement the minimal stdlib webhook sender and wire `notify_slack_tool` to use it.
- [x] Run targeted pytest, then the full suite, and fix any regressions.
- [x] Record verification notes and commit the green change.

## Review

- Slack delivery now attempts a real webhook POST when `SLACK_WEBHOOK_URL` or `SLACK_WEBHOOK` is set, and still returns `not_configured` with `fallback=local_mirror` when no webhook is present.
- Canonical payload hashing remains stable because the facade still hashes the sorted JSON brief.
- Verification: `.venv/bin/python -m pytest -q tests/test_mcp_facade.py tests/test_slack_sender.py` and `.venv/bin/python -m pytest -q`.

## Task C/D Review Fixes

- [x] Add structuredContent-first parsing in the MCP transport client while keeping legacy content-shape compatibility.
- [x] Cover MCP transport HTTPError and URLError branches with direct tests.
- [x] Exercise resolver fallback through `MCPTransportClientError` on the real client path.
- [x] Make Slack sender reject malformed/non-dict `brief` payloads without crashing.
- [x] Isolate the notify hash test from ambient Slack webhook env vars.
- [x] Verify the focused task suite and the full pytest run.
