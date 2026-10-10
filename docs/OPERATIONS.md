# Operations, access and recovery runbook

## Responsibilities

Data steward owns contracts/quarantine; operations lead owns service definitions and the pilot; finance controller owns monetization assumptions; release owner publishes validated snapshots. These are fictional roles, not actual account grants.

## Access design

The existing Power BI deployment uses the user's personal workspace. This case does not create users, broaden sharing or enable Publish to web. A team deployment should separate viewers, builders and release operators, with real groups, access review and agreed terminal-level RLS. **That design is documented, not configured here.** The attempted membership API inspection did not provide a reliable roster; no access-audit pass is claimed.

Public GitHub content contains synthetic sources, reproducible summaries, report-building code and documentation. Generated private IDs, raw source files, SQLite databases, publication receipts and account settings stay under ignored `build/`. CLI authentication handles credentials; no tokens are written to public source.

## Monitor

`python -m harbor_pulse monitor` prints local load status/counters. Inspect quarantine reasons, reconciliation, coverage and watermarks. A watermark is the newest source revision time, not proof that a feed is fresh. In a production adapter, compare it with an agreed source SLA and ingest clock; this case uses generated dates and makes no real freshness claim.

GitHub Actions runs tests and reproduces the synthetic evidence on changes, manually and weekly. It does **not** schedule Power BI publication or deliver real-time alerts. A production refresh/alerting integration requires a service identity, source schedule and operator-approved notification destination.

## Release

1. Reproduce the pipeline in a fresh output directory; pass data-quality gates.
2. Run unit tests, evidence checks and PBIR schema/geometry validation.
3. Export the current report definition as a private backup.
4. Publish a new immutable model snapshot through your authenticated CLI.
5. Execute visual queries and independently reconcile KPIs.
6. Update the report definition/model reference; confirm asynchronous success, pages and model binding.
7. Read definitions back and compare them with source; then archive the previous model.

## Recover

- Failed local load: transaction rollback preserves current events/facts/watermarks. Fix the source, inspect quarantine and replay.
- Failed model upload: do not append blindly; inspect per-table receipts and counts before retrying.
- Failed report release: publish the private previous report-definition backup, restoring its previous model reference. Confirm pages and DAX before marking recovery complete.
- Never delete a historical model while it is still referenced by a backup or report. This case does not automatically purge source or model history.

The tests cover local atomic rollback. Cloud rollback is a documented operator procedure with saved backups; no deliberately disruptive production rollback drill was run.
