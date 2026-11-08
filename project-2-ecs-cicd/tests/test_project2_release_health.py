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
    verifier = Path(__file__).resolve().parents[2] / "project-2-ecs-cicd/verify-release-health.py"
    result = subprocess.run(
        [sys.executable, str(verifier), "1234567", "dev"], capture_output=True, text=True,
        input=json.dumps({"status": "ok", "version": version, "env": environment}),
    )
    assert (result.returncode == 0) == accepted, result.stderr


@pytest.mark.parametrize("active,version,verified", [
    ("previous", "1234567", True),
    ("candidate", "1234567", False),
    ("previous", "7654321", False),
])
def test_rollback_verifies_previous_release(tmp_path, active, version, verified):
    workflow = Path(__file__).resolve().parents[2] / ".github/workflows/ecs-project2-deploy.yml"
    program = dedent(workflow.read_text().split("- name: Roll back failed deployment")[1].split("run: |", 1)[1])
    shims = {
        "aws": 'case "$2" in update-service) echo "$*" > calls ;; wait) echo "$*" >> calls ;; describe-services) echo "$ACTIVE" ;; *) exit 2 ;; esac',
        "curl": 'echo "$HEALTH"',
    }
    for name, body in shims.items():
        binary = tmp_path / name
        binary.write_text("#!/bin/sh\n" + body + "\n")
        binary.chmod(0o755)
    result = subprocess.run(["bash", "-eo", "pipefail", "-c", program], cwd=tmp_path, capture_output=True,
                            text=True, env={**os.environ, "PATH": str(tmp_path) + ":" + os.environ["PATH"],
                            "GITHUB_WORKSPACE": str(workflow.parents[2]), "ACTIVE": active, "PREVIOUS_TASK_DEF": "previous", "ECS_CLUSTER": "dev",
                            "ECS_SERVICE": "demo", "EXPECTED_ENV": "dev", "PREVIOUS_VERSION": "1234567",
                            "SERVICE_URL": "https://example.invalid",
                            "HEALTH": json.dumps({"status": "ok", "env": "dev", "version": version})})
    assert result.returncode != 0
    assert ("Previous release verified" in result.stdout) == verified
    calls = (tmp_path / "calls").read_text()
    assert "--task-definition previous" in calls
    assert "wait services-stable" in calls
