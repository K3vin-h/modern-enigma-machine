# `components.py`: the parts of the machine

[Back to the code guide](README.md)

## What it's for

This file builds each physical part of an Enigma as a Python class: rotors, the thin Greek wheel, the reflector, the entry wheel and the plugboard. Each part takes a letter (as a number 0–25) and gives back another. The parts don't know about each other; `machine.py` connects them.

**Errors when building a part.** Each part checks its settings when you create it:
- `TypeError`: wrong kind of value, like the number `3` instead of a string.
- `ValueError`: right kind but a bad value, like a rotor called `"IX"`, which doesn't exist.

Once a part is built, the methods that move a signal through it don't check their input again. They trust `machine.py` to pass valid numbers, which keeps them fast.

## `_letter(value, what)`: a letter setting to a number

A small helper used for ring and position settings. It turns `"C"` into `2`, and raises an error if you pass anything other than one capital A–Z.

| You pass | You get |
|---|---|
| `"C"` | `2` |
| `"ab"`, `""`, `"c"`, `"é"` | `ValueError` |
| `3` | `TypeError` |

`what` is just a label (`"ring"` or `"position"`) so the error message says which setting was wrong.

## `Rotor`: the spinning wheels

A rotor is a wheel with scrambled wiring inside. It turns as you type, so pressing the same key twice gives different letters.

```python
r = Rotor("I", "A", "Q")   # rotor I, ring A, Q showing in the window
```

Each rotor has two settings:
- **Position**: the letter showing in the window. It changes as you type.
- **Ring**: rotates the wiring inside the wheel. It's set once and doesn't change.

**When it's built,** the rotor looks up its wiring in `wiring.py`, stores it as a list of numbers, and also builds the **reverse** wiring. If A goes to E on the way in, E must go back to A on the way out.

**What really matters is position minus ring.** The code calls this the offset. A rotor at position B with ring B behaves exactly like one at A with ring A, because the two shifts cancel out.

### `forward(i)` and `backward(i)`

`forward` is the trip in, toward the reflector. `backward` is the trip back out. Both do three things:
1. shift the input to match how far the wheel is turned;
2. follow the wire;
3. shift back so the next part gets the right number.

Rotor I, pressing A:

| Ring / position | `forward` gives |
|---|---|
| A / A | E |
| A / B | J (one turn changes the answer) |
| B / A | K |
| B / B | E (ring and position cancel) |

`backward` exactly undoes `forward`: at A/A, forward turns A into E, and backward turns E into A.

### `position`, `at_turnover()` and `step()`

- `position` gives the window letter, like `"Q"`.
- `at_turnover()` is True when the window shows a notch letter, meaning the next rotor should turn. Rotor I at Q → True; at R → False. Rotors VI–VIII return True at both Z and M.
- `step()` turns the rotor one click. After Z it wraps around to A.

The ring setting never moves the notch. The notch is always checked against the window letter, just like the real machine.

## `ThinRotor`: the M4's Greek wheel

The navy's M4 had a fourth, thinner wheel (Beta or Gamma) next to the reflector. It scrambles letters like a normal rotor but **never turns while you type.**

`ThinRotor` is a kind of `Rotor`, so it reuses all the rotor code and changes three things:
- it looks up its wiring in the `THIN` table, so `ThinRotor("I", …)` is an error;
- `at_turnover()` always returns False, because it has no notch;
- `step()` always raises `RuntimeError`. If the program ever tries to turn this wheel, that's a bug, and it should fail loudly instead of giving wrong output.

```python
ThinRotor("Beta", "A", "A").forward(0)   # 11, which is L
```

## `Reflector`: bounces the signal back

The reflector sits at the end of the rotors and sends the signal back through them. It doesn't turn and has no ring.

```python
Reflector("B").reflect(0)    # 24 (A → Y)
Reflector("B").reflect(24)   # 0  (Y → A)
```

Two features make Enigma work the way it does:
- **No letter maps to itself.** That's why Enigma can never encrypt a letter as itself, a weakness the codebreakers used.
- **It works the same both ways.** That's why typing the ciphertext with the same settings gives back the original message.

## `EntryWheel`: passes the signal straight through

On military Enigmas the entry wheel connects the plugboard to the rotors with no scrambling, so A stays A. `forward(7)` and `backward(7)` both return 7. It's included so the signal path matches the real machine.

## `Plugboard`: the cables on the front

Cables swap pairs of letters. If A and T are connected, A becomes T and T becomes A. Letters with no cable stay the same.

```python
p = Plugboard("at bl")
p.swap(0)    # 19 (A → T)
p.swap(19)   # 0  (T → A)
p.swap(2)    # 2  (C has no cable)
```

Pairs are separated by spaces, and upper or lower case both work. The plugboard rejects anything a real one couldn't do:

| Input | Why it's rejected |
|---|---|
| 14 or more pairs | 26 letters only make 13 pairs |
| `"AA"` | a cable can't connect a letter to itself |
| `"AB BC"` | B can't have two cables |
| `"A1"`, `"ABC"` | each pair must be exactly two letters |
| `"ﬁ"` | looks like "fi" but is one special character |

The last one is a real trap. `"ﬁ"` turns into `"FI"` when made uppercase, so the code checks each pair *before* converting it to capitals.
