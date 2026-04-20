import os

from incident_copilot.mcp_transport_client import MCPTransportClient, MCPTransportClientError
from incident_copilot.openmetadata_client import OpenMetadataClient, OpenMetadataClientError


def _env_flag(name: str) -> bool:
    return (os.environ.get(name) or "").strip().lower() in {"1", "true", "yes", "on"}


def _resolve_via_http(envelope, max_depth=2):
    client = OpenMetadataClient.from_env()
    return client.fetch_incident_context(envelope, max_depth=max_depth)


def _resolve_via_mcp(envelope, max_depth=2):
    client = MCPTransportClient.from_env()
    return client.fetch_incident_context(envelope, max_depth=max_depth)


def _normalize_payload(envelope, payload, max_depth=2):
    owners = payload.get("owners", {})
    fallback_reason_codes = []
    if not owners.get("asset_owner") and not owners.get("domain_owner") and not owners.get("team_owner"):
        fallback_reason_codes.append("MISSING_OWNER_METADATA")

    classifications_map = payload.get("classifications", {})
    impacted = []
    for item in payload.get("lineage", []):
        if item.get("distance", 99) > max_depth:
            continue
        merged = dict(item)
        merged["classifications"] = merged.get("classifications") or classifications_map.get(merged.get("fqn"), [])
        impacted.append(merged)

    # Failed-test precedence: concrete webhook data beats synthetic OM placeholders.
    # OM's HTTP client emits a placeholder `{testType: "unknown"}` when it can't
    # resolve the test_case_id (ad-hoc / demo events). Envelope data from the raw
    # webhook is always more authoritative for `message` and `testType` when present.
    om_failed = payload.get("failed_test") or {}
    env_failed = envelope.get("failed_test") or {}
    failed_test = dict(om_failed)
    if env_failed.get("message"):
        failed_test["message"] = env_failed["message"]
    if env_failed.get("testType"):
        failed_test["testType"] = env_failed["testType"]

    return {
        "incident_id": envelope["incident_id"],
        "failed_test": failed_test,
        "impacted_assets": impacted,
        "owners": owners,
        "classifications": classifications_map,
        "fallback_reason_codes": fallback_reason_codes,
    }


def resolve_context(envelope, om_client_data=None, max_depth=2):
    fallback_reason_codes = []
    source_mode = (os.environ.get("OM_CONTEXT_SOURCE") or "").strip().lower()
    use_mcp = _env_flag("USE_OM_MCP")
    prefer_live_http = source_mode in {"direct_http", "live"}

    payload = None
    if use_mcp:
        try:
            payload = _resolve_via_mcp(envelope, max_depth=max_depth)
        except MCPTransportClientError:
            fallback_reason_codes.append("OM_MCP_FALLBACK_TO_HTTP")

    if payload is None and (prefer_live_http or om_client_data is None or use_mcp):
        try:
            payload = _resolve_via_http(envelope, max_depth=max_depth)
        except OpenMetadataClientError:
            fallback_reason_codes.append("OM_HTTP_FALLBACK_TO_FIXTURE")
            payload = om_client_data or {}

    if payload is None:
        payload = om_client_data or {}

    normalized = _normalize_payload(envelope, payload, max_depth=max_depth)
    normalized["fallback_reason_codes"] = normalized["fallback_reason_codes"] + fallback_reason_codes
    return normalized
