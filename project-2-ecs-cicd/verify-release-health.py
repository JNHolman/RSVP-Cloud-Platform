"""Verify a deployed release using the /health JSON on standard input."""
import argparse
import json
import sys

parser = argparse.ArgumentParser()
parser.add_argument("version")
parser.add_argument("environment")
args = parser.parse_args()
payload = json.load(sys.stdin)
if (payload.get("status"), payload.get("version"), payload.get("env")) != (
    "ok", args.version, args.environment
):
    sys.exit("Unexpected release health, version or environment")
