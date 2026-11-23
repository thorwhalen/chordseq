# Chord-sequence search in the browser: client-side index options for songleaf

Research date: 2026-11-08. Scope: running the chord-sequence search on the phone, for a vanilla-JS page served from a Python package with no build step, behind a memory-constrained server. Sizes marked *measured* were taken from the published npm artifacts on this date; everything marked *estimate* shows its arithmetic.

## Summary and recommendation

The corpus is small once it is encoded for the job: ~15M chord tokens over a 48-symbol transposition-invariant alphabet (12 root intervals × 4 qualities) is **~15 MB as one byte per token, before compression** (estimate), and a song-level 3-gram postings index over it is **~4-6 MB varint-coded** (estimate). Nothing off the shelf matches this shape: the pure-JS libraries (FlexSearch, MiniSearch, Orama, Lunr, Fuse) are bag-of-words engines with no ordered-sequence query; the SQLite-in-WASM route gives phrase and NEAR queries through FTS5 but costs a 0.35-0.41 MB (compressed) engine plus a ~24 MB (estimate) index or a latency-bound range-request VFS; DuckDB-WASM is 35-41 MB of wasm and out of the question on a phone; the Rust-to-WASM text indexes are either unmaintained (Stork, tantivy-wasm) or built for web pages, not symbol sequences (Pagefind).

Recommendation: **build a hand-rolled index as typed arrays in a few static binary files, computed by the Python side and served as content-hashed immutable assets; the page searches in a Web Worker in plain JS.** Shard it the way Pagefind and the static-SQLite technique do: posting lists grouped by the query's first n-gram so a query downloads only the lists it touches (tens of KB), and the token stream sharded by popularity so the popular shard (top 20K songs, ~2.2 MB raw, ~0.5 MB compressed, estimate) is searchable within seconds on "Slow 4G" and the long tail arrives lazily or stays on the server. Transposition invariance comes from interval encoding, not from running twelve queries. The server does no per-request work: Starlette's `FileResponse` already answers HTTP Range requests with 206 (verified in the installed 0.49.3) and Caddy serves precompressed sidecars and partial content, so even the range-request variant needs no server code. Keep WASM as the upgrade path for the scan kernel (Rust, `fm-index` crate or a hand scan) only if a measured JS scan is too slow on a mid-range phone; design the kernel as one function over `Uint8Array`s so the swap is local.

Caching an index is a different category from songleaf's "URL is the state" rule: it is a derived, re-fetchable asset, like the page's own JS. Content-hashed URLs with `Cache-Control: max-age=31536000, immutable` get it cached by the ordinary HTTP cache, which is not even under Safari's script-writable storage quota or its 7-day eviction; no Cache API, IndexedDB or service worker is needed for v1.

## 1. Options for a client-side search index

