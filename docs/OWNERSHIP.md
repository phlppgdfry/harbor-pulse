# Ownership, choices and interview preparation

**Portfolio owner:** Philippe Godfroy. **Implementation support:** AI-assisted development. **Domain:** fictional terminal network; no employer endorsement or real operational results.

The repository demonstrates completed artifacts. It does not claim that Philippe personally wrote every line or has independently validated every modeling choice. Recruiters can inspect the work and ask him to explain or modify it.

## Choices made in this case

| Choice | Reason | Tradeoff |
|---|---|---|
| Batch sources with explicit vehicle units | Preserve the denominator without pretending to have individual vehicle events | Within-batch distribution is unavailable |
| Key/version/hash upserts | Retain corrections and prevent double counting | Snapshot reads still scan all inputs |
| Weighted KPIs and explicit departure coverage | Avoid giving small batches equal importance and missing data zero dwell | More definitions to explain |
| SQLite and Python standard library | Let reviewers reproduce the core locally | Single writer; no distributed production orchestration |
| Native model with versioned embedded source | Supports typed import, native roles and actual refresh history | Changed source requires explicit release; real source adapter still needed |
| Pilot before a major investment | Test the intervention instead of monetizing a coefficient | Requires real operational agreement and measurement |

## Explain before using this as interview evidence

1. Reproduce the case yourself and inspect a quarantined record.
2. Trace one corrected batch from source version to audit log and daily fact.
3. Explain a weighted measure and why a ratio of averages differs.
4. Change an assumption and show whether the recommended option changes.
5. Explain why an association coefficient is not a staffing intervention effect.
6. Explain the bootstrap unit, missingness, spillover and carryover limitations.
7. Run the tests, deliberately break a control and explain the failure.
8. Describe which cloud controls are verified and which remain blocked.

## CV wording supported by the repository

“Built an AI-assisted, reproducible synthetic Power BI portfolio case combining Python/SQLite ingestion, weighted DAX, data-quality gates, scenario sensitivity and a simulated pilot.”

Avoid claiming actual savings, real stakeholder leadership, production RLS or senior professional experience from this case.

## Interview exercise

Change departure coverage from 99% to 99.9%, show the resulting publication decision, then explain whether the threshold is operationally appropriate. This tests understanding of policy versus arithmetic rather than memorization.
