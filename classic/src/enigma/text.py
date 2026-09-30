"""Message normalization and output grouping."""


def normalize(text: str) -> tuple[str, int]:
    """Reduce ``text`` to the letters Enigma can encipher.

    Keeps ASCII letters only (uppercased). Everything else is dropped, and
    nothing is transliterated, so ``"ß"`` is dropped rather than becoming
    ``"SS"``.

    Args:
        text: Arbitrary input text.

    Returns:
        A tuple ``(letters, dropped)``: the uppercase A-Z string and the
        number of characters that were discarded.

    Raises:
        TypeError: If ``text`` is not a ``str``.
    """
    if not isinstance(text, str):
        raise TypeError("text must be a str")
    kept = "".join(c.upper() for c in text if c.isascii() and c.isalpha())
    return kept, len(text) - len(kept)


def group5(text: str) -> str:
    """Split ``text`` into space-separated groups of five letters.

    The last group may be shorter; there is no trailing space.
    """
    return " ".join(text[i : i + 5] for i in range(0, len(text), 5))
