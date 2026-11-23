"""Chord symbols to comparable tokens, at one of three levels of detail.

A chord is reduced to ``(root, triad, seventh)``: the root pitch class, one of five triad
classes and one of four seventh classes. The *level* decides how much of that survives
into the token the search compares (names follow mir_eval's chord-evaluation levels):

- ``"root"``: the root only (``E``, ``Em`` and ``E7`` are the same token).
- ``"triads"`` (default): root and triad (``E`` and ``E7`` match, ``E`` and ``Em`` do not).
- ``"tetrads"``: root, triad and seventh (``E`` and ``E7`` differ).

Inversions are always ignored. Spans of chords that are not chords at all (``N``, section
markers such as ``<verse_1>``) become the token :data:`NO_CHORD`, which matches nothing.

>>> chord_parts("Am7"), chord_parts("E7"), chord_parts("Bdim7"), chord_parts("Bridge")
((9, 1, 1), (4, 0, 1), (11, 2, 3), None)
>>> token("E7", level="triads") == token("E", level="triads")
True
>>> token("E7", level="tetrads") == token("E", level="tetrads")
False
>>> token("Bridge") == NO_CHORD
True
"""

from __future__ import annotations

from collections.abc import Iterable

from chordsym import Dialect, chord_tones, parse_chord

LEVELS = ("root", "triads", "tetrads")
DEFAULT_LEVEL = "triads"

TRIADS = ("major", "minor", "diminished", "augmented", "open")
SEVENTHS = ("", "7", "maj7", "dim7")  # "7" is the minor (flat) seventh
N_TRIADS, N_SEVENTHS = len(TRIADS), len(SEVENTHS)
CLASSES_PER_ROOT = N_TRIADS * N_SEVENTHS

CHAR_BASE = 0x100  # token characters start here, clear of ASCII and of NO_CHORD
NO_CHORD = "\x00"  # matches nothing, not even the wildcard
ANY_CHORD = f"[{chr(CHAR_BASE)}-{chr(CHAR_BASE + 12 * CLASSES_PER_ROOT - 1)}]"

_MAJOR_SEVENTH, _MINOR_SEVENTH, _SIXTH_OR_DIM_SEVENTH = 11, 10, 9

Parts = tuple[int, int, int]  # (root, triad index, seventh index)


def check_level(level: str) -> str:
    """``level`` if it is one of :data:`LEVELS`; a ``ValueError`` naming them otherwise."""
    if level not in LEVELS:
        raise ValueError(f"level must be one of {LEVELS}, not {level!r}")
    return level


def chord_parts(symbol: str, *, dialect: str | Dialect = "default") -> Parts | None:
    """``(root, triad index, seventh index)`` of a chord symbol; None if it is not a chord.

    The indices point into :data:`TRIADS` and :data:`SEVENTHS`. Sixths and added ninths
    are ignored (``C6`` is a C major triad); a bass note is ignored.
    """
    parsed = parse_chord(symbol, dialect=dialect)
    if parsed is None:
        return None
    root, quality = parsed
    tones = chord_tones(symbol, dialect=dialect, bass_first=False) or ()
    intervals = {(tone - root) % 12 for tone in tones}
    if quality == "open":
        triad = TRIADS.index("open")
    elif quality == "diminished":
        triad = TRIADS.index("diminished")
    elif 8 in intervals and 7 not in intervals:
        triad = TRIADS.index("augmented")
    else:
        triad = TRIADS.index(quality)
    if _MAJOR_SEVENTH in intervals:
        seventh = SEVENTHS.index("maj7")
    elif _MINOR_SEVENTH in intervals:
        seventh = SEVENTHS.index("7")
    elif quality == "diminished" and _SIXTH_OR_DIM_SEVENTH in intervals:
        seventh = SEVENTHS.index("dim7")
    else:
        seventh = 0
    return root, triad, seventh


def parts_token(parts: Parts, *, level: str = DEFAULT_LEVEL) -> str:
    """The one-character token for ``(root, triad, seventh)`` at ``level``."""
    root, triad, seventh = parts
    if level == "root":
        triad = seventh = 0
    elif level == "triads":
        seventh = 0
    return chr(CHAR_BASE + root * CLASSES_PER_ROOT + triad * N_SEVENTHS + seventh)


def token_parts(char: str) -> Parts | None:
    """Inverse of :func:`parts_token` (``None`` for :data:`NO_CHORD`)."""
    if char == NO_CHORD:
        return None
    root, rest = divmod(ord(char) - CHAR_BASE, CLASSES_PER_ROOT)
    triad, seventh = divmod(rest, N_SEVENTHS)
    return root, triad, seventh


def transpose_token(char: str, semitones: int) -> str:
    """``char`` moved up ``semitones`` (``NO_CHORD`` stays)."""
    parts = token_parts(char)
    if parts is None:
        return char
    root, triad, seventh = parts
    return parts_token(((root + semitones) % 12, triad, seventh), level="tetrads")


def token(
    symbol: str, *, level: str = DEFAULT_LEVEL, dialect: str | Dialect = "default"
) -> str:
    """The one-character token of a chord symbol at ``level``; :data:`NO_CHORD` if not a chord."""
    parts = chord_parts(symbol, dialect=dialect)
    return NO_CHORD if parts is None else parts_token(parts, level=level)


def collapse_runs(chars: Iterable[str]) -> list[tuple[str, int, int]]:
    """Runs of equal tokens as ``(token, first index, last index)``.

    >>> collapse_runs("aabcc")
    [('a', 0, 1), ('b', 2, 2), ('c', 3, 4)]
    """
    runs: list[tuple[str, int, int]] = []
    for i, char in enumerate(chars):
        if runs and runs[-1][0] == char:
            runs[-1] = (char, runs[-1][1], i)
        else:
            runs.append((char, i, i))
    return runs


def split_item(item) -> tuple[str, object]:
    """``(symbol, payload)`` of a sequence item: a bare symbol, or a ``(symbol, payload)`` pair.

    >>> split_item("Am"), split_item(("Am", {"t": 1.5}))
    (('Am', None), ('Am', {'t': 1.5}))
    """
    if isinstance(item, str):
        return item, None
    symbol, payload = item
    return symbol, payload


def encode(
    sequence: Iterable,
    *,
    level: str = DEFAULT_LEVEL,
    collapse: bool = True,
    dialect: str | Dialect = "default",
) -> tuple[list[tuple[str, int, int]], list]:
    """A sequence as token runs ``(token, first, last)`` over its original indices, plus its items.

    With ``collapse=True`` (default) consecutive equal tokens share one run, so a chord
    held for four bars and one written once are the same; with ``collapse=False`` every
    item is its own run.
    """
    check_level(level)
    items = list(sequence)
    chars = [
        token(split_item(item)[0], level=level, dialect=dialect) for item in items
    ]
    if collapse:
        return collapse_runs(chars), items
    return [(c, i, i) for i, c in enumerate(chars)], items
