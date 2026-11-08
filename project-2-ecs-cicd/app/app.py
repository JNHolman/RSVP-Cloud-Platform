#!/usr/bin/env python3
import datetime
import os

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
<p>Containerized workload running on ECS Fargate behind an HTTPS Application Load Balancer.</p>
<ul>
<li>Environment: <strong>{{ env_name }}</strong></li>
<li>Version: <strong>{{ app_version }}</strong></li>
<li>Delivery: GitHub Actions + immutable ECR SHA tags</li>
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
    return render_template_string(
        HTML_TEMPLATE,
        service_name=SERVICE_NAME,
        app_version=APP_VERSION,
        env_name=ENV_NAME,
        timestamp=utc_now(),
    )


@app.get("/health")
def health():
    return jsonify(status="ok", version=APP_VERSION, env=ENV_NAME, timestamp=utc_now())


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "8080")))
