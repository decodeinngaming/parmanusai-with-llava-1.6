import logging
from typing import List

from googlesearch import search

from app.tool.search.base import SearchItem, WebSearchEngine

logger = logging.getLogger(__name__)


class GoogleSearchEngine(WebSearchEngine):
    def perform_search(
        self, query: str, num_results: int = 10, *args, **kwargs
    ) -> List[SearchItem]:
        """
        Google search engine.

        Returns results formatted according to SearchItem model.
        """
        try:
            raw_results = search(query, num_results=num_results, advanced=True)

            results = []
            for i, item in enumerate(raw_results):
                if isinstance(item, str):
                    # If it's just a URL, validate it
                    url = item.strip()
                    # Skip invalid URLs (relative URLs, etc.)
                    if not url.startswith(("http://", "https://")):
                        logger.warning(f"Skipping invalid URL: {url}")
                        continue

                    results.append(
                        SearchItem(
                            title=f"Google Result {i+1}", url=url, description=""
                        )
                    )
                else:
                    # Validate URL from advanced search result
                    url = getattr(item, "url", "").strip()
                    if not url or not url.startswith(("http://", "https://")):
                        logger.warning(
                            f"Skipping invalid URL from advanced result: {url}"
                        )
                        continue

                    results.append(
                        SearchItem(
                            title=getattr(item, "title", f"Google Result {i+1}"),
                            url=url,
                            description=getattr(item, "description", ""),
                        )
                    )

            logger.info(
                f"Google search returned {len(results)} valid results for query: {query}"
            )
            return results

        except Exception as e:
            logger.error(f"Google search failed: {e}")
            return []