| Option | Maturity / licence | Size (compressed over the wire) | Sequence queries | Transposition (12-way) | Verdict |
|---|---|---|---|---|---|
| Official `@sqlite.org/sqlite-wasm` + FTS5, whole DB loaded | 3.54.1, Apache-2.0 on npm [3]; FTS5 compiled in (`SQLITE_ENABLE_FTS5` present in the binary, measured) | wasm 0.88 MB raw, 407 KB gzip, 353 KB brotli (measured [4]); index ~24 MB est. (section 2) | Phrase (ordered tokens), `NEAR(... , N)` for gaps, trailing `*` prefix only [22] | Interval tokens → one query | **study**: right query language, wrong weight for a phone first load |
| Same engine over HTTP range requests (`sqlite-wasm-http` [7], the official-build successor of `sql.js-httpvfs` [1][6]) | `sqlite-wasm-http` 1.2.0, ISC, "experimental", last publish 2023-12 [7]; `sql.js-httpvfs` 0.8.12, Apache-2.0, last publish 2022-09 [6] | engine as above; per query only the pages touched: 70 KiB for an FTS5 search over an 8 MB FTS table in the original post [1] | as FTS5 | as FTS5 | **study**: latency-bound (dependent B-tree reads × 165-560 ms RTT on 4G [28]); the fallback backend without `SharedArrayBuffer` uses synchronous XHR in the worker [7] |
| `sql.js` (in-memory sqlite) | 1.15.2, MIT [5]; build has FTS3, not FTS5 (`SQLITE_ENABLE_FTS3` present, measured) | wasm 0.69 MB raw, 335 KB gzip, 290 KB brotli (measured [4]) | FTS3 phrase/NEAR | as above | **avoid**: whole DB in memory, older FTS |
| `wa-sqlite` | 1.0.0, MIT since 2023-02 [8] | 0.56 MB (sync) / 1.14 MB (asyncify) raw (measured [4]) | none: default build has no FTS (measured); needs an emcc rebuild | - | **avoid** (build burden for no gain over the official build) |
| DuckDB-WASM | 1.29.x, MIT [9] | `duckdb-mvp.wasm` 40.6 MB, `-eh` 35.7 MB, `-coi` 35.3 MB raw (measured [4]) | SQL only, no phrase index | SQL | **avoid** on a phone page |
| Pagefind (Rust→WASM, static chunks) | 1.6.0, MIT, active [11][12] | small WASM plus index chunks fetched by word prefix ("Created 27 index chunks" for 2,496 pages [12]; exact byte figures not verified) | word search over HTML pages; phrase support not verified | no | **study the design, do not depend**: the chunk-by-prefix layout is the pattern to copy |
| Stork (Rust→WASM) | Apache-2.0; README: "I'm winding down my work with Stork" [13] | not stated | word search | no | **avoid** |
| tantivy-wasm (Rust, range requests) | draft PR, unmerged, last activity 2022 [14] | 14 GB index searched with ~1.5 MB downloaded, ~2 s [14] | phrase | no | **avoid** (unmaintained), keep as a reference for the read-ahead design |
| `fm-index` crate (Rust) | 0.3.1, MIT OR Apache-2.0; SA-IS construction, multi-piece texts, sampled suffix array for `locate` [15] | index ≈ n·H_k bits + samples; wasm target not documented [15] | exact substring over an arbitrary `Character` alphabet; wildcards/gaps need extra work | interval tokens | **study**: the one library that natively does substring search over symbol sequences on a compressed index |
| FlexSearch | 0.8.212, Apache-2.0 [16] | 16.8 KB gzip (bundlephobia [21]); README says 4.5-16.3 KB by build [16] | no exact phrase; "context" scoring by proximity only [16] | no | **avoid** for sequences |
| MiniSearch | 7.2.0, MIT [17] | 5.7 KB gzip [21] | no phrase/positional [17] | no | **avoid** for sequences |
| Orama | 3.1.18, Apache-2.0 [18] | 24.4 KB gzip [21] | "exact match" on tokens; no phrase documented [18] | no | **avoid** for sequences |
| Lunr | 2.3.9, MIT, last publish 2023-07 [19] | 8.4 KB gzip [21] | leading/trailing/mid-term wildcards, no phrase [19] | no | **avoid** for sequences |
| Fuse.js | 7.5.0, Apache-2.0 [20] | 9.4 KB gzip [21] | fuzzy string matching only | no | **avoid** |
| Hand-rolled typed arrays (n-gram postings + token stream) in binary files | yours; ~300 lines JS + the Python builder | 3-6 MB full, <1 MB popular shard (estimates, section 2) | exact, gaps, wildcards, triad-only: all by construction | interval encoding: one pass | **build** (recommended) |
| Sharded static JSON | - | ints in JSON are ~2-3× the varint bytes and parse slowly (estimate) | - | - | **avoid** for postings; fine for small metadata |

How the alphabet makes the hard requirements cheap: encode each song as a sequence of (interval from previous root mod 12, quality) pairs, with the first chord carrying only its quality. A query "Am E F" becomes "(m) (+7, M) (+1, M)" and matches "Dm A Bb" with no second pass, which is the "12-way transposed query" collapsed to one. Triad-only versus exact-extension is two alphabets over the same positions: a 48-symbol triad alphabet (1 byte per token) and an extension alphabet (a dictionary of the few hundred distinct root-normalised symbols; 1 byte with an escape or 2 bytes). Index the triad alphabet; verify the extension alphabet against the candidate song's token run. Gaps, skips and single-chord wildcards are verification-time patterns over a candidate's ~111 tokens, not index features. One caveat: interval coding makes a skipped chord change the next interval, so a query with a gap must be verified with root-relative absolute positions within the candidate (recover absolute pitch classes by prefix-summing the intervals of the candidate; one small loop).

