# Metadata Incident Copilot Design Spec

## Context

This specification defines a hackathon-scoped, decision-support copilot for OpenMetadata incident triage.

- Primary theme: Data Observability (`2`)
- Supporting themes: MCP/AI Agents (`1`), Community & Comms (`5`), Governance & Classification (`6`)
- Primary user: Data Reliability Engineer
- Secondary user: Data Steward
- Domain: Customer Analytics

## Problem

DQ incidents are slow to triage when responders must manually gather:

1. what failed,
2. downstream impact,
3. first responder ownership,
4. governance constraints.

## Goal

Produce a deterministic, evidence-backed incident brief for one OpenMetadata DQ incident with governance-aware next-step guidance in a 2-5 minute demo flow.

## Product Boundary (v1)

In scope:

1. Data Quality incidents only.
2. Read-only decision support only.
3. Deterministic enrichment and policy decision.
4. Slack delivery plus local mirrored fallback.

Out of scope:

1. Auto-remediation.
2. Multi-incident support (schema/pipeline).
3. Unbounded RCA speculation.
4. Broad chat assistant UX.

## Architecture

1. OpenMetadata Incident Adapter
2. Context Resolver
3. Impact Prioritizer (depth <= 2, top <= 3)
4. Policy Advisor (`PII.Sensitive -> approval_required`)
5. Brief Generator (canonical 4-block brief)
6. Delivery Layer (Slack + local mirror)
7. Demo Harness (deterministic trigger/replay)

## Canonical Brief Structure

1. What failed
2. What is impacted
3. Who acts first
4. What to do next

Each brief statement must be evidence-linked to incident/test/lineage/owner/classification references.

## Deterministic Rules

Owner routing fallback chain:

1. Asset owner
2. Domain owner
3. Team owner
4. Default incident channel

Policy rule:

- If any impacted asset has `PII.Sensitive`, set `approval_required` and require steward sign-off.

Impact bounds:

- Max lineage depth `2`
- Max impacted assets `3`
- Prioritize business-facing assets first

## Reliability and Demo Safety

1. If live incident emission fails, replay deterministic payload.
2. If Slack fails, local mirror becomes primary output.
3. If metadata fields are missing, degrade gracefully with explicit fallback reason codes.

## Success Criteria

1. One-click trigger yields reproducible incident flow.
2. Brief always includes owner, impacted assets, and next step.
3. `PII.Sensitive` scenario always returns `approval_required`.
4. Slack and local mirror show parity on core brief fields.
5. Demo script remains within 2-5 minutes with no manual patching.

