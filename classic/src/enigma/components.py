"""Enigma components. Contacts are zero-based ints (A=0 .. Z=25)."""

import string

from .wiring import REFLECTORS, ROTORS, THIN

A = string.ascii_uppercase


def _letter(value: str, what: str) -> int:
    if not isinstance(value, str):
        raise TypeError(f"{what} must be a str")
    if len(value) != 1 or value not in A:
        raise ValueError(f"{what} must be a single uppercase letter A-Z, got {value!r}")
    return A.index(value)


class Rotor:
    def __init__(self, name: str, ring: str, position: str):
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
    def _lookup(name):
        if name not in ROTORS:
            raise ValueError(f"unknown rotor {name!r}")
        return ROTORS[name]

    @property
    def position(self) -> str:
        return A[self._pos]

    @property
    def _offset(self) -> int:
        return self._pos - self._ring

    def forward(self, i: int) -> int:
        d = self._offset
        return (self._fwd[(i + d) % 26] - d) % 26

    def backward(self, i: int) -> int:
        d = self._offset
        return (self._inv[(i + d) % 26] - d) % 26

    def at_turnover(self) -> bool:
        return self.position in self._turnover

    def step(self) -> None:
        self._pos = (self._pos + 1) % 26


class ThinRotor(Rotor):
    """M4 Beta/Gamma: fixed in place, never carries."""

    @staticmethod
    def _lookup(name):
        if name not in THIN:
            raise ValueError(f"unknown thin rotor {name!r}")
        return THIN[name], ""

    def at_turnover(self) -> bool:
        return False

    def step(self) -> None:
        raise RuntimeError("thin rotors never step")


class Reflector:
    def __init__(self, name: str):
        if not isinstance(name, str) or name not in REFLECTORS:
            raise ValueError(f"unknown reflector {name!r}")
        self.name = name
        self._map = [A.index(c) for c in REFLECTORS[name]]

    def reflect(self, i: int) -> int:
        return self._map[i]


class EntryWheel:
    """ETW: identity wiring."""

    def forward(self, i: int) -> int:
        return i

    backward = forward


class Plugboard:
    def __init__(self, pairs: str = ""):
        if not isinstance(pairs, str):
            raise TypeError("plugboard must be a str")
        self._map = list(range(26))
        tokens = pairs.split()
        if len(tokens) > 13:
            raise ValueError("plugboard allows at most 13 pairs")
        seen: set[str] = set()
        for tok in tokens:
            if len(tok) != 2 or not (tok.isascii() and tok.isalpha()):
                raise ValueError(
                    f"plug pair must be exactly two ASCII letters, got {tok!r}"
                )
            a, b = tok = tok.upper()
            if a == b:
                raise ValueError(f"cannot plug {a} to itself")
            if a in seen or b in seen:
                raise ValueError(f"letter used twice in plugboard: {tok!r}")
            seen.update((a, b))
            self._map[A.index(a)], self._map[A.index(b)] = A.index(b), A.index(a)

    def swap(self, i: int) -> int:
        return self._map[i]
