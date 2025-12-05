from flask import Flask, jsonify, render_template_string, request
import os
import datetime

app = Flask(__name__)

APP_VERSION = os.getenv("APP_VERSION", "v1.0.4-ci")
SERVICE_NAME = os.getenv("SERVICE_NAME", "RSVP Cloud Service")
ENV_NAME = os.getenv("ENV_NAME", "dev")

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <title>RSVP Cloud Service {{ version }}</title>
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <style>
    * {
      box-sizing: border-box;
    }
    body {
      margin: 0;
      padding: 0;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", system-ui, sans-serif;
      background: #020617;
      color: #e5e7eb;
      min-height: 100vh;
      display: flex;
      justify-content: center;
      align-items: center;
    }
    .shell {
      width: 100%;
      max-width: 1200px;
      padding: 32px 16px;
    }
    .card {
      background: radial-gradient(circle at top left, #0f172a, #020617);
      border-radius: 24px;
      padding: 32px 40px;
      box-shadow: 0 22px 80px rgba(15, 23, 42, 0.9);
    }
    .badge-row {
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 12px;
      margin-bottom: 18px;
      flex-wrap: wrap;
    }
    .badge {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      padding: 6px 16px;
      border-radius: 999px;
      background: rgba(34, 197, 94, 0.12);
      color: #22c55e;
      font-size: 11px;
      letter-spacing: 0.08em;
      text-transform: uppercase;
    }
    .badge-dot {
      width: 8px;
      height: 8px;
      border-radius: 999px;
      background: #22c55e;
      box-shadow: 0 0 0 6px rgba(34, 197, 94, 0.25);
    }
    .env-pill {
      font-size: 11px;
      color: #9ca3af;
      text-transform: uppercase;
      letter-spacing: 0.15em;
    }
    h1 {
      margin: 0;
      font-size: 30px;
      letter-spacing: 0.02em;
    }
    .subtitle {
      margin-top: 8px;
      margin-bottom: 26px;
      color: #9ca3af;
      font-size: 14px;
    }
    .grid {
      display: grid;
      grid-template-columns: 1.1fr 1.1fr;
      gap: 22px 64px;
      font-size: 13px;
    }
    @media (max-width: 840px) {
      .card {
        padding: 24px 18px;
      }
      .grid {
        grid-template-columns: 1fr;
        gap: 20px;
      }
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
      gap: 16px;
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
    .api-card {
      margin-top: 28px;
      padding-top: 22px;
      border-top: 1px solid rgba(55, 65, 81, 0.7);
    }
    .api-title-row {
      display: flex;
      justify-content: space-between;
      align-items: baseline;
      gap: 16px;
      margin-bottom: 12px;
      flex-wrap: wrap;
    }
    .api-title {
      font-size: 13px;
      font-weight: 600;
    }
    .api-subtitle {
      font-size: 12px;
      color: #6b7280;
    }
    .api-input-row {
      margin-top: 6px;
      display: flex;
      gap: 10px;
      flex-wrap: wrap;
    }
    .api-input-row input[type="text"] {
      flex: 1 1 260px;
      border-radius: 999px;
      border: 1px solid rgba(55, 65, 81, 0.9);
      background: rgba(15, 23, 42, 0.9);
      padding: 10px 14px;
      color: #e5e7eb;
      font-size: 13px;
      outline: none;
    }
    .api-input-row input[type="text"]::placeholder {
      color: #6b7280;
    }
    .api-input-row button {
      border-radius: 999px;
      border: none;
      padding: 9px 18px;
      font-size: 13px;
      font-weight: 500;
      background: #f97316;
      color: #0b1120;
      cursor: pointer;
      transition: transform 0.08s ease, box-shadow 0.08s ease, background 0.08s ease;
      white-space: nowrap;
    }
    .api-input-row button:hover {
      background: #fb923c;
      box-shadow: 0 12px 30px rgba(248, 152, 56, 0.38);
      transform: translateY(-1px);
    }
    .api-input-row button:active {
      transform: translateY(0);
      box-shadow: none;
    }
    .api-result {
      margin-top: 12px;
      min-height: 24px;
      font-size: 12px;
      color: #9ca3af;
    }
    .api-result span.label {
      color: #6b7280;
      margin-right: 6px;
    }
    .footer {
      margin-top: 24px;
      font-size: 11px;
      color: #6b7280;
      text-align: center;
    }
    .footer span {
      color: #e5e7eb;
      font-weight: 500;
    }
  </style>
</head>
<body>
  <div class="shell">
    <div class="card">
      <div class="badge-row">
        <div class="badge">
          <div class="badge-dot"></div>
          Container-ready API · Project 2
        </div>
        <div class="env-pill">
          VERSION {{ version }} · ENV {{ environment | upper }}
        </div>
      </div>

      <h1>RSVP Cloud Service</h1>
      <div class="subtitle">
        Stateless API backing the RSVP Cloud Platform — built for containers, CI/CD, and
        zero-downtime deployments.
      </div>

      <div class="grid">
        <div>
          <div class="section-title">Environment</div>
          <div class="row">
            <div class="label">Region</div>
            <div class="value">us-east-1</div>
          </div>
          <div class="row">
            <div class="label">Runtime</div>
            <div class="value">Flask + Gunicorn</div>
          </div>
          <div class="row">
            <div class="label">Current deploy</div>
            <div class="value-strong">Local Docker / Dev</div>
          </div>
          <div class="row">
            <div class="label">Target</div>
            <div class="value-strong">ECS Fargate + GitHub Actions</div>
          </div>
        </div>

        <div>
          <div class="section-title">Service</div>
          <div class="row">
            <div class="label">Primary role</div>
            <div class="value">JSON API &amp; healthcheck</div>
          </div>
          <div class="row">
            <div class="label">Key endpoint</div>
            <div class="value-strong">POST /api/message</div>
          </div>
          <div class="row">
            <div class="label">CI/CD</div>
            <div class="value">GitHub Actions → ECR → ECS service</div>
          </div>
          <div class="row">
            <div class="label ai">Future AI</div>
            <div class="value ai">Request tracing + smart alerts</div>
          </div>
        </div>
      </div>

      <div class="api-card">
        <div class="api-title-row">
          <div class="api-title">API smoke test</div>
          <div class="api-subtitle">Send a message and see the JSON response from <code>/api/message</code>.</div>
        </div>
        <form id="message-form">
          <div class="api-input-row">
            <input
              id="message-input"
              type="text"
              name="message"
              placeholder="Type something like: 'Hello from RSVP Project 2'"
              autocomplete="off"
            />
            <button type="submit">Send</button>
          </div>
        </form>
        <div class="api-result" id="api-result">
          <span class="label">Response:</span>
          <span id="api-result-text">waiting for a request…</span>
        </div>
      </div>

      <div class="footer">
        This is <span>Project 2</span> of the RSVP Cloud Platform — containerized app layer that will
        sit behind the same ALB as your core platform services.
      </div>
    </div>
  </div>

  <script>
    const form = document.getElementById("message-form");
    const input = document.getElementById("message-input");
    const resultText = document.getElementById("api-result-text");

    form.addEventListener("submit", async (e) => {
      e.preventDefault();
      const value = input.value.trim();
      if (!value) {
        resultText.textContent = "Please enter a message first.";
        return;
      }

      resultText.textContent = "Sending…";

      try {
        const res = await fetch("/api/message", {
          method: "POST",
          headers: {
            "Content-Type": "application/json"
          },
          body: JSON.stringify({ message: value })
        });

        if (!res.ok) {
          resultText.textContent = `Error: ${res.status} ${res.statusText}`;
          return;
        }

        const data = await res.json();
        resultText.textContent = JSON.stringify(data);
      } catch (err) {
        resultText.textContent = "Network error talking to the API.";
      }
    });
  </script>
</body>
</html>
"""

"""

@app.route("/")
def index():
    return render_template_string(
        INDEX_HTML,
        service_name=SERVICE_NAME,
        version=APP_VERSION,
        env_name=ENV_NAME,
    )

@app.route("/health")
def health():
    return jsonify({
        "status": "ok",
        "timestamp": datetime.datetime.utcnow().isoformat()
    })

@app.route("/api/message", methods=["POST"])
def api_message():
    payload = request.get_json() or {}
    msg = payload.get("message", "")
    return jsonify({
        "echo": msg,
        "version": APP_VERSION,
        "env": ENV_NAME,
        "timestamp": datetime.datetime.utcnow().isoformat()
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "8080")))
