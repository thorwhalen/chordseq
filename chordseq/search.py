"""Find a chord pattern in chord sequences, in any key.

The engine knows nothing about audio, pages or songs: a *sequence* is an iterable of chord
symbols, each optionally paired with an opaque payload (``("Am", payload)``). A match is an
index span over the sequence as given; callers map spans back to times, bars or pages
through the payloads.

Defaults: ``level="triads"`` (``E`` matches ``E7``), transposition-invariant, inversions
ignored, repeated chords collapsed (a chord held for four bars and one written once are the
same). Matches are overlapping, at most one per start position and transposition, and
``*`` takes as few chords as will do.

>>> hits = find("Am F", ["C", "G", "Am", "Am", "F", "C"])
>>> [(m.start, m.stop, m.items) for m in hits]
[(2, 5, ('Am', 'Am', 'F'))]
>>> [m.transposition for m in find("C F G", ["A", "D", "E"])]  # same shape, up a minor sixth
[9]
>>> [m.start for m in find("vi IV I V", ["Dm", "Bb", "F", "C", "Dm", "Bb", "F", "C"])]
[0, 4]
>>> find("Am E F", [("Am", "t=0.0"), ("E7", "t=2.1"), ("F", "t=4.0")])[0].payloads
('t=0.0', 't=2.1', 't=4.0')
"""

from __future__ import annotations

import re
from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from functools import lru_cache

from chordsym import Dialect, Key

from chordseq.query import Query, QueryError, parse_query
from chordseq.tokens import (
    ANY_CHORD,
    DEFAULT_LEVEL,
    check_level,
    encode,
    parts_token,
    split_item,
)


@dataclass(frozen=True)
class Match:
    """A match: the span ``[start, stop)`` of sequence ``sequence_index`` (original indices).

    ``transposition`` is the number of semitones the query was moved up to match (0 when it
    matched as written).
    """

    sequence_index: int
    start: int
    stop: int
    items: tuple
    transposition: int = 0

    @property
    def symbols(self) -> tuple[str, ...]:
        return tuple(split_item(item)[0] for item in self.items)

    @property
    def payloads(self) -> tuple:
        return tuple(split_item(item)[1] for item in self.items)


def _item_regex(item, *, level: str, shift: int) -> str:
    if item.alternatives is None:
        body = ANY_CHORD
    else:
        chars = dict.fromkeys(
            re.escape(parts_token(((root + shift) % 12, triad, seventh), level=level))
            for root, triad, seventh in item.alternatives
        )
        body = "(?:" + "|".join(chars) + ")"
    if item.quantifier == "*":
        return f"(?:{body})*?"
    return f"(?:{body})?" if item.quantifier == "?" else body


@lru_cache(maxsize=256)
def _regex(query: Query, level: str, shift: int) -> re.Pattern:
    body = "".join(_item_regex(item, level=level, shift=shift) for item in query.items)
    return re.compile(f"(?=({body}))")  # lookahead: overlapping matches


def _shifts(query: Query, *, transposition_invariant: bool, key: Key | None):
    if transposition_invariant:
        return range(12)
    if query.roman:
        if key is None:
            raise ValueError(
                "a Roman-numeral query needs key= when transposition_invariant=False"
            )
        return (key.tonic,)
    return (0,)


def search(
    query: str | Query,
    sequences: Iterable[Iterable],
    *,
    level: str = DEFAULT_LEVEL,
    collapse: bool = True,
    transposition_invariant: bool = True,
    key: Key | None = None,
    dialect: str | Dialect = "default",
) -> Iterator[Match]:
    """Matches of ``query`` in each sequence, lazily, in sequence then start order.

    ``level`` is ``"root"``, ``"triads"`` or ``"tetrads"`` (see :mod:`chordseq.tokens`).
    ``transposition_invariant=False`` matches the query's own key: chord symbols as written,
    Roman numerals against ``key``. ``dialect`` names how the *sequences* spell chords
    (``"chordonomicon"``, ``"harte"``, see :data:`chordsym.DIALECTS`); the query is in the
    default spelling.
    """
    check_level(level)
    if isinstance(query, str):
        query = parse_query(query)
    shifts = _shifts(query, transposition_invariant=transposition_invariant, key=key)
    for index, sequence in enumerate(sequences):
        runs, items = encode(sequence, level=level, collapse=collapse, dialect=dialect)
        text = "".join(char for char, _, _ in runs)
        found: dict[tuple[int, int], int] = {}
        for shift in shifts:
            for m in _regex(query, level, shift).finditer(text):
                first, stop = m.start(), m.end(1)
                if stop > first:
                    found.setdefault((first, stop), shift)
        for (first, stop), shift in sorted(found.items()):
            start_item, stop_item = runs[first][1], runs[stop - 1][2] + 1
            yield Match(
                index, start_item, stop_item, tuple(items[start_item:stop_item]), shift
            )


def find(query: str | Query, sequence: Iterable, **kwargs) -> list[Match]:
    """:func:`search` in one sequence; a list of its matches."""
    return list(search(query, [sequence], **kwargs))


__all__ = ["Match", "QueryError", "find", "search"]
