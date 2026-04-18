# Metadata Incident Copilot Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a deterministic, read-only OpenMetadata DQ incident copilot that produces an evidence-backed brief with `approval_required` when `PII.Sensitive` is impacted, and delivers the same brief to Slack and a local mirror fallback.

**Architecture:** The system normalizes one native incident event, resolves context from OpenMetadata (test failure, bounded lineage, ownership, classifications), applies deterministic impact and policy rules, and generates one canonical brief payload. Delivery has explicit degraded-mode behavior: if Slack fails, local mirror becomes primary while preserving full brief content.

**Tech Stack:** Python 3.14, pytest, dataclasses, standard library JSON/HTTP, Markdown docs in repo.

---

## References

- Spec: `docs/superpowers/specs/2026-04-18-metadata-incident-copilot-design.md`
- Apply DRY, YAGNI, TDD, and frequent commits.
- Relevant process guidance: @test-driven-development, @verification-before-completion.

## Scope Check

Single subsystem plan: **DQ incident decision-support copilot** only.  
Out of scope: auto-remediation, multi-incident support, broad chat UX.

## Planned File Structure

### Create

- `projects/main-submission/pyproject.toml`
- `projects/main-submission/README.md`
- `projects/main-submission/src/incident_copilot/__init__.py`
- `projects/main-submission/src/incident_copilot/contracts.py`
- `projects/main-submission/src/incident_copilot/adapter.py`
- `projects/main-submission/src/incident_copilot/context_resolver.py`
- `projects/main-submission/src/incident_copilot/owner_routing.py`
- `projects/main-submission/src/incident_copilot/impact.py`
- `projects/main-submission/src/incident_copilot/policy.py`
- `projects/main-submission/src/incident_copilot/brief.py`
- `projects/main-submission/src/incident_copilot/delivery.py`
- `projects/main-submission/src/incident_copilot/orchestrator.py`
- `projects/main-submission/src/incident_copilot/demo_harness.py`
- `projects/main-submission/scripts/run_demo.py`
- `projects/main-submission/tests/test_bootstrap_smoke.py`
- `projects/main-submission/tests/test_contracts.py`
- `projects/main-submission/tests/test_adapter.py`
- `projects/main-submission/tests/test_context_resolver.py`
- `projects/main-submission/tests/test_owner_routing.py`
- `projects/main-submission/tests/test_impact.py`
- `projects/main-submission/tests/test_policy.py`
- `projects/main-submission/tests/test_brief.py`
- `projects/main-submission/tests/test_delivery.py`
- `projects/main-submission/tests/test_orchestrator.py`
- `projects/main-submission/tests/test_demo_harness.py`
- `projects/main-submission/runtime/local_mirror/.gitkeep`
- `projects/main-submission/runtime/fixtures/replay_event.json`
- `projects/main-submission/runtime/fixtures/replay_om_context.json`

### Modify

- `docs/architecture.md`
- `docs/demo-script.md`
- `docs/submission-checklist.md`
- `docs/decision-log.md`

---

### Task 1: Bootstrap Package and Test Harness

**Files:**
- Create: `projects/main-submission/pyproject.toml`
- Create: `projects/main-submission/src/incident_copilot/__init__.py`
- Create: `projects/main-submission/tests/test_bootstrap_smoke.py`
- Modify: `projects/main-submission/README.md`

- [ ] **Step 1: Write failing smoke test**

```python
def test_package_importable():
    from incident_copilot import __all__  # noqa: F401
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest projects/main-submission/tests/test_bootstrap_smoke.py -v`  
Expected: `FAIL` with module import error.

- [ ] **Step 3: Add minimal package scaffold**

```python
# projects/main-submission/src/incident_copilot/__init__.py
__all__ = []
```

```toml
# projects/main-submission/pyproject.toml
[project]
name = "metadata-incident-copilot"
version = "0.1.0"
requires-python = ">=3.14"

[tool.pytest.ini_options]
pythonpath = ["src"]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest projects/main-submission/tests/test_bootstrap_smoke.py -v`  
Expected: `PASS`.

- [ ] **Step 5: Commit**

```bash
git add projects/main-submission/pyproject.toml \
  projects/main-submission/src/incident_copilot/__init__.py \
  projects/main-submission/tests/test_bootstrap_smoke.py \
  projects/main-submission/README.md
git commit -m "chore: scaffold incident copilot package and smoke test"
```

---

### Task 2: Define Canonical Contracts with Evidence and Degraded Modes

