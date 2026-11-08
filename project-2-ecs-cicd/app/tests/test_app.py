import importlib.util
from pathlib import Path

APP_PATH = Path(__file__).resolve().parents[1] / "app.py"
spec = importlib.util.spec_from_file_location("rsvp_app", APP_PATH)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
app = module.app


def test_health_endpoint():
    client = app.test_client()
    response = client.get("/health")
    assert response.status_code == 200
    payload = response.get_json()
    assert payload["status"] == "ok"
    assert payload["version"]
    assert payload["env"]


def test_home_has_security_headers(tmp_path, monkeypatch):
    import sqlite3

    path = tmp_path / "demo.sqlite"
    with sqlite3.connect(path) as db:
        db.executescript((APP_PATH.parent / "demo.sql").read_text())
    monkeypatch.setenv("FIXTURE_DB", str(path))
    client = app.test_client()
    response = client.get("/")
    assert response.status_code == 200
    assert b"Portfolio rehearsal" in response.data
    assert response.headers["Cache-Control"] == "no-store"
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"
    assert response.headers["Referrer-Policy"] == "no-referrer"
    assert "frame-ancestors 'none'" in response.headers["Content-Security-Policy"]
    assert response.headers["Strict-Transport-Security"].startswith("max-age=31536000")


def test_demo_message_endpoint_is_not_exposed():
    client = app.test_client()
    response = client.post("/api/message", json={"message": "deploy-check"})
    assert response.status_code == 404


def test_shared_query_reads_persisted_rows(tmp_path, monkeypatch):
    import sqlite3

    path = tmp_path / "demo.sqlite"
    with sqlite3.connect(path) as db:
        seed = (APP_PATH.parent / "demo.sql").read_text()
        db.executescript(seed)
        db.executescript(seed)
        db.execute("INSERT INTO demo_reservations VALUES (2, 'Recovery exercise')")
    monkeypatch.setenv("FIXTURE_DB", str(path))
    response = app.test_client().get("/api/reservations")
    assert response.status_code == 200
    assert response.json["reservations"] == [
        {"id": 1, "event": "Portfolio rehearsal"}, {"id": 2, "event": "Recovery exercise"}
    ]


def test_unavailable_database_preserves_liveness(tmp_path, monkeypatch):
    missing = tmp_path / "missing"
    monkeypatch.setenv("FIXTURE_DB", str(missing))
    client = app.test_client()
    assert client.get("/api/reservations").status_code == 503
    assert not missing.exists()
    assert client.get("/health").status_code == 200


def test_mysql_path_uses_iam_and_verified_tls(monkeypatch):
    import ssl
    from unittest.mock import MagicMock

    host = "example.us-east-1.rds.amazonaws.com"
    for key, value in {"DB_MODE": "rds", "DB_HOST": host, "DB_NAME": "rsvp_app",
                       "AWS_REGION": "us-east-1", "RDS_CA_FILE": "/unused-in-production-test"}.items():
        monkeypatch.setenv(key, value)
    tls = ssl.create_default_context()
    def load_test_ca(*, cafile):
        assert cafile == "/unused-in-production-test"
        return tls
    monkeypatch.setattr(module.ssl, "create_default_context", load_test_ca)
    rds = MagicMock()
    rds.generate_db_auth_token.return_value = "ephemeral-token"
    monkeypatch.setattr(module.boto3, "client", lambda service, region_name: rds)
    connect = MagicMock()
    cursor = connect.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value
    cursor.fetchall.return_value = [(1, "Portfolio rehearsal")]
    monkeypatch.setattr(module.pymysql, "connect", connect)
    result = app.test_client().get("/api/reservations")
    assert result.json == {"reservations": [{"id": 1, "event": "Portfolio rehearsal"}]}
    rds.generate_db_auth_token.assert_called_once_with(DBHostname=host, Port=3306, DBUsername="rsvp_reader")
    config = connect.call_args.kwargs
    assert config["ssl"].check_hostname and config["ssl"].verify_mode == ssl.CERT_REQUIRED
    assert config["password"] == "ephemeral-token" and config["database"] == "rsvp_app"
    assert cursor.execute.call_args.args[0].startswith("SELECT id, event_name FROM demo_reservations")
