"""Management-only staging: supervised API + UI, no autonomous worker processes."""

import os
import signal
import subprocess
import sys
import time


def main():
    if os.environ.get("RUNTIME") != "staging":
        raise RuntimeError("This combined entrypoint is restricted to staging")
    if not os.environ.get("DATABASE_URL"):
        raise RuntimeError("A persistent staging PostgreSQL connection is required")
    for key in ("SESSION_SECRET", "BOOTSTRAP_TOKEN"):
        if len(os.environ.get(key, "")) < 32:
            raise RuntimeError(f"A private {key} of at least 32 characters is required")
    if not os.environ.get("APP_ORIGIN"):
        origin = os.environ.get("RENDER_EXTERNAL_URL", "")
        if not origin.startswith("https://"):
            raise RuntimeError("Configure the public HTTPS APP_ORIGIN")
        os.environ["APP_ORIGIN"] = origin.rstrip("/")
    # Migration commands do not echo connection strings or credentials.
    subprocess.run([sys.executable, "-m", "alembic", "upgrade", "head"], check=True)
    subprocess.run([sys.executable, "-m", "company_os.bootstrap"], check=True)
    children = []
    stopping = False

    def stop(*_):
        nonlocal stopping
        stopping = True

    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    try:
        children.append(
            subprocess.Popen(
                [
                    sys.executable,
                    "-m",
                    "uvicorn",
                    "company_os.api:app",
                    "--host",
                    "127.0.0.1",
                    "--port",
                    "8000",
                    "--no-access-log",
                    "--timeout-graceful-shutdown",
                    "5",
                ],
                start_new_session=True,
            )
        )
        web_env = {**os.environ, "PORT": os.environ.get("PORT", "10000"), "HOSTNAME": "0.0.0.0"}
        children.append(
            subprocess.Popen(
                ["node", os.environ.get("STAGING_WEB_SERVER", "apps/web/server.js")],
                env=web_env,
                start_new_session=True,
            )
        )
        exit_code = 0
        while not stopping:
            for child in children:
                if child.poll() is not None:
                    exit_code = child.returncode or 1
                    stopping = True
                    break
            time.sleep(0.2)
        return exit_code
    finally:
        for child in children:
            if child.poll() is None:
                os.killpg(child.pid, signal.SIGTERM)
        deadline = time.monotonic() + 8
        for child in children:
            try:
                child.wait(timeout=max(0.1, deadline - time.monotonic()))
            except subprocess.TimeoutExpired:
                os.killpg(child.pid, signal.SIGKILL)
                child.wait()


if __name__ == "__main__":
    sys.exit(main())
