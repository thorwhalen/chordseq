"""Behaviour of the query language, the matching defaults and the n-gram counts."""

import pytest
from chordsym import Key

from chordseq import QueryError, find, ngrams, parse_query, to_roman_sequence

SEQ = ["Am", "E7", "F", "C", "G", "Am", "E", "F"]


def spans(query, seq=SEQ, **kw):
    return [(m.start, m.stop) for m in find(query, seq, **kw)]


def test_triads_level_matches_sevenths_and_tetrads_does_not():
    assert spans("Am E F") == [(0, 3), (5, 8)]
    assert spans("Am E F", level="tetrads") == [(5, 8)]
    assert spans("Am E7 F", level="tetrads") == [(0, 3)]


def test_root_level_ignores_quality():
    assert spans("A E F", level="root") == [(0, 3), (5, 8)]


def test_transposition_invariance_and_literal_mode():
    assert [m.transposition for m in find("Dm A Bb", SEQ)] == [7, 7]
    assert spans("Dm A Bb", transposition_invariant=False) == []
    assert spans("Am E F", transposition_invariant=False) == [(0, 3), (5, 8)]


def test_wildcard_optional_and_alternatives():
    assert spans("Am . C") == []  # E7 F is two chords
    assert spans("Am . F") == [(0, 3), (5, 8)]
    assert spans("Am * C") == [(0, 4)]
    assert spans("Am E7? F") == [(0, 3), (5, 8)]
    assert spans("Am E|E7 F", level="tetrads") == [(0, 3), (5, 8)]


def test_repeats_collapse_but_spans_cover_originals():
    seq = ["C", "C", "G", "G", "G", "Am"]
    assert spans("C G Am", seq) == [(0, 6)]
    assert spans("C G Am", seq, collapse=False) == []


def test_non_chords_break_matches():
    seq = ["C", "<verse_2>", "G"]
    assert spans("C G", seq) == []
    assert spans("C . G", seq) == []


def test_roman_query_and_key():
    seq = ["Dm", "Bb", "F", "C"]
    assert spans("vi IV I V", seq) == [(0, 4)]
    assert spans("vi IV I V", seq, transposition_invariant=False, key=Key(5)) == [
        (0, 4)
    ]
    assert spans("vi IV I V", seq, transposition_invariant=False, key=Key(0)) == []
    with pytest.raises(ValueError, match="key"):
        find("vi IV", seq, transposition_invariant=False)


def test_payloads_ride_along():
    (m,) = find("Am E F", [("Am", 1), ("E7", 2), ("F", 3), ("C", 4)])
    assert m.payloads == (1, 2, 3) and m.symbols == ("Am", "E7", "F")


def test_bad_queries_are_refused_with_a_hint():
    with pytest.raises(QueryError, match="E\\|E7"):
        parse_query("Am E(7) F")
    with pytest.raises(QueryError, match="mixes"):
        parse_query("Am IV")
    with pytest.raises(QueryError, match="neither"):
        parse_query("Am Zz")
    with pytest.raises(QueryError):
        parse_query(". *")


def test_dialect_for_sequences():
    assert spans("Am F", ["Amin", "F"], dialect="chordonomicon") == [(0, 2)]


def test_ngram_levels_and_relativity():
    seq = ["C", "G7", "Am", "F"]
    assert ngrams([seq], 2, level="tetrads")[("I", "V7")] == 1
    assert ngrams([seq], 2)[("I", "V")] == 1
    assert ngrams([seq], 2, relative_to="first")[("I", "V")] == 1
    assert (
        ngrams([seq], 2, relative_to=None)[("G7", "Am")] == 0
    )  # triads level drops the 7
    assert ngrams([seq], 2, relative_to=None)[("G", "Am")] == 1


def test_ngram_sizes_and_pooling():
    seqs = [["C", "G", "Am", "F"], ["D", "A", "Bm", "G"]]
    pooled = ngrams(seqs, (2, 3, 4))
    assert pooled[("I", "V", "vi", "IV")] == 2
    assert sum(len(c) > 0 for c in ngrams(seqs, 2, per_sequence=True)) == 2


def test_to_roman_sequence():
    assert to_roman_sequence(["G", "D", "Em", "C", "G"]) == ["I", "V", "vi", "IV", "I"]
    assert to_roman_sequence(["Em", "N", "G"], key=Key(7)) == ["vi", None, "I"]
