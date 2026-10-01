# Code guide

Plain-language explanations of each source file in `classic/src/enigma/`. Each page explains what the file is for, then walks through its classes and functions with examples. Every example output was produced by running the real code.

| File | What it does | Page |
|---|---|---|
| `wiring.py` | The historical wiring tables, data only | [wiring.md](wiring.md) |
| `components.py` | The physical parts: rotors, reflector, entry wheel, plugboard | [components.md](components.md) |
| `text.py` | Cleans up input text and groups output into fives | [text.md](text.md) |
| `machine.py` | Puts the parts together: stepping, the signal path, Enigma I and M4 | [machine.md](machine.md) |
| `__init__.py` | Empty. Its only job is to mark `enigma` as a Python package so `from enigma.machine import EnigmaI` works. | — |

## Two ideas used everywhere

- **Letters are stored as numbers.** A=0, B=1, C=2 … Z=25. The code switches back to letters only when showing results.
- **`% 26` wraps around the alphabet.** Counting past Z lands back on A (`26 % 26 = 0`), and counting back before A lands on Z (`-1 % 26 = 25`).

## How the files depend on each other

```
wiring.py  ──►  components.py  ──►  machine.py
                                       ▲
text.py  ──────────────────────────────┘
```

`wiring.py` has no code, only data. `components.py` turns that data into working parts. `machine.py` connects the parts and uses `text.py` to clean up messages before enciphering them.

## A quick taste

```python
from enigma.machine import EnigmaI

m = EnigmaI(["I", "II", "III"], "B", "AAA")
m.process("AAAAA")   # 'BDZGO'
m.reset()
m.process("BDZGO")   # 'AAAAA'  (same settings decrypt)
```
