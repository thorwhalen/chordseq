"""Prototype of the chord-sequence index, to measure sizes and query times on the real corpus.

Stream: one byte per chord = root*5 + family (M m d a o), consecutive repeats collapsed,
0xFE = section boundary, 0xFF = song boundary. Postings: transposition-normalised 3-grams
(first root 0, later roots as intervals from the first) -> sorted song ids, varint-delta coded.
Stats only; the cached sequences live in the scratchpad, nothing is written to the repo.
Usage: python proto_index.py <cache.pkl>  (builds the cache on first run)
"""
import array, collections, gzip, json, os, pickle, sys, time, zlib
FAM = {"major": 0, "minor": 1, "diminished": 2, "open": 4}  # 3 = augmented (not in harmony.py yet)
SEC, END = 0xFE, 0xFF

def load_sequences(cache):
    if os.path.exists(cache):
        with open(cache, "rb") as f: return pickle.load(f)
    from songleaf.sources import KaggleChordsSource
    from songleaf.harmony import parse_chord
    src = KaggleChordsSource(); ids = src._ids; pops = src._popularity
    seqs = []  # per song: list of (byte,) with SEC markers
    t = time.time()
    for row in range(len(ids)):
        try: song = src.get(ids[row])
        except Exception: seqs.append((ids[row], pops[row], [])); continue
        marks = sorted(a.start for a in song.of_kind("section"))
        out, mi, prev = [], 0, None
        for a in song.of_kind("chord"):
            while mi < len(marks) and marks[mi] <= a.start:
                if out and out[-1] != SEC: out.append(SEC); prev = None
                mi += 1
            p = parse_chord(a.body["symbol"])
            if p is None: continue
            b = p[0] * 5 + FAM[p[1]]
            if b != prev: out.append(b); prev = b
        seqs.append((ids[row], pops[row], out))
        if row % 20000 == 0: print(f"  parsed {row} ({time.time()-t:.0f}s)", flush=True)
    with open(cache, "wb") as f: pickle.dump(seqs, f)
    return seqs

def norm3(a, b, c):
    """Transposition-normalised key of three tokens."""
    r0 = a // 5
    return ((a % 5), ((b // 5 - r0) % 12) * 5 + b % 5, ((c // 5 - r0) % 12) * 5 + c % 5)

def varint(n, out):
    while n >= 0x80: out.append((n & 0x7F) | 0x80); n >>= 7
    out.append(n)

def main(cache):
    t0 = time.time(); seqs = load_sequences(cache); print(f"sequences: {len(seqs)} ({time.time()-t0:.0f}s)")
    stream = array.array("B"); offsets = array.array("I"); post = collections.defaultdict(list)
    ntok = 0
    for sid, (song_id, pop, toks) in enumerate(seqs):
        offsets.append(len(stream)); stream.extend(toks); stream.append(END); ntok += sum(1 for x in toks if x < SEC)
        seen = set()
        for i in range(len(toks) - 2):
            a, b, c = toks[i], toks[i+1], toks[i+2]
            if a >= SEC or b >= SEC or c >= SEC: continue
            seen.add(norm3(a, b, c))
        for k in seen: post[k].append(sid)
    print(f"tokens {ntok}, stream bytes {len(stream)}, songs {len(offsets)}, 3-gram keys {len(post)}, postings {sum(map(len, post.values()))}")
    enc = bytearray(); keyidx = {}
    for k, ids in post.items():
        keyidx[k] = (len(enc), len(ids)); prev = -1
        for s in ids: varint(s - prev - 1, enc); prev = s
    sb = stream.tobytes()
    print(f"postings varint bytes {len(enc)}, gzip {len(gzip.compress(enc, 9))}; stream gzip {len(gzip.compress(sb, 9))}; key table ~{len(post)*8}")
    pops = sorted(((p, i) for i, (_, p, _) in enumerate(seqs)), reverse=True)
    top = set(i for _, i in pops[:20000]); topbytes = sum(len(seqs[i][2]) + 1 for i in top)
    print(f"top-20K-songs stream bytes {topbytes}, gzip {len(gzip.compress(bytes(x for i in sorted(top) for x in seqs[i][2] + [END]), 9))}")
    # 4-gram count
    seen4 = 0; keys4 = set()
    for _, _, toks in seqs:
        s = set()
        for i in range(len(toks) - 3):
            w = toks[i:i+4]
            if max(w) >= SEC: continue
            r0 = w[0] // 5; s.add(tuple(((x // 5 - r0) % 12) * 5 + x % 5 for x in w))
        seen4 += len(s); keys4 |= s
    print(f"4-gram keys {len(keys4)}, postings {seen4}")
    # queries: Am E F ; C G Am F ; Am E F with gap (Am . F); 12 transpositions collapse to one key
    def q(pattern_bytes, name):
        t = time.time(); key = norm3(*pattern_bytes[:3]); cands = post.get(key, [])
        hits = []
        for sid in cands:
            toks = seqs[sid][2]; n = 0
            for i in range(len(toks) - len(pattern_bytes) + 1):
                w = toks[i:i+len(pattern_bytes)]
                if max(w) >= SEC: continue
                r = (w[0] // 5 - pattern_bytes[0] // 5) % 12
                if all(((x // 5 - r) % 12) * 5 + x % 5 == pb for x, pb in zip(w, pattern_bytes)): n += 1
            if n: hits.append((seqs[sid][1], n, sid))
        hits.sort(reverse=True)
        print(f"query {name}: {len(cands)} candidates, {len(hits)} songs, {1000*(time.time()-t):.1f} ms; top: {[(round(h[0]),h[1]) for h in hits[:3]]}")
    A, E, F, C, G, Am = 9*5, 4*5, 5*5, 0, 7*5, 9*5+1
    q([Am, E, F], "Am E F"); q([C, G, Am, F], "C G Am F (axis)"); q([Am, F, C, G], "Am F C G"); q([E, Am], "E Am (2 chords: no 3-gram key)" ) if False else None
    print(f"total {time.time()-t0:.0f}s")

if __name__ == "__main__": main(sys.argv[1])
