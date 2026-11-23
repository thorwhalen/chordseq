# chordseq.tokens

Chord symbols to comparable tokens, at one of three levels of detail.

A chord is reduced to `(root, triad, seventh)`: the root pitch class, one of five triad
classes and one of four seventh classes. The *level* decides how much of that survives
into the token the search compares (names follow mir_eval’s chord-evaluation levels):

- `"root"`: the root only (`E`, `Em` and `E7` are the same token).
- `"triads"` (default): root and triad (`E` and `E7` match, `E` and `Em` do not).
- `"tetrads"`: root, triad and seventh (`E` and `E7` differ).

Inversions are always ignored. Spans of chords that are not chords at all (`N`, section
markers such as `<verse_1>`) become the token `NO_CHORD`, which matches nothing.

```pycon
>>> chord_parts("Am7"), chord_parts("E7"), chord_parts("Bdim7"), chord_parts("Bridge")
((9, 1, 1), (4, 0, 1), (11, 2, 3), None)
>>> token("E7", level="triads") == token("E", level="triads")
True
>>> token("E7", level="tetrads") == token("E", level="tetrads")
False
>>> token("Bridge") == NO_CHORD
True
```

### Functions

| [`check_level`](#chordseq.tokens.check_level)(level)                               | `level` if it is one of `LEVELS`; a `ValueError` naming them otherwise.                            |
|---------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------|
| [`chord_parts`](#chordseq.tokens.chord_parts)(symbol, \*[, dialect])               | `(root, triad index, seventh index)` of a chord symbol; None if it is not a chord.                 |
| [`collapse_runs`](#chordseq.tokens.collapse_runs)(chars)                             | Runs of equal tokens as `(token, first index, last index)`.                                        |
| [`encode`](#chordseq.tokens.encode)(sequence, \*[, level, collapse, dialect]) | A sequence as token runs `(token, first, last)` over its original indices, plus its items.         |
| [`parts_token`](#chordseq.tokens.parts_token)(parts, \*[, level])                  | The one-character token for `(root, triad, seventh)` at `level`.                                   |
| [`split_item`](#chordseq.tokens.split_item)(item)                                 | `(symbol, payload)` of a sequence item: a bare symbol, or a `(symbol, payload)` pair.              |
| [`token`](#chordseq.tokens.token)(symbol, \*[, level, dialect])              | The one-character token of a chord symbol at `level`; `NO_CHORD` if not a chord.                   |
| [`token_parts`](#chordseq.tokens.token_parts)(char)                                | Inverse of [`parts_token()`](#chordseq.tokens.parts_token) (`None` for `NO_CHORD`). |
| [`transpose_token`](#chordseq.tokens.transpose_token)(char, semitones)                 | `char` moved up `semitones` (`NO_CHORD` stays).                                                    |

### chordseq.tokens.check_level(level)

`level` if it is one of `LEVELS`; a `ValueError` naming them otherwise.

* **Return type:**
  [`str`](https://docs.python.org/3/builtins/stdtypes.html#str)

### chordseq.tokens.chord_parts(symbol, , dialect='default')

`(root, triad index, seventh index)` of a chord symbol; None if it is not a chord.

The indices point into `TRIADS` and `SEVENTHS`. Sixths and added ninths
are ignored (`C6` is a C major triad); a bass note is ignored.

* **Return type:**
  [`tuple`](https://docs.python.org/3/builtins/stdtypes.html#tuple)[[`int`](https://docs.python.org/3/builtins/functions.html#int), [`int`](https://docs.python.org/3/builtins/functions.html#int), [`int`](https://docs.python.org/3/builtins/functions.html#int)] | [`None`](https://docs.python.org/3/builtins/constants.html#None)

### chordseq.tokens.collapse_runs(chars)

Runs of equal tokens as `(token, first index, last index)`.

```pycon
>>> collapse_runs("aabcc")
[('a', 0, 1), ('b', 2, 2), ('c', 3, 4)]
```

* **Return type:**
  [`list`](https://docs.python.org/3/builtins/stdtypes.html#list)[[`tuple`](https://docs.python.org/3/builtins/stdtypes.html#tuple)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`int`](https://docs.python.org/3/builtins/functions.html#int), [`int`](https://docs.python.org/3/builtins/functions.html#int)]]

### chordseq.tokens.encode(sequence, , level='triads', collapse=True, dialect='default')

A sequence as token runs `(token, first, last)` over its original indices, plus its items.

With `collapse=True` (default) consecutive equal tokens share one run, so a chord
held for four bars and one written once are the same; with `collapse=False` every
item is its own run.

* **Return type:**
  [`tuple`](https://docs.python.org/3/builtins/stdtypes.html#tuple)[[`list`](https://docs.python.org/3/builtins/stdtypes.html#list)[[`tuple`](https://docs.python.org/3/builtins/stdtypes.html#tuple)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`int`](https://docs.python.org/3/builtins/functions.html#int), [`int`](https://docs.python.org/3/builtins/functions.html#int)]], [`list`](https://docs.python.org/3/builtins/stdtypes.html#list)]

### chordseq.tokens.parts_token(parts, , level='triads')

The one-character token for `(root, triad, seventh)` at `level`.

* **Return type:**
  [`str`](https://docs.python.org/3/builtins/stdtypes.html#str)

### chordseq.tokens.split_item(item)

`(symbol, payload)` of a sequence item: a bare symbol, or a `(symbol, payload)` pair.

```pycon
>>> split_item("Am"), split_item(("Am", {"t": 1.5}))
(('Am', None), ('Am', {'t': 1.5}))
```

* **Return type:**
  [`tuple`](https://docs.python.org/3/builtins/stdtypes.html#tuple)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`object`](https://docs.python.org/3/builtins/functions.html#object)]

### chordseq.tokens.token(symbol, , level='triads', dialect='default')

The one-character token of a chord symbol at `level`; `NO_CHORD` if not a chord.

* **Return type:**
  [`str`](https://docs.python.org/3/builtins/stdtypes.html#str)

### chordseq.tokens.token_parts(char)

Inverse of [`parts_token()`](#chordseq.tokens.parts_token) (`None` for `NO_CHORD`).

* **Return type:**
  [`tuple`](https://docs.python.org/3/builtins/stdtypes.html#tuple)[[`int`](https://docs.python.org/3/builtins/functions.html#int), [`int`](https://docs.python.org/3/builtins/functions.html#int), [`int`](https://docs.python.org/3/builtins/functions.html#int)] | [`None`](https://docs.python.org/3/builtins/constants.html#None)

### chordseq.tokens.transpose_token(char, semitones)

`char` moved up `semitones` (`NO_CHORD` stays).

* **Return type:**
  [`str`](https://docs.python.org/3/builtins/stdtypes.html#str)
