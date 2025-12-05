#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import datetime

from flask import Flask, jsonify, render_template_string, request

app = Flask(__name__)

APP_VERSION = os.getenv("APP_VERSION", "v1.0.4-ci")
ENV_NAME = os.getenv("ENV_NAME", "dev")
SERVICE_NAME = "RSVP Cloud Service"

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <title>{{ service_name }} {{ app_version }}</title>
  <style>
    html, body {
      margin: 0;
      padding: 0;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", system-ui, sans-serif;
      background: #020617;
      color: #e5e7eb;
      height: 100%;
    }
    body {
      display: flex;
      justify-content: center;
      align-items: center;
      min-height: 100vh;
    }
    .card {
      background: radial-gradient(circle at top left, #0f172a, #020617);
      border-radius: 24px;
      padding: 40px 56px;
      box-shadow: 0 24px 80px rgba(15, 23, 42, 0.9);
      width: 980px;
      max-width: 95vw;
    }
    .badge-row {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 16px;
    }
    .badge {
      display: inline-block;
      padding: 6px 16px;
      border-radius: 999px;
      background: rgba(34, 197, 94, 0.12);
      color: #22c55e;
      font-size: 12px;
      letter-spacing: 0.08em;
      text-transform: uppercase;
    }
    .version-pill {
      font-size: 12px;
      color: #9ca3af;
    }
    h1 {
      margin: 0;
      font-size: 32px;
      letter-spacing: 0.03em;
    }
    .subtitle {
      margin-top: 8px;
      margin-bottom: 28px;
      color: #9ca3af;
      font-size: 14px;
    }
    .grid {
      display: grid;
      grid-template-columns: 1.1fr 1.1fr 1.2fr;
      gap: 24px 40px;
      font-size: 13px;
    }
    .section-title {
      color: #6b7280;
      text-transform: uppercase;
      letter-spacing: 0.18em;
      font-size: 11px;
      margin-bottom: 10px;
    }
    .row {
      display: flex;
      justify-content: space-between;
      margin-bottom: 4px;
    }
    .label {
      color: #9ca3af;
    }
    .value {
      color: #e5e7eb;
      font-weight: 500;
      text-align: right;
    }
    .value-strong {
      color: #e5e7eb;
      font-weight: 600;
      text-align: right;
    }
    .ai {
      color: #a855f7;
    }
    .footer {
      margin-top: 24px;
      font-size: 12px;
      color: #6b7280;
      text-align: center;
    }
    .footer strong {
      color: #e5e7eb;
    }
    .api-section {
      margin-top: 32px;
      padding-top: 20px;
      border-top: 1px solid rgba(148, 163, 184, 0.3);
    }
    .api-title {
      font-size: 14px;
      font-weight: 500;
      margin-bottom: 10px;
    }
    .api-input-row {
      display: flex;
      gap: 8px;
      margin-bottom: 10px;
    }
    .api-input {
      flex: 1;
      padding: 10px 12px;
      border-radius: 999px;
      border: 1px solid rgba(148, 163, 184, 0.5);
      background: #020617;
      color: #e5e7eb;
      font-size: 14px;
      outline: none;
    }
    .api-input:focus {
      border-color: #38bdf8;
      box-shadow: 0 0 0 1px #38bdf8;
    }
    .api-button {
      padding: 10px 20px;
      border-radius: 999px;
      border: none;
      background: #f97316;
      color: #020617;
      font-weight: 600;
      font-size: 14px;
      cursor: pointer;
    }
    .api-button:hover {
      background: #fb923c;
    }
    .api-result {
      min-height: 28px;
      padding: 8px 12px;
      border-radius: 999px;
      background: #020617;
      border: 1px dashed rgba(148, 163, 184, 0.5);
      font-size: 12px;
      color: #9ca3af;
      display: flex;
      align-items: center;
    }
    .api-result strong {
      color: #e5e7eb;
    }
  </style>
</head>
<body>
  <div class="card">
    <div class="badge-row">
      <div class="badge">Deployed with Terraform and GitHub Actions</div>
      <div class="version-pill">Service version: <strong>{{ app_version }}</strong></div>
    </div>

    <h1>{{ service_name }}</h1>
    <div class="subtitle">
      Containerized RSVP microservice running behind an Application Load Balancer in ECS Fargate.
    </div>

    <div class="grid">
      <div>
        <div class="section-title">Environment</div>
        <div class="row">
          <div class="label">Region</div>
          <div class="value">us-east-1</div>
        </div>
        <div class="row">
          <div class="label">Environment</div>
          <div class="value-strong">{{ env_name }}</div>
        </div>
        <div class="row">
          <div class="label">Frontend access</div>
          <div class="value-strong">ALB (HTTP 8080)</div>
        </div>
      </div>

      <div>
        <div class="section-title">Workload</div>
        <div class="row">
          <div class="label">Runtime</div>
          <div class="value">Python + Flask</div>
        </div>
        <div class="row">
          <div class="label">Execution</div>
          <div class="value">ECS Fargate task</div>
        </div>
        <div class="row">
          <div class="label">Images</div>
          <div class="value">Pushed from GitHub to ECR</div>
        </div>
        <div class="row">
          <div class="label">Deployments</div>
          <div class="value">GitHub Actions workflow</div>
        </div>
      </div>

      <div>
        <div class="section-title">Observability & AI</div>
        <div class="row">
          <div class="label">Logs</div>
          <div class="value">CloudWatch Logs per task</div>
        </div>
        <div class="row">
          <div class="label">Metrics</div>
          <div class="value">ECS service CPU / memory</div>
        </div>
        <div class="row">
          <div class="label ai">AI integration</div>
          <div class="value ai">Future AI incident assistant</div>
        </div>
        <div class="row">
          <div class="label">Source</div>
          <div class="value">GitHub: RSVP-Cloud-Platform</div>
        </div>
      </div>
    </div>

    <div class="api-section">
      <div class="api-title">Test the <code>/api/message</code> endpoint</div>
      <div class="api-input-row">
        <input
          id="msg-input"
          class="api-input"
          type="text"
          placeholder="Type a message to send into the container..."
        />
        <button class="api-button" onclick="sendMessage()">Send</button>
      </div>
      <div id="api-result" class="api-result">
        Response will appear here.
      </div>
    </div>

    <div class="footer">
      Task time: <strong>{{ timestamp }}</strong> &nbsp;&middot;&nbsp;
      Built for: <strong>RSVP Platform Project 2 (ECS + CI/CD)</strong>
    </div>
  </div>

  <script>
    function sendMessage() {
      var input = document.getElementById("msg-input");
      var result = document.getElementById("api-result");
      var msg = input.value || "";

      result.textContent = "Sending...";

      fetch("/api/message", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({ message: msg })
      })
        .then(function (res) { return res.json(); })
        .then(function (data) {
          result.innerHTML =
            "<strong>Echo:</strong> " + (data.echo || "") +
            " &nbsp;&middot;&nbsp; " +
            "<strong>Version:</strong> " + (data.version || "") +
            " &nbsp;&middot;&nbsp; " +
            "<strong>Env:</strong> " + (data.env || "") +
            " &nbsp;&middot;&nbsp; " +
            "<strong>Time:</strong> " + (data.timestamp || "");
        })
        .catch(function (err) {
          console.error(err);
          result.textContent = "Error calling /api/message. Check browser console.";
        });
    }
  </script>
</body>
</html>
"""

@app.route("/", methods=["GET"])
def home():
  now = datetime.datetime.utcnow().isoformat()
  return render_template_string(
      HTML_TEMPLATE,
      service_name=SERVICE_NAME,
      app_version=APP_VERSION,
      env_name=ENV_NAME,
      timestamp=now,
  )


@app.route("/health", methods=["GET"])
def health():
  return jsonify(
      status="ok",
      version=APP_VERSION,
      env=ENV_NAME,
      timestamp=datetime.datetime.utcnow().isoformat(),
  )


@app.route("/api/message", methods=["POST"])
def api_message():
  payload = request.get_json() or {}
  msg = payload.get("message", "")
  return jsonify(
      echo=msg,
      version=APP_VERSION,
      env=ENV_NAME,
      timestamp=datetime.datetime.utcnow().isoformat(),
  )


if __name__ == "__main__":
  port = int(os.getenv("PORT", "8080"))
  app.run(host="0.0.0.0", port=port)
