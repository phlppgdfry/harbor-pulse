# Power BI and CLI publication

Local reproduction is account-free. Publication needs Microsoft Fabric CLI (`fab`), an existing authorized Microsoft account and a workspace you can write to. This code grants no additional permissions.

The model schema/data are generated at `build/run/model.json` and `build/run/tables.json`. `scripts/publish_powerbi.py` publishes a validated new model snapshot using the CLI's Power BI audience. It refuses to create another snapshot if a publication receipt exists.

```bash
python -m harbor_pulse demo
python -m pip install -r requirements-report.txt
python scripts/publish_powerbi.py
python scripts/build_report.py
python scripts/validate_report.py
python scripts/verify_powerbi.py
```

The builder uses the ignored `build/publication.private.json` to bind the report. Without that file, it produces reviewable source with a deliberately unconfigured connection placeholder. It is not a credential-free live report.

Before updating an existing report, obtain a private backup of its definition. Then use your own workspace/report IDs:

```bash
fab api workspaces/WORKSPACE_ID/reports/REPORT_ID/updateDefinition \
  -X post -i build/update.json --show_headers
```

The API may return 202; check its operation status before claiming success. List pages, verify the bound model and read the definition back. Keep tenant IDs and receipts out of Git. Do not clear existing push-table rows to simulate row-level incremental refresh.

Relevant Microsoft references: [push dataset schema](https://learn.microsoft.com/en-us/rest/api/power-bi/push-datasets/datasets-post-dataset), [execute DAX queries](https://learn.microsoft.com/en-us/rest/api/power-bi/datasets/execute-queries), [update report definition](https://learn.microsoft.com/en-us/rest/api/fabric/report/items/update-report-definition).
