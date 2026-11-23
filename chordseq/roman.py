"""Roman numerals: chords relative to a key, both ways.

One chromatic scheme, measured from the key's tonic whether the key is major or minor
(so ``bIII``, ``bVI``, ``bVII`` in a minor key, and ``to_roman`` and ``parse_roman`` round-trip):
``I bII II bIII III IV #IV V bVI VI bVII VII``. Upper case is major, lower case minor,
``°`` diminished, ``ø`` half-diminished (``ø7``), ``+`` augmented, ``sus`` suspended or
power; the seventh follows as ``7``, ``maj7`` or (after ``°``) ``°7``.

>>> from chordsym import Key
>>> to_roman("Am", Key(0)), to_roman("G7", Key(0), level="tetrads"), to_roman("Bb", Key(0))
('vi', 'V7', 'bVII')
>>> to_roman_sequence(["Am", "F", "C", "G"], key=Key(0))
['vi', 'IV', 'I', 'V']
>>> parse_roman("V7"), parse_roman("bVII"), parse_roman("Am")
((7, 0, 1), (10, 0, 0), None)
"""

from __future__ import annotations

import re
from collections.abc import Iterable

from chordsym import Dialect, Key, estimate_key

from chordseq.tokens import (
    DEFAULT_LEVEL,
    SEVENTHS,
    TRIADS,
    Parts,
    check_level,
    chord_parts,
)

NUMERALS = ("I", "bII", "II", "bIII", "III", "IV", "#IV", "V", "bVI", "VI", "bVII", "VII")
_DEGREE = {"I": 0, "II": 2, "III": 4, "IV": 5, "V": 7, "VI": 9, "VII": 11}
_ROMAN_RE = re.compile(
    r"(?P<acc>[b#]?)(?P<num>VII|VI|IV|V|III|II|I|vii|vi|iv|v|iii|ii|i)"
    r"(?P<q>°|o|ø|\+|sus)?(?P<sev>maj7|M7|7)?"
)


def is_roman(token: str) -> bool:
    """Whether ``token`` is a Roman-numeral chord as :func:`parse_roman` reads them."""
    return _ROMAN_RE.fullmatch(token) is not None


def parse_roman(token: str) -> Parts | None:
    """``(degree, triad index, seventh index)`` of a Roman numeral; None if it is not one.

    The degree is semitones above the tonic. Case gives major or minor; ``°7`` is a
    diminished seventh chord, ``ø`` and ``ø7`` a half-diminished one.
    """
    m = _ROMAN_RE.fullmatch(token)
    if m is None:
        return None
    num = m["num"]
    degree = (_DEGREE[num.upper()] + {"b": -1, "#": 1, "": 0}[m["acc"]]) % 12
    q, sev = m["q"], m["sev"]
    if q == "sus":
        triad = TRIADS.index("open")
    elif q == "+":
        triad = TRIADS.index("augmented")
    elif q in ("°", "o", "ø"):
        triad = TRIADS.index("diminished")
    else:
        triad = TRIADS.index("minor" if num.islower() else "major")
    if sev in ("maj7", "M7"):
        seventh = SEVENTHS.index("maj7")
    elif sev == "7" or q == "ø":
        seventh = SEVENTHS.index("dim7" if q in ("°", "o") else "7")
    else:
        seventh = 0
    return degree, triad, seventh


def roman_from_parts(parts: Parts, *, level: str = DEFAULT_LEVEL) -> str:
    """The Roman numeral for ``(degree, triad, seventh)`` (degree = semitones above the tonic)."""
    check_level(level)
    degree, triad, seventh = parts
    if level == "root":
        triad = seventh = 0
    elif level == "triads":
        seventh = 0
    name, kind, sev = NUMERALS[degree % 12], TRIADS[triad], SEVENTHS[seventh]
    if kind == "minor":
        name = name.lower()
    if kind == "diminished":
        name = name.lower()
        if sev == "7":
            return name + "ø7"
        return name + ("°7" if sev == "dim7" else "°")
    if kind == "augmented":
        name += "+"
    elif kind == "open":
        name += "sus"
    return name + sev


def to_roman(
    symbol: str,
    key: Key,
    *,
    level: str = DEFAULT_LEVEL,
    dialect: str | Dialect = "default",
) -> str | None:
    """The Roman numeral of ``symbol`` in ``key``; None if ``symbol`` is not a chord."""
    parts = chord_parts(symbol, dialect=dialect)
    if parts is None:
        return None
    root, triad, seventh = parts
    return roman_from_parts(((root - key.tonic) % 12, triad, seventh), level=level)


def to_roman_sequence(
    symbols: Iterable[str],
    *,
    key: Key | None = None,
    level: str = DEFAULT_LEVEL,
    dialect: str | Dialect = "default",
) -> list[str | None]:
    """Roman numerals of a chord sequence in ``key`` (estimated from the sequence when None)."""
    symbols = list(symbols)
    if key is None:
        key = estimate_key(symbols, dialect=dialect)
    if key is None:
        return [None] * len(symbols)
    return [to_roman(s, key, level=level, dialect=dialect) for s in symbols]
