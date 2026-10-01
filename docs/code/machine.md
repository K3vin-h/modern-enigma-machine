# `machine.py`: the whole machine

[Back to the code guide](README.md)

## What it's for

This file connects the parts from [`components.py`](components.md) into a working Enigma. It decides which rotors turn on each key press, sends the signal through every part in the right order, and can record each step for teaching.

It has four classes:

| Class | What it is |
|---|---|
| `Enigma` | All the shared behaviour. You don't use it directly. |
| `EnigmaI` | The army and air force machine: 3 rotors. |
| `EnigmaM4` | The navy machine: a Greek wheel plus 3 rotors. |
| `Trace` | A record of what happened on one key press. |

## Building a machine

```python
from enigma.machine import EnigmaI, EnigmaM4

m  = EnigmaI(["I", "II", "III"], "B", "AAA")
m4 = EnigmaM4(["Beta", "II", "IV", "I"], "B-thin", "AAAA", rings="AAAV",
              plugboard="AT BL DF GJ HM NW OP QY RZ VX")
```

The settings are:
- **rotors**: rotor names, **left to right** as they sit in the machine. On the M4 the Greek wheel comes first.
- **reflector**: the reflector name.
- **positions**: the starting window letters, one per rotor, left to right.
- **rings**: one ring letter per rotor. Leave it out and all rings are A.
- **plugboard**: cable pairs like `"AT BL"`. Leave it out for no cables.

### What each model allows

`EnigmaI` and `EnigmaM4` contain no code of their own. They only list the rules for that model, and `Enigma` does all the work using those rules.

| | Enigma I | Enigma M4 |
|---|---|---|
| Number of rotors | 3 | 4 |
| Reflectors | A, B, C | B-thin, C-thin |
| Rotors | I–V | I–VIII |
| Greek wheel (first slot) | none | Beta or Gamma |

If you try `Enigma(...)` directly, you get a `TypeError` telling you to pick a model.

### Checking the settings

The machine checks every setting before building anything, and stops at the first problem:

| Bad setting | Error message |
|---|---|
| `["I", "I", "III"]` | a rotor can only be used once |
| `["I", "II", "VI"]` on Enigma I | rotor 'VI' is not legal in slot 2 |
| reflector `"B-thin"` on Enigma I | reflector 'B-thin' is not legal for this model |
| positions `"AA"` | positions needs 3 letters, got 2 |
| positions `"aaa"` | positions must be uppercase A-Z, got 'aaa' |
| rotors `"I II III"` (one string) | rotors must be an ordered list of names |

The last one is a `TypeError`. A plain string isn't allowed because Python would split it into single characters. Sets and dictionaries aren't allowed because they have no reliable order, and rotor order matters.

The rotor list is also **copied** when the machine is built. If you change your list afterwards, the machine isn't affected.

## How a key press works

Each key press happens in two stages: **first the rotors turn, then the signal goes through.** The order matters; the real machine turns its rotors as the key goes down, before the lamp lights.

### Stage 1: turning the rotors (`_step`)

Only the three right-hand rotors ever turn. Call them L (left), M (middle) and R (right).

1. **R always turns.**
2. **M turns** if R is at its notch, *or* if M itself is at its notch.
3. **L turns** if M is at its notch.

The code checks both notches **before** anything moves, which is how the real machine behaves too.

Rule 2's second half is the famous **double step**: when the middle rotor reaches its own notch, it turns again on the very next key press, along with the left rotor. With rotors I, II, III:

| Before | After | Which turned | Why |
|---|---|---|---|
| ADU | ADV | R | normal step |
| ADV | AEW | M, R | R was at its notch (V) |
| AEW | BFX | L, M, R | M was at its notch (E), so it double-steps and pushes L |

The middle rotor moved D → E → F on two key presses in a row. That's the double step.

### Stage 2: the signal path (`_build` and `_encipher`)

When the machine is built, it makes a list of every part the signal passes through, in order. Each key press then walks the list, feeding each part's output into the next:

```
plugboard → entry wheel → R → M → L → (Greek wheel on M4)
   → reflector
   → (Greek wheel on M4) → L → M → R → entry wheel → plugboard → lamp
```

Here is the real path for pressing A on Enigma I, rotors I-II-III, reflector B, starting at AAA:

| Part | In | Out |
|---|---|---|
| plug | A | A |
| ETW | A | A |
| R(III) | A | C |
| M(II) | C | D |
| L(I) | D | F |
| UKW(B) | F | S |
| L(I) | S | S |
| M(II) | S | E |
| R(III) | E | B |
| ETW | B | B |
| plug | B | B |

Pressing A lights up **B**. Before the signal went through, R had already turned from A to B, so the window shows AAB.

## Using the machine

### `press(ch)`: one key
```python
m = EnigmaI(["I", "II", "III"], "B", "AAA")
m.press("A")   # 'B'
```
It must be exactly one capital A–Z. Anything else raises an error and **nothing turns**.

### `process(text)`: a whole message
```python
m = EnigmaI(["I", "II", "III"], "B", "AAA")
m.process("AAAAA")   # 'BDZGO'
m.positions          # 'AAF'
```
The text is cleaned up first with [`normalize`](text.md), so spaces and punctuation are dropped and lowercase is fine. The output is one long string of capitals; use [`group5`](text.md) to split it into fives.

The machine **remembers where it stopped.** Calling `process` again carries on from there, just like typing more on the real machine.

### `reset()`: back to the start
```python
m.reset()
m.positions          # 'AAA'
m.process("BDZGO")   # 'AAAAA'
```
Puts every rotor back at its starting position. Running the ciphertext through with the same starting settings gives back the original message.

### `positions`: what the windows show
`m.positions` gives the window letters, left to right, like `'AAF'`. On the M4 the Greek wheel's letter comes first.

## `Trace` and `process_traced`: seeing inside

`process_traced(text)` does the same as `process`, but also returns one `Trace` per letter, saying exactly what happened:

| Field | Meaning | Example |
|---|---|---|
| `letter` | the key typed | `'A'` |
| `output` | the lamp that lit | `'B'` |
| `before` | windows before turning | `'AAA'` |
| `after` | windows after turning | `'AAB'` |
| `stepped` | which rotors turned | `('R',)` |
| `stages` | every part in the path, with its input and output | the table above |

A `Trace` is **frozen**: once made, it can't be changed. It's a record of what happened, so it shouldn't be possible to edit it afterwards.

## Proof it matches the real machine

The tests decrypt an authentic message sent by the U-boat U-264 on 25 November 1942, using the M4 settings shown at the top of this page plus starting positions `VJNA`. The whole 232-letter message comes out right. It starts:

```
VONVONJLOOKSJHFFTTTEINSEINSDREIZWOYYQNNS…
```

(German: "von von 'Looks'": a message from the U-boat commanded by Hartwig Looks.)
