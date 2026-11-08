"""Exercise the same response check that the ECS deploy workflow runs."""
import json
import os
import subprocess
import sys
from pathlib import Path
from textwrap import dedent

import pytest


@pytest.mark.parametrize("version,environment,accepted", [
    ("1234567", "dev", True),
    ("7654321", "dev", False),
    ("1234567", "prod", False),
])
def test_smoke_verifies_serving_revision(tmp_path, version, environment, accepted):
    workflow = Path(__file__).resolve().parents[1] / ".github/workflows/ecs-project2-deploy.yml"
    smoke = workflow.read_text().split("- name: Smoke test", 1)[1]
    program = dedent(smoke.split("python - <<'PY'", 1)[1].split("\n          PY", 1)[0])
    (tmp_path / "health.json").write_text(json.dumps({
        "status": "ok", "version": version, "env": environment,
    }))
    result = subprocess.run(
        [sys.executable, "-c", program], cwd=tmp_path, capture_output=True,
        env={**os.environ, "GITHUB_SHA": "1234567890", "EXPECTED_ENV": "dev"},
    )
    assert (result.returncode == 0) == accepted, result.stderr
