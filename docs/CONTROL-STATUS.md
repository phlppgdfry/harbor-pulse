# Implemented, demonstrated, designed

| Capability | Status | Practical limit |
|---|---|---|
| KPI definitions / role ownership | Implemented contracts and report page | Roles are fictional; no real organizational sign-off |
| Multiple source feeds and deliberate defects | Executable synthetic generator | Batch-level aggregates, not real vehicle-level feeds |
| Incremental updates | Implemented versioned SQLite upserts | File adapter still scans snapshots |
| Error handling / quarantine / audit | Implemented and tested | Local single-writer database, no distributed retry orchestration |
| Reconciliation / publication gate | Implemented and tested | Thresholds are case assumptions |
| Daily dimensional model and DAX | Implemented, published and query-checked | Native import with typed M snapshot partitions; no source CDC or native incremental partitions |
| Alternative-explanation analysis | OLS, weekly bootstrap, VIF, residual diagnostics and chronological holdout | Synthetic association; Q4 lacks the maintenance episode; no production validation |
| Costs / constraints / uncertainty | Monte Carlo plus sensitivity, break-even and first-year cash | Parameters are invented; sensitivity is not a forecast |
| Effect measurement | Randomized simulation, null/placebo, power, dropout and spillover planning; written pre-registration | No real intervention, registered protocol or measured guardrail outcomes |
| Local monitoring and weekly CI | Daily native refresh + reconciliation, hourly ingest/refresh SLA monitor and weekly CI | Requires this Mac and CLI auth; embedded synthetic source, no live operational feed or external notifications |
| Access roles / RLS | Three native terminal roles deployed; explicit owner-only access audited via admin APIs | Role-specific viewer rendering is license-blocked; no enforcement pass claimed |
| Report backup / recovery | Local rollback and isolated cloud report-definition restore tested | Snapshot data refresh/recovery is not exercised by the report-only drill |
| Pixel-level report QA | All twelve pages captured with the Microsoft SDK and visually reviewed; concrete rendering defects fixed | API file export stays restricted; selected desktop viewport, not every device/filter combination |

This case demonstrates an end-to-end analytical operating model. It does not label its author senior based on code volume or page count, and it does not present simulated outcomes as professional business achievements.

## Recruiter release evidence

Public walkthrough, narrated 120-second video, captions, one-page PDF, SQL/DAX examples and role-based review routes are included. Headless desktop/mobile website QA is separate from Power BI pixel QA. See [the 15-point delivery ledger](DELIVERY-STATUS.md), [live health](../evidence/cloud-health.json), [recovery drill](../evidence/recovery-drill.json) and [export capability checks](../evidence/export-capabilities.json).

## HP-2026.2 strengthened controls

Automatic existing-report rollback now verifies complete definitions and original binding; an isolated live copy exercises an injected verification failure. Offline publication/refresh faults fail closed and preserve verified state. An explicit case contract and artifact registry check headline claims and artifact identity in CI. A clean git-archive installation is reproduced in an isolated environment. Six assumption challenges and independent hand calculations are included. Website accessibility is automatically checked; report alt text, reading order and markers are supplied. See [control evidence and exact boundaries](RELEASE-CONTROLS.md), [data fitness](DATA-FITNESS.md) and [the challenges](ASSUMPTION-CHALLENGES.md).

**Still unverified:** effective-role viewer rendering remains license-blocked; complete assistive-technology/user accessibility testing and real production source operations are not claimed. Expanded interaction results describe the tested owner session only.
