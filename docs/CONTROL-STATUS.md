# Implemented, demonstrated, designed

| Capability | Status | Practical limit |
|---|---|---|
| KPI definitions / role ownership | Implemented contracts and report page | Roles are fictional; no real organizational sign-off |
| Multiple source feeds and deliberate defects | Executable synthetic generator | Batch-level aggregates, not real vehicle-level feeds |
| Incremental updates | Implemented versioned SQLite upserts | File adapter still scans snapshots |
| Error handling / quarantine / audit | Implemented and tested | Local single-writer database, no distributed retry orchestration |
| Reconciliation / publication gate | Implemented and tested | Thresholds are case assumptions |
| Daily dimensional model and DAX | Implemented, published and query-checked | Power BI receives immutable snapshots, not native incremental refresh |
| Alternative-explanation analysis | OLS, weekly bootstrap, VIF, residual diagnostics and chronological holdout | Synthetic association; Q4 lacks the maintenance episode; no production validation |
| Costs / constraints / uncertainty | Monte Carlo plus sensitivity, break-even and first-year cash | Parameters are invented; sensitivity is not a forecast |
| Effect measurement | Randomized simulation, null/placebo, power, dropout and spillover planning; written pre-registration | No real intervention, registered protocol or measured guardrail outcomes |
| Local monitoring and weekly CI | Local hourly live API monitor activated and first run succeeded; weekly synthetic CI | Requires this Mac and CLI auth; no automatic tenant/source refresh or external notifications |
| Production access roles / RLS | Designed and documented | Real groups/workspace setup not performed |
| Report backup / recovery | Local rollback and isolated cloud report-definition restore tested | Snapshot data refresh/recovery is not exercised by the report-only drill |
| Pixel-level report QA | Blocked: PNG tenant disabled; PDF lacks dedicated capacity | Schema/DAX/read-back do not prove pixel rendering |

This case demonstrates an end-to-end analytical operating model. It does not label its author senior based on code volume or page count, and it does not present simulated outcomes as professional business achievements.

## Recruiter release evidence

Public walkthrough, narrated 120-second video, captions, one-page PDF, SQL/DAX examples and role-based review routes are included. Headless desktop/mobile website QA is separate from Power BI pixel QA. See [the 15-point delivery ledger](DELIVERY-STATUS.md), [live health](../evidence/cloud-health.json), [recovery drill](../evidence/recovery-drill.json) and [export capability checks](../evidence/export-capabilities.json).
