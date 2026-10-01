"""Tests for the Enigma machine: stepping, signal path, model rules and trace.

Expected values come from the plan, the pinned fixture or hand calculation,
never from the code under test.
"""

import dataclasses
import json
import random
import string
from pathlib import Path

import pytest

import enigma.machine as machine_module
from enigma.machine import Enigma, EnigmaI, EnigmaM4, Trace
from enigma.text import normalize

A = string.ascii_uppercase
FIXTURE = json.loads((Path(__file__).parent / "data" / "m4_reference.json").read_text())
# Turnover notches from the plan, independent of wiring.py.
NOTCHES = {
    "I": "Q",
    "II": "E",
    "III": "V",
    "IV": "J",
    "V": "Z",
    "VI": "ZM",
    "VII": "ZM",
    "VIII": "ZM",
}
PLUGS_10 = "AB CD EF GH IJ KL MN OP QR ST"
PLUGS_13 = "AB CD EF GH IJ KL MN OP QR ST UV WX YZ"


def enigma_i(
    rotors=("I", "II", "III"), reflector="B", positions="AAA", rings=None, plugboard=""
):
    return EnigmaI(list(rotors), reflector, positions, rings, plugboard)


def m4(
    rotors=("Beta", "I", "II", "III"),
    reflector="B-thin",
    positions="AAAA",
    rings=None,
    plugboard="",
):
    return EnigmaM4(list(rotors), reflector, positions, rings, plugboard)


def random_text(n, seed=7):
    rng = random.Random(seed)
    return "".join(rng.choice(A) for _ in range(n))


# --- Frozen vectors ---------------------------------------------------------

VECTORS = [
    (enigma_i, dict(reflector="A"), "HELLOWORLD", "KCUBRKIDKN"),
    (enigma_i, dict(reflector="C"), "HELLOWORLD", "XKVWSXCNHR"),
    (enigma_i, dict(reflector="B", rings="BBB"), "AAAAA", "EWTYX"),
    (enigma_i, dict(reflector="B"), "AAAAA", "BDZGO"),
    (
        m4,
        dict(
            rotors=("Gamma", "V", "VII", "VIII"),
            reflector="C-thin",
            rings="BDFH",
            positions="VJLM",
        ),
        "THEQUICKBROWNFOXJUMPSOVERTHELAZYDOG",
        "WFBMIMUDUOCLWYXRBRJVNQMBZOJLNDQPKKD",
    ),
    (
        m4,
        dict(
            rotors=("Beta", "VI", "IV", "I"),
            reflector="B-thin",
            rings="CDEF",
            positions="XAMZ",
        ),
        "THEQUICKBROWNFOXJUMPSOVERTHELAZYDOG",
        "JFOSZTIGNUWIEPXOUQTYIJWWMONMXERWJGI",
    ),
]


@pytest.mark.parametrize("make, kwargs, plain, cipher", VECTORS)
def test_frozen_vector_encrypts_and_decrypts(make, kwargs, plain, cipher):
    machine = make(**kwargs)
    assert machine.process(plain) == cipher
    machine.reset()
    assert machine.process(cipher) == plain


def fixture_machine():
    s = FIXTURE["settings"]
    return EnigmaM4(
        s["rotors"], s["reflector"], s["positions"], s["rings"], s["plugboard"]
    )


def test_reference_message_first_group():
    assert fixture_machine().process("NCZWVUSX") == "VONVONJL"


def test_reference_message_cipher_to_plain():
    assert len(FIXTURE["ciphertext"]) == 232
    assert fixture_machine().process(FIXTURE["ciphertext"]) == FIXTURE["plaintext"]


def test_reference_message_plain_to_cipher():
    assert fixture_machine().process(FIXTURE["plaintext"]) == FIXTURE["ciphertext"]


# --- Stepping ---------------------------------------------------------------

