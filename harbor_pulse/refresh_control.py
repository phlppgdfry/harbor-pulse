"""Refresh policy evaluated against a release/ingestion clock, not event dates.

Future-dated synthetic events must never masquerade as a fresh production feed.
"""

import datetime as dt


def evaluate(manifest, now=None, max_age_hours=26):
    now = now or dt.datetime.now(dt.timezone.utc)
    errors = []
    try:
        loaded = dt.datetime.fromisoformat(manifest["ingested_at"].replace("Z", "+00:00"))
        if loaded.tzinfo is None:
            raise ValueError("timezone required")
        age = (now - loaded).total_seconds() / 3600
        if age < 0:
            errors.append("ingest_clock_in_future")
        if age > max_age_hours:
            errors.append("ingest_sla_exceeded")
    except (KeyError, TypeError, ValueError):
        age = None
        errors.append("invalid_ingest_clock")
    if manifest.get("source_fact_difference") != 0:
        errors.append("reconciliation_failed")
    if manifest.get("departure_coverage", 0) < 0.99:
        errors.append("coverage_failed")
    if manifest.get("release_status") != "verified":
        errors.append("release_not_verified")
    if manifest.get("source_kind") not in ("synthetic", "operational"):
        errors.append("source_kind_missing")
    return dict(
        healthy=not errors,
        errors=errors,
        ingest_age_hours=age,
        max_age_hours=max_age_hours,
        synthetic=manifest.get("source_kind") == "synthetic",
        clock="verified ingestion time; source event time is never used as freshness proof",
    )
