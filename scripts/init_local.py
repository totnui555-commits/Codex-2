"""Initialize a private local owner account; never print generated credentials."""

import json
import secrets
from pathlib import Path

import httpx
from company_os.settings import settings


def main():
    password = secrets.token_urlsafe(24)
    response = httpx.post(
        "http://127.0.0.1:8000/auth/bootstrap",
        json={
            "email": settings().founder_email,
            "password": password,
            "bootstrap_token": settings().bootstrap_token,
            "organization_name": "AI Company OS",
        },
    )
    if response.status_code == 409:
        print("Installation already initialized; use the existing private credential file.")
        return
    response.raise_for_status()
    folder = Path(".local")
    folder.mkdir(exist_ok=True)
    file = folder / "owner-credentials.json"
    file.write_text(
        json.dumps(
            {"email": settings().founder_email, "password": password, "url": "http://localhost:3000"},
            indent=2,
        )
        + "\n"
    )
    file.chmod(0o600)
    print(
        "Initialized owner, tenant and Founder Inbox. Local credentials saved privately in .local/owner-credentials.json."
    )


if __name__ == "__main__":
    main()
