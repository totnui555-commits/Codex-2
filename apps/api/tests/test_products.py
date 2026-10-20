from company_os.db import Session
from company_os.models import Artifact, Organization, Products, Project
from conftest import create_task


def product(client, project, **extra):
    data = {
        "project_id": project["id"],
        "name": "Workflow hypothesis",
        "problem": "Repeated manual status reconciliation wastes time",
        "target_customer": "Small operations teams",
        "mvp_scope": ["Import permitted CSV", "Review exceptions"],
    }
    data.update(extra)
    return client.post("/products", json=data)


def test_product_persistence_unknown_costs_and_release_gates(owner_client, project):
    response = product(owner_client, project)
    assert response.status_code == 201, response.text
    row = response.json()
    assert row["data"]["economics"]["break_even_customers"] is None
    assert row["data"]["published"] is False
    assert owner_client.get("/snapshot").json()["products"][0]["id"] == row["id"]
    readiness = owner_client.get(f"/products/{row['id']}/readiness").json()
    assert readiness["release_authorized"] is False
    assert len(readiness["blockers"]) >= 3
    assert owner_client.get("/snapshot").json()["revenue"] == []
    assert owner_client.get("/audit/verify").json()["valid"]
    with Session() as db:
        assert db.get(Products, row["id"]).data["name"] == "Workflow hypothesis"


def test_forecasts_are_explicit_and_never_revenue(owner_client, project):
    row = product(
        owner_client,
        project,
        proposed_price_minor=10000,
        estimated_variable_cost_minor=2000,
        estimated_monthly_fixed_cost_minor=20000,
    ).json()
    assert row["data"]["economics"]["unit_contribution_minor"] == 8000
    assert row["data"]["economics"]["break_even_customers"] == 3
    assert row["data"]["economics"]["costs_complete"] is False
    assert "estimate" in row["data"]["economics"]["classification"]
    assert owner_client.get("/snapshot").json()["revenue"] == []
    assert product(owner_client, project, proposed_price_minor=True).status_code == 422
    assert product(owner_client, project, mvp_scope=[""]).status_code == 422


def test_experiment_link_scope_stale_revision_and_archive(owner_client, project):
    other = owner_client.post("/projects", json={"name": "Other product project"}).json()
    experiment = owner_client.post(
        "/experiments",
        json={
            "project_id": other["id"],
            "title": "Scoped validation",
            "hypothesis": "A measured workflow task can be completed",
            "metric": "Completion",
            "minimum_samples": 100,
            "continue_rate": 0.2,
            "stop_rate": 0.05,
        },
    ).json()
    row = product(owner_client, project).json()
    path = f"/products/{row['id']}"
    assert (
        owner_client.post(
            path + "/experiment", json={"expected_version": 1, "experiment_id": experiment["id"]}
        ).status_code
        == 422
    )
    archive = owner_client.post(path + "/archive", json={"expected_version": 1})
    assert archive.status_code == 200
    assert owner_client.post(path + "/archive", json={"expected_version": 1}).status_code == 409
    assert (
        owner_client.post(
            path + "/experiment", json={"expected_version": 2, "experiment_id": experiment["id"]}
        ).status_code
        == 409
    )
    assert owner_client.get(path + "/readiness").json()["release_authorized"] is False


def test_advisory_report_cannot_be_claimed_as_built_prototype(owner_client, project):
    task = create_task(owner_client, project)
    with Session.begin() as db:
        artifact = Artifact(
            organization_id=project["organization_id"],
            task_id=task["id"],
            kind="specialist_report",
            uri="private-file://not-a-prototype",
            sha256="a" * 64,
            verified=True,
        )
        db.add(artifact)
        db.flush()
        artifact_id = artifact.id
    row = product(owner_client, project).json()
    response = owner_client.post(
        f"/products/{row['id']}/prototype", json={"expected_version": 1, "artifact_id": artifact_id}
    )
    assert response.status_code == 422
    assert owner_client.get("/snapshot").json()["products"][0]["data"]["prototype"] is None