**Files:**
- Create: `projects/main-submission/src/incident_copilot/contracts.py`
- Test: `projects/main-submission/tests/test_contracts.py`

- [ ] **Step 1: Write failing contract tests**

```python
from incident_copilot.contracts import BriefBlock, PolicyDecision, DeliveryResult

def test_brief_block_requires_evidence_refs():
    block = BriefBlock(text="what failed", evidence_refs=["incident_ref", "test_ref"])
    assert block.evidence_refs == ["incident_ref", "test_ref"]

def test_policy_decision_has_reason_codes_and_approver():
    item = PolicyDecision(
        incident_id="inc-1",
        status="approval_required",
        reason_codes=["PII_SENSITIVE_IMPACTED"],
        required_approver_role="data_steward",
    )
    assert item.required_approver_role == "data_steward"

def test_delivery_result_tracks_primary_output():
    out = DeliveryResult(slack_status="failed", local_status="rendered", primary_output="local_mirror")
    assert out.primary_output == "local_mirror"
```

- [ ] **Step 2: Run tests to verify failure**

Run: `python -m pytest projects/main-submission/tests/test_contracts.py -v`  
Expected: `FAIL` due missing models.

- [ ] **Step 3: Implement dataclass contracts**

```python
from dataclasses import dataclass

@dataclass(frozen=True)
class BriefBlock:
    text: str
    evidence_refs: list[str]

@dataclass(frozen=True)
class PolicyDecision:
    incident_id: str
    status: str  # allowed | approval_required
    reason_codes: list[str]
    required_approver_role: str | None

@dataclass(frozen=True)
class DeliveryResult:
    slack_status: str
    local_status: str
    primary_output: str  # slack | local_mirror
    degraded_reason_codes: list[str] | None = None
```

- [ ] **Step 4: Run tests to verify pass**

Run: `python -m pytest projects/main-submission/tests/test_contracts.py -v`  
Expected: `PASS`.

- [ ] **Step 5: Commit**

```bash
git add projects/main-submission/src/incident_copilot/contracts.py \
  projects/main-submission/tests/test_contracts.py
git commit -m "feat: define evidence-linked contracts and delivery status models"
```

---

### Task 3: Implement Context Resolver

**Files:**
- Create: `projects/main-submission/src/incident_copilot/context_resolver.py`
- Test: `projects/main-submission/tests/test_context_resolver.py`

- [ ] **Step 1: Write failing resolver tests**

```python
from incident_copilot.context_resolver import resolve_context

def test_resolver_returns_required_context_sections():
    env = {"incident_id": "inc-1", "entity_fqn": "svc.db.customer_profiles"}
    fake_client = {
        "failed_test": {"name": "null_check", "message": "null ratio high"},
        "lineage": [{"fqn": "svc.db.customer_curated", "distance": 1}],
        "owners": {"asset_owner": "dre-oncall", "domain_owner": "domain-lead"},
        "classifications": {"svc.db.customer_curated": ["PII.Sensitive"]},
    }
    out = resolve_context(env, fake_client, max_depth=2)
    assert "failed_test" in out and "impacted_assets" in out and "fallback_reason_codes" in out
    assert out["impacted_assets"][0]["classifications"] == ["PII.Sensitive"]

def test_resolver_adds_reason_code_for_missing_owner():
    env = {"incident_id": "inc-1", "entity_fqn": "svc.db.customer_profiles"}
    fake_client = {"failed_test": {}, "lineage": [], "owners": {}, "classifications": {}}
    out = resolve_context(env, fake_client, max_depth=2)
    assert "MISSING_OWNER_METADATA" in out["fallback_reason_codes"]

def test_resolver_uses_classification_map_when_lineage_item_has_none():
    env = {"incident_id": "inc-1", "entity_fqn": "svc.db.customer_profiles"}
    fake_client = {
        "failed_test": {"message": "x"},
        "lineage": [{"fqn": "svc.db.customer_curated", "distance": 1}],
        "owners": {"asset_owner": "dre-oncall"},
        "classifications": {"svc.db.customer_curated": ["PII.Sensitive"]},
    }
    out = resolve_context(env, fake_client, max_depth=2)
    assert out["impacted_assets"][0]["classifications"] == ["PII.Sensitive"]
```

- [ ] **Step 2: Run tests to verify failure**

Run: `python -m pytest projects/main-submission/tests/test_context_resolver.py -v`  
Expected: `FAIL`.

- [ ] **Step 3: Implement minimal resolver**

