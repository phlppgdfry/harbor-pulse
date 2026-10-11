-- SQLite warehouse produced by python -m harbor_pulse demo.
-- Run: sqlite3 build/run/warehouse.sqlite < sql/reviewer_queries.sql

-- 1. Reconciliation: canonical arrivals versus materialized facts.
WITH source AS (
 SELECT SUM(CAST(json_extract(payload, '$.Units') AS INTEGER)) AS vehicles
 FROM events WHERE source = 'arrivals'
), target AS (SELECT SUM(vehicles) AS vehicles FROM facts)
SELECT source.vehicles AS source_vehicles, target.vehicles AS fact_vehicles,
       source.vehicles-target.vehicles AS unexplained_difference
FROM source CROSS JOIN target;

-- 2. A correction trail: old and new versions are explicit.
SELECT source,event_key,old_version,new_version,run
FROM audit ORDER BY run,event_key LIMIT 10;

-- 3. Completeness: missing units are separate from dwell-time denominators.
SELECT terminal_key, SUM(vehicles) AS vehicles,
 SUM(json_extract(payload,'$.MissingDepartureUnits')) AS missing_departure_units,
 1.0*SUM(json_extract(payload,'$.CompleteDepartureUnits'))/SUM(vehicles) AS departure_coverage
FROM facts GROUP BY terminal_key;

-- 4. Weighted delay: do not average terminal/day averages equally.
SELECT terminal_key,
 SUM(vehicles*json_extract(payload,'$.DelayMinutes'))/SUM(vehicles) AS weighted_delay_minutes
FROM facts GROUP BY terminal_key;

-- 5. Quarantine is a visible outcome, not deleted evidence.
SELECT run,source,reason,COUNT(*) AS rejected_rows
FROM quarantine GROUP BY run,source,reason ORDER BY run,source;

-- 6. A key is unique by construction; duplicate input is handled before storage.
SELECT source,event_key,COUNT(*) AS versions_in_current_state
FROM events GROUP BY source,event_key HAVING COUNT(*)>1;

-- 7. Run history exposes idempotent replay and subsequent correction.
SELECT id,status,inserted,updated,duplicates,stale,rejected FROM runs ORDER BY id;
