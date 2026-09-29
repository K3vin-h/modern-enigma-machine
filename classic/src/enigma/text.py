"""Message normalization and output grouping."""


def normalize(text: str) -> tuple[str, int]:
    """Keep ASCII letters (uppercased); return (letters, number of dropped chars)."""
    if not isinstance(text, str):
        raise TypeError("text must be a str")
    kept = "".join(c.upper() for c in text if c.isascii() and c.isalpha())
    return kept, len(text) - len(kept)


def group5(text: str) -> str:
    return " ".join(text[i : i + 5] for i in range(0, len(text), 5))
