# chordseq.query

The query notation: regex-shaped, over plain chord symbols or Roman numerals.

A query is whitespace-separated items:

- a chord symbol (`Am`, `E7`, `F#m7b5`) or a Roman numeral (`vi`, `V7`, `bVII`);
- `.` any one chord;
- `|` between alternatives in one item, no spaces (`E|E7`, `V|bVII`);
- `?` after an item makes it optional (`E7?`); `*` after an item, or alone, any run of
  chords (`.*` and `*` are the same: zero or more chords, as few as will do).

`E(7)` is refused: parentheses already mean alterations in chord symbols. At the default
level (`triads`) `E` already matches `E7`; write `E|E7` to be explicit, or search
at `level="tetrads"` to tell them apart. Chord symbols and Roman numerals do not mix in
one query. Chord symbols in a query use the default spelling.

```pycon
>>> [item.text for item in parse_query("Am E7? F").items]
['Am', 'E7?', 'F']
>>> parse_query("vi IV I V").roman
True
```

### Functions

| [`parse_query`](#chordseq.query.parse_query)(text)   | Read a query (see the module docstring for the notation); `QueryError` if it is not one.   |
|----------------------------------------------------------------------|--------------------------------------------------------------------------------------------|

### Classes

| [`Item`](#chordseq.query.Item)(text, alternatives[, quantifier])   | One query item: alternatives (None = any chord) and a quantifier ('', '?' or '\*').   |
|-------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------|
| [`Query`](#chordseq.query.Query)(items, roman)                      | A parsed query.                                                                       |

### Exceptions

| [`QueryError`](#chordseq.query.QueryError)   | A query that cannot be read; the message says which item and why.   |
|---------------------------------------------------------------|---------------------------------------------------------------------|

### *class* chordseq.query.Item(text, alternatives, quantifier='')

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

One query item: alternatives (None = any chord) and a quantifier (‘’, ‘?’ or ‘\*’).

### *class* chordseq.query.Query(items, roman)

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

A parsed query. `roman` is True when its atoms are degrees, not roots.

### *exception* chordseq.query.QueryError

Bases: [`ValueError`](https://docs.python.org/3/builtins/exceptions.html#ValueError)

A query that cannot be read; the message says which item and why.

### chordseq.query.parse_query(text)

Read a query (see the module docstring for the notation); `QueryError` if it is not one.

* **Return type:**
  [`Query`](#chordseq.query.Query)