```python
def resolve_context(envelope, om_client_data, max_depth=2):
    owners = om_client_data.get("owners", {})
    fallback_reason_codes = []
    if not owners.get("asset_owner") and not owners.get("domain_owner") and not owners.get("team_owner"):
        fallback_reason_codes.append("MISSING_OWNER_METADATA")
    classifications_map = om_client_data.get("classifications", {})
    impacted = []
    for item in om_client_data.get("lineage", []):
        if item.get("distance", 99) > max_depth:
            continue
        merged = dict(item)
        merged["classifications"] = merged.get("classifications") or classifications_map.get(merged.get("fqn"), [])
        impacted.append(merged)
    return {
        "incident_id": envelope["incident_id"],
        "failed_test": om_client_data.get("failed_test", {}),
        "impacted_assets": impacted,
        "owners": owners,
        "classifications": classifications_map,
        "fallback_reason_codes": fallback_reason_codes,
    }
```

- [ ] **Step 4: Run tests to verify pass**

Run: `python -m pytest projects/main-submission/tests/test_context_resolver.py -v`  
Expected: `PASS`.

- [ ] **Step 5: Commit**

```bash
git add projects/main-submission/src/incident_copilot/context_resolver.py \
  projects/main-submission/tests/test_context_resolver.py
git commit -m "feat: add context resolver with missing-metadata fallback codes"
```

---

### Task 4: Implement Owner Routing with Full Fallback Coverage

**Files:**
- Create: `projects/main-submission/src/incident_copilot/owner_routing.py`
- Test: `projects/main-submission/tests/test_owner_routing.py`

- [ ] **Step 1: Write failing fallback-chain tests**

```python
from incident_copilot.owner_routing import resolve_first_responder

def test_asset_owner_priority():
    assert resolve_first_responder("a", "d", "t", "#x") == ("a", "asset_owner")

def test_domain_owner_fallback():
    assert resolve_first_responder(None, "d", "t", "#x") == ("d", "domain_owner")

def test_team_owner_fallback():
    assert resolve_first_responder(None, None, "t", "#x") == ("t", "team_owner")

def test_default_channel_fallback():
    assert resolve_first_responder(None, None, None, "#x") == ("#x", "default_channel")
```

- [ ] **Step 2: Run tests to verify failure**

Run: `python -m pytest projects/main-submission/tests/test_owner_routing.py -v`  
Expected: `FAIL`.

- [ ] **Step 3: Implement fallback resolver**

```python
def resolve_first_responder(asset_owner, domain_owner, team_owner, default_channel):
    if asset_owner:
        return asset_owner, "asset_owner"
    if domain_owner:
        return domain_owner, "domain_owner"
    if team_owner:
        return team_owner, "team_owner"
    return default_channel, "default_channel"
```

- [ ] **Step 4: Run tests to verify pass**

Run: `python -m pytest projects/main-submission/tests/test_owner_routing.py -v`  
Expected: `PASS`.

- [ ] **Step 5: Commit**

```bash
git add projects/main-submission/src/incident_copilot/owner_routing.py \
  projects/main-submission/tests/test_owner_routing.py
git commit -m "feat: add full owner fallback chain"
```

---

### Task 5: Implement Impact Prioritizer (Business-Facing First)

**Files:**
- Create: `projects/main-submission/src/incident_copilot/impact.py`
- Test: `projects/main-submission/tests/test_impact.py`

- [ ] **Step 1: Write failing prioritization tests**

```python
from incident_copilot.impact import select_top_impacted_assets

def test_business_facing_assets_rank_first():
    assets = [
        {"fqn": "a.raw", "distance": 1, "business_facing": False},
        {"fqn": "a.dashboard", "distance": 2, "business_facing": True},
    ]
    out = select_top_impacted_assets(assets, max_assets=3, max_depth=2)
    assert out[0]["fqn"] == "a.dashboard"

def test_caps_to_three_and_depth_two():
    assets = [{"fqn": f"a{i}", "distance": 1, "business_facing": True} for i in range(5)]
    out = select_top_impacted_assets(assets, max_assets=3, max_depth=2)
    assert len(out) == 3
```

- [ ] **Step 2: Run tests to verify failure**

Run: `python -m pytest projects/main-submission/tests/test_impact.py -v`  
Expected: `FAIL`.

- [ ] **Step 3: Implement deterministic ranking**

