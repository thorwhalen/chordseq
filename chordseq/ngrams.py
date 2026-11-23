"""N-gram counts of chord progressions, in the same alphabet the search uses.

Each sequence is tokenised as in :mod:`chordseq.search` (level, repeats collapsed), windows
of ``n`` chords are counted, and a window that holds a non-chord is skipped. How an n-gram is
*named* decides what counts as the same progression:

- ``relative_to="key"`` (default): Roman numerals in the sequence's key (estimated by
  ``chordsym.estimate_key`` unless ``key=`` is given); ``I V vi IV`` however it is transposed.
- ``relative_to="first"``: Roman numerals measured from the n-gram's first chord, so no key is
  needed (``vi IV I V`` becomes ``I bVI bIII bVII``).
- ``relative_to=None``: absolute chord names (``Am F C G``).

>>> seqs = [["C", "G", "Am", "F", "C", "G", "Am", "F"], ["D", "A", "Bm", "G"]]
>>> counts = ngrams(seqs, n=4)
>>> counts[("I", "V", "vi", "IV")], counts[("V", "vi", "IV", "I")]
(3, 1)
>>> ngrams(seqs, n=2, relative_to=None)[("C", "G")]
2
>>> ngrams(seqs, n=2, per_sequence=True)[1][("I", "V")]
1
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable

from chordsym import Dialect, Key, estimate_key

from chordseq.roman import roman_from_parts
from chordseq.tokens import (
    DEFAULT_LEVEL,
    SEVENTHS,
    TRIADS,
    check_level,
    encode,
    split_item,
    token_parts,
)

DEFAULT_SIZES = (2, 3, 4)
_RELATIVE_TO = ("key", "first", None)
_ROOT_NAMES = ("C", "C#", "D", "Eb", "E", "F", "F#", "G", "Ab", "A", "Bb", "B")
_TRIAD_SUFFIX = {
    "major": "",
    "minor": "m",
    "diminished": "dim",
    "augmented": "aug",
    "open": "sus",
}
_SEVENTH_SUFFIX = {"": "", "7": "7", "maj7": "maj7", "dim7": "7"}


def _chord_name(parts) -> str:
    root, triad, seventh = parts
    kind, sev = TRIADS[triad], SEVENTHS[seventh]
    if kind == "diminished" and sev:
        return _ROOT_NAMES[root] + ("dim7" if sev == "dim7" else "m7b5")
    return _ROOT_NAMES[root] + _TRIAD_SUFFIX[kind] + _SEVENTH_SUFFIX[sev]


def ngrams(
    sequences: Iterable[Iterable],
    n: int | Iterable[int] = DEFAULT_SIZES,
    *,
    level: str = DEFAULT_LEVEL,
    collapse: bool = True,
    relative_to: str | None = "key",
    key: Key | None = None,
    per_sequence: bool = False,
    dialect: str | Dialect = "default",
) -> Counter | list[Counter]:
    """Counts of n-grams (tuples of chord names) pooled over ``sequences``.

    ``n`` is one size or several (default 2, 3 and 4). With ``per_sequence=True`` the result is
    one :class:`~collections.Counter` per sequence, in order, instead of one pooled counter.
    """
    check_level(level)
    if relative_to not in _RELATIVE_TO:
        raise ValueError(
            f"relative_to must be one of {_RELATIVE_TO}, not {relative_to!r}"
        )
    sizes = (n,) if isinstance(n, int) else tuple(n)
    if not sizes or min(sizes) < 1:
        raise ValueError(f"n-gram sizes must be positive, not {sizes!r}")
    results = [
        _count(seq, sizes, level, collapse, relative_to, key, dialect)
        for seq in sequences
    ]
    if per_sequence:
        return results
    pooled: Counter = Counter()
    for counter in results:
        pooled.update(counter)
    return pooled


def _count(sequence, sizes, level, collapse, relative_to, key, dialect) -> Counter:
    items = list(sequence)
    runs, _ = encode(items, level=level, collapse=collapse, dialect=dialect)
    parts = [token_parts(char) for char, _, _ in runs]
    if relative_to == "key" and key is None:
        key = estimate_key((split_item(i)[0] for i in items), dialect=dialect)
    counter: Counter = Counter()
    for size in sizes:
        for start in range(len(parts) - size + 1):
            window = parts[start : start + size]
            if None in window:
                continue
            counter[_name_window(window, relative_to, key, level)] += 1
    return counter


def _name_window(window, relative_to, key, level) -> tuple[str, ...]:
    if relative_to is None:
        return tuple(_chord_name(p) for p in window)
    tonic = window[0][0] if relative_to == "first" else key.tonic
    return tuple(
        roman_from_parts(((root - tonic) % 12, triad, seventh), level=level)
        for root, triad, seventh in window
    )
