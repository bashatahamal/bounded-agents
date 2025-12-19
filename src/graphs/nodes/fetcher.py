from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup
from langchain_core.prompts import PromptTemplate
from langsmith import traceable

# from readability import Document
from tavily import TavilyClient

from config import prompt_general, settings
from graphs.states.research import ResearchState, SearchResult
from integrations.llm import llm_client

tavily = TavilyClient(api_key=settings.TAVILY_API_KEY)

SERPER_ENDPOINT = "https://google.serper.dev/search"
headers = {
    "X-API-KEY": settings.SERPER_API_KEY,
    "Content-Type": "application/json",
}


# def fetch_search_snippets(company_name: str) -> str:
#     query = f"What does {company_name} do company"

#     results = tavily.search(query=query, search_depth="basic", max_results=5)

#     snippets = []
#     for r in results.get("results", []):
#         if r.get("content"):
#             snippets.append(r["content"])

#     return "\n".join(snippets) if snippets else None


# tavily
def fetch_search_snippets(company_name: str) -> str:
    query = f"Latest {company_name} company overview, products, founders, financial information, news"

    results = tavily.search(query=query, search_depth="basic", max_results=8)

    snippets = []
    for r in results.get("results", []):
        if r.get("content"):
            snippets.append(r["content"])

    return "\n".join(snippets) if snippets else None


def fetch_linkedin_snippet(company_name: str) -> str:
    query = f"site:linkedin.com/company {company_name}"

    results = tavily.search(query=query, search_depth="basic", max_results=3)

    for r in results.get("results", []):
        content = r.get("content", "")
        if "linkedin" in r.get("url", "").lower():
            return content

    return None


# serper
def discover_linkedin_company(company_name: str) -> str | None:
    payload = {
        "q": f"site:linkedin.com/company {company_name}",
        "num": 5,
    }

    resp = requests.post(SERPER_ENDPOINT, headers=headers, json=payload)
    resp.raise_for_status()

    for r in resp.json().get("organic", []):
        link = r.get("link")
        if link and "linkedin.com/company" in link:
            return link

    return None


def fetch_search_snippets_serper(company_name: str) -> str | None:
    query = (
        f"Latest {company_name} company overview, products, founders, "
        f"financial information, news"
    )

    payload = {
        "q": query,
        "num": 8,
    }

    resp = requests.post(
        SERPER_ENDPOINT,
        headers=headers,
        json=payload,
        timeout=10,
    )
    resp.raise_for_status()

    data = resp.json()

    snippets = []

    for item in data.get("organic", []):
        snippet = item.get("snippet")
        if snippet:
            snippets.append(snippet)

    return "\n".join(snippets) if snippets else None


def fetch_linkedin_snippet_serper(company_name: str) -> str | None:
    query = f"site:linkedin.com/company {company_name}"

    payload = {
        "q": query,
        "num": 3,
    }

    resp = requests.post(
        SERPER_ENDPOINT,
        headers=headers,
        json=payload,
        timeout=10,
    )
    resp.raise_for_status()

    data = resp.json()

    for item in data.get("organic", []):
        link = item.get("link", "").lower()
        snippet = item.get("snippet", "")

        if "linkedin.com/company" in link and snippet:
            return snippet

    return None


@traceable
def discover_official_website(company_name: str) -> str | None:
    EXCLUDED_DOMAINS = (
        "linkedin.com",
        "facebook.com",
        "twitter.com",
        "wikipedia.org",
        "crunchbase.com",
        "instagram.com",
    )

    payload = {
        "q": f"{company_name} official website",
        "num": 10,
    }

    resp = requests.post(
        SERPER_ENDPOINT,
        headers=headers,
        json=payload,
        timeout=10,
    )
    resp.raise_for_status()

    data = resp.json()

    candidates: list[str] = []

    for result in data.get("organic", []):
        link = result.get("link")
        if not link:
            continue

        parsed = urlparse(link)
        domain = parsed.netloc.lower()

        # Skip obvious non-official domains
        if any(bad in domain for bad in EXCLUDED_DOMAINS):
            continue

        if parsed.scheme and parsed.netloc:
            candidates.append(f"{parsed.scheme}://{parsed.netloc}")

    if not candidates:
        return None

    # Prefer domains containing the company name
    company_token = company_name.lower().replace(" ", "")

    candidates.sort(
        key=lambda d: company_token in d.replace(".", "").lower(),
        reverse=True,
    )

    return candidates[0]


