"""Physical Enigma components: rotors, reflector, entry wheel and plugboard.

Signal contacts are zero-based ints (A=0 .. Z=25); the mapping methods
expect values in that range and do not validate them. Rings and window
positions are given as single uppercase letters. Constructors raise
``TypeError`` for non-``str`` arguments and ``ValueError`` for invalid
values, so callers should handle both.
"""

import string

from .wiring import REFLECTORS, ROTORS, THIN

A = string.ascii_uppercase


def _letter(value: str, what: str) -> int:
    """Convert a single uppercase letter to its contact index.

    Args:
        value: The letter to convert.
        what: Name of the argument, used in error messages.

    Returns:
        The zero-based index (A=0 .. Z=25).

    Raises:
        TypeError: If ``value`` is not a ``str``.
        ValueError: If ``value`` is not exactly one letter A-Z.
    """
    if not isinstance(value, str):
        raise TypeError(f"{what} must be a str")
    if len(value) != 1 or value not in A:
        raise ValueError(f"{what} must be a single uppercase letter A-Z, got {value!r}")
    return A.index(value)


class Rotor:
    """A stepping rotor with a ring setting and a window position.

    The ring setting only shifts the electrical wiring relative to the
    rotor's alphabet ring; it does not move the turnover notch, which is
    always checked against the window letter.

    Attributes:
        name: The rotor's name, e.g. ``"III"``.
    """

    def __init__(self, name: str, ring: str, position: str) -> None:
        """Build a rotor.

        Args:
            name: Rotor name (I-VIII for the base class).
            ring: Ring setting, one uppercase letter.
            position: Window letter the rotor starts at, one uppercase letter.

        Raises:
            TypeError: If any argument is not a ``str``.
            ValueError: If the name is unknown or ring/position is not A-Z.
        """
        if not isinstance(name, str):
            raise TypeError("rotor name must be a str")
        wiring, self._turnover = self._lookup(name)
        self.name = name
        self._ring = _letter(ring, "ring")
        self._pos = _letter(position, "position")
        self._fwd = [A.index(c) for c in wiring]
        self._inv = [0] * 26
        for i, c in enumerate(self._fwd):
            self._inv[c] = i

    @staticmethod
    def _lookup(name: str) -> tuple[str, str]:
        """Return ``(wiring, turnover_letters)`` for ``name``.

        Raises:
            ValueError: If ``name`` is not a known rotor.
        """
        if name not in ROTORS:
            raise ValueError(f"unknown rotor {name!r}")
        return ROTORS[name]

    @property
    def position(self) -> str:
        """The letter currently showing in the window."""
        return A[self._pos]

    @property
    def _offset(self) -> int:
        """Electrical offset ``position - ring`` (may be negative)."""
        return self._pos - self._ring

    def forward(self, i: int) -> int:
        """Map contact ``i`` on the entry side (right-to-left pass)."""
        d = self._offset
        return (self._fwd[(i + d) % 26] - d) % 26

    def backward(self, i: int) -> int:
        """Map contact ``i`` on the reflector side (left-to-right pass)."""
        d = self._offset
        return (self._inv[(i + d) % 26] - d) % 26

    def at_turnover(self) -> bool:
        """Return whether the window letter is a turnover notch."""
        return self.position in self._turnover

    def step(self) -> None:
        """Advance one position, wrapping Z to A."""
        self._pos = (self._pos + 1) % 26


class ThinRotor(Rotor):
    """M4 Greek wheel (Beta or Gamma).

    Maps like a normal rotor, with ring and position, but has no notch and
    is never stepped by the machine.
    """

    @staticmethod
    def _lookup(name: str) -> tuple[str, str]:
        """Return ``(wiring, "")`` for a thin rotor; there is no turnover.

        Raises:
            ValueError: If ``name`` is not Beta or Gamma.
        """
        if name not in THIN:
            raise ValueError(f"unknown thin rotor {name!r}")
        return THIN[name], ""

    def at_turnover(self) -> bool:
        """Always ``False``: thin rotors never carry."""
        return False

    def step(self) -> None:
        """Not supported.

        Raises:
            RuntimeError: Always; thin rotors never step.
        """
        raise RuntimeError("thin rotors never step")


class Reflector:
    """A fixed reflector (UKW) that sends the signal back through the rotors.

    Every contact maps to a different contact, and the mapping is its own
    inverse. It has no position or ring offset.

    Attributes:
        name: The reflector's name, e.g. ``"B"`` or ``"B-thin"``.
    """

    def __init__(self, name: str) -> None:
        """Build a reflector.

        Args:
            name: One of the names in ``wiring.REFLECTORS``.

        Raises:
            TypeError: If ``name`` is not a ``str``.
            ValueError: If ``name`` is not a known reflector.
        """
        if not isinstance(name, str):
            raise TypeError("reflector name must be a str")
        if name not in REFLECTORS:
            raise ValueError(f"unknown reflector {name!r}")
        self.name = name
        self._map = [A.index(c) for c in REFLECTORS[name]]

    def reflect(self, i: int) -> int:
        """Return the contact that ``i`` is wired to."""
        return self._map[i]


class EntryWheel:
    """The entry wheel (ETW): identity wiring between plugboard and rotors."""

    def forward(self, i: int) -> int:
        """Return ``i`` unchanged."""
        return i

    backward = forward


class Plugboard:
    """A plugboard of up to 13 letter-pair swaps.

    Unlisted letters map to themselves, so the mapping is always an
    involution.
    """

    def __init__(self, pairs: str = "") -> None:
        """Build a plugboard.

        Args:
            pairs: Whitespace-separated two-letter pairs, e.g. ``"AT BL DF"``.
                Case is ignored. Empty or whitespace-only means no plugs.

        Raises:
            TypeError: If ``pairs`` is not a ``str``.
            ValueError: If there are more than 13 pairs, a token is not exactly
                two ASCII letters, a pair plugs a letter to itself, or a
                letter appears in more than one pair.
        """
        if not isinstance(pairs, str):
            raise TypeError("plugboard must be a str")
        self._map = list(range(26))
        tokens = pairs.split()
        if len(tokens) > 13:
            raise ValueError("plugboard allows at most 13 pairs")
        seen: set[str] = set()
        for tok in tokens:
            # Check ASCII before upper-casing: e.g. "ﬁ".upper() is "FI".
            if len(tok) != 2 or not (tok.isascii() and tok.isalpha()):
                raise ValueError(
                    f"plug pair must be exactly two ASCII letters, got {tok!r}"
                )
            pair = tok.upper()
            a, b = pair
            if a == b:
                raise ValueError(f"cannot plug {a} to itself")
            if a in seen or b in seen:
                raise ValueError(f"letter used twice in plugboard: {pair!r}")
            seen.update((a, b))
            self._map[A.index(a)], self._map[A.index(b)] = A.index(b), A.index(a)

    def swap(self, i: int) -> int:
        """Return the contact that ``i`` is plugged to (or ``i`` itself)."""
        return self._map[i]
