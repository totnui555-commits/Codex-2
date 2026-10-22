"""Idempotently restore detached development services; never enables paid execution."""

import fcntl
import json
import os
import subprocess
import time
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[1]
PYTHON = str(ROOT / ".venv/bin/python")
COMMANDS = {
    "api": [
        PYTHON,
        "-m",
        "uvicorn",
        "company_os.api:app",
        "--host",
        "0.0.0.0",
        "--port",
        "8000",
        "--no-access-log",
    ],
    "worker": [PYTHON, "-m", "company_os.worker"],
    "scheduler": [PYTHON, "-m", "company_os.scheduler"],
    "watchtower": [PYTHON, "-m", "company_os.watchtower"],
}


def main():
    os.chdir(ROOT)
    directory = ROOT / ".local/runtime"
    directory.mkdir(mode=0o700, parents=True, exist_ok=True)
    with (directory / "startup.lock").open("w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        processes = subprocess.check_output(["ps", "-eo", "pid,args"], text=True).splitlines()[1:]
        known = {}
        for line in processes:
            parts = line.strip().split(None, 1)
            if len(parts) == 2:
                known[parts[1]] = int(parts[0])
        services = {}
        for name, command in COMMANDS.items():
            command_text = " ".join(command)
            pid = known.get(command_text)
            if name == "api" and not pid:
                try:
                    response = httpx.get("http://localhost:8000/health", timeout=2)
                    if response.status_code == 200 and response.json().get("database") == "postgresql":
                        services[name] = {"state": "existing_healthy_listener"}
                        continue
                except (httpx.HTTPError, ValueError):
                    pass
            if pid:
                services[name] = {"state": "already_running", "pid": pid}
                continue
            with (directory / (name + ".log")).open("a") as log:
                process = subprocess.Popen(
                    command,
                    cwd=ROOT,
                    stdin=subprocess.DEVNULL,
                    stdout=log,
                    stderr=subprocess.STDOUT,
                    start_new_session=True,
                )
            services[name] = {"state": "started_detached", "pid": process.pid}
        for _ in range(50):
            try:
                response = httpx.get("http://localhost:8000/health", timeout=2)
                if response.status_code == 200:
                    break
            except httpx.HTTPError:
                pass
            time.sleep(0.2)
        else:
            raise RuntimeError("API failed readiness; inspect private .local/runtime logs")
        for name, entry in services.items():
            if "pid" in entry:
                os.kill(entry["pid"], 0)
        (directory / "services.json").write_text(json.dumps(services, indent=2) + "\n")
        print(json.dumps(services))


if __name__ == "__main__":
    main()
