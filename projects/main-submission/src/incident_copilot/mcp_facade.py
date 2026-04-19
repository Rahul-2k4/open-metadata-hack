from fastmcp import FastMCP

from incident_copilot.rca_engine import build_rca

mcp = FastMCP("incident-copilot")


def get_rca_tool(test_case_id: str, signal_type: str = "unknown") -> dict:
    result = build_rca(
        failed_test={"message": signal_type, "testType": signal_type},
        entity_fqn=test_case_id,
        use_ai=False,
    )
    return {
        "cause_tree": result.cause_tree,
        "narrative": result.narrative,
        "narrative_source": result.narrative_source,
        "signal_type": result.signal_type,
    }


def score_impact_tool(entity_fqn: str, lineage_depth: int = 2) -> list[dict]:
    return []


def notify_slack_tool(incident_id: str) -> dict:
    return {
        "status": "not_configured",
        "incident_id": incident_id,
        "fallback": "local_mirror",
    }


@mcp.tool
def triage_incident(incident_id: str, entity_fqn: str) -> dict:
    """Run full incident triage pipeline and return a 4-block brief."""
    from incident_copilot.orchestrator import run_pipeline
    raw_event = {
        "incident_id": incident_id,
        "entity_fqn": entity_fqn,
        "test_case_id": f"tc-{incident_id}",
        "severity": "high",
        "occurred_at": "",
        "raw_ref": incident_id,
    }
    om_data = {"failed_test": {}, "lineage": [], "owners": {}, "classifications": {}}
    result = run_pipeline(raw_event, om_data, slack_sender=lambda _: False)
    return result["brief"]


@mcp.tool
def score_impact(entity_fqn: str, lineage_depth: int = 2) -> list[dict]:
    """Score impacted assets for a given entity FQN."""
    return score_impact_tool(entity_fqn, lineage_depth)


@mcp.tool
def get_rca(test_case_id: str, signal_type: str = "unknown") -> dict:
    """Get root cause analysis for a failed test case."""
    return get_rca_tool(test_case_id, signal_type)


@mcp.tool
def notify_slack(incident_id: str) -> dict:
    """Trigger Slack notification for an incident brief."""
    return notify_slack_tool(incident_id)


if __name__ == "__main__":
    mcp.run()
