from __future__ import annotations

import logging
from typing import Any


logger = logging.getLogger(__name__)


def web_search(query: str, max_results: int = 5) -> dict[str, Any]:
    if not query or not query.strip():
        return {
            "status": "error",
            "error": "Search query is empty.",
            "results": [],
        }

    try:
        from duckduckgo_search import DDGS
    except Exception as exc:
        return {
            "status": "error",
            "error": f"duckduckgo-search is unavailable: {exc}",
            "results": [],
        }

    results: list[dict[str, Any]] = []
    try:
        with DDGS() as ddgs:
            for item in ddgs.text(query, max_results=max_results):
                if not isinstance(item, dict):
                    continue
                title = (item.get("title") or "").strip()
                url = (item.get("href") or "").strip()
                snippet = (item.get("body") or "").strip()
                if title or url:
                    results.append(
                        {
                            "title": title,
                            "url": url,
                            "snippet": snippet,
                        }
                    )
    except Exception as exc:
        logger.exception("Web search failed for query: %s", query)
        return {
            "status": "error",
            "error": f"Web search failed: {exc}",
            "results": [],
        }

    return {
        "status": "success",
        "query": query,
        "count": len(results),
        "results": results,
    }
