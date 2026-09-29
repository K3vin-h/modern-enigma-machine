import string

import pytest

from enigma.components import EntryWheel, Plugboard, Reflector, Rotor, ThinRotor
from enigma.wiring import REFLECTORS, ROTORS, THIN

A = string.ascii_uppercase
ALL_ROTORS = list(ROTORS) + list(THIN)


def make(name, ring="A", pos="A"):
    return ThinRotor(name, ring, pos) if name in THIN else Rotor(name, ring, pos)


# --- wiring data ---------------------------------------------------------


def test_wiring_names_are_exactly_the_expected_sets():
    assert set(ROTORS) == {"I", "II", "III", "IV", "V", "VI", "VII", "VIII"}
    assert set(THIN) == {"Beta", "Gamma"}
    assert set(REFLECTORS) == {"A", "B", "C", "B-thin", "C-thin"}


@pytest.mark.parametrize("name", list(ROTORS))
def test_rotor_wiring_is_a_permutation(name):
    assert sorted(ROTORS[name][0]) == list(A)


@pytest.mark.parametrize("name", list(THIN))
def test_thin_wiring_is_a_permutation(name):
    assert sorted(THIN[name]) == list(A)


@pytest.mark.parametrize("name", list(REFLECTORS))
def test_reflector_is_fixed_point_free_involution(name):
    w = REFLECTORS[name]
    assert sorted(w) == list(A)
    for i in range(26):
        j = A.index(w[i])
        assert j != i
        assert A.index(w[j]) == i


@pytest.mark.parametrize(
    "name, turnover",
    [
        ("I", "Q"),
        ("II", "E"),
        ("III", "V"),
        ("IV", "J"),
        ("V", "Z"),
        ("VI", "ZM"),
        ("VII", "ZM"),
        ("VIII", "ZM"),
    ],
)
def test_turnover_letters(name, turnover):
    assert set(ROTORS[name][1]) == set(turnover)


# --- rotor mapping -------------------------------------------------------


@pytest.mark.parametrize("name", ALL_ROTORS)
@pytest.mark.parametrize("ring", ["A", "B", "Z"])
def test_backward_inverts_forward_everywhere(name, ring):
    for pos in A:
        r = make(name, ring, pos)
        for i in range(26):
            assert r.backward(r.forward(i)) == i


def test_rotor_i_spot_values():
    assert Rotor("I", "A", "A").forward(0) == A.index("E")
    assert Rotor("I", "A", "B").forward(0) == A.index("J")


def test_ring_b_at_b_equals_ring_a_at_a():
    a, b = Rotor("I", "A", "A"), Rotor("I", "B", "B")
    assert [a.forward(i) for i in range(26)] == [b.forward(i) for i in range(26)]


# --- rotor stepping ------------------------------------------------------


def test_step_advances_and_wraps():
    r = Rotor("I", "A", "A")
    r.step()
    assert r.position == "B"
    z = Rotor("I", "A", "Z")
    z.step()
    assert z.position == "A"


def test_turnover_is_on_window_letter_regardless_of_ring():
    for ring in "AZ":
        for pos in A:
            assert Rotor("I", ring, pos).at_turnover() == (pos == "Q")


@pytest.mark.parametrize("name", ["VI", "VII", "VIII"])
def test_double_notch_rotors(name):
    for pos in A:
        assert Rotor(name, "A", pos).at_turnover() == (pos in "ZM")


# --- thin rotor ----------------------------------------------------------


@pytest.mark.parametrize("name", list(THIN))
def test_thin_never_turns_over_and_cannot_step(name):
    for pos in A:
        assert ThinRotor(name, "A", pos).at_turnover() is False
    with pytest.raises(RuntimeError):
        ThinRotor(name, "A", "A").step()


def test_thin_mapping_honours_ring_and_position():
    t = ThinRotor("Beta", "B", "C")
    assert ThinRotor("Beta", "A", "A").forward(0) == A.index("L")
    # d = 2 - 1 = 1: wiring[1] = E (4), minus d = 3
    assert t.forward(0) == 3


# --- constructor errors --------------------------------------------------


