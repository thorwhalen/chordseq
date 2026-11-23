// JS timing of the browser-side scan: one pass over the Uint8Array stream, relative roots.
import { readFileSync } from "node:fs";
const stream = new Uint8Array(readFileSync(process.argv[2]));
const offs = new Uint32Array(readFileSync(process.argv[2] + ".offsets.npy").buffer.slice(128)); // npy header is 128 bytes here
const SEC = 0xFE;
function scan(bs, wild = new Set()) {
  const n = bs.length, L = stream.length - n + 1, q0 = bs[0] / 5 | 0, f0 = bs[0] % 5;
  const dr = bs.map(b => (((b / 5 | 0) - q0) % 12 + 12) % 12), df = bs.map(b => b % 5);
  const hits = [];
  outer: for (let i = 0; i < L; i++) {
    const a = stream[i]; if (a >= SEC || a % 5 !== f0) continue;
    const r0 = a / 5 | 0;
    for (let k = 1; k < n; k++) {
      const x = stream[i + k]; if (x >= SEC) continue outer;
      if (wild.has(k)) continue;
      if ((((x / 5 | 0) - r0) % 12 + 12) % 12 !== dr[k] || x % 5 !== df[k]) continue outer;
    }
    hits.push(i);
  }
  return hits;
}
function songOf(pos) { let lo = 0, hi = offs.length; while (lo < hi) { const m = (lo + hi) >> 1; if (offs[m] <= pos) lo = m + 1; else hi = m; } return lo - 1; }
function run(name, bs, wild) {
  const t = performance.now(); const hits = scan(bs, wild); const t1 = performance.now();
  const per = new Map(); for (const h of hits) { const s = songOf(h); per.set(s, (per.get(s) || 0) + 1); }
  console.log(`${name}: ${hits.length} matches in ${per.size} songs; scan ${(t1 - t).toFixed(0)} ms, group ${(performance.now() - t1).toFixed(0)} ms`);
}
const [A, E, F, C, G, D, Am, Em, Bm] = [45, 20, 25, 0, 35, 10, 46, 21, 56];
for (let rep = 0; rep < 2; rep++) {
  run("Am E F", [Am, E, F]); run("C G Am F", [C, G, Am, F]); run("C F C G F C", [C, F, C, G, F, C]); run("Em C", [Em, C]); run("Am . F", [Am, 0, F], new Set([1]));
}