STEP_CASES = [
    ("AAA", "AAB", None),
    ("AAV", "ABW", None),  # right carry
    ("AZZ", "AZA", None),  # right wrap, no carry (III notch is V)
    ("AZV", "AAW", None),  # middle wraps on carry
    ("ZEA", "AFB", None),  # left wraps on double-step
    ("ZZZ", "ZZA", None),  # no notch involved
    ("QAA", "QAB", None),  # left at its notch never carries
    ("AEV", "BFW", None),  # simultaneous turnover: middle steps once
    ("AEV", "BFW", "BBB"),  # rings never move the turnover
    ("ADU", "ADV", None),
    ("ADV", "AEW", None),
    ("AEW", "BFX", None),
    ("ADV", "AEW", "BBB"),
    ("AEW", "BFX", "BBB"),
]


@pytest.mark.parametrize("start, expected, rings", STEP_CASES)
def test_stepping_one_keypress(start, expected, rings):
    machine = enigma_i(positions=start, rings=rings)
    machine.press("A")
    assert machine.positions == expected


@pytest.mark.parametrize("rings", [None, "BBB"])
def test_double_step_sequence_advances_middle_twice_in_a_row(rings):
    machine = enigma_i(positions="ADU", rings=rings)
    seen = []
    for _ in range(3):
        machine.press("A")
        seen.append(machine.positions)
    assert seen == ["ADV", "AEW", "BFX"]


@pytest.mark.parametrize("six", ["VI", "VII", "VIII"])
@pytest.mark.parametrize(
    "slot, start, expected",
    [
        ("right", "AAZ", "ABA"),
        ("right", "AAM", "ABN"),
        ("middle", "AZA", "BAB"),
        ("middle", "AMA", "BNB"),
    ],
)
def test_two_notch_rotors_turn_over_at_z_and_m(six, slot, start, expected):
    rotors = ("Beta", "I", "II", six) if slot == "right" else ("Beta", "I", six, "II")
    machine = m4(rotors=rotors, positions="A" + start, rings="ACDE")
    machine.press("A")
    assert machine.positions == "A" + expected


# --- M4 Greek wheel ---------------------------------------------------------


def test_greek_wheel_never_moves_and_others_follow_reference_stepping():
    rotors = ("Beta", "VI", "VII", "VIII")
    machine = m4(rotors=rotors)
    # Independent model of the three stepping wheels.
    pos = [0, 0, 0]
    notch = [set(NOTCHES[r]) for r in rotors[1:]]
    for _ in range(26**3):
        r_turn = A[pos[2]] in notch[2]
        m_turn = A[pos[1]] in notch[1]
        if m_turn:
            pos[0] = (pos[0] + 1) % 26
        if r_turn or m_turn:
            pos[1] = (pos[1] + 1) % 26
        pos[2] = (pos[2] + 1) % 26
        machine.press("A")
        assert len(machine.positions) == 4
        assert machine.positions == "A" + "".join(A[p] for p in pos)


# --- Model rules ------------------------------------------------------------

BAD_I = [
    dict(rotors=["Beta", "II", "III"]),
    dict(rotors=["I", "VI", "III"]),
    dict(rotors=["I", "II", "VIII"]),
    dict(rotors=["I", "II"], positions="AA"),
    dict(rotors=["I", "II", "III", "IV"], positions="AAAA"),
    dict(reflector="B-thin"),
    dict(reflector="Z"),
    dict(rotors=["I", "I", "III"]),
    dict(positions="AA"),
    dict(positions="AAAA"),
    dict(rings="AA"),
    dict(rings="AAAA"),
    dict(positions="AAa"),
    dict(plugboard="AA"),
]


@pytest.mark.parametrize("override", BAD_I)
def test_enigma_i_rejects(override):
    args = dict(rotors=["I", "II", "III"], reflector="B", positions="AAA")
    args.update(override)
    with pytest.raises(ValueError):
        EnigmaI(**args)


