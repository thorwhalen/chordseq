"""Smoke test on real Chordonomicon progressions: search, n-grams and spans, end to end.

Reads the first rows of the Chordonomicon dataset (CC-BY-NC) over the public datasets-server
JSON API with the standard library; skipped when the network is not there. Run alone with
``pytest tests/test_smoke.py``.
"""

import json
import re
import urllib.parse
import urllib.request

import pytest

from chordseq import find, ngrams

ROWS_URL = "https://datasets-server.huggingface.co/rows"
N_ROWS = 20


def chordonomicon_progressions(n=N_ROWS):
    query = urllib.parse.urlencode(
        dict(
            dataset="ailsntua/Chordonomicon",
            config="default",
            split="train",
            offset=0,
            length=n,
        )
    )
    with urllib.request.urlopen(f"{ROWS_URL}?{query}", timeout=30) as response:
        rows = json.load(response)["rows"]
    # Section markers like <verse_1> are not chords: they stay in and break matches.
    return [re.findall(r"<\w+>|\S+", r["row"]["chords"]) for r in rows]


@pytest.fixture(scope="module")
def progressions():
    try:
        return chordonomicon_progressions()
    except OSError as error:
        pytest.skip(f"Chordonomicon not reachable: {error}")


def test_real_progressions(progressions):
    hits = list(find("Amin F C G", progressions[0], dialect="chordonomicon"))
    assert all(m.symbols for m in hits)
    counts = ngrams(progressions, n=4, dialect="chordonomicon")
    assert counts, "no 4-grams counted"
    (gram, count), *_ = counts.most_common(1)
    assert count >= 1 and len(gram) == 4
    # The same query, transposed, finds at least what the literal one does.
    literal = [
        m
        for p in progressions
        for m in find(
            "C F G", p, dialect="chordonomicon", transposition_invariant=False
        )
    ]
    anykey = [
        m for p in progressions for m in find("C F G", p, dialect="chordonomicon")
    ]
    assert len(anykey) >= len(literal)