```python
def _sort_key(item):
    return (
        0 if item.get("business_facing") else 1,
        item.get("distance", 99),
        item.get("fqn", ""),
    )

def select_top_impacted_assets(assets, max_assets=3, max_depth=2):
    bounded = [x for x in assets if x.get("distance", 99) <= max_depth]
    return sorted(bounded, key=_sort_key)[:max_assets]
```

- [ ] **Step 4: Run tests to verify pass**

Run: `python -m pytest projects/main-submission/tests/test_impact.py -v`  
Expected: `PASS`.

- [ ] **Step 5: Commit**

```bash
git add projects/main-submission/src/incident_copilot/impact.py \
  projects/main-submission/tests/test_impact.py
git commit -m "feat: add bounded impact prioritization with business-facing rank"
```

---

### Task 6: Implement Policy Advisor

**Files:**
- Create: `projects/main-submission/src/incident_copilot/policy.py`
- Test: `projects/main-submission/tests/test_policy.py`

- [ ] **Step 1: Write failing policy tests**

```python
from incident_copilot.policy import evaluate_policy

def test_pii_sensitive_requires_steward_approval():
    assets = [{"classifications": ["PII.Sensitive"]}]
    out = evaluate_policy("inc-1", assets)
    assert out.status == "approval_required"
    assert out.required_approver_role == "data_steward"

def test_no_pii_sensitive_is_allowed():
    assets = [{"classifications": ["Finance.Public"]}]
    out = evaluate_policy("inc-1", assets)
    assert out.status == "allowed"
```

- [ ] **Step 2: Run tests to verify failure**

Run: `python -m pytest projects/main-submission/tests/test_policy.py -v`  
Expected: `FAIL`.

- [ ] **Step 3: Implement deterministic policy rule**

```python
from incident_copilot.contracts import PolicyDecision

def evaluate_policy(incident_id, impacted_assets):
    has_pii_sensitive = any(
        "PII.Sensitive" in (a.get("classifications") or [])
        for a in impacted_assets
    )
    if has_pii_sensitive:
        return PolicyDecision(
            incident_id=incident_id,
            status="approval_required",
            reason_codes=["PII_SENSITIVE_IMPACTED"],
            required_approver_role="data_steward",
        )
    return PolicyDecision(
        incident_id=incident_id,
        status="allowed",
        reason_codes=[],
        required_approver_role=None,
    )
```

- [ ] **Step 4: Run tests to verify pass**

Run: `python -m pytest projects/main-submission/tests/test_policy.py -v`  
Expected: `PASS`.

- [ ] **Step 5: Commit**

```bash
git add projects/main-submission/src/incident_copilot/policy.py \
  projects/main-submission/tests/test_policy.py
git commit -m "feat: add pii-sensitive policy decisioning"
```

---

### Task 7: Implement Canonical Brief Generator with Per-Block Evidence

**Files:**
- Create: `projects/main-submission/src/incident_copilot/brief.py`
- Test: `projects/main-submission/tests/test_brief.py`

- [ ] **Step 1: Write failing evidence-link tests**

```python
from incident_copilot.brief import build_incident_brief

def test_each_brief_block_has_evidence_refs():
    brief = build_incident_brief(
        incident_id="inc-1",
        what_failed=("Null ratio exceeded", ["incident_ref", "test_ref"]),
        what_is_impacted=("customer_curated, dashboard_x", ["lineage_ref"]),
        who_acts_first=("dre-oncall via asset_owner", ["owner_ref"]),
        what_to_do_next=("Escalate for steward approval", ["classification_ref", "policy_ref"]),
        policy_state="approval_required",
    )
    assert brief["what_failed"]["evidence_refs"]
    assert brief["what_is_impacted"]["evidence_refs"]
    assert brief["who_acts_first"]["evidence_refs"]
    assert brief["what_to_do_next"]["evidence_refs"]
```

- [ ] **Step 2: Run tests to verify failure**

Run: `python -m pytest projects/main-submission/tests/test_brief.py -v`  
Expected: `FAIL`.

- [ ] **Step 3: Implement block-structured brief**

```python
def _block(text, refs):
    return {"text": text, "evidence_refs": refs}

def build_incident_brief(
    incident_id,
    what_failed,
    what_is_impacted,
    who_acts_first,
    what_to_do_next,
    policy_state,
):
    wf_text, wf_refs = what_failed
    wi_text, wi_refs = what_is_impacted
    wa_text, wa_refs = who_acts_first
    wn_text, wn_refs = what_to_do_next
    return {
        "incident_id": incident_id,
        "what_failed": _block(wf_text, wf_refs),
        "what_is_impacted": _block(wi_text, wi_refs),
        "who_acts_first": _block(wa_text, wa_refs),
        "what_to_do_next": _block(wn_text, wn_refs),
        "policy_state": policy_state,
    }
```

