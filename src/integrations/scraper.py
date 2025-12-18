import time
from typing import Literal

import structlog
from tavily import TavilyClient

from config import settings

logger = structlog.get_logger(__name__)


class WebScraper:
    def __init__(
        self,
        max_results: int = 5,
        delay: int = 0.25,
        api_key: str | None = None,
        search_depth: Literal["basic", "advanced"] = "basic",
    ):
        self.api_key = api_key or settings.TAVILY_API_KEY
        self.client = TavilyClient(api_key=self.api_key)
        self.max_results = max_results
        self.search_depth = search_depth
        self.delay = delay

    def search(
        self,
        query: str,
        max_results: int | None = None,
        include_answer: bool = False,
        include_raw_content: bool = False,
        include_domains: list[str] = None,
        exclude_domains: list[str] = None,
    ) -> dict:
        """General search function using Tavily."""
        try:
            time.sleep(self.delay)  # Rate limiting

            search_params = {"query": query}

            if max_results is not None:
                search_params["max_results"] = max_results

            if self.search_depth is not None:
                search_params["search_depth"] = self.search_depth

            if include_answer:
                search_params["include_answer"] = include_answer

            if include_raw_content:
                search_params["include_raw_content"] = include_raw_content

            if include_domains:
                search_params["include_domains"] = include_domains

            if exclude_domains:
                search_params["exclude_domains"] = exclude_domains

            logger.info(
                "Searching for: {query} with params: {search_params}".format(
                    query=query, search_params=search_params
                )
            )
            results = self.client.search(**search_params)
            text_result = ""
            for d in results["results"]:
                text_result += f"Title: {d['title']}\n"
                text_result += f"URL: {d['url']}\n"
                text_result += f"Content: {d['content']}\n"
                text_result += "\n\n"
            return text_result

        except Exception as e:
            raise Exception(f"Search failed for query '{query}': {str(e)}")

    def extract_content(self, urls: list[str] | str) -> dict:
        """Extract content from specific URLs using Tavily."""
        try:
            result = self.client.extract(urls=urls)
            return result
        except Exception as e:
            raise Exception(f"Content extraction failed for URLs {urls}: {str(e)}")


if __name__ == "__main__":
    scraper = WebScraper()
    # list_company = ["Meta", "NVIDIA", "Apple"]
    # for company in list_company:
    #     profile = scraper.search(
    #         # query=f"company profile page about us {company}",
    #         query=f"company profile page about us {company}",
    #         max_results=5,
    #     )
    #     print(profile)
    #     print("\n\n")
    result = scraper.extract_content("https://www.linkedin.com/company/nvidia/about/")
    print(result)
