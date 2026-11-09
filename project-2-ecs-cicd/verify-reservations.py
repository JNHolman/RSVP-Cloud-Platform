"""Check the demo.sql seed returned by the serving application's database."""
import argparse
import os
import json
import sys

parser = argparse.ArgumentParser()
parser.add_argument("mode", choices=("fixture", "rds"))
mode = parser.parse_args().mode
payload = json.load(sys.stdin)
rows = payload.get("reservations") if isinstance(payload, dict) else None
if not isinstance(rows, list) or not any(
    isinstance(row, dict)
    and type(row.get("id")) is int
    and row["id"] == 1
    and row.get("event") == "Portfolio rehearsal"
    for row in rows
):
    sys.exit("Expected reservation missing from serving database")

if mode == "rds":
    marker = os.environ.get("RDS_SMOKE_EVENT")
    if not marker or marker == "Portfolio rehearsal" or not any(
        isinstance(row, dict) and type(row.get("id")) is int and row["id"] > 1
        and row.get("event") == marker for row in rows
    ):
        sys.exit("Expected RDS-only reservation missing")