FTS5 would give phrase and NEAR queries with these tokens as "words" (a custom tokenizer or a tokenizer-friendly spelling such as `m i7M i1M`) [22], which is why it stays a "study": if the hand-rolled path turns out to need a query language, FTS5 over the same interval tokens is the fallback with a known cost.

## 2. Index size and load time (estimates, with arithmetic)

Inputs: 135K songs, ~15M tokens, so ~111 tokens per song on average. Alphabet: 12 × 4 = 48 symbols → 1 byte per token.

- **Token stream**: 15M × 1 B = **15 MB raw**; song offsets 135K × 4 B = 0.54 MB. Chord charts repeat sections, so the stream is highly compressible; a 4-8× ratio is plausible for brotli on a 48-symbol repetitive stream (estimate; measure) → **2-4 MB over the wire**. Popular shard of the top 20K songs by popularity: 20/135 × 15 MB ≈ **2.2 MB raw, ~0.5 MB compressed**.
- **3-gram postings, song level** (one posting per distinct 3-gram per song): possible 3-grams = 4 × 48 × 48 = 9,216; distinct per song perhaps 20-40 because of repeats → take 30 → ~4M postings. Raw `Uint32Array`: 16 MB. Delta-coded, varint: the common progressions dominate and have gaps of 1-2 songs (1 byte), rare ones have larger gaps (2 bytes), so ~1.1-1.3 B per posting → **~4.5-5.5 MB**, and gzip/brotli trims a varint-gap stream a further ~20-30% → **~3.5-4.5 MB over the wire**. Lemire and Boytsov report delta coding plus SIMD bit packing at a few bits per integer for sorted id lists [24]; VByte is the simple byte-aligned version of the same idea.
- **4-gram postings**: possible = 4 × 48³ ≈ 442K; occurring perhaps 50-100K; ~40 distinct per song → ~5.4M postings; average list length ~70 → average gap ~1,900 → 2 B varint → **~11 MB plus a 0.8 MB key table**, ~7-9 MB over the wire. More selective, twice the download; the 3-gram index plus verification is the better first cut, and 4-grams can be added for the most common 3-grams only (the Zipf head is where intersections get long).
- **Positional postings** (song id and position per occurrence): 15M × (~1.1 B gap + ~1 B position) ≈ **30 MB**, consistent with the textbook rule that a positional index is 2-4× a non-positional one [23]. Not needed: the token stream is the positional index, read per candidate.
- **Suffix array** over the stream: 15M × 4 B = 60 MB plus 15 MB text = **75 MB**, and a permutation does not compress. Avoid on a phone. A compressed suffix array / FM-index [27] over a 48-symbol, repetitive text would be a few bits per token plus a sampled suffix array (sampling 32 → 15M/32 × 4 B ≈ 1.9 MB), **~5-10 MB total** (estimate); Rust `fm-index` does this but wasm support is undocumented [15]. Construction is linear with SA-IS [26]; the classic suffix array is Manber and Myers [25].
- **FTS5**: SQLite's own measurement on a 1,636 MiB mail corpus gives detail=full at 743 MiB (45%), detail=column 340 MiB (21%), detail=none 134 MiB (8%) [22]. Tokens spelled as 3-4 characters plus a space make ~52 MB of "text"; detail=full (needed for phrase and NEAR [22]) → **~24 MB index**, plus 0.35-0.41 MB of engine. Over a range-request VFS only touched pages move: 70 KiB per FTS5 search in the original experiment [1], so perhaps 100-500 KB per query here, but in 10-50 small dependent reads.

What a phone will tolerate: Chrome DevTools' "Slow 4G" preset (renamed from "Fast 3G" in May 2024) is 1.6 Mbit/s × 0.9 = 180 KB/s down with 562.5 ms added latency; "Fast 4G" is 9 Mbit/s × 0.9 ≈ 1 MB/s with 165 ms [28]. So 1 MB is ~5.6 s on Slow 4G and ~1 s on Fast 4G; 4 MB is 22 s and 4 s. Ookla's 2025 global median mobile download is reported around 91-93 Mbit/s but that mixes 5G in [29] (secondary summary, not verified against the index itself). Budget: the page itself and the search code under ~100 KB; the first searchable shard (popular token stream + its postings) **≤ 1 MB compressed**, fetched after first paint; the full 3-6 MB only lazily, in the background, and cached. Anything larger must be range-fetched per query or kept on the server.

## 3. WASM versus JS