BAD_M4 = [
    dict(rotors=["I", "II", "III", "IV"]),
    dict(rotors=["Beta", "Beta", "II", "III"]),
    dict(rotors=["Beta", "Gamma", "II", "III"]),
    dict(rotors=["Beta", "I", "II", "Gamma"]),
    dict(reflector="A"),
    dict(reflector="B"),
    dict(reflector="C"),
    dict(rotors=["Beta", "I", "II"], positions="AAA"),
    dict(rotors=["Beta", "I", "II", "III", "IV"], positions="AAAAA"),
    dict(rotors=["Beta", "I", "II", "I"]),
    dict(positions="AAA"),
    dict(rings="AAAAA"),
]


@pytest.mark.parametrize("override", BAD_M4)
def test_m4_rejects(override):
    args = dict(rotors=["Beta", "I", "II", "III"], reflector="B-thin", positions="AAAA")
    args.update(override)
    with pytest.raises(ValueError):
        EnigmaM4(**args)


def test_non_str_arguments_raise_type_error():
    with pytest.raises(TypeError):
        EnigmaI(["I", "II", 3], "B", "AAA")
    with pytest.raises(TypeError):
        EnigmaI(["I", "II", "III"], None, "AAA")
    with pytest.raises(TypeError):
        EnigmaI(["I", "II", "III"], "B", ["A", "A", "A"])
    with pytest.raises(TypeError):
        EnigmaI(["I", "II", "III"], "B", "AAA", rings=["A", "A", "A"])


def test_rotors_may_be_any_iterable_including_a_one_shot_generator():
    machine = EnigmaI((r for r in ["I", "II", "III"]), "B", "AAA")
    assert machine.positions == "AAA"
    assert machine.process("AAAAA") == "BDZGO"


def test_rotors_as_a_bare_string_is_a_type_error():
    with pytest.raises(TypeError):
        EnigmaI("III", "B", "AAA")


@pytest.mark.parametrize(
    "unordered",
    [{"I", "II", "III"}, frozenset({"I", "II", "III"}), {"I": 0, "II": 0, "III": 0}],
)
def test_unordered_rotor_collections_are_a_type_error(unordered):
    with pytest.raises(TypeError):
        EnigmaI(unordered, "B", "AAA")


@pytest.mark.parametrize(
    "field, value",
    [
        ("positions", "aaa"),
        ("positions", "AA1"),
        ("positions", "AAÄ"),
        ("rings", "aaa"),
        ("rings", "AA1"),
        ("rings", "AAÄ"),
    ],
)
def test_bad_letters_are_reported_before_the_plugboard(field, value):
    args = dict(
        rotors=["I", "II", "III"], reflector="B", positions="AAA", plugboard="AA"
    )
    args[field] = value
    with pytest.raises(ValueError, match=field):
        EnigmaI(**args)


def test_later_changes_to_the_callers_rotor_list_have_no_effect():
    rotors = ["I", "II", "III"]
    machine = EnigmaI(rotors, "B", "AAA")
    rotors[0] = "V"
    machine.reset()
    assert machine.process("AAAAA") == "BDZGO"


def test_rings_none_means_all_a():
    explicit = enigma_i(rings="AAA").process("HELLOWORLD")
    assert enigma_i(rings=None).process("HELLOWORLD") == explicit
    assert m4(rings=None).process("HELLOWORLD") == m4(rings="AAAA").process(
        "HELLOWORLD"
    )


def test_base_class_cannot_be_instantiated():
    with pytest.raises(TypeError):
        Enigma(["I", "II", "III"], "B", "AAA")


# --- Equivalences -----------------------------------------------------------

ORDERS = [("I", "II", "III"), ("V", "III", "I"), ("IV", "I", "V")]


@pytest.mark.parametrize(
    "greek, thin, ukw", [("Beta", "B-thin", "B"), ("Gamma", "C-thin", "C")]
)
@pytest.mark.parametrize("order", ORDERS)
def test_greek_at_a_is_equivalent_to_enigma_i(greek, thin, ukw, order):
    text = random_text(200)
    classic = enigma_i(order, ukw, "GHZ", "BDF", PLUGS_10).process(text)
    modern = m4((greek, *order), thin, "AGHZ", "ABDF", PLUGS_10).process(text)
    assert modern == classic


