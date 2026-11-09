"""Check the demo.sql seed returned by the serving application's database."""
import json
import sys

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
