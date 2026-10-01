# Modern Enigma Machine

A terminal simulator of the WWII Enigma I and M4 cipher machines, built in object-oriented Python. It reproduces the machines' real rotor wiring, turnover notches, double-stepping, ring settings, reflectors and plugboard. A modern, improved Enigma will follow as a separate part of the project.

## Why

This project started from two 2022 IEEE papers: *Analysis and Implementation of the Enigma Machine* (IEEE 9758506) and *Analysis and Illustration of the Enigma Machine* (IEEE 9758550). Both explain Enigma well and include their own simulators. However, those simulators simplify the machine: one treats each rotor as a Caesar shift, the other uses randomly wired rotors, and neither models ring settings or the double-step.

I wanted a simulator that matches the real hardware closely enough to decrypt an authentic wartime U-boat message. I also want to understand each component well before designing an improved version of the machine. The papers provide the structure and explanations; the implementation follows the historical wiring tables.

## Code guide

New to the code? The [code guide](docs/code/README.md) explains each source file in plain language, with examples.
