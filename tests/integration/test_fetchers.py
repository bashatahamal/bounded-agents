from unittest.mock import MagicMock, patch

from company_research import fetchers


def _fake_response(json_data=None, status_code=200, text="", content_type="text/html"):
    resp = MagicMock()
    resp.status_code = status_code
    resp.headers = {"Content-Type": content_type}
    resp.text = text
    resp.json.return_value = json_data or {}
    resp.raise_for_status = MagicMock()
    return resp


def test_discover_official_website_prefers_domain_matching_company_name():
    payload = {
        "organic": [
            {"link": "https://en.wikipedia.org/wiki/Acme"},
            {"link": "https://blog.example.com/about-acme"},
            {"link": "https://acme.com/"},
        ]
    }
    with patch("company_research.fetchers.requests.post", return_value=_fake_response(payload)):
        result = fetchers.discover_official_website("Acme")

    assert result == "https://acme.com"


def test_discover_official_website_excludes_social_and_reference_domains():
    payload = {
        "organic": [
            {"link": "https://www.linkedin.com/company/acme"},
            {"link": "https://www.facebook.com/acme"},
        ]
    }
    with patch("company_research.fetchers.requests.post", return_value=_fake_response(payload)):
        result = fetchers.discover_official_website("Acme")

    assert result is None


def test_extract_text_from_url_strips_scripts_and_short_lines():
    html = """
    <html><body>
      <script>var x = 1;</script>
      <p>short</p>
      <p>This is a long enough paragraph to survive the 30 character filter easily.</p>
    </body></html>
    """
    with patch(
        "company_research.fetchers.requests.get",
        return_value=_fake_response(text=html, status_code=200),
    ):
        result = fetchers.extract_text_from_url("https://acme.com")

    assert "var x = 1" not in result
    assert "short" not in result
    assert "long enough paragraph" in result


def test_extract_text_from_url_returns_none_on_non_200():
    with patch(
        "company_research.fetchers.requests.get",
        return_value=_fake_response(status_code=404),
    ):
        assert fetchers.extract_text_from_url("https://acme.com/missing") is None


def test_extract_text_from_url_returns_none_for_non_html_content_type():
    with patch(
        "company_research.fetchers.requests.get",
        return_value=_fake_response(text="{}", content_type="application/json"),
    ):
        assert fetchers.extract_text_from_url("https://acme.com/api") is None


def test_fetch_search_snippets_serper_joins_snippets():
    payload = {"organic": [{"snippet": "Acme makes widgets."}, {"snippet": "Founded in 2015."}]}
    with patch("company_research.fetchers.requests.post", return_value=_fake_response(payload)):
        result = fetchers.fetch_search_snippets_serper("Acme")

    assert result == "Acme makes widgets.\nFounded in 2015."


def test_fetch_search_snippets_serper_returns_none_when_no_snippets():
    with patch(
        "company_research.fetchers.requests.post",
        return_value=_fake_response({"organic": []}),
    ):
        assert fetchers.fetch_search_snippets_serper("Acme") is None


def test_fetch_linkedin_snippet_serper_only_matches_company_pages():
    payload = {
        "organic": [
            {"link": "https://linkedin.com/in/someone", "snippet": "a person, not a company"},
            {"link": "https://linkedin.com/company/acme", "snippet": "Acme company page"},
        ]
    }
    with patch("company_research.fetchers.requests.post", return_value=_fake_response(payload)):
        result = fetchers.fetch_linkedin_snippet_serper("Acme")

    assert result == "Acme company page"


def test_fetch_search_snippets_uses_tavily_and_joins_content():
    with patch.object(fetchers, "_tavily_client") as mock_tavily:
        mock_tavily.return_value.search.return_value = {
            "results": [{"content": "Acme makes widgets."}, {"content": "Founded in 2015."}]
        }
        result = fetchers.fetch_search_snippets("Acme")

    assert result == "Acme makes widgets.\nFounded in 2015."


def test_fetch_linkedin_snippet_returns_first_linkedin_result():
    with patch.object(fetchers, "_tavily_client") as mock_tavily:
        mock_tavily.return_value.search.return_value = {
            "results": [
                {"url": "https://example.com", "content": "not linkedin"},
                {"url": "https://linkedin.com/company/acme", "content": "Acme on LinkedIn"},
            ]
        }
        result = fetchers.fetch_linkedin_snippet("Acme")

    assert result == "Acme on LinkedIn"