Plain JS over typed arrays is fast enough for postings intersections (a few thousand integers) and probably for the full scan: 15 MB per keystroke scanned by a tight `Uint8Array` loop is on the order of tens of milliseconds on a laptop and low hundreds on a mid-range phone (estimate; measure on a real device). WASM pays off for CPU-bound scans with SIMD (fixed-width SIMD is in Safari from 16.4, March 2023 [33]) and for structures like the FM-index whose inner loops JS JITs poorly; it costs a download (the sqlite engines above are 0.27-0.41 MB compressed, measured [4]) and a compile, which browsers overlap with the download through streaming compilation and a baseline tier (Firefox's baseline compiled 10-15× faster than its optimizer in 2018; V8's Liftoff plays the same role) [43][44]. Memory: Chrome allows 4 GB of wasm memory since M83 [31], but iOS Safari refuses large reservations: a Godot export failed on iOS 16.2 with a 2,048 MB `WebAssembly.Memory` maximum and worked at 256 MB [30]. Keep any wasm maximum at or below 256 MB; this index needs ~25 MB.

Responsiveness: run the search in a Web Worker, which exists for exactly this ("perform processor-intensive calculations without blocking the user interface thread"), can `fetch()` itself, and receives the index buffers as transferable `ArrayBuffer`s with zero copy [32]. Debounce input (100-150 ms), cancel the previous query on a new keystroke (a generation counter the worker checks between songs), stream the first results back early, and keep ranking by popularity on the worker so the main thread only renders.

## 4. Caching and versioning

Serve each index file under a content-hashed name with `Cache-Control: public, max-age=31536000, immutable`; the page's HTML names the current hashes (that is the "manifest"). MDN recommends exactly this pattern, including `immutable` to stop revalidation on reload [37]. The HTTP cache then does the work with no storage API, and it sits outside Safari's script-writable quota ("Cookies and HTTP cache are not bounded by this quota") [35].

If more than the HTTP cache is wanted later (true offline, a PWA): the Cache API, IndexedDB and OPFS share one origin quota; Safari 17 gives an origin up to 60% of disk in a browser app and evicts least-recently-used origins under pressure, with `navigator.storage.persist()` decided by heuristics such as being installed to the Home Screen [35]. Separately, WebKit deletes all script-writable storage (IndexedDB, LocalStorage, service worker registrations and caches) "after seven days of Safari use without user interaction on the site", with Home Screen web apps exempt [34]; Chrome allows an origin up to 60% of disk and evicts LRU [36]. For a derived index this is harmless: eviction means a re-download.

Is this a different category from "nothing in browser storage"? Yes. That rule keeps state in the URL so a sheet is reproducible from its link; an index is a cacheable immutable asset with no state in it, the same category as the page's `app.js`. Static-search projects treat it that way: Pagefind, Kiwix and PMTiles all rely on the HTTP cache for immutable chunks [11][39][40]. Keep the rule as stated and add one line: "immutable, content-hashed assets (code and index) may be cached by the browser; nothing else".

## 5. Hybrid designs

- **Server computes candidate ids, client ranks and filters.** Cheap for the server: the postings (~5 MB) and even the token stream (15 MB) sit comfortably in a worker process; the memory rule guards against the 1.1-1.6 GB DataFrame, not a 20 MB index. Cost: one round trip per keystroke (165-560 ms on 4G [28]) and every parameter change (gaps, triad-only) is a round trip too.
- **Client holds the popular shard, server holds the long tail.** Good fit: instant results from the shard, long-tail results merged in when the server answers; unknown-popularity songs are in the long tail by definition, which matches "unknown is probably not popular".
- **Server returns only the postings the query touches.** Make them static files: group posting lists by first symbol (48 files of ~100 KB, or 48 × 48 files of a few KB) and the client fetches only the groups its n-grams fall in. This is Pagefind's chunk-by-prefix layout [12] and the static-SQLite insight [1] without SQLite; it needs no server compute, works over the HTTP cache, and Starlette's `FileResponse` (206, `accept-ranges: bytes`, verified in the installed 0.49.3 [42]) and Caddy's `file_server` (206 partial content, precompressed sidecars [41]) already serve it.

Recommended composition: the third design for postings, the second for the token stream (popular shard first, remaining shards lazily or on demand), and a separate tiny popularity file (135K × 1-2 B = 135-270 KB, quantised rank) refreshed on its own schedule, so "popularity refreshed periodically" does not invalidate the index.

