"""chordseq: search chord progressions in any key, count n-grams, name chords by key.

>>> from chordseq import find, ngrams, to_roman_sequence
>>> [(m.start, m.stop) for m in find("Am F C", ["Dm", "Bb", "F", "G", "Em", "Bb", "G"])]
[(0, 3)]
>>> to_roman_sequence(["G", "D", "Em", "C", "G"])
['I', 'V', 'vi', 'IV', 'I']
>>> ngrams([["C", "G", "Am", "F"]], n=2).most_common(2)
[(('I', 'V'), 1), (('V', 'vi'), 1)]
"""

from chordseq.ngrams import ngrams
from chordseq.query import Query, QueryError, parse_query
from chordseq.roman import parse_roman, to_roman, to_roman_sequence
from chordseq.search import Match, find, search
from chordseq.tokens import LEVELS

__all__ = [
    "LEVELS",
    "Match",
    "Query",
    "QueryError",
    "find",
    "ngrams",
    "parse_query",
    "parse_roman",
    "search",
    "to_roman",
    "to_roman_sequence",
]
