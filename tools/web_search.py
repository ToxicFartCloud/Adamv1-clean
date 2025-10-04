from typing import Any, Dict
import logging

METADATA = {
    "label": "Web Search",
    "description": "Performs web search using DuckDuckGo (no server required).",
    "executable": True,
}

logger = logging.getLogger("adam")

# Lazy import
try:
    from duckduckgo_search import DDGS

    _ddg_available = True
except ImportError:
    _ddg_available = False
    logger.warning(
        "duckduckgo-search not installed. Install with: pip install duckduckgo-search"
    )


def run(**kwargs) -> Dict[str, Any]:
    """
    Perform web search using DuckDuckGo.

    Expected kwargs:
        - query: str (required)
        - max_results: int (default: 5)

    Returns:
        { "ok": bool, "data": list[dict], "error": str or None }
    """
    try:
        query = kwargs.get("query", "").strip()
        if not query:
            return {"ok": False, "data": None, "error": "'query' is required."}

        max_results = kwargs.get("max_results", 5)

        if not _ddg_available:
            # Fallback to mock
            mock_results = [
                {
                    "title": f"Mock Result 1 for '{query}'",
                    "url": "https://example.com/mock1",
                    "content": f"This is a simulated search result for '{query}'. duckduckgo-search not installed.",
                    "engine": "mock",
                },
            ] * min(max_results, 3)
            logger.info(
                "web_search: duckduckgo-search not available — returning mock results"
            )
            return {
                "ok": True,
                "data": mock_results,
                "error": None,
            }

        # Real search
        with DDGS() as ddgs:
            results = []
            for r in ddgs.text(query, max_results=max_results):
                results.append(
                    {
                        "title": r.get("title", ""),
                        "url": r.get("href", ""),
                        "content": r.get("body", "")[:200] + "..."
                        if r.get("body")
                        else "",
                        "engine": "ddg",
                    }
                )

        logger.info("web_search: found %d results for '%s'", len(results), query)
        return {
            "ok": True,
            "data": results,
            "error": None,
        }

    except Exception as e:
        error_msg = f"Web search failed: {str(e)}"
        logger.exception(error_msg)
        return {
            "ok": False,
            "data": None,
            "error": error_msg,
        }
