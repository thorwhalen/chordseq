# chordseq

chordseq: search chord progressions in any key, count n-grams, name chords by key.

```pycon
>>> from chordseq import find, ngrams, to_roman_sequence
>>> [(m.start, m.stop) for m in find("Am F C", ["Dm", "Bb", "F", "G", "Em", "Bb", "G"])]
[(0, 3)]
>>> to_roman_sequence(["G", "D", "Em", "C", "G"])
['I', 'V', 'vi', 'IV', 'I']
>>> ngrams([["C", "G", "Am", "F"]], n=2).most_common(2)
[(('I', 'V'), 1), (('V', 'vi'), 1)]
```

### Functions

| [`find`](#chordseq.find)(query, sequence, \*\*kwargs)                 | [`search()`](#chordseq.search) in one sequence; a list of its matches.   |
|----------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------|
| [`ngrams`](#chordseq.ngrams)(sequences[, n, level, collapse, ...])      | Counts of n-grams (tuples of chord names) pooled over `sequences`.                                  |
| [`parse_query`](#chordseq.parse_query)(text)                                 | Read a query (see the module docstring for the notation); `QueryError` if it is not one.            |
| [`parse_roman`](#chordseq.parse_roman)(token)                                | `(degree, triad index, seventh index)` of a Roman numeral; None if it is not one.                   |
| [`search`](#chordseq.search)(query, sequences, \*[, level, ...])        | Matches of `query` in each sequence, lazily, in sequence then start order.                          |
| [`to_roman`](#chordseq.to_roman)(symbol, key, \*[, level, dialect])       | The Roman numeral of `symbol` in `key`; None if `symbol` is not a chord.                            |
| [`to_roman_sequence`](#chordseq.to_roman_sequence)(symbols, \*[, key, level, ...]) | Roman numerals of a chord sequence in `key` (estimated from the sequence when None).                |

### Classes

| [`Match`](#chordseq.Match)(sequence_index, start, stop, items[, ...])   | A match: the span `[start, stop)` of sequence `sequence_index` (original indices).   |
|-----------------------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------|
| [`Query`](#chordseq.Query)(items, roman)                                | A parsed query.                                                                      |

### Exceptions

| [`QueryError`](#chordseq.QueryError)   | A query that cannot be read; the message says which item and why.   |
|---------------------------------------------------------------|---------------------------------------------------------------------|

### *class* chordseq.Match(sequence_index, start, stop, items, transposition=0)

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

A match: the span `[start, stop)` of sequence `sequence_index` (original indices).

`transposition` is the number of semitones the query was moved up to match (0 when it
matched as written).

### *class* chordseq.Query(items, roman)

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

A parsed query. `roman` is True when its atoms are degrees, not roots.

### *exception* chordseq.QueryError

Bases: [`ValueError`](https://docs.python.org/3/builtins/exceptions.html#ValueError)

A query that cannot be read; the message says which item and why.

### chordseq.find(query, sequence, \*\*kwargs)

[`search()`](#chordseq.search) in one sequence; a list of its matches.

* **Return type:**
  [`list`](https://docs.python.org/3/builtins/stdtypes.html#list)[[`Match`](#chordseq.Match)]

### chordseq.ngrams(sequences, n=(2, 3, 4), , level='triads', collapse=True, relative_to='key', key=None, per_sequence=False, dialect='default')

Counts of n-grams (tuples of chord names) pooled over `sequences`.

`n` is one size or several (default 2, 3 and 4). With `per_sequence=True` the result is
one [`Counter`](https://docs.python.org/3/library/collections.html#collections.Counter) per sequence, in order, instead of one pooled counter.

* **Return type:**
  [`Counter`](https://docs.python.org/3/library/collections.html#collections.Counter) | [`list`](https://docs.python.org/3/builtins/stdtypes.html#list)[[`Counter`](https://docs.python.org/3/library/collections.html#collections.Counter)]

### chordseq.parse_query(text)

Read a query (see the module docstring for the notation); `QueryError` if it is not one.

* **Return type:**
  [`Query`](chordseq.query.html.md#chordseq.query.Query)

### chordseq.parse_roman(token)

`(degree, triad index, seventh index)` of a Roman numeral; None if it is not one.

The degree is semitones above the tonic. Case gives major or minor; `°7` is a
diminished seventh chord, `ø` and `ø7` a half-diminished one.

* **Return type:**
  [`tuple`](https://docs.python.org/3/builtins/stdtypes.html#tuple)[[`int`](https://docs.python.org/3/builtins/functions.html#int), [`int`](https://docs.python.org/3/builtins/functions.html#int), [`int`](https://docs.python.org/3/builtins/functions.html#int)] | [`None`](https://docs.python.org/3/builtins/constants.html#None)

### chordseq.search(query, sequences, , level='triads', collapse=True, transposition_invariant=True, key=None, dialect='default')

Matches of `query` in each sequence, lazily, in sequence then start order.

`level` is `"root"`, `"triads"` or `"tetrads"` (see [`chordseq.tokens`](chordseq.tokens.html.md#module-chordseq.tokens)).
`transposition_invariant=False` matches the query’s own key: chord symbols as written,
Roman numerals against `key`. `dialect` names how the *sequences* spell chords
(`"chordonomicon"`, `"harte"`, see `chordsym.DIALECTS`); the query is in the
default spelling.

* **Return type:**
  [`Iterator`](https://docs.python.org/3/library/collections.abc.html#collections.abc.Iterator)[[`Match`](#chordseq.Match)]

### chordseq.to_roman(symbol, key, , level='triads', dialect='default')

The Roman numeral of `symbol` in `key`; None if `symbol` is not a chord.

* **Return type:**
  [`str`](https://docs.python.org/3/builtins/stdtypes.html#str) | [`None`](https://docs.python.org/3/builtins/constants.html#None)

### chordseq.to_roman_sequence(symbols, , key=None, level='triads', dialect='default')

Roman numerals of a chord sequence in `key` (estimated from the sequence when None).

* **Return type:**
  [`list`](https://docs.python.org/3/builtins/stdtypes.html#list)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str) | [`None`](https://docs.python.org/3/builtins/constants.html#None)]

### Modules

| [`query`](chordseq.query.html.md#module-chordseq.query)   | The query notation: regex-shaped, over plain chord symbols or Roman numerals.   |
|--------------------------------------------------------------------------------|---------------------------------------------------------------------------------|
| [`roman`](chordseq.roman.html.md#module-chordseq.roman)   | Roman numerals: chords relative to a key, both ways.                            |
| [`tokens`](chordseq.tokens.html.md#module-chordseq.tokens) | Chord symbols to comparable tokens, at one of three levels of detail.           |
