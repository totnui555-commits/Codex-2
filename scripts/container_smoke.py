"""Real Compose acceptance check on isolated smoke ports; never a production install."""

import json
import secrets
import time
from pathlib import Path

import httpx
from company_os.settings import settings

with httpx.Client(
    base_url="http://localhost:18030", timeout=10, headers={"Origin": "http://localhost:18030"}
) as client:
    for attempt in range(30):
        try:
            if client.get("/api/health").status_code == 200:
                break
        except httpx.HTTPError:
            pass
        time.sleep(1)
    else:
        raise AssertionError("Container proxy/API did not become healthy")
    response = client.post(
        "/api/auth/bootstrap",
        json={
            "email": "smoke@example.com",
            "password": secrets.token_urlsafe(24),
            "bootstrap_token": settings().bootstrap_token,
            "organization_name": "Isolated container acceptance",
        },
    )
    response.raise_for_status()
    project = client.post(
        "/api/projects",
        json={
            "name": "Container orchestration verification",
            "description": "Actual acceptance check of built images, durable dispatch and isolated database.",
        },
    )
    project.raise_for_status()
    task = client.post(
        "/api/tasks",
        json={
            "project_id": project.json()["id"],
            "title": "Verify hosted factory preflight",
            "objective": "Check configured hosted worker permissions before any paid execution.",
            "acceptance": ["Block without provider credentials"],
            "agent_role": "backend_engineer",
        },
    )
    task.raise_for_status()
    for attempt in range(30):
        state = client.get("/api/snapshot")
        state.raise_for_status()
        snapshot = state.json()
        status = next(t["status"] for t in snapshot["tasks"] if t["id"] == task.json()["id"])
        if status == "blocked" and snapshot.get("services", {}).get("watchtower", {}).get("state") == "live":
            break
        time.sleep(1)
    else:
        raise AssertionError("Durable worker/Watchtower state did not become ready")
    assert len(snapshot["roles"]) == 25
    assert snapshot["organization"]["paid_execution_authorized"] is False
    assert snapshot["runs"] == []
    assert client.get("/api/audit/verify").json()["valid"]
    result = {
        "compose_configuration": "valid",
        "api_image_build": "passed",
        "web_standalone_image_build": "passed",
        "clean_compose_startup": "passed",
        "frontend_proxy_auth_project_task_crud": "passed",
        "postgres_migration_and_role_seed": "passed",
        "real_temporal_dispatch": "passed_blocked_without_credentials",
        "watchtower": "live",
        "role_count": 25,
        "audit_valid": True,
        "paid_runs": 0,
        "sandbox_image_build": "unverified_disk_limit",
        "hosted_sandbox_execution": "not_configured_not_executed",
    }
    Path("docs/evidence/containers.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