## 6. Prior art

- The static-SQLite post [1]: 670 MiB database on GitHub Pages, 1 KiB pages, three read-ahead heads, ~1 KB fetched for a key lookup, 130-270 KiB for a complex query, 70 KiB for an FTS5 search over an 8 MB table. Its lessons are page alignment, read-ahead, and "indexes must fit the queries or every miss is a round trip". Successors: `sqlite-wasm-http` [7] (official build, shared cache needs COOP/COEP; fallback without it) and the SQLite project's own OPFS VFS, which needs COOP/COEP headers and Workers, or `opfs-sahpool` which does not [2].
- Pagefind [11][12]: Rust indexer, small WASM searcher, index split into chunks loaded by the prefix typed. Stork [13] is winding down; Lunr prebuilt indexes [19] are the older static-site pattern and have wildcards but no phrases.
- DuckDB-WASM reads remote Parquet by byte range ("we may not need to download the entire file for a query but only required bytes") [10] but ships 35-41 MB of wasm (measured [4]); the right tool for analysts' tabs, not for phones.
- Kiwix-JS (GPL-3) searches offline Wikipedia in the browser: fast title index built into the ZIM, slower Xapian full-text through libzim compiled to wasm, requiring Atomics (Safari iOS 15+) [39]. PMTiles serves a whole map from one static file through range requests and lists which hosts honour them [40]. In-browser OpenStreetMap offline *search* (geocoding) prior art was not found in this pass; not verified.

## Terminology and what an expert would add

Terms: inverted index and posting lists; k-gram (n-gram) index; positional index and phrase query; proximity or NEAR query; delta (gap) coding and VByte/varint; suffix array; FM-index / compressed suffix array and backward search; interval (relative) encoding for transposition invariance; static or "serverless" search; HTTP range requests and lazy VFS; cache busting with content-hashed, immutable assets; search-as-you-type / incremental search with debounce; Web Worker offloading with transferable buffers.

Accessibility of search-as-you-type on a phone: use the WAI-ARIA combobox pattern: the input has `role="combobox"`, `aria-expanded`, `aria-controls` to a `listbox`, `aria-autocomplete="list"`, and DOM focus stays on the input while `aria-activedescendant` names the highlighted result [38]; add a polite live region that announces the result count after a pause so VoiceOver does not chatter on every keystroke (the APG page itself does not cover live regions; this is the common complement). Keep results in the URL (`?chords=Am+E+F&gaps=1`) so Back and sharing keep working, which songleaf already does for sheets.

Offline and PWA: a service worker plus the Cache API makes the page work offline, but on iOS the 7-day eviction applies unless the user installs the page to the Home Screen [34], and a service worker must never cache authenticated API responses; for a private app this is a later, explicit decision, not part of the index work.

## REFERENCES

