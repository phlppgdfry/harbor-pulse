# Operations, access and recovery runbook

## Responsibilities

Data steward owns contracts/quarantine; operations lead owns service definitions and the pilot; finance controller owns monetization assumptions; release owner publishes validated snapshots. These are fictional roles, not actual account grants.

## Access and monitoring

The active report uses a native import model in the personal workspace. Three terminal roles are deployed, and admin APIs confirm explicit owner-only report/model access. Role-specific viewer rendering remains license-blocked. No extra users were granted access.

Daily guarded native refresh and hourly ingestion/refresh SLA monitoring are activated locally. Read the complete [native operating runbook](NATIVE-OPERATIONS.md) for implementation, failure behavior, private logs, scheduler controls and remaining license/source limits. Generated sources, private account receipts and credentials stay outside public Git content.

## Release

1. Reproduce the pipeline in a fresh output directory; pass data-quality gates.
2. Run unit tests, evidence checks and PBIR schema/geometry validation.
3. Export the current report definition as a private backup.
4. Publish a validated native model definition through your authenticated CLI; keep the previous source/data version and private definition backup.
5. Execute visual queries and independently reconcile KPIs.
6. Update the report definition/model reference; confirm asynchronous success, pages and model binding.
7. Read definitions back and compare them with source; then archive the previous model.

## Recover

- Failed local load: transaction rollback preserves current events/facts/watermarks. Fix the source, inspect quarantine and replay.
- Failed model upload: do not append blindly; inspect per-table receipts and counts before retrying.
- Failed report release: publish the private previous report-definition backup, restoring its previous model reference. Confirm pages and DAX before marking recovery complete.
- Never delete a historical model while it is still referenced by a backup or report. This case does not automatically purge source or model history.

The tests cover local atomic rollback. An isolated temporary report copy was changed, restored from its own private backup and deleted. All definition parts and binding matched; the original report stayed unchanged. [Cloud recovery evidence](../evidence/recovery-drill.json). This drill tests report-definition rollback, not warehouse corruption or model-data recovery.

## Activated local jobs

`com.reviewell.harbor-pulse.refresh`: daily synthetic ingestion, content/quality gate, native refresh, cloud reconciliation and atomic verified state. `com.reviewell.harbor-pulse.health`: hourly binding, access, refresh completion and 26-hour ingestion/refresh SLA. Both require this Mac and authenticated CLI. No operational system or external notification destination is configured.

[Native runbook](NATIVE-OPERATIONS.md) · [successful native refresh](../evidence/native-refresh.json) · [access audit](../evidence/access-audit.json) · [deployed role definitions](../evidence/rls-definition.json).
