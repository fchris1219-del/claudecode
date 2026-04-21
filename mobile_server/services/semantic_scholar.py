import httpx


_BASE = "https://api.semanticscholar.org/graph/v1"
_FIELDS = "title,abstract,authors,year,externalIds,openAccessPdf,url"


async def search_papers(query: str, limit: int = 8) -> list[dict]:
    """Search Semantic Scholar and return structured paper dicts."""
    async with httpx.AsyncClient(timeout=20) as client:
        resp = await client.get(
            f"{_BASE}/paper/search",
            params={"query": query, "limit": limit, "fields": _FIELDS},
            headers={"User-Agent": "mobile-messaging-server/1.0"},
        )
        resp.raise_for_status()
        data = resp.json()

    papers = []
    for p in data.get("data", []):
        pdf_url = None
        if p.get("openAccessPdf"):
            pdf_url = p["openAccessPdf"].get("url")
        papers.append({
            "title": p.get("title", ""),
            "abstract": p.get("abstract") or "",
            "authors": [a["name"] for a in p.get("authors", [])[:3]],
            "year": p.get("year"),
            "url": p.get("url") or f"https://www.semanticscholar.org/paper/{p.get('paperId', '')}",
            "pdf_url": pdf_url,
        })
    return papers
