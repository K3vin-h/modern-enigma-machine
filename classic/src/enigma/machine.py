"""The Enigma machine: model rules, rotor stepping and the signal path.

Rotors are named left to right, as they sit in the machine. ``EnigmaI`` and
``EnigmaM4`` only differ in the rule constants they carry; all behavior lives
in ``Enigma``.
"""

import string
from collections.abc import Iterable, Mapping
from collections.abc import Set as AbstractSet
from dataclasses import dataclass

from .components import EntryWheel, Plugboard, Reflector, Rotor, ThinRotor
from .text import normalize

A = string.ascii_uppercase

# Stepping slots, right to left; M4's extra Greek wheel is labelled "thin".
_SLOT_LABELS = ("R", "M", "L", "thin")


@dataclass(frozen=True)
class Trace:
    """Immutable record of one keypress.

    Attributes:
        letter: The letter typed.
        output: The letter lit up.
        before: Window letters before the rotors moved.
        after: Window letters after the rotors moved.
        stepped: Slots that moved, from ``("L", "M", "R")`` in that order.
        stages: ``(label, input letter, output letter)`` per stage, in
            signal order, including both entry-wheel and both plugboard passes.
    """

    letter: str
    output: str
    before: str
    after: str
    stepped: tuple[str, ...]
    stages: tuple[tuple[str, str, str], ...]


