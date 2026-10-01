# `wiring.py`: the wiring tables

[Back to the code guide](README.md)

## What it's for

This file holds the real wiring of the historical Enigma parts, copied from the [Crypto Museum wiring tables](https://www.cryptomuseum.com/crypto/enigma/wiring.htm). It has no functions or classes, only three dictionaries. Keeping the data separate means the rest of the code never has long strings of letters mixed into its logic.

## How to read a wiring string

Each wiring is a 26-letter string. **The letter at spot N is where letter N goes.**

```
Input:     ABCDEFGHIJKLMNOPQRSTUVWXYZ
Rotor I:   EKMFLGDQVZNTOWYHXUSPAIBRCJ
```

So for rotor I, A→E, B→K, C→M, and so on. This is the mapping when the rotor is at position A with ring setting A. `components.py` handles how it changes as the rotor turns.

## `ROTORS`

The eight normal rotors, I to VIII. Each entry is a pair: `(wiring, notch letters)`.

```python
ROTORS["I"]  == ("EKMFLGDQVZNTOWYHXUSPAIBRCJ", "Q")
ROTORS["VI"] == ("JPGVOUMFYQBENHZRDKASXLICTW", "ZM")
```

The notch letters say when this rotor makes the next rotor turn. Rotor I does it when Q shows in its window. Rotors VI, VII and VIII have two notches (Z and M), so they turn the next rotor twice per full turn.

- **Enigma I** (army and air force) can use rotors I–V.
- **Enigma M4** (navy) can use all eight.

## `THIN`

The two thin "Greek" wheels used only in the M4: `Beta` and `Gamma`. They have no notch, because they never turn while typing, so each entry is just the wiring string.

```python
THIN["Beta"] == "LEYJVCNIXWPBQMDRTAKZGFUHOS"
```

## `REFLECTORS`

The reflectors, which bounce the signal back through the rotors.

| Name | Used in |
|---|---|
| `A`, `B`, `C` | Enigma I |
| `B-thin`, `C-thin` | Enigma M4 (thinner, to make room for the Greek wheel) |

Every reflector wiring pairs letters up. In reflector B, A→Y and Y→A. No letter ever maps to itself.