def extract_text_from_url(url: str) -> str | None:
    HEADERS = {"User-Agent": "Mozilla/5.0"}

    MAX_CHARS = 5000
    try:
        resp = requests.get(url, headers=HEADERS, timeout=10)
        if resp.status_code != 200:
            return None
    except requests.RequestException:
        return None

    if "text/html" not in resp.headers.get("Content-Type", ""):
        return None

    soup = BeautifulSoup(resp.text, "html.parser")

    # Remove obvious noise only
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()

    if not soup.body:
        return None

    text = soup.body.get_text(separator="\n", strip=True)

    # Basic cleanup: drop very short lines
    lines = [x for x in text.splitlines() if len(x.strip()) > 30]
    text = "\n".join(lines)

    return text[:MAX_CHARS] if text else None


def crawl_official_website(company_name: str) -> str | None:
    IMPORTANT_PATHS = [
        "",
        "about",
        "about-us",
        "company",
        "products",
        "solutions",
        "partnership",
    ]
    base_url = discover_official_website(company_name)
    if not base_url:
        return None

    collected = []

    for path in IMPORTANT_PATHS:
        try:
            url = urljoin(base_url + "/", path)
            text = extract_text_from_url(url)
            if len(text) > 200:
                collected.append(text)
        except Exception:
            continue

    return "\n".join(collected) if collected else None

# Node
def fetch_website(state: ResearchState) -> dict:
    try:
        return {"website_text": crawl_official_website(state["company_name"])}
    except Exception as e:
        return {
            "website_text": None,
            "errors": [f"Website fetch failed: {e}"],
        }


def fetch_linkedin(state: ResearchState) -> dict:
    try:
        # return {"linkedin_text": fetch_linkedin_snippet(state["company_name"])}
        return {"linkedin_text": fetch_linkedin_snippet_serper(state["company_name"])}
    except Exception as e:
        return {
            "linkedin_text": None,
            "errors": [f"LinkedIn fetch failed: {e}"],
        }


def fetch_search(state: ResearchState) -> dict:
    try:
        # return {"results": fetch_search_snippets(state["company_name"])}
        return {"results": fetch_search_snippets_serper(state["company_name"])}
    except Exception as e:
        return {
            "results": None,
            "errors": [f"Search fetch failed: {e}"],
        }


def search_general(state: SearchResult) -> dict:
    prompt_template = PromptTemplate(
        template=prompt_general["search_general"],
        input_variables=["search_result"],
    )
    result = llm_client.completion(
        user_input=prompt_template.format(search_result=state["results"])
    )
    return {"search_general": result}


def search_founder(state: SearchResult) -> dict:
    prompt_template = PromptTemplate(
        template=prompt_general["search_founder"],
        input_variables=["search_result"],
    )

    result = llm_client.completion(
        user_input=prompt_template.format(search_result=state["results"])
    )

    return {"search_founder": result}


def search_finance(state: SearchResult) -> dict:
    prompt_template = PromptTemplate(
        template=prompt_general["search_finance"],
        input_variables=["search_result"],
    )

    result = llm_client.completion(
        user_input=prompt_template.format(search_result=state["results"])
    )

    return {"search_finance": result}


def search_news(state: SearchResult) -> dict:
    prompt_template = PromptTemplate(
        template=prompt_general["search_news"],
        input_variables=["search_result"],
    )

    result = llm_client.completion(
        user_input=prompt_template.format(search_result=state["results"])
    )

    return {"search_news": result}


# from langsmith import traceable
# @traceable
# def discover_official_website(company_name: str) -> str | None:
#     query = f"{company_name} official website"

#     results = tavily.search(
#         query=query,
#         search_depth="basic",
#         max_results=5
#     )
#     print(results)
#     for r in results.get("results", []):
#         url = r.get("url", "")
#         if url.startswith("http"):
#             return url

#     return None
# from langsmith import traceable
# @traceable
# def discover_official_website(company_name: str) -> str | None:
#     query = f"{company_name} official website"
#     results = tavily.search(query=query, search_depth="basic", max_results=5)

#     for r in results.get("results", []):
#         url = r.get("url", "")
#         if not url.startswith("http"):
#             continue

#         parsed = urlparse(url)
#         if (
#             parsed.netloc
#             and company_name.lower().replace(" ", "") in parsed.netloc.lower()
#         ):
#             return f"{parsed.scheme}://{parsed.netloc}"

#     return None

# def extract_text_from_url(url: str) -> str:
#     resp = requests.get(url, headers=HEADERS, timeout=10)
#     resp.raise_for_status()

#     doc = Document(resp.text)
#     soup = BeautifulSoup(doc.summary(), "html.parser")

#     return soup.get_text(separator="\n", strip=True)
