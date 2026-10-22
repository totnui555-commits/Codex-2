import json
from pathlib import Path

from sqlalchemy import select

from .db import Session
from .models import AgentRole


def seed_roles():
    path = Path.cwd() / "config/roles.json"
    with Session.begin() as db:
        for config in json.loads(path.read_text()):
            if not db.scalar(select(AgentRole).where(AgentRole.key == config["id"])):
                db.add(AgentRole(key=config["id"], config=config))


if __name__ == "__main__":
    seed_roles()