1. [Hosting SQLite databases on GitHub Pages (phiresky, 2021)](https://phiresky.github.io/blog/2021/hosting-sqlite-databases-on-github-pages/)
2. [SQLite WASM: persistent storage options (OPFS, opfs-sahpool, kvvfs)](https://sqlite.org/wasm/doc/trunk/persistence.md)
3. [@sqlite.org/sqlite-wasm on npm](https://www.npmjs.com/package/@sqlite.org/sqlite-wasm)
4. [jsDelivr package file listing used for the measured wasm sizes (sqlite-wasm 3.54.1-build1; same API for sql.js 1.15.2, wa-sqlite 1.0.0, duckdb-wasm 1.29.0)](https://data.jsdelivr.com/v1/packages/npm/@sqlite.org/sqlite-wasm@3.54.1-build1?structure=flat)
5. [sql.js (GitHub)](https://github.com/sql-js/sql.js)
6. [sql.js-httpvfs (GitHub)](https://github.com/phiresky/sql.js-httpvfs)
7. [sqlite-wasm-http (GitHub)](https://github.com/mmomtchev/sqlite-wasm-http)
8. [wa-sqlite (GitHub)](https://github.com/rhashimoto/wa-sqlite)
9. [DuckDB-Wasm overview (DuckDB docs)](https://duckdb.org/docs/2.0/clients/wasm/overview.html)
10. [DuckDB-Wasm: Efficient Analytical SQL in the Browser (DuckDB blog, 2021)](https://duckdb.org/2021/10/29/duckdb-wasm.html)
11. [Pagefind (GitHub)](https://github.com/Pagefind/pagefind)
12. [Pagefind documentation](https://pagefind.app/docs/)
13. [Stork (GitHub)](https://github.com/jameslittle230/stork)
14. [tantivy PR #1067: make tantivy work in the browser with a statically hosted database](https://github.com/quickwit-oss/tantivy/pull/1067)
15. [fm-index crate documentation (docs.rs)](https://docs.rs/fm-index/latest/fm_index/)
16. [FlexSearch (GitHub)](https://github.com/nextapps-de/flexsearch)
17. [MiniSearch (GitHub)](https://github.com/lucaong/minisearch)
18. [Orama (GitHub)](https://github.com/oramasearch/orama)
19. [Lunr: Searching guide](https://lunrjs.com/guides/searching.html)
20. [fuse.js on npm](https://www.npmjs.com/package/fuse.js)
21. [Bundlephobia (minified and gzipped sizes)](https://bundlephobia.com/)
22. [SQLite FTS5 Extension](https://www.sqlite.org/fts5.html)
23. [Manning, Raghavan, Schütze: Introduction to Information Retrieval, "Positional index size"](https://nlp.stanford.edu/IR-book/html/htmledition/positional-index-size-1.html)
24. [Lemire, Boytsov: Decoding billions of integers per second through vectorization (arXiv 1209.2137)](https://arxiv.org/abs/1209.2137)
25. [Manber, Myers: Suffix arrays: a new method for on-line string searches (SIAM J. Comput. 1993)](https://doi.org/10.1137/0222058)
26. [Nong, Zhang, Chan: Linear suffix array construction by almost pure induced-sorting (DCC 2009)](https://doi.org/10.1109/DCC.2009.42)
27. [Ferragina, Manzini: Opportunistic data structures with applications (FOCS 2000)](https://pages.di.unipi.it/ferragina/Libraries/fmindex/FM-pages/Abs_focs00.html)
28. [Chrome DevTools frontend source: NetworkManager.ts throttling presets](https://cdn.jsdelivr.net/npm/chrome-devtools-frontend@1.0.1593518/front_end/core/sdk/NetworkManager.ts)
29. [Mobile internet speeds by country 2026 (secondary summary of Ookla Speedtest Global Index)](https://cellesim.com/en/mobile-internet-speeds-by-country-2026)
30. [Godot issue #70621: WebAssembly maximum memory 2GB causes Out of Memory on iOS Safari 16.2](https://github.com/godotengine/godot/issues/70621)
31. [V8 blog: Up to 4GB of memory in WebAssembly (2020)](https://v8.dev/blog/4gb-wasm-memory)
32. [MDN: Using Web Workers](https://developer.mozilla.org/en-US/docs/Web/API/Web_Workers_API/Using_web_workers)
33. [Can I use: WebAssembly SIMD](https://caniuse.com/wasm-simd)
34. [WebKit blog: Full Third-Party Cookie Blocking and More (7-day cap on script-writable storage)](https://webkit.org/blog/10218/full-third-party-cookie-blocking-and-more/)
35. [WebKit blog: Updates to Storage Policy (Safari 17)](https://webkit.org/blog/14403/updates-to-storage-policy/)
36. [web.dev: Storage for the web](https://web.dev/articles/storage-for-the-web)
37. [MDN: HTTP caching (cache busting, immutable)](https://developer.mozilla.org/en-US/docs/Web/HTTP/Guides/Caching)
38. [W3C WAI-ARIA Authoring Practices: Combobox pattern](https://www.w3.org/WAI/ARIA/apg/patterns/combobox/)
39. [Kiwix JS (GitHub)](https://github.com/kiwix/kiwix-js)
40. [PMTiles (Protomaps docs)](https://docs.protomaps.com/pmtiles/)
41. [Caddy: file_server directive](https://caddyserver.com/docs/caddyfile/directives/file_server)
42. [Starlette (GitHub; FileResponse Range handling verified in the installed 0.49.3)](https://github.com/encode/starlette)
43. [Mozilla Hacks: Making WebAssembly even faster: Firefox's new streaming and tiering compiler (2018)](https://hacks.mozilla.org/2018/01/making-webassembly-even-faster-firefoxs-new-streaming-and-tiering-compiler/)
44. [web.dev: Loading WebAssembly modules efficiently](https://web.dev/articles/loading-wasm)
