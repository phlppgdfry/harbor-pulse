# Release, recovery and evidence controls

## Existing report publication

`scripts/release_report.py` updates one existing report and never creates a model. It
captures the complete definition and original binding before publication. Verification
compares every intended definition part and the expected model binding. Any exception
including an uncertain update time-out attempts restoration, followed by read-back of
**all** backup parts and the original binding. Binding drift triggers Rebind to the
captured model. A failed release remains failed even if restoration succeeds. Failed
restoration exits nonzero with `rollback_verified=false`; it cannot report release success.
Private backups and receipts live in ignored `build/releases/`. Public receipts omit
report/model identifiers and payloads. This script supports the case's **My workspace**
Power BI report endpoints; adapting to another workspace requires group-scoped endpoints.

The live proof in `scripts/prove_release_recovery.py` creates only an isolated report copy,
updates that copy, injects a verifier failure after the real cloud update, and exercises
the same automatic restore function. It independently checks the restored definition,
binding, unchanged production report and deletion of that exact clone. It does not induce
a real tenant outage and does not demonstrate semantic-model data recovery.

## Failure injection

Offline tests cover expired authentication, safe HTTP429 retries, non-retry of creation,
request/polling time-outs, failed operations, wrong model binding, wrong definition,
failed rollback, partial model loading and native refresh failure. They require no cloud
account. Native refresh preserves the previous verified state unless source hash,
publication gate, successful refresh, cloud totals, coverage and binding all reconcile.
Only then does the atomic state replacement advance the ingest clock.

The legacy push-model publisher writes a durable `creation_pending` intent before its
non-idempotent request. A lost response can mean the model was created. Existing intent
or partial-load receipts block another create; an operator must reconcile cloud inventory
and explicitly resume/recover. It does not silently retry or claim completed loading.
This is fail-closed duplicate prevention, not automatic exactly-once cloud provisioning.

## Consistent release evidence

`contracts/case-release.json` defines the case version, headline metrics, recommendation
and blocked RLS viewer status. README, website and PDF carry the same structured claim;
visible headline values are checked separately. `scripts/audit_case.py` compares these
against generated totals, native-model inventory, report source and screenshot inventory.
It checks registered SHA256 hashes for PDF, figures, screenshot files, report source and
JSON. It also compares the website scenario data with analytical evidence. Mutation tests
prove that visible KPI drift, JSON drift and changed screenshot bytes fail validation.

A reviewed release explicitly runs `audit_case.py --register`. CI **never** registers new
hashes automatically. Hashes establish exact artifact identity and inventory, not OCR of
all screenshot labels, validity of every prose statement or a causal economic conclusion.
SDK capture receipts establish screenshot origin. Images are also visually inspected.
Historical receipts are dated evidence, not a claim that the cloud is continuously healthy.

## Clean installation

`scripts/check_clean_clone.py` extracts **git archive HEAD** into a temporary directory,
without `.git`, `.venv`, ignored `build/`, receipts or machine-specific paths. It creates a
new locked environment, runs tests, reproduces the demo and builds/validates the report.
CI repeats this on Ubuntu. Package/download caches may be reused; this tests filesystem
and environment isolation, not a network-isolated machine. Website CI separately installs
Chromium and its system dependencies using the committed Node lockfile.

## Accessibility and interactions

The website has a skip link, visible keyboard focus, row/column table headers, semantic
landmarks, descriptive image text, captions and a readable slider value. Axe checks WCAG
A/AA rules at desktop/mobile sizes; automated success is not full WCAG certification.
Power BI source supplies filter-aware alt text, visual reading order, marker-enabled line
charts, a chart palette checked at 3:1 against white, explicit labels/status text and access to numeric tables. Native keyboard support
and screen-reader behavior still need assistive-technology review by real users.

The expanded live SDK matrix checks empty-result filters, multiple terminals, all twelve
months, reset and extreme **actual slicer** states against source totals. Session changes
are not saved to the report. It does not test every cross-highlight, mobile layout or
screen reader. Viewer-role RLS rendering remains **license-blocked**; no enforcement pass
is claimed. Ownership/access audits do not substitute for a viewer-role test.

Microsoft references: [report accessibility](https://learn.microsoft.com/en-us/power-bi/create-reports/desktop-accessibility-creating-reports),
[SDK filters](https://learn.microsoft.com/en-us/javascript/api/overview/powerbi/control-report-filters),
[SDK slicers](https://learn.microsoft.com/en-us/javascript/api/overview/powerbi/control-report-slicers),
[Rebind](https://learn.microsoft.com/en-us/rest/api/power-bi/reports/rebind-report).
