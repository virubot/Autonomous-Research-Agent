from __future__ import annotations

import json
import logging
import re
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from urllib.parse import urlparse
from typing import Any

logger = logging.getLogger(__name__)

# Simple in-process cache to reduce repeat API calls
_CACHE: dict[str, dict[str, Any]] = {}
_CACHE_TTL: dict[str, float] = {}
_CACHE_SECONDS = 120  # 2 minutes

_HIGH_TRUST_DOMAINS = {
    "arxiv.org": 1.0,
    "cloud.google.com": 1.0,
    "docs.cloud.google.com": 1.0,
    "developers.google.com": 0.96,
    "storage.googleapis.com": 0.92,
    "googleapis.com": 0.92,
    "ieeexplore.ieee.org": 0.95,
    "doi.org": 0.93,
    "dl.acm.org": 0.93,
    "acm.org": 0.9,
    "nature.com": 0.9,
    "science.org": 0.9,
    "openreview.net": 0.88,
}

_LOW_QUALITY_DOMAINS = {
    "facebook.com",
    "instagram.com",
    "medium.com",
    "pinterest.com",
    "quora.com",
    "reddit.com",
    "tiktok.com",
    "x.com",
    "twitter.com",
    "youtube.com",
}


def _cache_get(key: str) -> dict[str, Any] | None:
    if key in _CACHE:
        if time.time() - _CACHE_TTL.get(key, 0) < _CACHE_SECONDS:
            return _CACHE[key]
        del _CACHE[key]
        _CACHE_TTL.pop(key, None)
    return None


def _cache_set(key: str, value: dict[str, Any]) -> None:
    _CACHE[key] = value
    _CACHE_TTL[key] = time.time()


def web_search(query: str, max_results: int = 5) -> dict[str, Any]:
    if not query or not query.strip():
        return {"status": "error", "error": "Search query is empty.", "results": []}

    cache_key = f"search:{query}:{max_results}"
    cached = _cache_get(cache_key)
    if cached is not None:
        logger.debug("Cache hit for query: %.60s", query)
        return cached

    results: list[dict[str, Any]] = []
    errors: list[str] = []

    # ── 1. DuckDuckGo web search ─────────────────────────────────────────
    DDGS = None
    try:
        from ddgs import DDGS
    except ImportError:
        try:
            from ddgs import DDGS
        except ImportError as exc:
            logger.warning("ddgs and ddgs are both unavailable: %s", exc)
            errors.append(f"Web search unavailable: {exc}")

    if DDGS is not None:
        try:
            with DDGS() as ddgs:
                for item in ddgs.text(query, max_results=max_results):
                    if not isinstance(item, dict):
                        continue
                    title = (item.get("title") or "").strip()
                    url = (item.get("href") or "").strip()
                    snippet = (item.get("body") or "").strip()
                    if title or url:
                        results.append({"title": title, "url": url, "snippet": snippet, "source": "web"})
        except Exception as exc:
            logger.warning("Web search failed: %s", exc)
            errors.append(f"Web search failed: {exc}")

    # ── 2. ArXiv API — with retry + backoff for 429 ─────────────────────
    arxiv_results = _arxiv_search(query, max_results, errors)
    results.extend(arxiv_results)

    # Short throttle between APIs to avoid rate-limiting
    time.sleep(0.3)

    # ── 3. Crossref API — with 30s timeout + retry ──────────────────────
    crossref_results = _crossref_search(query, max_results, errors)
    results.extend(crossref_results)

    ranked_results = _rank_and_filter_results(query=query, results=results, max_results=max_results)

    response = {
        "status": "success" if ranked_results else "error",
        "query": query,
        "count": len(ranked_results),
        "results": ranked_results,
        "errors": errors,
    }
    if ranked_results:
        _cache_set(cache_key, response)
    return response


def _arxiv_search(query: str, max_results: int, errors: list[str]) -> list[dict[str, Any]]:
    """ArXiv search with exponential backoff on 429."""
    url = (
        f"http://export.arxiv.org/api/query"
        f"?search_query=all:{urllib.parse.quote(query)}&start=0&max_results={max_results}"
    )
    headers = {
        "User-Agent": "AutonomousResearchAgent/1.0 (research platform; mailto:research@ara-platform.ai)"
    }
    results: list[dict[str, Any]] = []

    for attempt in range(3):
        try:
            if attempt > 0:
                backoff = 2 ** attempt  # 2s, 4s
                logger.info("ArXiv retry %d — waiting %ds", attempt, backoff)
                time.sleep(backoff)

            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=15) as resp:
                body = resp.read()

            root = ET.fromstring(body)
            ns = {"atom": "http://www.w3.org/2005/Atom"}
            for entry in root.findall("atom:entry", ns):
                title_el = entry.find("atom:title", ns)
                summary_el = entry.find("atom:summary", ns)
                id_el = entry.find("atom:id", ns)
                title = title_el.text.strip() if title_el is not None else "Untitled"
                summary = summary_el.text.strip() if summary_el is not None else ""
                url_str = id_el.text.strip() if id_el is not None else ""
                results.append({
                    "title": f"[ArXiv] {title}",
                    "url": url_str,
                    "snippet": summary[:500],
                    "source": "arxiv",
                })
            return results

        except Exception as exc:
            err_str = str(exc)
            if "429" in err_str or "Too Many Requests" in err_str.lower():
                logger.warning("ArXiv 429 rate limit (attempt %d): %s", attempt + 1, exc)
                if attempt == 2:
                    errors.append("ArXiv API rate-limited — skipping.")
                continue
            logger.warning("ArXiv search failed: %s", exc)
            errors.append(f"ArXiv API failed: {exc}")
            break

    return results