def test_greek_not_at_a_is_not_equivalent():
    text = random_text(200)
    classic = enigma_i(("I", "II", "III"), "B", "GHZ", "BDF", PLUGS_10).process(text)
    shifted = m4(("Beta", "I", "II", "III"), "B-thin", "BGHZ", "ABDF", PLUGS_10)
    assert shifted.process(text) != classic


# --- Properties -------------------------------------------------------------

ROUND_TRIP = [
    (enigma_i, dict(reflector=u, plugboard=p))
    for u in "ABC"
    for p in ("", PLUGS_10, PLUGS_13)
] + [
    (m4, dict(reflector=u, plugboard=p))
    for u in ("B-thin", "C-thin")
    for p in ("", PLUGS_10, PLUGS_13)
]


@pytest.mark.parametrize("make, kwargs", ROUND_TRIP)
def test_round_trip_returns_normalized_plaintext(make, kwargs):
    machine = make(positions="QEV" if make is enigma_i else "AQEV", **kwargs)
    plain = "Meet me at 9, by the old bridge!"
    expected, _ = normalize(plain)
    cipher = machine.process(plain)
    machine.reset()
    assert machine.process(cipher) == expected


def test_no_letter_ever_maps_to_itself_for_random_settings():
    rng = random.Random(1234)
    for _ in range(500):
        if rng.random() < 0.5:
            machine = EnigmaI(
                rng.sample(["I", "II", "III", "IV", "V"], 3),
                rng.choice("ABC"),
                "".join(rng.choice(A) for _ in range(3)),
                "".join(rng.choice(A) for _ in range(3)),
                _random_plugs(rng),
            )
        else:
            machine = EnigmaM4(
                [rng.choice(["Beta", "Gamma"])]
                + rng.sample(["I", "II", "III", "IV", "V", "VI", "VII", "VIII"], 3),
                rng.choice(["B-thin", "C-thin"]),
                "".join(rng.choice(A) for _ in range(4)),
                "".join(rng.choice(A) for _ in range(4)),
                _random_plugs(rng),
            )
        for letter in A:
            machine.reset()
            assert machine.press(letter) != letter


def _random_plugs(rng):
    letters = rng.sample(A, 26)
    pairs = rng.randint(0, 13)
    return " ".join(letters[2 * i] + letters[2 * i + 1] for i in range(pairs))


def test_chunks_without_reset_equal_the_whole():
    whole = enigma_i(positions="ADU").process("ABCD")
    machine = enigma_i(positions="ADU")
    assert machine.process("AB") + machine.process("CD") == whole


@pytest.mark.parametrize("make", [enigma_i, m4])
def test_reset_restores_every_slot(make):
    machine = make(positions="QEV" if make is enigma_i else "BQEV")
    start = machine.positions
    machine.process("A" * 300)
    assert machine.positions != start
    machine.reset()
    assert machine.positions == start


# --- Input edges ------------------------------------------------------------


@pytest.mark.parametrize("text", ["", "123 !!", "é ß"])
def test_process_without_letters_returns_empty_and_does_not_step(text):
    machine = enigma_i(positions="ADU")
    assert machine.process(text) == ""
    assert machine.positions == "ADU"


@pytest.mark.parametrize(
    "bad, error",
    [
        ("a", ValueError),
        ("AB", ValueError),
        ("", ValueError),
        ("É", ValueError),
        ("1", ValueError),
        (1, TypeError),
        (None, TypeError),
    ],
)
def test_press_rejects_bad_input_without_stepping(bad, error):
    machine = enigma_i(positions="ADU")
    with pytest.raises(error):
        machine.press(bad)
    assert machine.positions == "ADU"


