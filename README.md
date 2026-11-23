# chordseq

Search chord progressions in any key, count n-grams, and name chords by key. Pure Python, one dependency ([chordsym](https://pypi.org/project/chordsym/)).

```python
>>> from chordseq import find, ngrams
>>> sequence = ["Dm", "Bb", "F", "C", "Dm", "Bb", "F", "C"]
>>> [(m.start, m.stop) for m in find("vi IV I V", sequence)]   # Roman numerals: any key
[(0, 4), (4, 8)]
>>> [m.transposition for m in find("Am F C G", sequence)]       # chord symbols: any key too
[5, 5]
```

`pip install chordseq`

## One-command test on real data

```bash
pytest tests/test_smoke.py
```

It reads the first Chordonomicon progressions over the public datasets-server API (standard library only; skipped offline), searches them and counts their 4-grams. The same by hand:

```python
from chordseq import find, ngrams

progressions = [row.split() for row in chordonomicon_rows]  # "<verse_1> C G Amin F ..."
hits = [m for p in progressions for m in find("Amin F C G", p, dialect="chordonomicon")]
ngrams(progressions, n=4, dialect="chordonomicon").most_common(5)
```

## The query

Whitespace-separated items, like a regular expression over chords:

| Item | Means |
|---|---|
| `Am`, `E7`, `F#m7b5` | a chord symbol |
| `vi`, `V7`, `bVII`, `ii`, `viiø7` | a Roman numeral (upper major, lower minor, `°` `ø` `+` `sus`) |
| `.` | any one chord |
| `E\|E7` | either (no spaces) |
| `E7?` | optional |
| `*` (alone, or after an item) | any run of chords, as few as will do |

`E(7)` is refused with a hint: parentheses already mean alterations in chord symbols. Chord symbols and Roman numerals do not mix in a query.

## Defaults

`level="triads"` (`E` matches `E7`; `"root"` and `"tetrads"` are the other mir_eval levels), transposition-invariant, inversions ignored, repeated chords collapsed. `transposition_invariant=False` matches the query's own key: chord symbols as written, Roman numerals against `key=`.

## Sequences, payloads, matches

A sequence is an iterable of chord symbols, each optionally `(symbol, payload)` with any payload you like (a time, a bar, a page). `find(query, sequence)` returns `Match` objects: `start`/`stop` are indices into the sequence as you gave it (so collapsed repeats are covered), `items`, `symbols`, `payloads`, `transposition`. `search(query, sequences)` does many sequences lazily, with `sequence_index`. The engine knows nothing about audio, pages or songs; you map spans to times or pages through the payloads. Anything that is not a chord (`N`, `<verse_1>`) matches nothing, so no match runs across it: cut a song into sections and the matches stay inside them.

## N-grams and Roman numerals

```python
ngrams(sequences, n=(2, 3, 4))  # pooled Counter of tuples, in the key of each sequence
ngrams(
    sequences, relative_to="first"
)  # keyless: numerals from each n-gram's first chord
ngrams(sequences, relative_to=None, per_sequence=True)
to_roman_sequence(["G", "D", "Em", "C"])  # ['I', 'V', 'vi', 'IV']
```

Roman numerals use one chromatic scheme from the tonic, major or minor key alike (`bIII`, `bVI`, `bVII` in a minor key), so `to_roman` and the query read each other.

## Seams

| Seam | Keyword | Default | Replacement that exists |
|---|---|---|---|
| Chord spelling of the input | `dialect=` | `"default"` (chart spellings) | `chordsym.DIALECTS` (`chordonomicon`, `harte`), `chordsym.register_dialect` |
| Detail of comparison | `level=` | `"triads"` | `"root"`, `"tetrads"` (mir_eval names) |
| Key for Roman numerals | `key=` | estimated by `chordsym.estimate_key` | any `chordsym.Key` |

**NOT seams (v1):** the scan engine (one regex pass per transposition over a string of one-character tokens; the packed-byte numpy scan of the phase-1 prototypes, in `misc/docs/research/prototypes/`, is the replacement when a corpus-sized consumer needs it, and then it lands behind the same `search` signature); an index; ranking and popularity; a browser or Web Worker build; a CLI; audio, pages and songs (callers map spans through payloads); chord symbols beyond what `chordsym` parses.

## Design and research

The phase-1 design, five research reports and prototypes are in `misc/docs/research/`.