class Enigma:
    """Common machine behavior; use ``EnigmaI`` or ``EnigmaM4``.

    Attributes:
        SLOTS: Number of rotors the model takes.
        REFLECTORS: Reflector names legal for the model.
        ROTORS: Rotor names legal in the stepping slots.
        GREEK: Thin rotor names legal in slot 0, or empty if the model has none.
    """

    SLOTS: int = 0
    REFLECTORS: tuple[str, ...] = ()
    ROTORS: tuple[str, ...] = ()
    GREEK: tuple[str, ...] = ()

    def __init__(
        self,
        rotors: Iterable[str],
        reflector: str,
        positions: str,
        rings: str | None = None,
        plugboard: str = "",
    ) -> None:
        """Build a machine at its start positions.

        Args:
            rotors: Rotor names, left to right (Greek wheel first on M4).
                Any ordered iterable (list, tuple, generator); it is copied.
            reflector: Reflector name.
            positions: One uppercase window letter per rotor, left to right.
            rings: One uppercase ring-setting letter per rotor; ``None``
                means all A.
            plugboard: Whitespace-separated plug pairs, e.g. ``"AT BL"``;
                case is ignored.

        Raises:
            TypeError: If an argument has the wrong type, or ``rotors`` is a
                str, set or mapping.
            ValueError: On the first invalid argument, checked in the order
                reflector, rotors, positions, rings, plugboard: an illegal
                name for the model or slot, a repeated rotor, a wrong
                length, a character outside uppercase A-Z, or a bad plug.
        """
        if not self.SLOTS:
            raise TypeError("instantiate EnigmaI or EnigmaM4, not Enigma")
        if rings is None:
            rings = "A" * self.SLOTS
        for what, value in (
            ("reflector", reflector),
            ("positions", positions),
            ("rings", rings),
        ):
            if not isinstance(value, str):
                raise TypeError(f"{what} must be a str")
        # A str would split into letters; sets and dicts have no slot order.
        if isinstance(rotors, (str, AbstractSet, Mapping)):
            raise TypeError("rotors must be an ordered list of names")
        if reflector not in self.REFLECTORS:
            raise ValueError(f"reflector {reflector!r} is not legal for this model")
        # Copy once: a generator can only be read once, and the caller's
        # list must not be able to change the machine afterwards.
        names = list(rotors)
        self._check_rotors(names)
        for what, value in (("positions", positions), ("rings", rings)):
            if len(value) != self.SLOTS:
                raise ValueError(f"{what} needs {self.SLOTS} letters, got {len(value)}")
            # Checked here, not left to Rotor, so this error precedes the
            # plugboard's. No case folding: config.py normalizes case.
            if any(c not in A for c in value):
                raise ValueError(f"{what} must be uppercase A-Z, got {value!r}")

        self._names = names
        self._rings = rings
        self._start = positions
        self._reflector = Reflector(reflector)
        self._plugboard = Plugboard(plugboard)
        self._etw = EntryWheel()
        self._build()

    def _check_rotors(self, names: list[str]) -> None:
        """Enforce rotor count, per-slot legality and uniqueness.

        Raises:
            TypeError: If a name is not a ``str``.
            ValueError: On a wrong count, an illegal name or a repeat.
        """
        if len(names) != self.SLOTS:
            raise ValueError(f"need {self.SLOTS} rotors, got {len(names)}")
        for i, name in enumerate(names):
            if not isinstance(name, str):
                raise TypeError("rotor names must be str")
            allowed = self.GREEK if self.GREEK and i == 0 else self.ROTORS
            if name not in allowed:
                raise ValueError(f"rotor {name!r} is not legal in slot {i}")
        if len(set(names)) != len(names):
            raise ValueError("a rotor can only be used once")

    def _build(self) -> None:
        """Create fresh rotors at the start positions and the signal path."""
        self._rotors = [
            (ThinRotor if self.GREEK and i == 0 else Rotor)(name, ring, pos)
            for i, (name, ring, pos) in enumerate(
                zip(self._names, self._rings, self._start)
            )
        ]
        # Right-to-left order: the order the signal meets the rotors.
        inbound = list(zip(_SLOT_LABELS, reversed(self._rotors)))
        self._path = (
            [("plug", self._plugboard.swap), ("ETW", self._etw.forward)]
            + [(f"{slot}({rotor.name})", rotor.forward) for slot, rotor in inbound]
            + [(f"UKW({self._reflector.name})", self._reflector.reflect)]
            + [
                (f"{slot}({rotor.name})", rotor.backward)
                for slot, rotor in reversed(inbound)
            ]
            + [("ETW", self._etw.backward), ("plug", self._plugboard.swap)]
        )

    @property
    def positions(self) -> str:
        """Window letters, left to right (Greek wheel first on M4)."""
        return "".join(r.position for r in self._rotors)

    def reset(self) -> None:
        """Return every rotor, including the Greek wheel, to its start position."""
        self._build()

    def _step(self) -> tuple[str, ...]:
        """Advance the rotors as before a keypress; return the slots that moved.

        Both turnover flags are read from the window letters before anything
        moves, so the middle rotor steps once even when both apply, and it
        double-steps when it sits on its own notch.
        """
        left, middle, right = self._rotors[-3:]
        r_turn, m_turn = right.at_turnover(), middle.at_turnover()
        stepped = []
        if m_turn:
            left.step()
            stepped.append("L")
        if r_turn or m_turn:
            middle.step()
            stepped.append("M")
        right.step()
        stepped.append("R")
        return tuple(stepped)

    def _encipher(
        self, i: int, stages: list[tuple[str, str, str]] | None = None
    ) -> int:
        """Send contact ``i`` through the machine; record stages if asked."""
        for label, wire in self._path:
            j = wire(i)
            if stages is not None:
                stages.append((label, A[i], A[j]))
            i = j
        return i

    def press(self, ch: str) -> str:
        """Type one letter: step the rotors, then return the lit letter.

        Raises:
            TypeError: If ``ch`` is not a ``str``.
            ValueError: If ``ch`` is not a single letter A-Z. Nothing moves.
        """
        if not isinstance(ch, str):
            raise TypeError("press() needs a str")
        if len(ch) != 1 or ch not in A:
            raise ValueError(f"press() needs one letter A-Z, got {ch!r}")
        return self._press(ch)

    def _press(self, ch: str) -> str:
        """``press`` without validation, for already-normalized letters."""
        self._step()
        return A[self._encipher(A.index(ch))]

    def process(self, text: str) -> str:
        """Encipher ``text`` from the current rotor state.

        The whole input is normalized first (see ``text.normalize``), so the
        result is ungrouped uppercase A-Z. Nothing resets automatically.

        Raises:
            TypeError: If ``text`` is not a ``str``; no state changes.
        """
        letters, _ = normalize(text)
        return "".join(self._press(c) for c in letters)

    def process_traced(self, text: str) -> tuple[str, list[Trace]]:
        """Like ``process`` but also return one ``Trace`` per letter.

        Raises:
            TypeError: If ``text`` is not a ``str``; no state changes.
        """
        letters, _ = normalize(text)
        out: list[str] = []
        traces: list[Trace] = []
        for c in letters:
            before = self.positions
            stepped = self._step()
            stages: list[tuple[str, str, str]] = []
            lit = A[self._encipher(A.index(c), stages)]
            out.append(lit)
            traces.append(Trace(c, lit, before, self.positions, stepped, tuple(stages)))
        return "".join(out), traces


class EnigmaI(Enigma):
    """Army/Air Force Enigma I: three rotors from I-V and UKW A, B or C."""

    SLOTS = 3
    REFLECTORS = ("A", "B", "C")
    ROTORS = ("I", "II", "III", "IV", "V")


class EnigmaM4(Enigma):
    """Naval Enigma M4: Beta/Gamma, three rotors from I-VIII, thin UKW B or C."""

    SLOTS = 4
    REFLECTORS = ("B-thin", "C-thin")
    ROTORS = ("I", "II", "III", "IV", "V", "VI", "VII", "VIII")
    GREEK = ("Beta", "Gamma")