- [ ] **Step 4: Run tests to verify pass**

Run: `python -m pytest projects/main-submission/tests/test_brief.py -v`  
Expected: `PASS`.

- [ ] **Step 5: Commit**

```bash
git add projects/main-submission/src/incident_copilot/brief.py \
  projects/main-submission/tests/test_brief.py
git commit -m "feat: add evidence-linked canonical brief blocks"
```

---

### Task 8: Implement Adapter + Delivery with Degraded-Mode Behavior

**Files:**
- Create: `projects/main-submission/src/incident_copilot/adapter.py`
- Create: `projects/main-submission/src/incident_copilot/delivery.py`
- Test: `projects/main-submission/tests/test_adapter.py`
- Test: `projects/main-submission/tests/test_delivery.py`

- [ ] **Step 1: Write failing adapter degraded-mode tests**

```python
from incident_copilot.adapter import normalize_event

def test_adapter_handles_missing_fields_gracefully():
    out = normalize_event({"incident_id": "inc-1"})
    assert "MISSING_EVENT_FIELDS" in out["fallback_reason_codes"]
```

- [ ] **Step 2: Write failing delivery primary-switch test**

```python
from incident_copilot.delivery import deliver

def test_local_mirror_becomes_primary_when_slack_fails():
    brief = {"incident_id": "inc-1"}
    captured = {}
    def writer(payload):
        captured["payload"] = payload
        return "/tmp/latest_brief.json"
    out = deliver(
        brief,
        slack_sender=lambda _brief: False,
        mirror_writer=writer,
    )
    assert out["delivery"].primary_output == "local_mirror"
    assert "SLACK_SEND_FAILED" in (out["delivery"].degraded_reason_codes or [])
    assert out["local_mirror_payload"]["brief"]["incident_id"] == out["slack_payload"]["brief"]["incident_id"]
    assert captured["payload"]["brief"]["incident_id"] == out["local_mirror_payload"]["brief"]["incident_id"]

def test_delivery_parity_across_core_brief_fields():
    brief = {
        "incident_id": "inc-1",
        "what_failed": {"text": "x", "evidence_refs": ["incident_ref"]},
        "what_is_impacted": {"text": "y", "evidence_refs": ["lineage_ref"]},
        "who_acts_first": {"text": "z", "evidence_refs": ["owner_ref"]},
        "what_to_do_next": {"text": "n", "evidence_refs": ["policy_ref"]},
        "policy_state": "approval_required",
    }
    out = deliver(brief, slack_sender=lambda _brief: True, mirror_writer=lambda _payload: "/tmp/latest_brief.json")
    for key in ["incident_id", "what_failed", "what_is_impacted", "who_acts_first", "what_to_do_next", "policy_state"]:
        assert out["slack_payload"]["brief"][key] == out["local_mirror_payload"]["brief"][key]

def test_delivery_persists_local_mirror_artifact(tmp_path):
    import json
    mirror_path = tmp_path / "latest_brief.json"
    brief = {
        "incident_id": "inc-1",
        "what_failed": {"text": "x", "evidence_refs": ["incident_ref"]},
        "what_is_impacted": {"text": "y", "evidence_refs": ["lineage_ref"]},
        "who_acts_first": {"text": "z", "evidence_refs": ["owner_ref"]},
        "what_to_do_next": {"text": "n", "evidence_refs": ["policy_ref"]},
        "policy_state": "approval_required",
    }
    def writer(payload):
        mirror_path.write_text(json.dumps(payload), encoding="utf-8")
        return str(mirror_path)
    out = deliver(brief, slack_sender=lambda _brief: True, mirror_writer=writer)
    persisted = json.loads(mirror_path.read_text(encoding="utf-8"))
    assert persisted["brief"] == out["local_mirror_payload"]["brief"]
    for key in ["incident_id", "what_failed", "what_is_impacted", "who_acts_first", "what_to_do_next", "policy_state"]:
        assert persisted["brief"][key] == out["slack_payload"]["brief"][key]
```

- [ ] **Step 3: Run tests to verify failure**

Run: `python -m pytest projects/main-submission/tests/test_adapter.py projects/main-submission/tests/test_delivery.py -v`  
Expected: `FAIL`.

- [ ] **Step 4: Implement adapter and delivery fallbacks**

