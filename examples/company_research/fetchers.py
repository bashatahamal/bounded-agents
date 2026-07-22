from __future__ import annotations

from functools import lru_cache
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup
from tavily import TavilyClient

from bounded.resilience import with_retry
from company_research.settings import get_settings

SERPER_ENDPOINT = "https://google.serper.dev/search"


@lru_cache(maxsize=1)
def _tavily_client() -> TavilyClient:
    return TavilyClient(api_key=get_settings().TAVILY_API_KEY)


def _serper_headers() -> dict[str, str]:
    return {"X-API-KEY": get_settings().SERPER_API_KEY, "Content-Type": "application/json"}


@with_retry(retry_on=(requests.RequestException,))
def _serper_search(payload: dict) -> dict:
    resp = requests.post(SERPER_ENDPOINT, headers=_serper_headers(), json=payload, timeout=10)
    resp.raise_for_status()
    return resp.json()


def fetch_search_snippets(company_name: str) -> str | None:
    """Broad company research via Tavily -- the default search backend."""
    query = (
        f"Latest {company_name} company overview, products, founders, financial information, news"
    )
    results = _tavily_client().search(query=query, search_depth="advanced", max_results=15)
    snippets = [r["content"] for r in results.get("results", []) if r.get("content")]
    return "\n".join(snippets) if snippets else None


def fetch_search_snippets_serper(company_name: str) -> str | None:
    """Alternative search backend, kept side-by-side with `fetch_search_snippets`
    to demonstrate that sources plug into the graph with minimal changes --
    see docs/DESIGN.md, "Source Acquisition Strategy". Swap it in by pointing
    `nodes/fetch.py::fetch_search` at this function instead.
    """
    query = (
        f"Latest {company_name} company overview, products, founders, financial information, news"
    )
    data = _serper_search({"q": query, "num": 8})
    snippets = [item["snippet"] for item in data.get("organic", []) if item.get("snippet")]
    return "\n".join(snippets) if snippets else None


def fetch_linkedin_snippet(company_name: str) -> str | None:
    query = f"site:linkedin.com/company {company_name}"
    results = _tavily_client().search(query=query, search_depth="basic", max_results=3)
    for r in results.get("results", []):
        if "linkedin" in r.get("url", "").lower():
            return r.get("content", "")
    return None


def fetch_linkedin_snippet_serper(company_name: str) -> str | None:
    query = f"site:linkedin.com/company {company_name}"
    data = _serper_search({"q": query, "num": 3})
    for item in data.get("organic", []):
        link = item.get("link", "").lower()
        snippet = item.get("snippet", "")
        if "linkedin.com/company" in link and snippet:
            return snippet
    return None


def discover_official_website(company_name: str) -> str | None:
    excluded_domains = (
        "linkedin.com",
        "facebook.com",
        "twitter.com",
        "wikipedia.org",
        "crunchbase.com",
        "instagram.com",
    )
    data = _serper_search({"q": f"{company_name} official website", "num": 10})

    candidates: list[str] = []
    for result in data.get("organic", []):
        link = result.get("link")
        if not link:
            continue
        parsed = urlparse(link)
        domain = parsed.netloc.lower()
        if any(bad in domain for bad in excluded_domains):
            continue
        if parsed.scheme and parsed.netloc:
            candidates.append(f"{parsed.scheme}://{parsed.netloc}")

    if not candidates:
        return None

    # Prefer domains containing the company name
    company_token = company_name.lower().replace(" ", "")
    candidates.sort(key=lambda d: company_token in d.replace(".", "").lower(), reverse=True)
    return candidates[0]


@with_retry(retry_on=(requests.RequestException,))
def extract_text_from_url(url: str) -> str | None:
    headers = {"User-Agent": "Mozilla/5.0"}
    max_chars = 5000

    resp = requests.get(url, headers=headers, timeout=10)
    if resp.status_code != 200 or "text/html" not in resp.headers.get("Content-Type", ""):
        return None

    soup = BeautifulSoup(resp.text, "html.parser")
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()
    if not soup.body:
        return None

    text = soup.body.get_text(separator="\n", strip=True)
    lines = [line for line in text.splitlines() if len(line.strip()) > 30]
    text = "\n".join(lines)
    return text[:max_chars] if text else None


def crawl_official_website(company_name: str) -> str | None:
    important_paths = ["", "about", "about-us", "company", "products", "solutions", "partnership"]
    base_url = discover_official_website(company_name)
    if not base_url:
        return None

    collected = []
    for path in important_paths:
        try:
            url = urljoin(base_url + "/", path)
            text = extract_text_from_url(url)
            if text and len(text) > 200:
                collected.append(text)
        except Exception:
            # One bad page (parse error, unexpected redirect) shouldn't sink
            # the whole crawl -- fetch_website (the caller) still surfaces a
            # top-level failure into state["errors"] if nothing comes back.
            continue

    return "\n".join(collected) if collected else None
