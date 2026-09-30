import pytest

from enigma.text import group5, normalize


def test_normalize_empty():
    assert normalize("") == ("", 0)


def test_normalize_uppercases():
    assert normalize("abc") == ("ABC", 0)


def test_normalize_drops_non_letters_and_counts():
    assert normalize("Meet at 9! ß") == ("MEETAT", 6)


@pytest.mark.parametrize("ch", ["é", "ß", "Ä", "Ж", "😀", "\t", "\n", "\r", "�", "́"])
def test_normalize_drops_each_code_point_once(ch):
    assert normalize("A" + ch + "B") == ("AB", 1)


def test_normalize_is_idempotent():
    once, _ = normalize("Hello, World! 123 ß")
    assert normalize(once) == (once, 0)


@pytest.mark.parametrize("bad", [None, 1, b"abc", ["a"]])
def test_normalize_rejects_non_str(bad):
    with pytest.raises(TypeError):
        normalize(bad)


@pytest.mark.parametrize(
    "text, expected",
    [
        ("", ""),
        ("ABCD", "ABCD"),
        ("ABCDE", "ABCDE"),
        ("ABCDEF", "ABCDE F"),
        ("ABCDEFGHIJ", "ABCDE FGHIJ"),
    ],
)
def test_group5(text, expected):
    assert group5(text) == expected


def test_group5_round_trips_through_normalize():
    assert normalize(group5("ABCDEFGHIJKLM"))[0] == "ABCDEFGHIJKLM"
