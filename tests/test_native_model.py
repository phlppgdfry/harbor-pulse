import base64
import json
import unittest

from scripts.build_native_model import build, definition


class NativeModelTests(unittest.TestCase):
    def model(self):
        names = [
            "DimTerminal",
            "FactOps",
            "DQRule",
            "LoadRun",
            "DecisionOption",
            "PilotSummary",
            "Association",
        ]
        push = {
            "tables": [
                {"name": n, "columns": [{"name": "TerminalKey", "dataType": "Int64"}]}
                for n in names
            ],
            "relationships": [],
        }
        return build(push, {n: [{"TerminalKey": 1}] for n in names})

    def test_roles_are_read_only_and_annual_evidence_is_denied(self):
        model = self.model()
        for i, role in enumerate(model["model"]["roles"], 1):
            self.assertEqual(role["modelPermission"], "read")
            self.assertNotIn("members", role)
            filters = {p["name"]: p["filterExpression"] for p in role["tablePermissions"]}
            self.assertEqual(filters["DimTerminal"], f"[TerminalKey] = {i}")
            for name in ["DQRule", "LoadRun", "DecisionOption", "PilotSummary", "Association"]:
                self.assertEqual(filters[name], "FALSE()")

    def test_embedded_import_source_contains_only_fixture_rows(self):
        table = self.model()["model"]["tables"][0]
        source = table["partitions"][0]["source"]["expression"]
        encoded = source.split('Binary.FromText("', 1)[1].split('"', 1)[0]
        self.assertEqual(json.loads(base64.b64decode(encoded)), [{"TerminalKey": 1}])
        self.assertEqual(table["partitions"][0]["mode"], "import")

    def test_definition_round_trips_without_account_binding(self):
        model = self.model()
        parts = definition(model)["parts"]
        self.assertEqual(json.loads(base64.b64decode(parts[0]["payload"])), model)
        self.assertNotIn("workspaceId", model)
