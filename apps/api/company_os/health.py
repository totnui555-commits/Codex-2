from sqlalchemy import select

from .db import Session
from .domain import lock_org
from .models import Decisions, Organization, now


def service_heartbeat(name):
    with Session.begin() as db:
        for org in db.scalars(select(Organization)).all():
            lock_org(db, org.id)
            rows = db.scalars(select(Decisions).where(Decisions.organization_id == org.id)).all()
            row = next((r for r in rows if r.data.get("service") == name), None)
            data = {"service": name, "last_seen_at": now().isoformat()}
            if row:
                row.data = data
            else:
                db.add(Decisions(organization_id=org.id, data=data))