@pytest.mark.parametrize(
    "args",
    [
        ("XX", "A", "A"),
        ("i", "A", "A"),
        ("I", "a", "A"),
        ("I", "A", "a"),
        ("I", "1", "A"),
        ("I", "AB", "A"),
        ("I", "", "A"),
        ("I", "A", ""),
    ],
)
def test_rotor_rejects_bad_arguments(args):
    with pytest.raises(ValueError):
        Rotor(*args)


@pytest.mark.parametrize("args", [("I", 1, "A"), ("I", "A", 1), (1, "A", "A")])
def test_rotor_rejects_non_str(args):
    with pytest.raises(TypeError):
        Rotor(*args)


def test_rotor_ring_b_pinned_values():
    # ring B, position A: d = -1. forward(A): wiring[25]=J(9), 9+1 = 10 (K)
    r = Rotor("I", "B", "A")
    assert r.forward(0) == 10
    # backward(K): inverse[(10-1)%26] -> index of J(9) is 25; 25+1 = 26 % 26 = 0
    assert r.backward(10) == 0


def test_rotor_backward_spot_value():
    # rotor I wires contact A to E, so backward(E) at position A, ring A is A
    assert Rotor("I", "A", "A").backward(A.index("E")) == 0


def test_ring_b_at_b_equals_ring_a_at_a_backward_too():
    a, b = Rotor("I", "A", "A"), Rotor("I", "B", "B")
    assert [a.backward(i) for i in range(26)] == [b.backward(i) for i in range(26)]


def test_thin_rotor_rejects_regular_names():
    with pytest.raises(ValueError):
        ThinRotor("I", "A", "A")


# --- reflector / entry wheel --------------------------------------------


@pytest.mark.parametrize("name", list(REFLECTORS))
def test_reflect_is_involution(name):
    r = Reflector(name)
    assert all(r.reflect(r.reflect(i)) == i and r.reflect(i) != i for i in range(26))


def test_reflector_unknown_name():
    with pytest.raises(ValueError):
        Reflector("D")


def test_entry_wheel_is_identity():
    e = EntryWheel()
    assert all(e.forward(i) == i and e.backward(i) == i for i in range(26))


# --- plugboard -----------------------------------------------------------


def test_plugboard_empty_is_identity():
    p = Plugboard("")
    assert all(p.swap(i) == i for i in range(26))


def test_plugboard_swaps_pairs_and_leaves_rest():
    p = Plugboard("ab cd")
    assert (p.swap(0), p.swap(1), p.swap(2), p.swap(3), p.swap(4)) == (1, 0, 3, 2, 4)


def test_plugboard_thirteen_pairs_is_involution():
    pairs = " ".join(f"{A[i]}{A[i + 1]}" for i in range(0, 26, 2))
    p = Plugboard(pairs)
    assert all(p.swap(p.swap(i)) == i and p.swap(i) != i for i in range(26))


def test_plugboard_whitespace_only_means_no_pairs():
    assert all(Plugboard("  \t ").swap(i) == i for i in range(26))


@pytest.mark.parametrize(
    "bad",
    [
        "AA",
        "AB AC",
        "AB BA",
        "A",
        "ABC",
        "A1",
        "AÉ",
        "ﬁ",  # ligature that upper-cases to "FI"
        "ſA",  # long s upper-cases to "S"
        "ıA",  # dotless i upper-cases to "I"
        "ß",  # sharp s upper-cases to "SS"
    ],
)
def test_plugboard_rejects_bad_input(bad):
    with pytest.raises(ValueError):
        Plugboard(bad)


def test_plugboard_accepts_thirteen_pairs_with_trailing_space():
    Plugboard(" ".join(f"{A[i]}{A[i + 1]}" for i in range(0, 26, 2)) + " ")


def test_plugboard_rejects_non_str():
    with pytest.raises(TypeError):
        Plugboard(1)


def test_plugboard_accepts_lowercase_pairs():
    assert Plugboard("ab").swap(0) == 1


def test_plugboard_rejects_fourteen_pairs():
    pairs = [f"{A[i]}{A[i + 1]}" for i in range(0, 26, 2)] + ["AB"]
    with pytest.raises(ValueError):
        Plugboard(" ".join(pairs))
