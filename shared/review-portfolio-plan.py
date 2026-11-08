"""Read terraform show -json from stdin. Never print plan values or use AWS."""
import argparse
import json
import re
import sys

TARGETS = {
    "p1": ("rsvp-pf1", "dev.cloud.rsvpsociety.com"),
    "p2": ("rsvp-project2", "ecs.cloud.rsvpsociety.com"),
}


def review(plan, target, zone):
    project, host = TARGETS[target]
    expected = {"project_name": project, "environment": "dev", "domain_name": host,
                "route53_zone_id": zone, "aws_region": "us-east-1"}
    findings = []
    if plan["format_version"].split(".")[0] != "1" or plan.get("errored"):
        raise ValueError("unsupported or errored plan")
    for key, value in expected.items():
        if plan["variables"].get(key, {}).get("value") != value:
            findings.append(f"Unexpected or missing input: {key}")

    pending_acm = False
    for item in plan["resource_changes"]:
        change = item["change"]
        actions = change["actions"]
        address = item["address"]
        if change.get("importing") is not None or item.get("previous_address"):
            findings.append(f"{address}: import or state move requires separate review")
        if actions in (["no-op"], ["read"]):
            continue
        if actions != ["create"]:
            findings.append(f"{address}: existing-resource change requires separate review")
        if item["type"].startswith("aws_route53") and item["type"] != "aws_route53_record":
            findings.append(f"{address}: unexpected DNS infrastructure change")
        if item["type"] != "aws_route53_record":
            continue
        after = change.get("after") or {}
        if after.get("zone_id") != zone:
            findings.append(f"{address}: unexpected or unknown hosted zone")
        name = (after.get("name") or "").lower().rstrip(".")
        if address == "aws_route53_record.app":
            if name != host or after.get("type") != "A":
                findings.append(f"{address}: unexpected application DNS record")
        elif address == f'aws_route53_record.acm_validation["{host}"]':
            unknown = change.get("after_unknown", {})
            if after.get("allow_overwrite") is not False:
                findings.append(f"{address}: ACM record takeover enabled or unknown")
            if not name and unknown.get("name"):
                pending_acm = True
            elif not re.fullmatch(r"_[a-z0-9-]+\." + re.escape(host), name):
                findings.append(f"{address}: unexpected validation name")
            if after.get("type") != "CNAME" and not unknown.get("type"):
                findings.append(f"{address}: unexpected validation record type")
        else:
            findings.append(f"{address}: unexpected DNS record")
    return findings, pending_acm


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("target", choices=TARGETS)
    parser.add_argument("child_zone_id", help="independently verified public child zone ID")
    args = parser.parse_args()
    try:
        findings, pending = review(json.load(sys.stdin), args.target, args.child_zone_id)
    except (KeyError, TypeError, AttributeError, ValueError):
        print("Invalid or unsupported Terraform plan JSON.", file=sys.stderr)
        return 2
    for finding in findings:
        print(finding)
    if pending:
        print("ACM validation name is provider-generated. Confirm the issued CNAME in the child zone.")
    if findings:
        return 1
    print("Portfolio input, DNS scope and first-deployment action checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
