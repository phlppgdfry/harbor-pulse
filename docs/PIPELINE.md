# Pipeline and reliability

Four replayable source feeds represent arrivals, departures, capacity and staffing. [Contracts](../contracts/source-contracts.json) identify the grain, key, revision field and role owner.

## Versioned ingestion

`events` holds the current valid revision per `(source, business key)`. `revisions` records accepted version/hash identities. `audit` stores old/new version and content hashes. Identical key/version/hash is a no-op; conflicting content at the same version is quarantined; a lower version cannot overwrite the current record.

The adapter reads complete files. **Database writes are incremental; source-file reading is not incremental.** This choice makes replay and backdated corrections safe. Recorded per-source watermarks are monitoring evidence. A future source API adapter can request a bounded overlap window, but must preserve a reconciliation/replay path for older corrections.

## Atomicity and errors

Current events, revision identities, materialized facts and watermarks change in one SQLite transaction. A failed load rolls back all of them; its run is separately marked failed. Tests inject a mid-load failure and verify that no partial event or watermark survives.

Invalid units, unknown terminals, malformed timestamps and same-version conflicts are stored in quarantine. A departure before arrival does not produce negative dwell time: it is excluded from coverage and counted as an invalid join. Missing capacity or staffing stops materialization rather than silently inventing inputs.

## Reconciliation and gates

Latest valid arrival Units are independently summed from canonical events and compared with materialized fact Units. A difference blocks publication. The demo also requires valid departure coverage ≥99% and rejected input rows ≤0.1% across the batch. Small known quarantines remain warnings; passing the gate does not mean every record is clean.

The reproduced sequence is initial ingest → identical replay → higher-version late corrections. It yields 216 duplicates, four quarantined records, zero replay changes and 36 audited corrections. Final valid vehicles are 366,910, with zero unexplained reconciliation difference.

## Power BI delivery

Push datasets append rows and do not offer row-level upserts through this case's API. Consequently **incremental processing lives in SQLite; Power BI receives a new immutable validated snapshot**. The report is rebound after query checks. The previous model and report-definition backup remain available for recovery. No clear-and-reload gap is presented as production-grade incremental refresh.

The demo retains all local history. Production retention, retry/backoff, source SLAs, distributed locking, secrets management and fleet-scale storage need explicit design before rollout. See [control status](CONTROL-STATUS.md).