@pytest.mark.parametrize("method", ["process", "process_traced"])
def test_non_str_text_raises_type_error_without_stepping(method):
    machine = enigma_i(positions="ADU")
    with pytest.raises(TypeError):
        getattr(machine, method)(None)
    assert machine.positions == "ADU"


def test_ten_thousand_letters_round_trip():
    text = random_text(10_000, seed=3)
    machine = m4(positions="BQEV", plugboard=PLUGS_10)
    cipher = machine.process(text)
    machine.reset()
    assert machine.process(cipher) == text


# --- Trace ------------------------------------------------------------------

EXAMPLE_STAGES = (
    ("plug", "A", "T"),
    ("ETW", "T", "T"),
    ("R(I)", "T", "D"),
    ("M(IV)", "D", "A"),
    ("L(II)", "A", "S"),
    ("thin(Beta)", "S", "R"),
    ("UKW(B-thin)", "R", "X"),
    ("thin(Beta)", "X", "E"),
    ("L(II)", "E", "K"),
    ("M(IV)", "K", "B"),
    ("R(I)", "B", "J"),
    ("ETW", "J", "J"),
    ("plug", "J", "G"),
)


def test_trace_matches_plan_for_first_letter_of_example_key():
    output, traces = fixture_machine().process_traced("A")
    assert output == "G"
    (trace,) = traces
    assert trace.letter == "A"
    assert trace.output == "G"
    assert (trace.before, trace.after) == ("VJNA", "VJNB")
    assert trace.stepped == ("R",)
    assert trace.stages == EXAMPLE_STAGES
    assert len(trace.stages) == 13


def test_enigma_i_trace_has_eleven_stages_and_no_thin():
    _, (trace,) = enigma_i().process_traced("A")
    assert len(trace.stages) == 11
    assert not any(label.startswith("thin") for label, _, _ in trace.stages)
    assert trace.stages[0][0] == "plug" and trace.stages[-1][0] == "plug"


@pytest.mark.parametrize(
    "start, stepped",
    [
        ("AAA", ("R",)),
        ("AAV", ("M", "R")),
        ("ADV", ("M", "R")),
        ("AEA", ("L", "M", "R")),  # double-step
        ("AEV", ("L", "M", "R")),  # simultaneous turnover
    ],
)
def test_trace_reports_which_slots_stepped(start, stepped):
    machine = enigma_i(positions=start)
    _, (trace,) = machine.process_traced("A")
    assert trace.before == start
    assert trace.after == machine.positions
    assert trace.stepped == stepped


def test_traced_and_untraced_runs_agree():
    text = random_text(500)
    plain, traced = m4(positions="AQEV"), m4(positions="AQEV")
    output, traces = traced.process_traced(text)
    assert output == plain.process(text)
    assert traced.positions == plain.positions
    assert len(traces) == 500
    assert "".join(t.output for t in traces) == output


def test_untraced_path_builds_no_trace_objects(monkeypatch):
    built = []

    def counting(*args, **kwargs):
        built.append(1)
        return Trace(*args, **kwargs)

    monkeypatch.setattr(machine_module, "Trace", counting)
    m4().process("HELLOWORLD")
    m4().press("A")
    assert built == []
    m4().process_traced("HELLOWORLD")
    assert len(built) == 10


def test_trace_snapshots_are_immutable_and_independent_of_later_presses():
    machine = enigma_i(positions="ADU")
    _, (first,) = machine.process_traced("A")
    snapshot = dataclasses.astuple(first)
    machine.process("ABCDEFGH")
    assert dataclasses.astuple(first) == snapshot
    with pytest.raises(dataclasses.FrozenInstanceError):
        first.output = "X"


def test_traced_empty_input_returns_nothing_and_does_not_step():
    machine = enigma_i(positions="ADU")
    assert machine.process_traced("") == ("", [])
    assert machine.process_traced("42") == ("", [])
    assert machine.positions == "ADU"
