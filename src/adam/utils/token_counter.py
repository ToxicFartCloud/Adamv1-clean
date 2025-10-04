from __future__ import annotations


def count_tokens(text: str, model: str = "gpt-4") -> int:
    """Return an approximate token count for the given text."""
    try:
        import tiktoken  # type: ignore

        encoder = tiktoken.encoding_for_model(model)
        return len(encoder.encode(text))
    except Exception:
        words = len(text.split())
        chars = len(text)
        return max(1, int((words * 4 + chars) / 4))
