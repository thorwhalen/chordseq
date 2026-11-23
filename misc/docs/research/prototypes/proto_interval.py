"""Third prototype: an interval stream (delta root from previous chord, family) so a contiguous
transposition-invariant query is ONE literal; absolute stream kept for gapped verification.
Also: numpy vectorised scan of the absolute stream for comparison."""

import bisect, collections, pickle, re, sys, time
import numpy as np

SEC, END = 0xFE, 0xFF
seqs = pickle.load(open(sys.argv[1], "rb"))
absb = bytearray()
ivb = bytearray()
offsets = []
for _, _, toks in seqs:
    offsets.append(len(absb))
    prev = None
    for b in toks:
        absb.append(b)
        if b >= SEC:
            ivb.append(b)
            prev = None
            continue
        ivb.append(
            (0 if prev is None else ((b // 5 - prev // 5) % 12)) * 5 + b % 5
            if prev is not None
            else 0xF0 + b % 5
        )  # first chord of a run: 0xF0+family (interval undefined)
        prev = b
    absb.append(END)
    ivb.append(END)
absb, ivb = bytes(absb), bytes(ivb)
offs = np.array(offsets)
print(f"abs {len(absb)} iv {len(ivb)}")
pops = np.array([p for _, p, _ in seqs])


def iv_pattern(bs):
    # first token: any byte whose family matches (interval unknown): 12 intervals + 0xF0 form -> char class
    fam0 = bs[0] % 5
    first = (
        b"["
        + b"".join(re.escape(bytes([i * 5 + fam0])) for i in range(12))
        + re.escape(bytes([0xF0 + fam0]))
        + b"]"
    )
    rest = b"".join(
        re.escape(bytes([((b // 5 - a // 5) % 12) * 5 + b % 5]))
        for a, b in zip(bs, bs[1:])
    )
    return re.compile(b"(?=(" + first + rest + b"))")


def run_iv(name, bs):
    t = time.time()
    rx = iv_pattern(bs)
    starts = [m.start() for m in rx.finditer(ivb)]
    t1 = time.time()
    sids = np.searchsorted(offs, np.array(starts), side="right") - 1
    ids, counts = np.unique(sids, return_counts=True)
    order = np.lexsort((-counts, -pops[ids]))
    print(
        f"IV  {name}: {len(starts)} matches in {len(ids)} songs; scan {1000 * (t1 - t):.0f} ms, group+rank {1000 * (time.time() - t1):.0f} ms"
    )


A_ = np.frombuffer(absb, dtype=np.uint8)


def run_np(name, bs):
    t = time.time()
    n = len(bs)
    L = len(A_) - n + 1
    hit = np.zeros(L, dtype=bool)
    roots = A_ // 5
    fams = A_ % 5
    for r in range(12):
        m = np.ones(L, dtype=bool)
        for k, b in enumerate(bs):
            want_r = (b // 5 + r) % 12
            want_f = b % 5
            m &= (roots[k : k + L] == want_r) & (fams[k : k + L] == want_f)
        hit |= m
    starts = np.flatnonzero(hit)
    t1 = time.time()
    sids = np.searchsorted(offs, starts, side="right") - 1
    ids, counts = np.unique(sids, return_counts=True)
    print(
        f"NP  {name}: {len(starts)} matches in {len(ids)} songs; scan {1000 * (t1 - t):.0f} ms, group {1000 * (time.time() - t1):.0f} ms"
    )


A, E, F, C, G, D, Am, Em, Bm = 45, 20, 25, 0, 35, 10, 46, 21, 56
for name, bs in [
    ("Am E F", [Am, E, F]),
    ("C G Am F", [C, G, Am, F]),
    ("Am F C G", [Am, F, C, G]),
    ("C F C G F C", [C, F, C, G, F, C]),
    ("D A Bm G", [D, A, Bm, G]),
    ("Em C (2 chords)", [Em, C]),
]:
    run_iv(name, bs)
    run_np(name, bs)
