"""The query notation: regex-shaped, over plain chord symbols or Roman numerals.

A query is whitespace-separated items:

- a chord symbol (``Am``, ``E7``, ``F#m7b5``) or a Roman numeral (``vi``, ``V7``, ``bVII``);
- ``.`` any one chord;
- ``|`` between alternatives in one item, no spaces (``E|E7``, ``V|bVII``);
- ``?`` after an item makes it optional (``E7?``); ``*`` after an item, or alone, any run of
  chords (``.*`` and ``*`` are the same: zero or more chords, as few as will do).

``E(7)`` is refused: parentheses already mean alterations in chord symbols. At the default
level (``triads``) ``E`` already matches ``E7``; write ``E|E7`` to be explicit, or search
at ``level="tetrads"`` to tell them apart. Chord symbols and Roman numerals do not mix in
one query. Chord symbols in a query use the default spelling.

>>> [item.text for item in parse_query("Am E7? F").items]
['Am', 'E7?', 'F']
>>> parse_query("vi IV I V").roman
True
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from chordsym import is_chord_token

from chordseq.roman import is_roman, parse_roman
from chordseq.tokens import Parts, chord_parts

_PAREN_SEVENTH_RE = re.compile(r"^[A-G][#b]?\(\d+\)")
_QUANTIFIERS = ("?", "*")


class QueryError(ValueError):
    """A query that cannot be read; the message says which item and why."""


@dataclass(frozen=True)
class Item:
    """One query item: alternatives (None = any chord) and a quantifier ('', '?' or '*')."""

    text: str
    alternatives: tuple[Parts, ...] | None
    quantifier: str = ""


@dataclass(frozen=True)
class Query:
    """A parsed query. ``roman`` is True when its atoms are degrees, not roots."""

    items: tuple[Item, ...]
    roman: bool


def _atom(text: str) -> tuple[Parts, bool]:
    if _PAREN_SEVENTH_RE.match(text):
        raise QueryError(
            f"{text!r}: parentheses mean alterations in chord symbols; "
            f"write {text[0]}|{text[0]}7 for 'with or without the seventh' "
            "(at the default level, plain "
            f"{text[0]} already matches {text[0]}7)"
        )
    if is_roman(text):
        return parse_roman(text), True
    if is_chord_token(text):
        return chord_parts(text), False
    raise QueryError(f"{text!r} is neither a chord symbol nor a Roman numeral")


def parse_query(text: str) -> Query:
    """Read a query (see the module docstring for the notation); ``QueryError`` if it is not one."""
    items: list[Item] = []
    kinds: set[bool] = set()
    for word in text.split():
        quantifier = ""
        body = word
        if word == "*":
            body, quantifier = ".", "*"
        elif word[-1] in _QUANTIFIERS and len(word) > 1:
            body, quantifier = word[:-1], word[-1]
        if body == ".":
            items.append(Item(word, None, quantifier))
            continue
        alternatives = []
        for part in body.split("|"):
            parts, is_degree = _atom(part)
            kinds.add(is_degree)
            alternatives.append(parts)
        items.append(Item(word, tuple(alternatives), quantifier))
    if not any(it.alternatives is not None for it in items):
        raise QueryError(f"{text!r} names no chord")
    if len(kinds) > 1:
        raise QueryError(f"{text!r} mixes chord symbols and Roman numerals")
    return Query(tuple(items), roman=kinds == {True})
