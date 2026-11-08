import json
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts/review-portfolio-plan.py"


@pytest.mark.parametrize("project,host,target", [
    ("rsvp-pf1", "dev.cloud.rsvpsociety.com", "p1"),
    ("rsvp-project2", "ecs.cloud.rsvpsociety.com", "p2"),
])
def test_first_deployment_review(project, host, target):
    zone = "ZCHILD"
    values = dict(project_name=project, environment="dev", domain_name=host,
                  route53_zone_id=zone, aws_region="us-east-1")
    alias = {"address": "aws_route53_record.app", "type": "aws_route53_record",
             "change": {"actions": ["create"], "after": {"name": host, "zone_id": zone, "type": "A"}}}
    validation = {
        "address": f'aws_route53_record.acm_validation["{host}"]', "type": "aws_route53_record",
        "change": {"actions": ["create"], "after": {"zone_id": zone, "allow_overwrite": False},
                   "after_unknown": {"name": True, "type": True}},
    }
    plan = {"format_version": "1.2", "variables": {k: {"value": v} for k, v in values.items()},
            "resource_changes": [alias, validation]}

    def run():
        return subprocess.run([sys.executable, str(SCRIPT), target, zone], input=json.dumps(plan),
                              capture_output=True, text=True)

    assert run().returncode == 0
    alias["change"]["after"]["name"] = "api.rsvpsociety.com"
    assert run().returncode == 1
    alias["change"]["after"]["name"] = host
    alias["change"]["after"]["zone_id"] = "ZPARENT"
    assert run().returncode == 1
    alias["change"]["after"]["zone_id"] = zone
    alias["change"]["actions"] = ["delete", "create"]
    assert run().returncode == 1
    alias["change"]["actions"] = ["create"]
    validation["change"]["after"]["allow_overwrite"] = True
    assert run().returncode == 1
