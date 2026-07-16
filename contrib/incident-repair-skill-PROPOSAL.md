# Proposed DataHub Skill: `incident-repair-investigation`

**Status:** Draft proposal, written for this hackathon. Intended to be opened as a PR
against the DataHub Skills repository (`datahub-project/datahub` or the community
skills repo, whichever the maintainers point contributors to) — not yet merged upstream.
Submitted here as the required disclosure per the hackathon's "New Projects Only" rule:
this file is original work produced during the Submission Period, not pre-existing code.

## Why this skill

PhoenixForge AI's Root Cause Agent and Repair Agent repeat the same reasoning shape
every time: given a dataset URN and a detected anomaly, (1) pull lineage, (2) pull recent
schema/description changes on upstream nodes, (3) check for an existing knowledge-base
runbook for this failure pattern before re-investigating from scratch. Today that
sequence is hand-coded in `root_cause_agent.py`. A DataHub Skill packages it as a
reusable, model-agnostic prompt + tool-call recipe that any DataHub-aware agent
(not just PhoenixForge AI) could reuse.

## Skill definition (draft)

```yaml
name: incident-repair-investigation
description: >
  Given a dataset URN suspected of a data-quality or pipeline incident, determine
  the most likely upstream root cause and check whether a prior runbook already
  covers this failure pattern, before generating a new fix.
inputs:
  - dataset_urn: string
tools_used:
  - search        # to look up prior knowledge-base documents for this failure pattern
  - get_lineage    # upstream traversal to find the true source of the break
  - list_schema_fields   # to detect column/type-level drift on upstream nodes
steps:
  1. Call get_lineage(dataset_urn, direction=upstream) to build the candidate cause set.
  2. Call search("runbook " + dataset_name) against DataHub's saved documents to check
     for a prior incident on the same or a structurally similar asset.
  3. If a matching runbook exists, return it directly (skip full re-investigation).
  4. Otherwise, call list_schema_fields on each upstream candidate to detect schema
     drift, and rank candidates by recency of change + distance from the failing node.
outputs:
  - likely_root_cause_urn: string
  - confidence: float
  - matched_prior_runbook: string | null
```

## Relationship to this submission

This is what PhoenixForge AI's own `root_cause_agent.py` + `lineage_agent.py` already do
in Python; this file expresses that same logic as a portable DataHub Skill so it could be
reused outside this project. We're including it as a disclosed draft, not claiming it's
merged — reviewers should judge it as "a proposed contribution," not an existing one.
