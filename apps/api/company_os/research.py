import httpx
from sqlalchemy import select

from .domain import emit, lock_org
from .models import Opportunity, now

DIMENSIONS = {
    "evidence_strength": 15,
    "willingness_to_pay": 15,
    "distribution": 10,
    "speed_to_mvp": 10,
    "build_cost": 10,
    "maintenance": 10,
    "defensibility": 5,
    "competition": 10,
    "legal_privacy": 10,
    "unit_economics": 5,
}


def opportunity_score(dimensions):
    if set(dimensions) != set(DIMENSIONS):
        raise ValueError("All scoring dimensions required")
    if any(type(v) is not int or not 0 <= v <= 100 for v in dimensions.values()):
        raise ValueError("Scores must be 0-100")
    return round(sum(dimensions[k] * w for k, w in DIMENSIONS.items()) / 100)


async def public_source_research(query="Ask HN business workflow automation"):
    # Official public search API: bounded read, no scraping, no third-party contact.
    async with httpx.AsyncClient(timeout=20, follow_redirects=False) as client:
        r = await client.get(
            "https://hn.algolia.com/api/v1/search", params={"query": query, "tags": "story", "hitsPerPage": 8}
        )
        r.raise_for_status()
    result = []
    for hit in r.json().get("hits", []):
        object_id = hit.get("objectID", "")
        if not str(object_id).isdigit():
            continue
        result.append(
            {
                "title": hit.get("title") or "Public discussion",
                "url": f"https://news.ycombinator.com/item?id={object_id}",
                "source": "Hacker News / Algolia public API",
                "published_at": hit.get("created_at"),
                "retrieved_at": now().isoformat(),
                "excerpt": (hit.get("story_text") or "")[:1200],
                "quality": "unvalidated_public_discussion",
                "content_version": str(hit.get("updated_at") or hit.get("created_at")),
            }
        )
    return result


def store_research(db, org_id, sources):
    lock_org(db, org_id)
    rows = []
    for source in sources:
        # Source-backed candidate; scoring is explicitly a heuristic, never demand proof.
        if not source.get("url", "").startswith("https://news.ycombinator.com/item?id="):
            continue
        existing = db.scalars(select(Opportunity).where(Opportunity.organization_id == org_id)).all()
        if any(any(e.get("url") == source["url"] for e in o.evidence) for o in existing):
            continue
        dimensions = {k: 20 for k in DIMENSIONS}
        dimensions["evidence_strength"] = 30
        row = Opportunity(
            organization_id=org_id,
            title=source["title"][:200],
            hypothesis="Investigate whether this public discussion identifies a repeatable workflow pain that customers would pay to solve.",
            score=opportunity_score(dimensions),
            dimensions=dimensions,
            uncertainties=[
                "Heuristic preliminary ranking, not validated demand",
                "Willingness to pay unknown",
                "Market size and distribution unverified",
                "Human source review required",
            ],
            evidence=[source],
        )
        db.add(row)
        db.flush()
        rows.append(row)
        emit(
            db,
            org_id,
            "opportunity",
            row.id,
            "opportunity.discovered",
            {
                "title": row.title,
                "score": row.score,
                "source_url": source["url"],
                "scoring": "preliminary_heuristic",
            },
        )
    return rows
