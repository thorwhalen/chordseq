"""Second prototype: the token stream as one bytes object, queries as compiled bytes regexes
(12 transposition alternatives, wildcards/gaps as regex), song id by bisect on offsets."""
import array, bisect, collections, pickle, re, sys, time
SEC, END = 0xFE, 0xFF
seqs = pickle.load(open(sys.argv[1], "rb"))
stream = bytearray(); offsets = []
for _, _, toks in seqs:
    offsets.append(len(stream)); stream.extend(toks); stream.append(END)
stream = bytes(stream); print(f"stream {len(stream)} bytes")
pops = [p for _, p, _ in seqs]
CH = b"[\\x00-\\x3b]"  # any chord byte (12 roots x 5 families = 60)

def lit(b): return re.escape(bytes([b]))
def transposed(pattern, r):
    """pattern: list of items; item = int byte | '.' | '*' | ('?', byte) | ('|', [bytes])."""
    out = []
    for it in pattern:
        if it == ".": out.append(CH)
        elif it == "*": out.append(CH + b"*")
        elif isinstance(it, tuple) and it[0] == "?": out.append(b"(?:" + lit(((it[1]//5 + r) % 12)*5 + it[1]%5) + b")?")
        elif isinstance(it, tuple) and it[0] == "|": out.append(b"(?:" + b"|".join(lit(((x//5 + r) % 12)*5 + x%5) for x in it[1]) + b")")
        else: out.append(lit(((it//5 + r) % 12)*5 + it%5))
    return b"".join(out)
def compile_query(pattern, transpose=True):
    alts = [transposed(pattern, r) for r in (range(12) if transpose else [0])]
    return re.compile(b"(?=(" + b"|".join(alts) + b"))")  # overlapping matches
def run(name, pattern, transpose=True, sort="pop"):
    t = time.time(); rx = compile_query(pattern, transpose)
    per = collections.Counter()
    for m in rx.finditer(stream):
        per[bisect.bisect_right(offsets, m.start()) - 1] += 1
    t1 = time.time()
    ranked = sorted(per.items(), key=lambda kv: (-pops[kv[0]], -kv[1]))
    print(f"{name}: {sum(per.values())} matches in {len(per)} songs; scan {1000*(t1-t):.0f} ms, rank {1000*(time.time()-t1):.0f} ms")
A, E, F, C, G, D, Am, Em = 45, 20, 25, 0, 35, 10, 46, 21
run("Am E F", [Am, E, F])
run("C G Am F", [C, G, Am, F])
run("Am F C G", [Am, F, C, G])
run("Am . F (one wildcard)", [Am, ".", F])
run("Am * F (any run)", [Am, "*", F])
run("Am E? F (optional E)", [Am, ("?", E), F])
run("Am E|Em F", [Am, ("|", [E, Em]), F])
run("C G Am F exact key only", [C, G, Am, F], transpose=False)
run("12-bar-ish: C F C G F C", [C, F, C, G, F, C])
run("D A Bm G", [D, A, 11*5+1, G])
