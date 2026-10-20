import os

os.environ["DATABASE_URL"] = os.getenv(
    "TEST_DATABASE_URL", "postgresql+psycopg://company:company@localhost:5432/company_test"
)
os.environ["SESSION_SECRET"] = "test-only-secret-with-at-least-thirty-two-characters"
os.environ["BOOTSTRAP_TOKEN"] = "test-bootstrap"
os.environ["SECURE_COOKIES"] = "false"
os.environ["MODEL_PROVIDER"] = "openai"
os.environ["OPENAI_API_KEY"] = ""
os.environ["OPENROUTER_API_KEY"] = ""
os.environ["ARTIFACT_BACKEND"] = "s3"
os.environ["ARTIFACT_ENCRYPTION_KEY"] = ""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from company_os.db import engine, Base, Session
from company_os.models import *
from company_os.api import app, login_attempts
from company_os.bootstrap import seed_roles


@pytest.fixture(autouse=True)
def clean_database():
    with engine.begin() as c:
        tables = ", ".join('"' + t.name + '"' for t in Base.metadata.sorted_tables)
        c.execute(text("TRUNCATE " + tables + " RESTART IDENTITY CASCADE"))
    login_attempts.clear()
    seed_roles()


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture
def owner_client(client):
    response = client.post(
        "/auth/bootstrap",
        json={
            "email": "founder@example.com",
            "password": "long-test-password-123",
            "bootstrap_token": "test-bootstrap",
            "organization_name": "Test company",
        },
    )
    assert response.status_code == 201, response.text
    return client


@pytest.fixture
def project(owner_client):
    return owner_client.post(
        "/projects", json={"name": "Real test project", "description": "Integration verification"}
    ).json()


def create_task(client, project, **kwargs):
    data = {
        "project_id": project["id"],
        "title": "Implement a useful feature",
        "objective": "Build and verify the feature",
        "acceptance": ["Passing tests and artifact checksum"],
    }
    data.update(kwargs)
    response = client.post("/tasks", json=data)
    assert response.status_code == 201, response.text
    return response.json()