def test_product_tenant_boundary(owner_client, project):
    with Session.begin() as db:
        org = Organization(name="Different company")
        db.add(org)
        db.flush()
        private = Project(organization_id=org.id, name="Hidden project")
        db.add(private)
        db.flush()
        hidden = Products(organization_id=org.id, data={"state": "draft"})
        db.add(hidden)
        db.flush()
        private_id, hidden_id = private.id, hidden.id
    assert product(owner_client, project, project_id=private_id).status_code == 404
    assert owner_client.get(f"/products/{hidden_id}/readiness").status_code == 404
    assert (
        owner_client.post(f"/products/{hidden_id}/archive", json={"expected_version": 1}).status_code == 404
    )
    assert owner_client.get("/snapshot").json()["products"] == []


def test_product_api_requires_owner_authentication(client):
    assert client.post("/products", json={}).status_code == 401
    assert client.get("/products/private/readiness").status_code == 401


def test_prototype_requires_actual_checked_commit_and_independent_qa(
    owner_client, project, tmp_path, monkeypatch
):
    from company_os.models import AgentRun, Task
    from company_os.providers import ArtifactStore
    from company_os.settings import settings
    from cryptography.fernet import Fernet

    for key, value in {
        "artifact_backend": "filesystem",
        "artifact_directory": str(tmp_path),
        "artifact_encryption_key": Fernet.generate_key().decode(),
        "runtime": "development",
        "github_repository": "test-owner/test-repo",
    }.items():
        monkeypatch.setattr(settings(), key, value)
    task = create_task(owner_client, project, agent_role="backend_engineer")
    proof = {
        "qa": {"exit_code": 0, "trusted_test_suite": "crud-benchmark-v1", "sandbox_id": "boundary-qa"},
        "export": {"sandbox_id": "boundary-build"},
        "pr": {"url": "https://github.com/test-owner/test-repo/pull/1", "commit": "a" * 40},
    }
    store = ArtifactStore()
    uri, sha = store.put(project["organization_id"], task["id"], "verified_pull_request", proof)
    with Session.begin() as db:
        db.get(Task, task["id"]).status = "completed"
        run = AgentRun(
            organization_id=project["organization_id"],
            task_id=task["id"],
            agent_role="backend_engineer",
            provider="daytona/codex",
            status="completed",
        )
        artifact = Artifact(
            organization_id=project["organization_id"],
            task_id=task["id"],
            kind="verified_pull_request",
            uri=uri,
            sha256=sha,
            verified=True,
            details={"verification": "independent_hosted_QA"},
        )
        db.add_all([run, artifact])
        db.flush()
        artifact_id = artifact.id
    row = product(owner_client, project).json()

    def github(self, method, path):
        assert method == "GET" and path == "/pulls/1"
        return {"head": {"sha": "b" * 40}, "base": {"repo": {"full_name": "test-owner/test-repo"}}}

    monkeypatch.setattr("company_os.products.GitHubProvider.__init__", lambda self: None)
    monkeypatch.setattr("company_os.products.GitHubProvider.request", github)
    path = f"/products/{row['id']}/prototype"
    assert (
        owner_client.post(path, json={"expected_version": 1, "artifact_id": artifact_id}).status_code == 409
    )
    monkeypatch.setattr(
        "company_os.products.GitHubProvider.request",
        lambda *args: {"head": {"sha": "a" * 40}, "base": {"repo": {"full_name": "test-owner/test-repo"}}},
    )
    result = owner_client.post(path, json={"expected_version": 1, "artifact_id": artifact_id})
    assert result.status_code == 200, result.text
    assert result.json()["data"]["state"] == "prototype_evidence_attached"
    assert result.json()["data"]["published"] is False
    assert owner_client.get(f"/products/{row['id']}/readiness").json()["release_authorized"] is False