```python
# adapter.py
REQUIRED = ["incident_id", "entity_fqn", "test_case_id", "severity", "occurred_at", "raw_ref"]

def normalize_event(raw):
    missing = [k for k in REQUIRED if k not in raw]
    return {
        "incident_id": raw.get("incident_id", "unknown-incident"),
        "source": "openmetadata",
        "event_type": "dq_incident",
        "entity_fqn": raw.get("entity_fqn", ""),
        "test_case_id": raw.get("test_case_id", ""),
        "severity": raw.get("severity", "unknown"),
        "occurred_at": raw.get("occurred_at", ""),
        "raw_ref": raw.get("raw_ref", ""),
        "fallback_reason_codes": ["MISSING_EVENT_FIELDS"] if missing else [],
    }
```

```python
# delivery.py
from incident_copilot.contracts import DeliveryResult

def deliver(brief, slack_sender, mirror_writer):
    slack_payload = {"channel": "slack", "brief": brief}
    local_mirror_payload = {"channel": "local_mirror", "brief": brief}
    mirror_writer(local_mirror_payload)
    slack_ok = bool(slack_sender(slack_payload))
    if slack_ok:
        result = DeliveryResult("sent", "rendered", "slack", [])
    else:
        result = DeliveryResult("failed", "rendered", "local_mirror", ["SLACK_SEND_FAILED"])
    return {
        "delivery": result,
        "slack_payload": slack_payload,
        "local_mirror_payload": local_mirror_payload,
    }
```

- [ ] **Step 5: Run tests to verify pass**

Run: `python -m pytest projects/main-submission/tests/test_adapter.py projects/main-submission/tests/test_delivery.py -v`  
Expected: `PASS`.

- [ ] **Step 6: Commit**

```bash
git add projects/main-submission/src/incident_copilot/adapter.py \
  projects/main-submission/src/incident_copilot/delivery.py \
  projects/main-submission/tests/test_adapter.py \
  projects/main-submission/tests/test_delivery.py
git commit -m "feat: add adapter and delivery degraded-mode handling"
```

---

### Task 9: Implement Orchestrator with Context Resolver (Golden + Degraded Paths)

**Files:**
- Create: `projects/main-submission/src/incident_copilot/orchestrator.py`
- Test: `projects/main-submission/tests/test_orchestrator.py`

- [ ] **Step 1: Write failing golden-path test**

```python
from incident_copilot.orchestrator import run_pipeline

def test_golden_path_returns_approval_required():
    raw = {"incident_id": "inc-1", "entity_fqn": "svc.db.customer_profiles", "test_case_id": "tc-1", "severity": "high", "occurred_at": "2026-04-18T00:00:00Z", "raw_ref": "evt-1"}
    om_data = {
        "failed_test": {"message": "null ratio high"},
        "lineage": [{"fqn": "svc.db.customer_curated", "distance": 1, "business_facing": True, "owner": "dre-oncall"}],
        "owners": {"asset_owner": "dre-oncall"},
        "classifications": {"svc.db.customer_curated": ["PII.Sensitive"]},
    }
    out = run_pipeline(raw, om_data, slack_sender=lambda _b: True)
    assert out["brief"]["policy_state"] == "approval_required"
```

- [ ] **Step 2: Write failing degraded-path test**

```python
from incident_copilot.orchestrator import run_pipeline

def test_degraded_path_carries_reason_codes():
    out = run_pipeline({"incident_id": "inc-1"}, {"failed_test": {}, "lineage": [], "owners": {}, "classifications": {}}, slack_sender=lambda _b: False)
    assert out["delivery"]["delivery"].primary_output == "local_mirror"
    assert out["fallback_reason_codes"]
```

- [ ] **Step 3: Run tests to verify failure**

Run: `python -m pytest projects/main-submission/tests/test_orchestrator.py -v`  
Expected: `FAIL`.

- [ ] **Step 4: Implement orchestration pipeline**

