"""Real local staging process/proxy smoke against the disposable integration-test DB."""

import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

import httpx


def main():
    root = Path(__file__).resolve().parents[1]
    os.chdir(root)
    server = root / "apps/web/.next/standalone/apps/web/server.js"
    if not server.exists():
        raise RuntimeError("Build the standalone web server before running this verification")
    api_was_running = False
    for line in subprocess.check_output(["ps", "-eo", "pid,args"], text=True).splitlines()[1:]:
        parts = line.strip().split(None, 1)
        if (
            len(parts) == 2
            and parts[1].startswith(str(root / ".venv/bin/python") + " .venv/bin/uvicorn company_os.api:app ")
            and "--port 8000" in parts[1]
        ):
            api_was_running = True
            os.kill(int(parts[0]), signal.SIGTERM)
            for _ in range(50):
                try:
                    os.kill(int(parts[0]), 0)
                except ProcessLookupError:
                    break
                time.sleep(0.1)
            else:
                raise RuntimeError("API did not stop; refusing a duplicate bind")
    process = None
    try:
        environment = {
            **os.environ,
            "RUNTIME": "staging",
            "PORT": "10000",
            "DATABASE_URL": os.environ.get(
                "TEST_DATABASE_URL", "postgresql+psycopg://company:company@localhost:5432/company_test"
            ),
            "SESSION_SECRET": "internal-staging-smoke-secret-at-least-32-chars",
            "BOOTSTRAP_TOKEN": "internal-staging-smoke-bootstrap-at-least-32-chars",
            "APP_ORIGIN": "http://localhost:10000",
            "SECURE_COOKIES": "false",
            "OPENROUTER_API_KEY": "",
            "OPENAI_API_KEY": "",
            "STAGING_WEB_SERVER": str(server),
            "HOSTNAME": "0.0.0.0",
        }
        with Path("/tmp/company-os-staging-runtime.log").open("w") as log:
            process = subprocess.Popen(
                [sys.executable, "infrastructure/staging_entrypoint.py"],
                env=environment,
                stdout=log,
                stderr=subprocess.STDOUT,
            )
        with httpx.Client(base_url="http://localhost:10000", timeout=5) as client:
            for attempt in range(50):
                try:
                    response = client.get("/api/health")
                    if response.status_code == 200:
                        break
                except httpx.TransportError:
                    pass
                if process.poll() is not None:
                    raise RuntimeError("Staging supervisor exited before readiness")
                time.sleep(0.2)
            else:
                raise RuntimeError("Staging proxy did not become ready")
            assert response.json()["database"] == "postgresql"
            assert client.get("/").status_code == 200
            client.post(
                "/api/auth/login", json={"email": "founder@example.com", "password": "long-test-password-123"}
            ).raise_for_status()
            snapshot = client.get("/api/snapshot").json()
            assert snapshot["deployment"]["runtime"] == "staging"
            assert not snapshot["organization"]["paid_execution_authorized"]
            assert len(snapshot["roles"]) == 25
            assert client.get("/api/audit/verify").json()["valid"]
        process.send_signal(signal.SIGTERM)
        assert process.wait(timeout=12) == 0
        process = None
        Path("docs/evidence/staging-local-runtime.json").write_text(
            json.dumps(
                {
                    "checks": [
                        "actual_staging_supervisor",
                        "postgresql_migration_and_role_seed",
                        "production_next_server",
                        "same_origin_proxy_health",
                        "owner_login",
                        "staging_runtime_metadata",
                        "paid_execution_disabled",
                        "25_real_role_configs",
                        "audit_chain_valid",
                        "graceful_supervisor_shutdown",
                    ],
                    "database": "disposable_local_integration_test_database",
                    "render_deployment": "not_performed_by_this_check",
                    "customer_data": False,
                },
                indent=2,
            )
            + "\n"
        )
        print("Real local staging API/UI/proxy and graceful shutdown verified.")
    finally:
        if process and process.poll() is None:
            process.send_signal(signal.SIGTERM)
            process.wait(timeout=12)
        if api_was_running:
            with Path("/tmp/company-os-api-render.log").open("a") as log:
                subprocess.Popen(
                    [
                        str(root / ".venv/bin/python"),
                        "-m",
                        "uvicorn",
                        "company_os.api:app",
                        "--host",
                        "0.0.0.0",
                        "--port",
                        "8000",
                        "--no-access-log",
                    ],
                    cwd=root,
                    stdout=log,
                    stderr=subprocess.STDOUT,
                    start_new_session=True,
                )
            print("Development API restored.")


if __name__ == "__main__":
    main()