def _crossref_search(query: str, max_results: int, errors: list[str]) -> list[dict[str, Any]]:
    """Crossref search with 30s timeout and retry."""
    url = (
        f"https://api.crossref.org/works"
        f"?query={urllib.parse.quote(query)}&select=title,URL,abstract&rows={max_results}"
    )
    headers = {
        "User-Agent": "AutonomousResearchAgent/1.0 (research platform; mailto:research@ara-platform.ai)"
    }
    results: list[dict[str, Any]] = []

    for attempt in range(2):
        try:
            if attempt > 0:
                time.sleep(3)
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read().decode())

            for item in data.get("message", {}).get("items", []):
                title = (item.get("title") or [""])[0]
                url_str = item.get("URL", "")
                abstract = item.get("abstract", "")
                # Strip HTML tags from abstract
                abstract = re.sub(r"<[^>]+>", "", abstract)
                if title and url_str:
                    results.append({
                        "title": f"[Crossref] {title}",
                        "url": url_str,
                        "snippet": abstract[:500],
                        "source": "crossref",
                    })
            return results

        except Exception as exc:
            logger.warning("Crossref attempt %d failed: %s", attempt + 1, exc)
            if attempt == 1:
                errors.append(f"Crossref API failed: {exc}")

    return results


def _normalize_domain(url: str) -> str:
    try:
        domain = urlparse(url).netloc.lower()
    except Exception:
        return ""
    if domain.startswith("www."):
        domain = domain[4:]
    return domain


def _normalize_url(url: str) -> str:
    parsed = urlparse(url.strip())
    scheme = parsed.scheme.lower() or "https"
    netloc = parsed.netloc.lower()
    if netloc.startswith("www."):
        netloc = netloc[4:]
    path = parsed.path.rstrip("/")
    return f"{scheme}://{netloc}{path}"


def _query_terms(query: str) -> list[str]:
    return [
        token
        for token in re.findall(r"[a-z0-9]+", query.lower())
        if len(token) > 2
    ]


def _score_result(query: str, item: dict[str, Any]) -> float:
    domain = _normalize_domain(str(item.get("url") or ""))
    title = str(item.get("title") or "").lower()
    snippet = str(item.get("snippet") or "").lower()
    source = str(item.get("source") or "").lower()
    haystack = f"{title} {snippet}"
    terms = _query_terms(query)

    source_bonus = {
        "arxiv": 0.35,
        "crossref": 0.28,
        "web": 0.16,
    }.get(source, 0.1)

    domain_bonus = 0.0
    for trusted_domain, bonus in _HIGH_TRUST_DOMAINS.items():
        if domain == trusted_domain or domain.endswith(f".{trusted_domain}"):
            domain_bonus = max(domain_bonus, bonus)

    term_hits = sum(1 for term in terms if term in haystack)
    relevance_bonus = min(term_hits * 0.08, 0.32)

    penalize_query_farms = 0.0
    if domain in _LOW_QUALITY_DOMAINS:
        penalize_query_farms = 0.75

    if not title:
        penalize_query_farms += 0.15
    if len(snippet) < 40:
        penalize_query_farms += 0.08

    return source_bonus + domain_bonus + relevance_bonus - penalize_query_farms


def _rank_and_filter_results(
    query: str,
    results: list[dict[str, Any]],
    max_results: int,
) -> list[dict[str, Any]]:
    deduped: dict[str, tuple[float, dict[str, Any]]] = {}
    for item in results:
        if not isinstance(item, dict):
            continue

        title = str(item.get("title") or "").strip()
        url = str(item.get("url") or "").strip()
        snippet = str(item.get("snippet") or "").strip()
        if not (title or url):
            continue

        score = _score_result(query=query, item=item)
        if score < 0.18:
            continue

        normalized = _normalize_url(url) if url else title.lower()
        enriched = {
            "title": title,
            "url": url,
            "snippet": snippet,
            "source": item.get("source", "web"),
            "domain": _normalize_domain(url),
        }
        previous = deduped.get(normalized)
        if previous is None or score > previous[0]:
            deduped[normalized] = (score, enriched)

    ranked = sorted(
        deduped.values(),
        key=lambda pair: (
            pair[0],
            len(str(pair[1].get("snippet") or "")),
        ),
        reverse=True,
    )
    return [item for _, item in ranked[:max_results]]
