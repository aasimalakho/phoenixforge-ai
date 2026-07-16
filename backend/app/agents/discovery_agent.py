"""
Discovery Agent
---------------
Continuously (or on-demand) scans DataHub's recent change feed for signs of trouble:
schema drift, broken lineage, missing ownership, failed jobs, freshness issues,
data-quality degradation, and contract violations.

In demo mode this reads the canned "recent_changes" list from the mock metadata file.
In production this would be a scheduled job (e.g. every few minutes) polling DataHub's
timeline / audit-log APIs, or subscribing to DataHub's Kafka change-log topic.
"""
from ..datahub_client import datahub_client


ANOMALY_TYPES = {
    "SCHEMA_CHANGE": "Schema drift",
    "JOB_FAILURE": "Failed job",
    "OWNERSHIP_MISSING": "Missing ownership",
    "FRESHNESS_SLA_BREACH": "Freshness issue",
    "QUALITY_DEGRADATION": "Data quality degradation",
    "CONTRACT_VIOLATION": "Data contract violation",
}


def scan_for_anomalies() -> list[dict]:
    """Returns a list of candidate incidents found in the recent change feed."""
    changes = datahub_client.get_recent_changes()
    candidates = []
    for change in changes:
        change_type = change.get("type")
        if change_type in ANOMALY_TYPES:
            candidates.append(
                {
                    "dataset_urn": change["dataset_urn"],
                    "title": f"{ANOMALY_TYPES[change_type]} on {change['dataset_urn'].split(',')[-2] if ',' in change['dataset_urn'] else change['dataset_urn']}",
                    "severity": change.get("severity", "medium"),
                    "detail": change,
                }
            )
    return candidates


def summarize_detection(dataset_urn: str, detail: dict) -> str:
    """Human-readable one-line summary of what the Discovery Agent found, used in the trace."""
    ds = datahub_client.get_dataset(dataset_urn)
    return (
        f"Detected '{detail.get('type', 'anomaly')}' on dataset '{ds.get('name', dataset_urn)}' "
        f"(platform: {ds.get('platform', 'unknown')}). Raw signal: {detail.get('description', 'n/a')}"
    )
