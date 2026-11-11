import os
import subprocess
from pathlib import Path

import pytest

WORKFLOWS = Path(__file__).resolve().parents[2] / ".github/workflows"


@pytest.mark.parametrize("workflow", ["ecs-project2-bootstrap-image.yml", "ecs-project2-deploy.yml"])
def test_production_release_requires_exact_successful_main_push(tmp_path, workflow):
    text = (WORKFLOWS / workflow).read_text()
    gate = text.split("- name: Require successful main CI", 1)[1].split("- name:", 1)[0]
    assert "if: inputs.environment == 'prod'" in gate
    assert text.index(gate) < text.index("Configure AWS credentials")
    script = gate.split("run: |", 1)[1]
    gh = tmp_path / "gh"
    gh.write_text('#!/bin/sh\nprintf "%s\\n" "$@" > "$ARGS"\necho "$CONCLUSION"\n')
    gh.chmod(0o755)
    env = dict(os.environ, PATH=f"{tmp_path}:{os.environ['PATH']}", ARGS=str(tmp_path / "args"),
               GITHUB_REPOSITORY="owner/repo", GITHUB_SHA="test-commit")
    for ref, result, allowed in [
        ("refs/heads/main", "success", True), ("refs/heads/topic", "success", False),
        ("refs/tags/main", "success", False), ("refs/heads/main", "failure", False),
        ("refs/heads/main", "null", False),
    ]:
        proc = subprocess.run(["bash", "-e", "-c", script], env=dict(env, GITHUB_REF=ref, CONCLUSION=result))
        assert (proc.returncode == 0) == allowed
    args = (tmp_path / "args").read_text().splitlines()
    for expected in ("repos/owner/repo/actions/workflows/ci.yml/runs", "event=push",
                     "branch=main", "head_sha=test-commit"):
        assert expected in args
