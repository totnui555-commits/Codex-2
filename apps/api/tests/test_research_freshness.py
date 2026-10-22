from datetime import timedelta

import httpx
from company_os.db import Session
from company_os.models import Opportunity, ResearchEvidence, now
from company_os.research import public_source_research, store_research
from sqlalchemy import func, select, text


async def test_source_collection_rejects_old_future_and_missing_dates(monkeypatch):
    current = now()
    original = httpx.AsyncClient

    async def response(request):
        assert request.url.path.endswith("/search_by_date")
        assert "numericFilters" in request.url.params
        return httpx.Response(
            200,
            json={
                "hits": [
                    {
                        "objectID": "123",
                        "title": "Recent source",
                        "created_at_i": int((current - timedelta(days=1)).timestamp()),
                    },
                    {
                        "objectID": "124",
                        "title": "Stale source",
                        "created_at_i": int((current - timedelta(days=100)).timestamp()),
                    },
                    {
                        "objectID": "125",
                        "title": "Future source",
                        "created_at_i": int((current + timedelta(days=1)).timestamp()),
                    },
                    {"objectID": "126", "title": "Undated source"},
                ]
            },
        )

    monkeypatch.setattr(
        "company_os.research.httpx.AsyncClient",
        lambda **kwargs: original(transport=httpx.MockTransport(response), **kwargs),
    )
    sources = await public_source_research()
    assert len(sources) == 1 and sources[0]["title"] == "Recent source"
    assert sources[0]["collection_window_days"] == 90
    assert sources[0]["quality"] == "unvalidated_public_discussion"


def test_source_versions_are_appended_without_duplicate_opportunities(owner_client, project):
    source = {
        "title": "Initial source",
        "url": "https://news.ycombinator.com/item?id=123",
        "source": "Boundary test",
        "published_at": now().isoformat(),
        "retrieved_at": now().isoformat(),
        "content_version": "1",
        "excerpt": "Initial observation",
        "quality": "unvalidated_public_discussion",
    }
    with Session.begin() as db:
        db.execute(text("SET LOCAL ROLE company_worker"))
        assert len(store_research(db, project["organization_id"], [source])) == 1
    with Session.begin() as db:
        assert (
            store_research(db, project["organization_id"], [{**source, "retrieved_at": now().isoformat()}])
            == []
        )
        changed = {**source, "content_version": "2", "excerpt": "A revised public observation"}
        assert store_research(db, project["organization_id"], [changed]) == []
    with Session() as db:
        assert db.scalar(select(func.count()).select_from(Opportunity)) == 1
        snapshots = db.scalars(select(ResearchEvidence).order_by(ResearchEvidence.created_at)).all()
        assert len(snapshots) == 2
        assert snapshots[0].data["excerpt"] == "Initial observation"
        assert snapshots[1].data["excerpt"] == "A revised public observation"
        assert snapshots[0].data["snapshot_sha256"] != snapshots[1].data["snapshot_sha256"]
    assert owner_client.get("/audit/verify").json()["valid"]
