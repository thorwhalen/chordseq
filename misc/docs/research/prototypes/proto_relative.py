"""Fourth prototype: numpy scan matching root intervals relative to the pattern's first chord,
so the 12 transpositions cost one pass. Also writes the streams for a JS timing run."""
import pickle, resource, sys, time
import numpy as np
SEC, END = 0xFE, 0xFF
seqs = pickle.load(open(sys.argv[1], "rb"))
absb = bytearray(); offsets = []
for _, _, toks in seqs:
    offsets.append(len(absb)); absb.extend(toks); absb.append(END)
A_ = np.frombuffer(bytes(absb), dtype=np.uint8); offs = np.array(offsets); pops = np.array([p for _, p, _ in seqs], dtype=np.float32)
open(sys.argv[2], "wb").write(bytes(absb)); np.save(sys.argv[2] + ".offsets.npy", offs.astype(np.uint32))
chord = A_ < SEC; roots = np.where(chord, A_ // 5, 255).astype(np.uint8); fams = np.where(chord, A_ % 5, 255).astype(np.uint8)
print(f"RSS after arrays: {resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/2**20:.0f} MB; stream {len(A_)} bytes")

def scan(bs, wild=None):
    """bs: pattern bytes; wild: set of positions that match any chord."""
    wild = wild or set(); n = len(bs); L = len(A_) - n + 1
    r0 = roots[0:L]; q0 = bs[0] // 5
    m = (fams[0:L] == bs[0] % 5)
    for k in range(1, n):
        if k in wild: m &= chord[k:k+L]; continue
        m &= ((roots[k:k+L].astype(np.int16) - r0) % 12 == (bs[k]//5 - q0) % 12) & (fams[k:k+L] == bs[k] % 5)
    return np.flatnonzero(m)

def run(name, bs, wild=None):
    t = time.time(); starts = scan(bs, wild); t1 = time.time()
    sids = np.searchsorted(offs, starts, side="right") - 1
    ids, counts = np.unique(sids, return_counts=True); order = np.lexsort((-counts, -pops[ids]))
    print(f"{name}: {len(starts)} matches in {len(ids)} songs; scan {1000*(t1-t):.0f} ms, rank {1000*(time.time()-t1):.0f} ms")
A, E, F, C, G, D, Am, Em, Bm = 45, 20, 25, 0, 35, 10, 46, 21, 56
run("Am E F", [Am, E, F]); run("C G Am F", [C, G, Am, F]); run("Am F C G", [Am, F, C, G]); run("C F C G F C", [C, F, C, G, F, C]); run("Em C", [Em, C]); run("Am . F", [Am, 0, F], wild={1})
print(f"RSS end: {resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/2**20:.0f} MB")
