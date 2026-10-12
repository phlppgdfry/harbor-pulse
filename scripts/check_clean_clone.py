"""Reproduce committed source in an isolated git archive, never copy ignored build/."""

import argparse
import json
import os
import pathlib
import subprocess
import tarfile
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[1]


def check(root=ROOT):
    with tempfile.TemporaryDirectory(prefix="harbor-clean-") as folder:
        folder = pathlib.Path(folder)
        archive = folder / "source.tar"
        checkout = folder / "checkout"
        checkout.mkdir()
        subprocess.run(
            ["git", "archive", "--format=tar", "HEAD", "-o", str(archive)], cwd=root, check=True
        )
        with tarfile.open(archive) as source:
            source.extractall(checkout, filter="data")
        if (checkout / "build").exists():
            raise RuntimeError("Ignored build state leaked into clean checkout")
        env = os.environ.copy()
        for name in [
            "PYTHONPATH",
            "VIRTUAL_ENV",
            "HARBOR_RUN",
            "HARBOR_CAPTURE_CONFIG",
            "HARBOR_FAB_PYTHON",
            "HARBOR_PLAYWRIGHT_MODULE",
        ]:
            env.pop(name, None)
        env["UV_PROJECT_ENVIRONMENT"] = str(checkout / ".venv")
        commands = [
            ["uv", "sync", "--locked", "--extra", "report"],
            ["uv", "run", "--locked", "python", "-m", "unittest", "discover", "-s", "tests"],
            ["uv", "run", "--locked", "python", "-m", "harbor_pulse", "demo"],
            ["uv", "run", "--locked", "python", "scripts/check_evidence.py"],
            ["uv", "run", "--locked", "python", "scripts/audit_case.py"],
            ["uv", "run", "--locked", "python", "scripts/check_report_accessibility.py"],
            ["uv", "run", "--locked", "python", "scripts/build_native_model.py"],
            ["uv", "run", "--locked", "python", "scripts/build_report.py"],
            ["uv", "run", "--locked", "python", "scripts/validate_report.py"],
        ]
        for command in commands:
            subprocess.run(command, cwd=checkout, env=env, check=True)
        return dict(
            status="passed",
            source="git archive HEAD",
            ignored_state_copied=False,
            cloud_credentials_required=False,
            commands=len(commands),
            limits="Fresh filesystem and virtualenv; uv package/download cache may be reused. Browser installation is independently tested in the website CI job.",
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.parse_args()
    result = check()
    (ROOT / "build").mkdir(exist_ok=True)
    (ROOT / "build/clean-clone.json").write_text(json.dumps(result, indent=2))
    print(json.dumps(result, indent=2))
