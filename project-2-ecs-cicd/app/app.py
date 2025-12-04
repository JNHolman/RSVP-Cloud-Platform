from flask import Flask, jsonify, render_template_string, request
import os
import datetime

app = Flask(__name__)

APP_VERSION = os.getenv("APP_VERSION", "v1.0.2")
SERVICE_NAME = os.getenv("SERVICE_NAME", "RSVP Cloud Service")
ENV_NAME = os.getenv("ENV_NAME", "dev")

INDEX_HTML = """
<!doctype html>
<html lang="en">
  <head>
    <title>{{ service_name }} - {{ version }}</title>
  </head>
  <body style="font-family: system-ui; background:#050816; color:#f9fafb;">
    <div style="max-width:640px;margin:80px auto;padding:32px;border-radius:24px;background:#0f172a;">
      <h1>{{ service_name }} {{ version }}</h1>
      <p>Environment: <strong>{{ env_name }}</strong></p>
      <p>Right now: <strong>running on your laptop</strong></p>
      <p>Later: <strong>ECS Fargate + GitHub Actions</strong></p>

      <hr style="border-color:#1f2937;">

      <h3>Test the /api/message endpoint</h3>
      <form id="message-form">
        <input type="text" id="message-input" placeholder="Type something..."
               style="padding:8px;border-radius:8px;border:1px solid #4b5563;width:70%;" />
        <button type="button" onclick="sendMessage()" 
                style="padding:8px 16px;border-radius:999px;border:none;cursor:pointer;">
          Send
        </button>
      </form>

      <pre id="response-box" style="background:#020617;padding:16px;border-radius:12px;margin-top:16px;max-height:240px;overflow:auto;"></pre>
    </div>

    <script>
      async function sendMessage() {
        const msg = document.getElementById("message-input").value;
        const res = await fetch("/api/message", {
          method: "POST",
          headers: {"Content-Type": "application/json"},
          body: JSON.stringify({ message: msg })
        });
        const data = await res.json();
        document.getElementById("response-box").textContent = JSON.stringify(data, null, 2);
      }
    </script>
  </body>
</html>
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
