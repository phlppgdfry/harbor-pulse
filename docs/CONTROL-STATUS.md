# Implemented, demonstrated, designed

| Capability | Status | Practical limit |
|---|---|---|
| KPI definitions / role ownership | Implemented contracts and report page | Roles are fictional; no real organizational sign-off |
| Multiple source feeds and deliberate defects | Executable synthetic generator | Batch-level aggregates, not real vehicle-level feeds |
| Incremental updates | Implemented versioned SQLite upserts | File adapter still scans snapshots |
| Error handling / quarantine / audit | Implemented and tested | Local single-writer database, no distributed retry orchestration |
| Reconciliation / publication gate | Implemented and tested | Thresholds are case assumptions |
| Daily dimensional model and DAX | Implemented, published and query-checked | Power BI receives immutable snapshots, not native incremental refresh |
| Alternative-explanation analysis | Executable descriptive regression | Synthetic association; no causal/forecast validation |
| Costs / constraints / uncertainty | Executable assumption simulation | Parameters are invented and independently drawn |
| Effect measurement | Executable randomized pilot simulation | No real business intervention, safety or cash-saving evidence |
| Local monitoring and weekly CI | Implemented | No live source SLA alerts or automatic tenant refresh |
| Production access roles / RLS | Designed and documented | Real groups/workspace setup not performed |
| Report backup / recovery | Backups captured; operator runbook | Local rollback tested; destructive cloud drill not run |
| Pixel-level report QA | Not performed in this CLI-only workflow | Schema, layout geometry, DAX and server read-back checked separately |

This case demonstrates an end-to-end analytical operating model. It does not label its author senior based on code volume or page count, and it does not present simulated outcomes as professional business achievements.