```python
from incident_copilot.adapter import normalize_event
from incident_copilot.context_resolver import resolve_context
from incident_copilot.owner_routing import resolve_first_responder
from incident_copilot.impact import select_top_impacted_assets
from incident_copilot.policy import evaluate_policy
from incident_copilot.brief import build_incident_brief
from incident_copilot.delivery import deliver

def run_pipeline(raw_event, om_data, slack_sender, mirror_writer=lambda _payload: "projects/main-submission/runtime/local_mirror/latest_brief.json"):
    env = normalize_event(raw_event)
    ctx = resolve_context(env, om_data, max_depth=2)
    impacted = select_top_impacted_assets(ctx["impacted_assets"], max_assets=3, max_depth=2)
    policy = evaluate_policy(env["incident_id"], impacted)
    first_actor, first_path = resolve_first_responder(
        ctx["owners"].get("asset_owner"),
        ctx["owners"].get("domain_owner"),
        ctx["owners"].get("team_owner"),
        "#metadata-incidents",
    )
    brief = build_incident_brief(
        incident_id=env["incident_id"],
        what_failed=(ctx["failed_test"].get("message", "unknown failure"), ["incident_ref", "test_ref"]),
        what_is_impacted=(", ".join([x.get("fqn", "") for x in impacted]) or "none", ["lineage_ref"]),
        who_acts_first=(f"{first_actor} via {first_path}", ["owner_ref"]),
        what_to_do_next=(
            "Escalate to data steward for approval" if policy.status == "approval_required"
            else "Proceed with manual remediation triage",
            ["policy_ref", "classification_ref"] if policy.status == "approval_required" else ["policy_ref"],
        ),
        policy_state=policy.status,
    )
    delivery_result = deliver(brief, slack_sender, mirror_writer)
    return {
        "brief": brief,
        "delivery": delivery_result,
        "fallback_reason_codes": env["fallback_reason_codes"] + ctx["fallback_reason_codes"] + (delivery_result["delivery"].degraded_reason_codes or []),
    }
```

- [ ] **Step 5: Run tests to verify pass**

Run: `python -m pytest projects/main-submission/tests/test_orchestrator.py -v`  
Expected: `PASS`.

- [ ] **Step 6: Commit**

```bash
git add projects/main-submission/src/incident_copilot/orchestrator.py \
  projects/main-submission/tests/test_orchestrator.py
git commit -m "feat: orchestrate golden and degraded incident paths"
```

---

### Task 10: Implement One-Click Demo Harness + Reproducibility

**Files:**
- Create: `projects/main-submission/src/incident_copilot/demo_harness.py`
- Create: `projects/main-submission/scripts/run_demo.py`
- Create: `projects/main-submission/runtime/fixtures/replay_event.json`
- Create: `projects/main-submission/runtime/fixtures/replay_om_context.json`
- Test: `projects/main-submission/tests/test_demo_harness.py`

- [ ] **Step 1: Write failing reproducibility tests**

```python
from incident_copilot.demo_harness import run_demo_once

def test_replay_mode_is_deterministic():
    replay = {"incident_id": "inc-replay", "entity_fqn": "svc.db.customer_profiles", "test_case_id": "tc-1", "severity": "high", "occurred_at": "2026-04-18T00:00:00Z", "raw_ref": "evt-1"}
    om_data = {"failed_test": {"message": "null ratio high"}, "lineage": [], "owners": {}, "classifications": {}}
    a = run_demo_once(live_event=None, replay_event=replay, om_data=om_data)
    b = run_demo_once(live_event=None, replay_event=replay, om_data=om_data)
    assert a["brief"] == b["brief"]

def test_cli_entrypoint_writes_reproducible_output(tmp_path):
    from incident_copilot.demo_harness import run_replay_command
    replay = {"incident_id": "inc-2", "entity_fqn": "svc.db.customer_profiles", "test_case_id": "tc-1", "severity": "high", "occurred_at": "2026-04-18T00:00:00Z", "raw_ref": "evt-1"}
    om_data = {"failed_test": {"message": "x"}, "lineage": [], "owners": {}, "classifications": {}}
    out1 = run_replay_command(replay, om_data, str(tmp_path / "latest_brief.json"))
    out2 = run_replay_command(replay, om_data, str(tmp_path / "latest_brief.json"))
    assert out1["brief"] == out2["brief"]
```

- [ ] **Step 2: Run tests to verify failure**

Run: `python -m pytest projects/main-submission/tests/test_demo_harness.py -v`  
Expected: `FAIL`.

- [ ] **Step 3: Implement one-click entrypoint**

```python
from incident_copilot.orchestrator import run_pipeline
import json

def run_demo_once(live_event, replay_event, om_data):
    event = live_event if live_event else replay_event
    return run_pipeline(event, om_data, slack_sender=lambda _brief: False)

def run_replay_command(replay_event, om_data, output_path):
    def mirror_writer(payload):
        with open(output_path, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2, sort_keys=True)
        return output_path
    return run_pipeline(
        replay_event,
        om_data,
        slack_sender=lambda _brief: False,
        mirror_writer=mirror_writer,
    )
```

