#!/usr/bin/env python3
"""
Polls OpenMetadata for Failed test cases and dispatches them to the copilot.
Run this in a loop: watch -n 30 python3 scripts/om_auto_dispatch.py
Or as a one-shot: python3 scripts/om_auto_dispatch.py
"""
import json, os, sys, time, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

BASE = os.environ.get("OPENMETADATA_BASE_URL", "http://localhost:8585/api")
TOKEN = os.environ.get("OPENMETADATA_JWT_TOKEN", "")
COPILOT = os.environ.get("COPILOT_URL", "http://localhost:8088")
SEEN_FILE = Path("/tmp/om_dispatch_seen.json")

def om_get(path):
    headers = {"Accept": "application/json"}
    if TOKEN:
        headers["Authorization"] = f"Bearer {TOKEN}"
    req = urllib.request.Request(f"{BASE}{path}", headers=headers)
    with urllib.request.urlopen(req, timeout=5) as r:
        return json.loads(r.read())

def post_to_copilot(payload):
    data = json.dumps(payload).encode()
    req = urllib.request.Request(
        f"{COPILOT}/webhooks/incidents",
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read())

def load_seen():
    if SEEN_FILE.exists():
        return set(json.loads(SEEN_FILE.read_text()))
    return set()

def save_seen(seen):
    SEEN_FILE.write_text(json.dumps(list(seen)))

def main():
    seen = load_seen()
    new_seen = set(seen)

    try:
        data = om_get("/v1/dataQuality/testCases?limit=50&fields=testCaseResult,testDefinition,entityLink")
    except Exception as e:
        print(f"[OM] fetch failed: {e}")
        return

    dispatched = 0
    for tc in data.get("data", []):
        status = (tc.get("testCaseResult") or {}).get("testCaseStatus", "")
        if status != "Failed":
            continue

        tc_id = tc.get("id", "")
        result_ts = (tc.get("testCaseResult") or {}).get("timestamp", 0)
        dedup_key = f"{tc_id}:{result_ts}"

        if dedup_key in seen:
            continue

        # Extract table FQN from entityLink or FQN
        fqn = tc.get("fullyQualifiedName", "")
        entity_link = tc.get("entityLink", "")
        if entity_link:
            import re
            m = re.search(r"<#E::[^:]+::((?:(?!::).)+?)(?:::|>)", entity_link)
            if m:
                fqn = m.group(1)
        elif fqn:
            parts = fqn.split(".")
            if len(parts) >= 5:
                fqn = ".".join(parts[:4])

        payload = {
            "entity": {
                "id": tc_id,
                "fullyQualifiedName": fqn,
                "testDefinition": tc.get("testDefinition", {}),
                "testCaseResult": tc.get("testCaseResult", {}),
            },
            "entityType": "testCase",
            "eventType": "testCaseResult",
            "timestamp": result_ts,
        }

        try:
            result = post_to_copilot(payload)
            print(f"[OK] {tc['name']} → incident={result.get('incident_id')} policy={result.get('brief',{}).get('policy_state')}")
            new_seen.add(dedup_key)
            dispatched += 1
        except Exception as e:
            print(f"[ERR] {tc['name']}: {e}")

    save_seen(new_seen)
    if dispatched == 0:
        print(f"[OK] No new failures (checked {len(data.get('data',[]))} test cases)")

if __name__ == "__main__":
    main()
