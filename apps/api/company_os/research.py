import hashlib
import json
import re
from datetime import UTC, datetime, timedelta

import httpx
from sqlalchemy import select

from .domain import emit, lock_org
from .models import Opportunity, ResearchEvidence, now

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


async def public_source_research(query="workflow automation"):
    # Official public search API: bounded read, no scraping, no third-party contact.
    observed = now()
    cutoff = observed - timedelta(days=90)
    async with httpx.AsyncClient(timeout=20, follow_redirects=False) as client:
        r = await client.get(
            "https://hn.algolia.com/api/v1/search_by_date",
            params={
                "query": query,
                "tags": "story",
                "hitsPerPage": 8,
                "numericFilters": f"created_at_i>{int(cutoff.timestamp())}",
            },
        )
        r.raise_for_status()
    result = []
    for hit in r.json().get("hits", [])[:8]:
        if not isinstance(hit, dict):
            continue
        timestamp = hit.get("created_at_i")
        if type(timestamp) is not int or not cutoff.timestamp() <= timestamp <= observed.timestamp() + 300:
            continue
        object_id = hit.get("objectID", "")
        if not str(object_id).isdigit():
            continue
        result.append(
            {
                "title": hit["title"]
                if isinstance(hit.get("title"), str) and hit["title"]
                else "Public discussion",
                "url": f"https://news.ycombinator.com/item?id={object_id}",
                "source": "Hacker News / Algolia public API",
                "published_at": datetime.fromtimestamp(timestamp, UTC).isoformat(),
                "retrieved_at": observed.isoformat(),
                "collection_window_days": 90,
                "collection_method": "official_search_by_date_with_local_timestamp_validation",
                "excerpt": hit["story_text"][:1200] if isinstance(hit.get("story_text"), str) else "",
                "quality": "unvalidated_public_discussion",
                "content_version": str(hit.get("updated_at") or hit.get("created_at")),
            }
        )
    return result


def store_research(db, org_id, sources):
    lock_org(db, org_id)
    existing = db.scalars(select(Opportunity).where(Opportunity.organization_id == org_id)).all()
    by_url = {e.get("url"): opportunity for opportunity in existing for e in opportunity.evidence}
    snapshots = db.scalars(select(ResearchEvidence).where(ResearchEvidence.organization_id == org_id)).all()
    fingerprints = {s.data.get("snapshot_sha256") for s in snapshots}
    rows = []
    for source in sources:
        url = source.get("url", "")
        if not re.fullmatch(r"https://news\.ycombinator\.com/item\?id=[0-9]+", url):
            continue
        canonical = {
            key: source.get(key)
            for key in ("title", "url", "source", "published_at", "excerpt", "quality", "content_version")
        }
        fingerprint = hashlib.sha256(json.dumps(canonical, sort_keys=True).encode()).hexdigest()
        if fingerprint not in fingerprints:
            snapshot = ResearchEvidence(
                organization_id=org_id,
                data={
                    **source,
                    "snapshot_sha256": fingerprint,
                    "trust": "unvalidated_public_discussion_not_customer_demand",
                },
            )
            db.add(snapshot)
            db.flush()
            fingerprints.add(fingerprint)
            emit(
                db,
                org_id,
                "research_evidence",
                snapshot.id,
                "research.source_observed",
                {
                    "url": url,
                    "snapshot_sha256": fingerprint,
                    "published_at": source.get("published_at"),
                    "retrieved_at": source.get("retrieved_at"),
                },
            )
        if url in by_url:
            opportunity = by_url[url]
            previous = opportunity.evidence[0] if opportunity.evidence else {}
            if any(previous.get(key) != canonical[key] for key in canonical):
                opportunity.evidence = [source]
                emit(
                    db,
                    org_id,
                    "opportunity",
                    opportunity.id,
                    "opportunity.evidence_refreshed",
                    {"url": url, "snapshot_sha256": fingerprint},
                )
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
        by_url[url] = row
        emit(
            db,
            org_id,
            "opportunity",
            row.id,
            "opportunity.discovered",
            {"title": row.title, "score": row.score, "source_url": url, "scoring": "preliminary_heuristic"},
        )
    return rows