- [ ] **Step 4: Run tests to verify pass**

Run: `python -m pytest projects/main-submission/tests/test_demo_harness.py -v`  
Expected: `PASS`.

- [ ] **Step 5: Add and verify one-click command entrypoint**

Create `projects/main-submission/scripts/run_demo.py` that:
1. loads `projects/main-submission/runtime/fixtures/replay_event.json`,
2. loads `projects/main-submission/runtime/fixtures/replay_om_context.json`,
3. calls `run_replay_command(...)`,
3. writes `projects/main-submission/runtime/local_mirror/latest_brief.json`.

Run twice:

```bash
python projects/main-submission/scripts/run_demo.py --replay projects/main-submission/runtime/fixtures/replay_event.json --context projects/main-submission/runtime/fixtures/replay_om_context.json --output projects/main-submission/runtime/local_mirror/latest_brief.json
python projects/main-submission/scripts/run_demo.py --replay projects/main-submission/runtime/fixtures/replay_event.json --context projects/main-submission/runtime/fixtures/replay_om_context.json --output projects/main-submission/runtime/local_mirror/latest_brief.json
```

Expected: command succeeds both times and `latest_brief.json` remains deterministic.

- [ ] **Step 6: Commit**

```bash
git add projects/main-submission/src/incident_copilot/demo_harness.py \
  projects/main-submission/scripts/run_demo.py \
  projects/main-submission/runtime/fixtures/replay_event.json \
  projects/main-submission/runtime/fixtures/replay_om_context.json \
  projects/main-submission/tests/test_demo_harness.py
git commit -m "feat: add one-click deterministic demo harness"
```

---

### Task 11: Final Docs, Verification, and Submission Readiness

**Files:**
- Modify: `docs/architecture.md`
- Modify: `docs/demo-script.md`
- Modify: `docs/submission-checklist.md`
- Modify: `docs/decision-log.md`
- Modify: `projects/main-submission/README.md`

- [ ] **Step 1: Update architecture doc with real components and fallbacks**

Document:
- Context Resolver,
- per-block evidence requirement,
- degraded modes and reason codes.

- [ ] **Step 2: Update demo script with timed, deterministic runbook**

Include:
- one-click trigger/replay,
- `approval_required` branch,
- Slack failure fallback demonstration.

- [ ] **Step 3: Add acceptance checks to submission checklist**

Add explicit checks for:
- domain/team owner fallback,
- business-facing priority,
- `required_approver_role == data_steward`,
- local mirror as primary on Slack failure.

- [ ] **Step 4: Run full copilot test suite**

Run: `python -m pytest projects/main-submission/tests -v`  
Expected: all tests `PASS`.

- [ ] **Step 5: Run repo-level validation checks**

Run:

```bash
. .venv/bin/activate
python -m pytest tests/tools/test_validate_docs_scope.py -v
python tools/validate_docs_scope.py $(git diff --name-only --cached)
```

Expected:
- `PASS` for validator tests.
- `docs-scope: OK`.

- [ ] **Step 6: Commit**

```bash
git add docs/architecture.md docs/demo-script.md docs/submission-checklist.md docs/decision-log.md \
  projects/main-submission/README.md
git commit -m "docs: finalize deterministic copilot architecture and demo narrative"
```

---

## End-to-End Verification Checklist

- [ ] `test_owner_routing.py` covers asset/domain/team/default fallback paths.
- [ ] `test_impact.py` proves business-facing-first and max 3 assets.
- [ ] `test_policy.py` proves `PII.Sensitive -> approval_required` and `required_approver_role == data_steward`.
- [ ] `test_brief.py` proves all four brief blocks carry evidence refs.
- [ ] `test_delivery.py` proves Slack failure sets `local_mirror` as primary.
- [ ] `test_delivery.py` proves parity across core brief fields for Slack and local mirror payloads.
- [ ] `test_delivery.py` proves persisted local mirror artifact matches Slack core brief fields.
- [ ] `test_orchestrator.py` proves both golden and degraded paths.
- [ ] `test_demo_harness.py` proves replay determinism on repeated runs.
- [ ] `scripts/run_demo.py` reproducibly writes `runtime/local_mirror/latest_brief.json` from the replay fixture.
- [ ] Docs-scope and repo validation checks pass before PR.

## Execution Notes

1. Keep commits task-scoped and linear.
2. If a task reveals new architecture scope, stop and update spec + plan first.
3. Do not skip failing-test-first workflow.
4. Preserve deterministic behavior in all final outputs.
