# Reproducible quality checks

The analytics core uses only the Python standard library. Developer checks and optional
report dependencies are resolved in `uv.lock`; the browser test runner is pinned in
`package-lock.json`. Python 3.12 is the tested default; Node.js 22+ is required for website QA.
This repository is a script-based project (`tool.uv.package = false`), not a distributable wheel.

## Bootstrap

Install [uv](https://docs.astral.sh/uv/getting-started/installation/) and
[Gitleaks](https://github.com/gitleaks/gitleaks#installing) using their official instructions.
On macOS, `brew install uv gitleaks` is one option. CI pins uv 0.12.23 and checksum-verifies
Gitleaks 8.30.1. Ruff, Coverage.py, Hypothesis, pre-commit and SQLFluff are local developer
dependencies, not global Python installations.

```sh
uv sync --locked --extra report
npm ci
npx playwright install chromium
uv run --locked pre-commit install
```

On Linux CI, Playwright additionally installs system browser dependencies with
`npx playwright install --with-deps chromium`. Hooks require the bootstrapped environment
and Gitleaks on PATH. No authentication or Power BI tenant is needed for these checks.

## Python, SQL and secrets

```sh
uv run --locked ruff check .
uv run --locked ruff format --check .
uv run --locked sqlfluff lint sql
uv run --locked coverage run -m unittest discover -s tests -v
uv run --locked coverage run --append scripts/review_evidence.py
uv run --locked coverage report
uv run --locked coverage html
uv run --locked coverage xml
uv run --locked pre-commit run --all-files
gitleaks git --redact --no-banner
```

`review_evidence.py` reads `build/run`; reproduce it first on a fresh checkout:
`uv run --locked python -m harbor_pulse demo`. Use a new `--output` directory for another
local run; the CLI deliberately refuses to overwrite a populated warehouse.

Ruff checks imports, unused variables, basic Python errors and bug-prone constructs.
SQLFluff uses the SQLite dialect. `ruff format .` and `sqlfluff fix sql` are explicit
formatting commands; commit hooks check the result rather than silently rewriting it.
The uv hook rejects dependency changes with a stale lockfile.
Gitleaks checks staged changes at commit time and full Git history in CI. Findings are
redacted. This is a detection control, not a guarantee that every possible secret is detected.

## What the coverage gate means

Coverage includes statements **and branches** in `harbor_pulse` and
`scripts.cloud_operations`, `scripts.release_report`, `scripts.publish_powerbi` and `scripts.native_refresh`, with a minimum combined score of 80%. HTML reports live in
`build/coverage/html/index.html`, XML in `build/coverage/coverage.xml`; CI uploads both.
Tests, generated artifacts and unrelated publishing/rendering scripts are outside this
scope. The gate does not assert 80% coverage of every cloud script.

Hypothesis generates 60 revision-order/duplicate cases and 25 transaction-failure cases
per run. An independent latest-version oracle checks totals; injected failures must
preserve previously committed facts and watermarks. These generated examples are additional
to unittest's test-method count. Deterministic generation makes CI runs reproducible.

Cloud contract tests mock the CLI and API. They check retries for safe operations,
non-retry of report creation, missing authentication, subprocess time-outs, operation
polling failures/time-outs, request-file cleanup, health drift, and isolated recovery.
They do not establish live RLS enforcement or cloud service availability. See
[control status](CONTROL-STATUS.md) for actual tenant evidence and remaining limitations.

## Website checks

```sh
npm run test:web
```

The committed Playwright suite starts its own localhost server and uses an isolated
headless Chromium, with desktop and mobile viewports. It tests all 32 assumption-grid
combinations against the committed analytical evidence, gallery keyboard controls,
full-resolution links, image loading, horizontal overflow, missing-evidence fallback,
and the two-minute video's metadata and captions. No user browser session is controlled.

Full-page screenshots, HTML reports and failure traces are local artifacts under
`test-results/` and `playwright-report/`; CI uploads them for review. These screenshots
are inspection evidence, **not pixel-diff baseline tests**. The scenario checks establish
agreement with existing evidence, not external economic validity. The existing Power BI
screenshots are checked as website assets; this suite does not render the live tenant.

## Continuous integration

`.github/workflows/verify.yml` runs independent reproduction, full-history secret scan
and browser QA jobs on pushes, pull requests, manual runs and the weekly schedule.
The reproduction job validates the publication gate, native model, report schemas and
reviewer SQL after linting/tests. Jobs have read-only repository permissions and need no
cloud credentials. A successful check is evidence for that commit, not a timeless badge.


HP-2026.2 adds `scripts/challenge_evidence.py`, `scripts/audit_case.py` and `scripts/check_clean_clone.py`. CI checks the committed artifact registry before evidence generators write new working outputs. A reviewer should run `uv run --locked python scripts/audit_case.py` after the fresh demo, before rebuilding tracked artifacts. Registering hashes is an explicit reviewed-release step. The expanded coverage scope now includes release, publication and refresh controls; its score is not directly comparable to the earlier narrower 94.4% measurement.
