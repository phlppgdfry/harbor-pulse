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

The tests cover local atomic rollback. An isolated temporary report copy was changed, restored from its own private backup and deleted. All definition parts and binding matched; the original report stayed unchanged. [Cloud recovery evidence](../evidence/recovery-drill.json). This drill tests report-definition rollback, not warehouse corruption or model-data recovery.

## Activated local live monitor

On the portfolio owner's Mac, `com.reviewell.harbor-pulse.health` is a LaunchAgent with a 3,600-second interval and RunAtLoad. It executes `scripts/cloud_operations.py health` using locally authenticated Fabric CLI. Account-specific arguments and the plist stay outside public source.

Checks: report/model binding, independently expected vehicle total, zero reconciliation difference and >=99% departure coverage. Refresh history is inspected; this immutable push snapshot currently has no conventional refresh entries. An empty history is not a successful source refresh. The access endpoint returns GroupNotAccessible for My workspace; no authoritative roster or RLS check is claimed.

Current private state: `build/cloud-health.private.json`. Logs: `build/health-monitor.log` and `build/health-monitor-error.log`. Failure produces a nonzero exit code for launchd/operator inspection. It does not send email or external messages. This is a local availability/consistency monitor, not a production freshness SLA service.

Inspect with `launchctl print gui/$(id -u)/com.reviewell.harbor-pulse.health`. Stop with `launchctl bootout gui/$(id -u)/com.reviewell.harbor-pulse.health`. Regenerate the local arguments after an intentional model rebind. Do not schedule competing publication jobs without a lock and idempotent release design.

The cloud helper retries transient read/idempotent operations and polls asynchronous operations. Ambiguous create/delete outcomes require inspection; do not blindly duplicate a mutation. Cleanup is limited to the temporary report created by the drill.
