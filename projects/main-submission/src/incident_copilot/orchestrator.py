from incident_copilot.adapter import normalize_event
from incident_copilot.context_resolver import resolve_context
from incident_copilot.owner_routing import resolve_first_responder
from incident_copilot.impact import select_top_impacted_assets
from incident_copilot.policy import evaluate_policy
from incident_copilot.brief import build_incident_brief
from incident_copilot.delivery import deliver

_DEFAULT_MIRROR = "projects/main-submission/runtime/local_mirror/latest_brief.json"


def run_pipeline(raw_event, om_data, slack_sender, mirror_writer=lambda _payload: _DEFAULT_MIRROR):
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
