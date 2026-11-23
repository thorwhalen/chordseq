# chordseq.roman

Roman numerals: chords relative to a key, both ways.

One chromatic scheme, measured from the key’s tonic whether the key is major or minor
(so `bIII`, `bVI`, `bVII` in a minor key, and `to_roman` and `parse_roman` round-trip):
`I bII II bIII III IV #IV V bVI VI bVII VII`. Upper case is major, lower case minor,
`°` diminished, `ø` half-diminished (`ø7`), `+` augmented, `sus` suspended or
power; the seventh follows as `7`, `maj7` or (after `°`) `°7`.

```pycon
>>> from chordsym import Key
>>> to_roman("Am", Key(0)), to_roman("G7", Key(0), level="tetrads"), to_roman("Bb", Key(0))
('vi', 'V7', 'bVII')
>>> to_roman_sequence(["Am", "F", "C", "G"], key=Key(0))
['vi', 'IV', 'I', 'V']
>>> parse_roman("V7"), parse_roman("bVII"), parse_roman("Am")
((7, 0, 1), (10, 0, 0), None)
```

### Functions

| [`is_roman`](#chordseq.roman.is_roman)(token)                                   | Whether `token` is a Roman-numeral chord as [`parse_roman()`](#chordseq.roman.parse_roman) reads them.   |
|----------------------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------------------------------|
| [`parse_roman`](#chordseq.roman.parse_roman)(token)                                | `(degree, triad index, seventh index)` of a Roman numeral; None if it is not one.                                        |
| [`roman_from_parts`](#chordseq.roman.roman_from_parts)(parts, \*[, level])              | The Roman numeral for `(degree, triad, seventh)` (degree = semitones above the tonic).                                   |
| [`to_roman`](#chordseq.roman.to_roman)(symbol, key, \*[, level, dialect])       | The Roman numeral of `symbol` in `key`; None if `symbol` is not a chord.                                                 |
| [`to_roman_sequence`](#chordseq.roman.to_roman_sequence)(symbols, \*[, key, level, ...]) | Roman numerals of a chord sequence in `key` (estimated from the sequence when None).                                     |

### chordseq.roman.is_roman(token)

Whether `token` is a Roman-numeral chord as [`parse_roman()`](#chordseq.roman.parse_roman) reads them.

* **Return type:**
  [`bool`](https://docs.python.org/3/builtins/functions.html#bool)

### chordseq.roman.parse_roman(token)

`(degree, triad index, seventh index)` of a Roman numeral; None if it is not one.

The degree is semitones above the tonic. Case gives major or minor; `°7` is a
diminished seventh chord, `ø` and `ø7` a half-diminished one.

* **Return type:**
  [`tuple`](https://docs.python.org/3/builtins/stdtypes.html#tuple)[[`int`](https://docs.python.org/3/builtins/functions.html#int), [`int`](https://docs.python.org/3/builtins/functions.html#int), [`int`](https://docs.python.org/3/builtins/functions.html#int)] | [`None`](https://docs.python.org/3/builtins/constants.html#None)

### chordseq.roman.roman_from_parts(parts, , level='triads')

The Roman numeral for `(degree, triad, seventh)` (degree = semitones above the tonic).

* **Return type:**
  [`str`](https://docs.python.org/3/builtins/stdtypes.html#str)

### chordseq.roman.to_roman(symbol, key, , level='triads', dialect='default')

The Roman numeral of `symbol` in `key`; None if `symbol` is not a chord.

* **Return type:**
  [`str`](https://docs.python.org/3/builtins/stdtypes.html#str) | [`None`](https://docs.python.org/3/builtins/constants.html#None)

### chordseq.roman.to_roman_sequence(symbols, , key=None, level='triads', dialect='default')

Roman numerals of a chord sequence in `key` (estimated from the sequence when None).

* **Return type:**
  [`list`](https://docs.python.org/3/builtins/stdtypes.html#list)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str) | [`None`](https://docs.python.org/3/builtins/constants.html#None)]
