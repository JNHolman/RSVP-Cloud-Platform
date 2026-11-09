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


SEED = {"id": 1, "event": "Portfolio rehearsal"}
MARKER = {"id": 2, "event": "DB marker"}


@pytest.mark.parametrize("active,version,rows,mode,verified", [
    ("previous", "1234567", [SEED], "fixture", True),
    ("previous", "1234567", [SEED, MARKER], "rds", True),
    ("previous", "1234567", [SEED], "rds", False),
    ("previous", "1234567", [SEED, {"id": 2, "event": "Other database"}], "rds", False),
    ("candidate", "1234567", [SEED], "fixture", False),
    ("previous", "7654321", [SEED], "fixture", False),
    ("previous", "1234567", [], "fixture", False),
])
def test_rollback_verifies_previous_release(tmp_path, active, version, rows, mode, verified):
    workflow = Path(__file__).resolve().parents[2] / ".github/workflows/ecs-project2-deploy.yml"
    program = dedent(workflow.read_text().split("- name: Roll back failed deployment")[1].split("run: |", 1)[1])
    shims = {
        "aws": 'case "$2" in update-service) echo "$*" > calls ;; wait) echo "$*" >> calls ;; describe-services) echo "$ACTIVE" ;; *) exit 2 ;; esac',
        "curl": 'case "$*" in */api/reservations) echo "$ROWS" ;; *) echo "$HEALTH" ;; esac',
    }
    for name, body in shims.items():
        binary = tmp_path / name
        binary.write_text("#!/bin/sh\n" + body + "\n")
        binary.chmod(0o755)
    result = subprocess.run(["bash", "-eo", "pipefail", "-c", program], cwd=tmp_path, capture_output=True,
                            text=True, env={**os.environ, "PATH": str(tmp_path) + ":" + os.environ["PATH"],
                            "GITHUB_WORKSPACE": str(workflow.parents[2]), "ACTIVE": active, "PREVIOUS_TASK_DEF": "previous", "ECS_CLUSTER": "dev",
                            "ECS_SERVICE": "demo", "EXPECTED_ENV": "dev", "PREVIOUS_VERSION": "1234567", "PREVIOUS_DB_MODE": mode, "RDS_SMOKE_EVENT": "DB marker",
                            "SERVICE_URL": "https://example.invalid",
                            "ROWS": json.dumps({"reservations": rows}),
                            "HEALTH": json.dumps({"status": "ok", "env": "dev", "version": version})})
    assert result.returncode != 0
    assert ("Previous release verified" in result.stdout) == verified
    calls = (tmp_path / "calls").read_text()
    assert "--task-definition previous" in calls
    assert "wait services-stable" in calls

@pytest.mark.parametrize("mode", ["fixture", "rds"])
@pytest.mark.parametrize("reply,accepted", [
    ('{"reservations":[{"id":1,"event":"Portfolio rehearsal"}]}', True),
    ('{"reservations":[{"id":1,"event":"Wrong database"}]}', False),
    ('{"reservations":[{"id":1,"event":"Portfolio rehearsal"},{"id":2,"event":"DB marker"}]}', True),
    ('{"reservations":[]}', False),
    ('{"error":"reservations unavailable"}', False),
    ('upstream unavailable', False),
])
def test_candidate_smoke_checks_reservations(tmp_path, reply, accepted, mode):
    workflow = Path(__file__).resolve().parents[2] / ".github/workflows/ecs-project2-deploy.yml"
    smoke = workflow.read_text().split("- name: Smoke test")[1].split("- name: Roll back")[0]
    program = dedent(smoke.split("run: |", 1)[1])
    for name, body in {
        "aws": "echo candidate",
        "curl": 'case "$*" in */api/reservations) echo "$ROWS" ;; *) echo "$HEALTH" ;; esac',
    }.items():
        binary = tmp_path / name
        binary.write_text("#!/bin/sh\n" + body + "\n")
        binary.chmod(0o755)
    env = dict(os.environ, PATH=str(tmp_path) + ":" + os.environ["PATH"],
               GITHUB_WORKSPACE=str(workflow.parents[2]), GITHUB_SHA="1234567",
               EXPECTED_ENV="dev", TASK_DEF_ARN="candidate", SERVICE_URL="https://example.invalid",
               CANDIDATE_DB_MODE=mode, RDS_SMOKE_EVENT="DB marker",
               HEALTH=json.dumps({"status": "ok", "version": "1234567", "env": "dev"}), ROWS=reply)
    result = subprocess.run(["bash", "-eo", "pipefail", "-c", program], env=env, capture_output=True)
    assert (result.returncode == 0) == (accepted and (mode == "fixture" or "DB marker" in reply))
    assert "steps.smoke.outcome == 'failure'" in workflow.read_text()
