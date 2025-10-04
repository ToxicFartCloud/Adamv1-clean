"""Mock backend — always available."""

from typing import List
from .base import MemorySearchBackend, register_backend


class MockMemoryBackend(MemorySearchBackend):
    def search(self, query: str, top_k: int) -> List[str]:
        return [
            f"Mock result 1 for '{query}'",
            f"Mock result 2 for '{query}'",
            f"Mock result 3 for '{query}' (simulated relevance: 0.92)",
        ][:top_k]

    async def asearch(self, query: str, top_k: int) -> List[str]:
        return self.search(query, top_k)


register_backend("mock", MockMemoryBackend)
