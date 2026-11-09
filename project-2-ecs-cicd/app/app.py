import datetime
import os
import sqlite3
import ssl
from contextlib import closing
from pathlib import Path

import boto3
import pymysql
from botocore.exceptions import BotoCoreError, ClientError
from flask import Flask, jsonify, render_template_string

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 64 * 1024

APP_VERSION = os.getenv("APP_VERSION", "local")
ENV_NAME = os.getenv("ENV_NAME", "dev")
SERVICE_NAME = os.getenv("SERVICE_NAME", "RSVP Cloud Service")

HTML_TEMPLATE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{{ service_name }} {{ app_version }}</title></head>
<body><main>
<h1>{{ service_name }}</h1>
<h2>Reservations</h2>
{% if unavailable %}
<p role="alert">Reservations are temporarily unavailable.</p>
{% elif rows %}
<table><thead><tr><th scope="col">Reservation ID</th><th scope="col">Event</th></tr></thead>
<tbody>{% for id, event in rows %}<tr><td>{{ id }}</td><td>{{ event }}</td></tr>{% endfor %}</tbody></table>
{% else %}
<p>No reservations yet.</p>
{% endif %}
<ul>
<li>Environment: <strong>{{ env_name }}</strong></li>
<li>Version: <strong>{{ app_version }}</strong></li>
<li><a href="/api/reservations">View reservation data as JSON</a></li>
<li>Operations: CloudWatch metrics, logs, alarms, and SNS alerting</li>
</ul>
<p>Generated: {{ timestamp }}</p>
</main></body></html>"""


def utc_now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


@app.after_request
def security_headers(response):
    response.headers["Cache-Control"] = "no-store"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; base-uri 'none'; frame-ancestors 'none'; form-action 'none'"
    )
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    return response


@app.get("/")
def home():
    rows = load_reservations()
    return render_template_string(
        HTML_TEMPLATE,
        service_name=SERVICE_NAME,
        app_version=APP_VERSION,
        env_name=ENV_NAME,
        timestamp=utc_now(), rows=rows, unavailable=rows is None,
    ), 503 if rows is None else 200


def reservation_rows():
    query = "SELECT id, event_name FROM demo_reservations ORDER BY id LIMIT 10"
    if os.environ.get("DB_MODE", "fixture") == "fixture":
        path = Path(os.environ.get("FIXTURE_DB", Path(__file__).with_name("demo.sqlite")))
        with closing(sqlite3.connect(path.resolve().as_uri() + "?mode=ro", uri=True)) as conn:
            return conn.execute(query).fetchall()
    if os.environ["DB_MODE"] != "rds":
        raise ValueError("unsupported database mode")

    host = os.environ["DB_HOST"]
    user = "rsvp_reader"
    token = boto3.client("rds", region_name=os.environ["AWS_REGION"]).generate_db_auth_token(
        DBHostname=host, Port=3306, DBUsername=user
    )
    tls = ssl.create_default_context(cafile=os.environ["RDS_CA_FILE"])
    with pymysql.connect(host=host, user=user, password=token, database=os.environ["DB_NAME"],
                         ssl=tls, connect_timeout=4, read_timeout=4, write_timeout=4) as conn:
        with conn.cursor() as cursor:
            cursor.execute(query)
            return cursor.fetchall()


def load_reservations():
    try:
        return reservation_rows()
    except (sqlite3.Error, pymysql.MySQLError, BotoCoreError, ClientError, OSError, KeyError, ValueError) as error:
        # Driver messages may include connection details. Keep only the error category.
        app.logger.error("reservation read failed (%s)", type(error).__name__)
        return None


@app.get("/api/reservations")
def reservations():
    rows = load_reservations()
    if rows is None:
        return jsonify(error="reservations unavailable"), 503
    return jsonify(reservations=[{"id": key, "event": name} for key, name in rows])


@app.get("/health")
def health():
    return jsonify(status="ok", version=APP_VERSION, env=ENV_NAME, timestamp=utc_now())


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "8080")))
