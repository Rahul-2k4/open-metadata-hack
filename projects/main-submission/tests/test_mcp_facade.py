from incident_copilot.mcp_facade import get_rca_tool, score_impact_tool, notify_slack_tool


def test_get_rca_returns_cause_tree_and_narrative():
    result = get_rca_tool(test_case_id="tc-null-1", signal_type="null_ratio_exceeded")
    assert "cause_tree" in result
    assert result["cause_tree"] == ["data_completeness", "upstream_null_propagation"]
    assert result["narrative"] != ""
    assert result["signal_type"] == "null_ratio_exceeded"


def test_get_rca_unknown_signal():
    result = get_rca_tool(test_case_id="tc-unknown", signal_type="unknown")
    assert "unclassified" in result["cause_tree"]


def test_score_impact_returns_list():
    result = score_impact_tool(entity_fqn="svc.db.orders", lineage_depth=2)
    assert isinstance(result, list)


def test_notify_slack_returns_status_dict():
    result = notify_slack_tool(incident_id="inc-1")
    assert "status" in result
    assert "incident_id" in result
    assert result["incident_id"] == "inc-1"
