# Native model, security and refresh

## Deployed model

The active report now binds to **Harbor Pulse - Secured Operations 2026**, an import semantic model created through the Fabric definition API. All 13 tables, two relationships and 56 measures retain the previous case results. All 66 report queries, terminal/date relationships, scenario arithmetic and source/fact reconciliations passed before rebinding. The previous push model is retained for recovery.

The native model uses typed Power Query M partitions with an embedded, versioned synthetic source snapshot. Native refresh now has actual Completed history. It is not a connection to a real terminal system. Changed source content is blocked pending an explicit model release and revalidation; unchanged replay is safe.

## Native row-level roles

Three read-only roles are deployed: Terminal_Zeebrugge, Terminal_Antwerpen and Terminal_Gent. Each filters DimTerminal[TerminalKey], propagating through the relationship to FactOps. Disconnected, full-network evidence tables are denied with FALSE() for these roles, preventing accidental aggregate leakage. Public scenario assumptions and KPI definitions remain available.

No additional users or groups were granted access. Admin APIs confirm only the expected owner in explicit report/model access lists. These APIs do not prove that no tenant administrator has inherited privileges. Owners/admins see the full model and are not suitable RLS viewer test subjects.

A disposable shared workspace and full test model/report were created. Effective-role tokens were issued for all three roles using a synthetic test identity; no Entra user was created. Every viewer render failed with PowerBINotLicensedException. Therefore **role deployment is verified, viewer enforcement is not claimed**. Test resources were deleted. A suitably licensed viewer/test environment is required to finish that test; no license or paid capacity was purchased.

## Activated daily refresh

`com.reviewell.harbor-pulse.refresh` runs `scripts/native_refresh.py` every 86,400 seconds on the owner's Mac. The job reproduces fresh synthetic ingestion, passes quality gates, compares the curated content hash with the approved snapshot and independently decoded live native partition source, requests native refresh, waits for Completed, checks report binding and reconciles cloud totals. A changed source hash fails before touching the active model and requires review.

A successful run writes atomic private ingestion state. A failing or timed-out run cannot overwrite the last verified state. `evidence/native-refresh.json` records the successful first run with zero reconciliation gap. Logs and generated sources remain in ignored build/.

`com.reviewell.harbor-pulse.health` runs hourly. It checks native refresh completion within 26 hours, latest refresh failure, verified ingestion freshness, coverage and report/model binding. Future-dated synthetic events are never used as freshness proof. Failures produce a nonzero process exit and local error logs; no unapproved email or Slack messages are sent.

These are local scheduled controls, dependent on the Mac being available and the CLI authentication remaining valid. They are not a 24/7 managed production service and no real operational source SLA is claimed.

## Operator actions

- Inspect: `launchctl print gui/$(id -u)/com.reviewell.harbor-pulse.refresh` and the equivalent `.health` agent.
- Read private logs/state: build/refresh-monitor.log, build/refresh-monitor-error.log, build/refresh-state.private.json, build/cloud-health.private.json.
- Manual run: `python scripts/native_refresh.py --model MODEL --report REPORT --workspace WORKSPACE --baseline build/run` using your own private IDs.
- Stop: `launchctl bootout gui/$(id -u)/com.reviewell.harbor-pulse.refresh`.
- Changed source: reproduce and gate it, build a new native definition, backup the current definition/data version, validate all queries and roles, then release explicitly. Do not silently turn a changed-source failure into an automatic deployment.

## Reproduce the native source

After `python -m harbor_pulse demo`, run `python scripts/build_native_model.py`. It produces inspectable powerbi/native/model.bim and an ignored API definition payload. Native definitions contain no account binding or credentials. Capture tooling uses the existing CLI token in memory and an isolated headless browser; it never copies a user's browser profile or publishes tokens.

CLI capture prerequisites: Node.js, Playwright and a usable headless Chromium installation; Fabric CLI authentication. Set HARBOR_FAB_PYTHON or HARBOR_CHROME for alternative installations. Capture tokens remain in process memory; short-lived RLS test tokens were removed after testing.
