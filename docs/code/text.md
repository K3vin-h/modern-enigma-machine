# `text.py`: cleaning up messages

[Back to the code guide](README.md)

## What it's for

A real Enigma only has 26 keys: A to Z. There's no space bar, no numbers and no punctuation. This file has two small helpers: one turns any text into something the machine can type, and one formats the result the way wartime operators wrote it down.

## `normalize(text)`: keep only A–Z

Takes any text and returns two things:
1. the text with only the English letters kept, in capitals;
2. how many characters were thrown away.

```python
normalize("Hello, World! ß")   # ('HELLOWORLD', 5)
```

The 5 dropped characters are the comma, two spaces, the `!` and the `ß`.

**How it works.** It goes through the text one character at a time and keeps a character only if it is a plain English letter (`c.isascii() and c.isalpha()`). Kept letters are made uppercase. The dropped count is just the original length minus the kept length.

**Things it deliberately does *not* do:**
- It doesn't convert special letters. `ß` is dropped, not turned into `SS`, and `é` is dropped, not turned into `E`. This keeps the rule simple and predictable: if it isn't A–Z, it's gone.
- It doesn't accept non-text. `normalize(123)` raises `TypeError`.

## `group5(text)`: split into groups of five

Operators sent messages in blocks of five letters so they were easier to read out and copy down. This function does the same.

```python
group5("HELLOWORLDABC")   # 'HELLO WORLD ABC'
```

The last group can be shorter than five, and there's no extra space at the end.

**How it works.** It takes slices of 5 letters (`text[0:5]`, `text[5:10]`, …) and joins them with spaces.
