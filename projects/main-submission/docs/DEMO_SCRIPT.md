# 2-Minute Demo Script

Use this when recording the hackathon submission video. Keep terminal font large (e.g. 18pt).

---

## Scene 1 — The problem (15 s)

**Voice-over:**
> When a data quality check fails in OpenMetadata, the on-call engineer has to gather four things by hand: what failed, who's affected downstream, who should act, and whether governance allows action. That takes minutes — sometimes hours — per incident.

**Visual:** Show OpenMetadata UI with a failed test, or a Slack channel with an incident ping.

---

## Scene 2 — One-click demo (30 s)

**Voice-over:**
> This copilot does it in one command. Reproducible, deterministic, evidence-backed.

**Terminal:**
```bash
cd projects/main-submission
./scripts/verify.sh
```

**Watch for:** `113 passed`, `determinism verified`, 4-block brief printing in colour.

---

## Scene 3 — Open the HTML brief (20 s)

**Voice-over:**
> Every run also produces a judge-ready visual report.

**Terminal:**
```bash
open runtime/local_mirror/latest_brief.html   # macOS
xdg-open runtime/local_mirror/latest_brief.html  # Linux
```

**Visual:** show the HTML page — the red `APPROVAL_REQUIRED` badge, four cards, evidence tags at the bottom of each card.

---

## Scene 4 — Determinism proof (15 s)

**Voice-over:**
> Judges can reproduce this exactly — same md5 hash every run.

**Terminal:**
```bash
python3 scripts/run_demo.py --replay runtime/fixtures/replay_event.json --context runtime/fixtures/replay_om_context.json --output /tmp/a.json
python3 scripts/run_demo.py --replay runtime/fixtures/replay_event.json --context runtime/fixtures/replay_om_context.json --output /tmp/b.json
md5sum /tmp/a.json /tmp/b.json
```

---

## Scene 5 — MCP composability (20 s)

**Voice-over:**
> It's also an MCP server — compose it with OpenMetadata's MCP, Slack MCP, or any agent framework.

**Terminal:**
```bash
python3 -c "
import sys; sys.path.insert(0, 'src')
from incident_copilot.mcp_facade import get_rca_tool, score_impact_tool
print(get_rca_tool('tc-1', 'null_ratio_exceeded'))
"
```

**Visual:** highlight the cause tree returned.

---

## Scene 6 — Problem-statement coverage (20 s)

**Voice-over:**
> This single project covers six hackathon problem statements: RCA, impact scoring, AI recommendations, multi-MCP orchestration, MCP alert tools, and Slack delivery.

**Visual:** flash the coverage table from the README.

---

## Closing (10 s)

**Voice-over:**
> Deterministic. Evidence-backed. Works without an API key. Ships an HTML report, a terminal TUI, a Slack post, and an MCP server — all from the same canonical payload.

**End card:** repo URL + 4-block brief screenshot.

---

## Pre-recording checklist

- [ ] `./scripts/verify.sh` passes clean
- [ ] `runtime/local_mirror/latest_brief.html` opens in a browser
- [ ] Terminal colour works (`echo -e '\033[31mRED\033[0m'`)
- [ ] Font ≥ 16pt so viewers on phones can read
- [ ] Optional: `OPENROUTER_API_KEY` set to show Claude-generated narratives (more impressive)
- [ ] Optional: `SLACK_WEBHOOK_URL` set to show real Slack delivery
