# Chord-sequence search for songleaf: research synthesis and design

*2026-11-08 · scope: query notation, transposition-invariant matching, matching parameters, sequence indexes, client-side search, popularity data and ranking, prior art · requested for: a chord-sequence search in songleaf ("Am E(7) F" finds every song with that progression in any key), session songleaf-chordseq, phase 1 (research and design, no code in the repo yet).*

## Summary and recommendation

songleaf has **no chord-sequence index today**: the SQLite/FTS5 index covers titles, artists, the per-artist popularity number and lyric words; `harmony.py` parses a chord to (root, quality) for key estimation and transposition only. Nothing else in the fleet indexes chord sequences either (accompy, tonal, scoreseek's Chordonomicon source, sung were checked).

The recommendation, in one paragraph: encode every song once into a **packed byte stream** (one byte per chord: root × class, consecutive repeats collapsed, 21 chord classes reduced by the MIREX largest-subset rule, three levels: root, triads, exact), and answer a query with **one vectorised pass that compares root intervals relative to the pattern's first chord**, so the twelve transpositions cost one scan. Measured on the real corpus (135,783 songs, 8.39M chords after collapsing repeats): the stream is 8.7 MB (2.3 MB gzip, 1.9 MB brotli), a query takes 26-100 ms in Python with numpy and 57-98 ms in JavaScript on a laptop, and the same bytes serve the server and, later, a Web Worker in the page. Gaps, wildcards, optional chords, alternatives, loop rotations and section scope are all masks or post-filters on that scan. The special sequence indexes the user remembers (n-gram postings, suffix arrays, FM-index) are real and were measured or sized (a transposition-normalised 3-gram postings file is 2.3 MB and finds candidates in microseconds; a suffix array is about 43 MB here), but at 135K songs they only remove a scan that already fits in a keystroke; they are the named upgrade for Chordonomicon-scale corpora (680K songs).

The query notation is regex-shaped over plain chord symbols: `Am E7? F`, `Am E|E7 F`, `Am . F`, `Am * F`. The user's `E(7)` is **not** adopted as syntax because parentheses already mean alterations and additions in chord symbols (`C7(b9)`, `C(add9)`), so every parser reads `E(7)` as "E with a seventh"; at the default level (`triads`) `Am E F` already matches `Am E7 F`, and `E|E7` is the explicit form. Matching levels take mir_eval's names (`root`, `triads`, `tetrads`), which have exact published rules.

Ranking defaults to popularity, then in-song occurrence count. The corpus's `popularity` column turned out to be **Spotify artist popularity** (constant per artist, 25-100, a 2022 snapshot), not song popularity; it is the right prior and the wrong name. Spotify's API is no longer a viable bulk source (the field was removed for new Development Mode apps in February 2026 and the terms forbid storing it), so song-level signals come from **ListenBrainz (CC0)** with Last.fm and Deezer as private-use options, shrunk toward the artist prior; a song nothing knows inherits its artist's number inside the corpus and gets zero when it came from the web.

Build in four pull requests behind three seams (the index, the chord parser, the popularity source), server search first, the browser worker fourth over the same files. Six decisions are needed from the owner before building; they are listed in section 5.

## What already exists (in-house)

- songleaf: `harmony.parse_chord` (root pitch class + quality in {major, minor, diminished, open}), `transpose_chord`, `estimate_key`; the chart parser's chord and section annotations; `sung.chords_index` (SQLite + FTS5 over titles, artists, popularity, lyric words); `tools.search` as the one-query search; the vanilla-JS page with URL-as-state. No sequence index.
- Open issues that this design depends on or touches: songleaf#31 and songleaf#48 (extract chord-symbol parsing into a shared stdlib-only package; name proposed `chordsym`, awaiting the owner), songleaf#3 (source survey), songleaf#61 and songleaf#62 (web search, owned by the sibling session songleaf-sources).
- Elsewhere in the fleet: accompy (chord-chart parsers including Roman and Nashville, backing tracks, heavy dependencies), tonal (music21-based), scoreseek's `ChordonomiconSource` (CC-BY-NC, no titles, live HTTP), the harmony-relations research note in the thoremin repo (neo-Riemannian relations and root motion; not about retrieval). None indexes sequences.
- On disk: the Kaggle chords-and-lyrics zip (135,783 songs) and Chordonomicon v2 (264 MB CSV, 679,807 progressions, Spotify ids, genres, decades, no titles) under the songleaf data root.

The five theme reports behind this synthesis are [1] notation and query language, [2] matching and sequence indexes, [3] client-side search, [4] popularity and ranking, [5] prior art. They are cited where a claim rests on them.

## 1. What the research found, by theme

**Notation and query language [1].** Harte et al. 2005 is the only formal chord grammar (`root:shorthand(degrees)/bass`, BNF published) and MIREX and mir_eval build on it [6][7][8]. mir_eval names the matching levels and gives their exact rules: `root` (roots equal), `thirds`, `triads` (root plus the bits from root to fifth), `tetrads` (the whole 12-bit interval set), each with an `_inv` variant that also compares the bass [8]. MIREX reduces a chord to a vocabulary by "the largest subset of the input interval set that is in the vocabulary" [7]. For optional and wildcard elements the precedent is regex, Lucene, Humdrum's `pattern` and Themefinder: `?`, `.`, `*`, `|`. Parentheses are chord syntax everywhere (alterations, adds, omits; Dorico even documents a parenthesised whole symbol as "an optional chord"), so `E(7)` is ambiguous [1]. Enharmonics are solved by pitch class arithmetic; the only locale trap is German `H`/`B`. Libraries: for the browser chord-symbol (MIT) and tonal (MIT); in Python pychord (MIT) and music21 (BSD-3) as study sources; mingus (GPL-3) and ChordSheetJS (GPL-2.0-only) must not become dependencies [1]. The corpus itself is largely in Brazilian notation (`7M` for maj7, `7+` for aug, `m5-/7` for m7b5, `º` for dim: see section 2), which `chordsym` must accept.

**Transposition-invariant matching and indexes [2].** Three representations: absolute tokens with the query run in all twelve transpositions, root-interval sequences (one query, index-friendly, but a skipped chord changes the next interval), and key-relative roman numerals (fails on modulation and on wrong key estimates; Hanna, Robine and Rocher measured absolute-plus-transposition at 0.840 first-tier against 0.71-0.72 for key-relative [9]). Hanna et al. also found that matching exact chord quality hurt similarity retrieval, which supports a triad-level default [9]. Index structures compared: SQLite FTS5 phrase queries (no new dependency, 12 OR'd phrases, `NEAR` for unordered gaps), positional n-gram postings, suffix arrays (pydivsufsort, MIT, builds 17M tokens in seconds, ~5 bytes per token [10]), FM-index (Rust crate, no mature JS build), and a linear scan of a packed byte array, which the report already judged sufficient for the browser at 135K songs [2]. Terminology: "chord sequence retrieval" (Hanna et al.), "harmonic similarity" (de Haas et al.), "pattern matching over a document collection" and "document listing" in string algorithms.

**Client-side search [3].** Nothing off the shelf does ordered symbol-sequence search on a phone: FlexSearch, MiniSearch, Orama, Lunr and Fuse are bag-of-words engines; the official SQLite WASM build has FTS5 but costs 0.35-0.41 MB of engine plus a ~24 MB index or latency-bound range reads; DuckDB-WASM is 35-41 MB. The recommendation is a hand-rolled index as typed arrays in static, content-hashed binary files, searched in a Web Worker in plain JS, popular shard first, with `Cache-Control: immutable` so the ordinary HTTP cache holds it (outside Safari's script-writable storage quota and its 7-day eviction) [3][11]. That cache is a different category from songleaf's "URL is the state" rule: an index is a derived, re-fetchable asset like `app.js`. Phone budget from Chrome's throttling presets: 1 MB is ~5.6 s on "Slow 4G", ~1 s on "Fast 4G" [3].

**Popularity [4].** The Kaggle corpus was built by walking a Spotify artists table sorted by popularity and scraping each artist's songs from e-chords; the `popularity` column is the artist's Spotify popularity copied onto every row (6,350 artists, 0 artists with two values, range 25-100, ≤ March 2022) [12][13]. Spotify's Web API removed `popularity` for Development Mode apps created from February 2026, removed Get Several Tracks, capped Search at 10 results, and its terms forbid compiling a database of Spotify content [14][15]. Usable sources: ListenBrainz popularity endpoints (CC0, batch by MusicBrainz id, no key) [16]; Last.fm (non-commercial, 100 MB stored-data cap, credit required); Deezer `rank` (no key, strong for the Portuguese and Spanish third of the corpus; terms non-commercial). Avoid YouTube (statistics may be stored 30 days), Genius, Musixmatch, Apple Music. Ranking with missing data: Bayesian shrinkage toward a prior (the IMDb form) [17], saturating transforms before mixing with a match score, reciprocal rank fusion for several sort keys [18]. The hypothesis "unknown means not popular" holds for the open catalogue (86% of streaming tracks had ≤ 1,000 plays in 2023) but not inside this corpus, which was selected from the popular end twice.

**Prior art [5].** Only Hooktheory's TheoryTab does real progression search over a large corpus (82K user-analysed songs, relative notation `1 5 6 4`, up to four chords, "Ignore Extensions & Inversions" and "Start of Section Only" switches, results ordered alphabetically, documented user complaints about minor-mode handling and unexplained partial matches) [19][20]. Chordify and Chord Genome are chord-*set* searches ("songs you can play with G C D"); Chord Genome's paid "Wildcard" (one chord you don't know) and "All Keys" are the only relaxations on the market. The architecture to copy is a three-commit hobby project, Jangle: Chordonomicon encoded as (semitones from the first chord's root, quality family), sliding windows of 3 and 4 chords, static JSON chunks fetched by the browser, no server [21]. No tool ranks by popularity, supports gaps or wildcards, shows the matched passage in context, or lets the user flip a hit between absolute and key-relative display. Those are the opportunities.

## 2. Measurements on the real corpus

Taken on 2026-11-08 with songleaf's own loader and parser over the full Kaggle corpus (scripts in the work folder: `corpus_stats.py`, `proto_index.py`, `proto_regex.py`, `proto_interval.py`, `proto_relative.py`, `proto_scan.mjs`). Stats only; no song text was written anywhere.

| Quantity | Measured |
|---|---|
| Songs / songs without any chord | 135,783 / 1,656 |
| Chord tokens (raw / after collapsing consecutive repeats) | 9,036,872 / 8,394,549 (92.5% kept) |
| Tokens per song: mean, p50, p90, p99, max | 66.6, 62, 114, 176, 1,552 |
| Sections per song (parsed headers) | 1.86 |
| Distinct raw symbols / symbols covering 99% of tokens | 10,230 / 1,066 |
| Distinct extension suffixes / suffixes covering 99% | 2,066 / 45 |
| Top suffixes | `''` 59%, `m` 22%, `7` 5.4%, `m7` 4.2%, `5`, `9`, `7M`, `maj7`, `dim`, `6`, `7+`, `sus4`, `add9`, `m6`, `4`, `sus2`, `m5-/7`, `7/9`, `sus`, `º`, `2`, `m9`, `7/9-` |
| Slash chords | 4.5% of tokens |
| (root, family) alphabet | 48 of 60 possible (no augmented quality in `harmony.py` yet) |
| Distinct transposition-normalised 3-grams / 4-grams | 5,831 / 55,465 (34,040 / 172,730 over the interval alphabet before normalising to the first root) |
| Packed stream (one byte per collapsed chord + a song terminator) | 8,687,281 B; gzip 2,294,181 B; brotli 1,896,167 B |
| Popular shard (top 20,000 songs by the corpus popularity) | 1,385,182 B; gzip 325,190 B |
| 3-gram postings (song ids, delta varint) | 2,070,821 postings → 2,334,813 B; gzip 1,638,301 B; key table ~47 KB |
| 4-gram postings | 2,574,935 postings (not encoded) |
| Query "Am E F" (12 transpositions, triad level) | 1,808 songs, 6,200 occurrences |
| Query "C G Am F" | 16,549 songs, 101,664 occurrences |
| Query "Em C" (two chords) | 57,622 songs |

Engine timings for the same queries (laptop; a mid-range phone is assumed 3-5× slower, to be measured):

| Engine | "Am E F" | "C G Am F" | 6 chords | 2 chords | wildcard "Am . F" | Notes |
|---|---|---|---|---|---|---|
| Python, 3-gram postings + per-candidate verification in pure Python | 110 ms | 2,175 ms | — | — | — | candidates in µs; the Python verification loop is the cost |
| Python `re` over the stream, 12 literal alternatives | 229 ms | 353 ms | 298 ms | — | 370 ms | `*` gap: 1,141 ms |
| Python `re` over an interval stream, one literal | 133 ms | 156 ms | 146 ms | 183 ms | — | the leading character class costs more than expected |
| **Python numpy, relative-root one pass** | **45 ms** | **58 ms** | **99 ms** | **26 ms** | **27 ms** | plus 1-26 ms to group by song and rank; 26 MB of arrays resident |
| **JavaScript (Node 23), same algorithm over `Uint8Array`** | **57 ms** | **94 ms** | **95 ms** | **63 ms** | **71 ms** | plus 1-37 ms grouping; this is the browser path |

Reading: at this corpus size a one-pass scan is already inside a keystroke, and it is the only engine that handles every parameter (gaps, wildcards, optional, alternatives, exact level, scope) by construction. The 3-gram postings file is small (2.3 MB) and finds candidates instantly, but its benefit only appears once verification is vectorised or the corpus grows several-fold; it is the browser's shard selector and the first upgrade, not the v1 engine.

## 3. Design

### 3.1 Terminology (the user's words, then the standard term)

| The request says | Standard term used from here on |
|---|---|
| "E(7): the seven is optional" | *matching level* (mir_eval `triads` vs `tetrads` [8]); explicit alternatives `E|E7`; an *optional chord* is `E7?` |
| "include transposed results", "Bb and A# both match" | *transposition-invariant matching* over *pitch classes* (enharmonic equivalence) |
| "the underlying triad is what the chord is" | *triad class* (root plus the intervals up to the fifth); extensions are *tetrads* and beyond |
| "special kinds of indexes to find sequences" | *positional inverted index of n-grams*, *suffix array*, *FM-index*; the whole task is *chord sequence retrieval* [9] |
| "computation of the search on the frontend" | *client-side (static) search* over *content-hashed immutable assets* in a *Web Worker* [3] |
| "how popular the song is", "assume unknown is not popular" | *popularity prior* (query-independent evidence), *shrinkage toward a prior* [17] |

### 3.2 Query language

A query is whitespace-separated chord patterns. A chord pattern is a chord symbol in any spelling `chordsym` accepts (`Am`, `E7`, `Bbmaj7/D`, `F#m7b5`, `C7M`, `Dm5-/7`, `N.C.`). Operators, all with regex, Lucene, Humdrum and Themefinder precedent [1]:

| Syntax | Meaning | Example |
|---|---|---|
| `X Y Z` | the chords in this order, contiguous (after collapsing repeats) | `Am E F` |
| `X?` | the chord is optional | `Am E7? F` = `Am F` or `Am E7 F` |
| `X|Y` | either chord here | `Am E|E7 F` |
| `.` | any one chord | `Am . F` |
| `*` | any run of chords, including none | `Am * F` |
| `(` `)` | never an operator: part of the chord symbol | `C7(b9)` is one chord |

What the user's examples become: `Am E(7) F` is rejected with a one-line hint ("parentheses are part of a chord symbol: write `Am E|E7 F`, or search at the triads level where `E` already matches `E7`"); the default level makes `Am E F` match `Am E7 F`, `Am E9 F` and `Am Emaj7 F`; `level=tetrads` with `Am E7 F` matches the dominant-seventh family only; `Am E F` with `transpose=True` (the default) also matches `Dm A Bb`, `Dm A A#`, `Bm F# G` and the other nine keys. Exactness per token is not syntax in v1 (the level is global); a prefix such as `=E7` is reserved if it is ever wanted.

### 3.3 Parameters

| Parameter | Values (default first) | What it does | Grounding |
|---|---|---|---|
| `level` | `triads`, `tetrads`, `root` | which projection of each chord is compared: triad class (maj, min, dim, aug, open); the full 21-class vocabulary; the root only (so `E` matches `Em`) | mir_eval levels and MIREX reduction [7][8]; Hanna et al.'s finding that strict quality hurts recall [9] |
| `transpose` | `True`, `False` | match in all twelve keys, or only as written | [2][9]; Chord Genome "All Keys", Hooktheory "Rel" [5] |
| `scope` | `section`, `song` | a match may not cross a section boundary (Verse, Chorus), or may | Hooktheory "Start of Section Only" [19]; Chordonomicon section tags [22] |
| `inversions` | `False`, `True` | ignore the bass note, or require it to match | mir_eval `_inv` [8]; Hanna et al. root vs bass scores 0.840 vs 0.808 [9] |
| `loop` | `False`, `True` | also match every rotation of the pattern (a 4-chord loop entered from any chord) | chordverse rotation matching [5] |
| `repeats` | `collapsed` (only value in v1) | `C C C G` and `C G` are the same sequence | Chordonomicon and Music Corpus Search collapse repeats [5][22] |
| `min_matches` | `1` | drop songs with fewer occurrences | expert addition in [2] |
| `sort` | `popularity`, `matches`, `coverage`, `title`, `artist`, `year` (year once a source carries it), several keys allowed in order | ranking, see 3.6 | [4] |
| `limit`, `offset` | `50`, `0` | paging | |

Not parameters in v1 (written directly, on purpose): the run-length rule, the class vocabulary, the byte layout, the detection rule that decides whether a search-box string is a chord sequence.

### 3.4 Representation and index

**Chord classes (exact level).** Twenty-one classes with Harte degree sets, assigned at build time by MIREX's largest-subset rule, so `G7(#9)` is class `7`, `Cadd9` is `add9`, `Dm5-/7` is `hdim7`, `E7M` is `maj7`, `C7+` is `aug` plus seventh, reduced to `aug` (or to `7` if a `aug7` class is added later), and anything unparseable is `X` [1][7]:

```
maj min dim aug sus4 sus2 5(power) 7 maj7 min7 dim7 hdim7 maj6 min6 9 add9 minmaj7 7sus4 min9 maj9 N
```

**Triad families (default level)** are a fixed projection of the class: maj, 7, maj7, maj6, 9, add9, maj9 → M; min, min7, min6, minmaj7, min9 → m; dim, dim7, hdim7 → d; aug → a; sus4, sus2, 5, 7sus4 → o (open, songleaf's existing name for "no third"). Whether `E` should match `Esus4` at the default level is a vocabulary choice (mir_eval `triads` says no); this design says no, and `level=root` says yes [1].

**Byte streams.** One byte per chord: `root * 21 + class` (0-251), 252 = unknown chord, 253 = song terminator; built once per corpus and level by `songleaf build-chord-index`, stored under the data root as `index/chordseq/<corpus>/<level>.bin` with a `offsets.u32` (song start per song), `ids.json` (song key per row), `sections.u32` (token positions where a section starts) and a `manifest.json` (version, content hashes, build date, corpus id). Three streams (exact, triads, root; repeats collapsed per level) cost about 26 MB on disk and in RAM, far from the 1.1-1.6 GB DataFrame the memory rule guards against; numpy views on the files give the `roots` and `families` arrays at load. A popularity array lives in its own file so a refresh never rebuilds the streams (section 3.6).

**Why no n-gram or suffix index in v1.** The one-pass scan is measured at 26-100 ms per query over all 135K songs and needs nothing beyond numpy, which pandas already pulls in. The 3-gram postings (2.3 MB, measured) become useful in two places and are built then: as the browser's shard selector (download only the songs that can match), and as a candidate filter when the corpus passes a few hundred thousand songs. The suffix array (pydivsufsort, MIT; about 43 MB here, ~5 bytes per token) answers exact contiguous queries in microseconds and is the step after that [2][10]. Both read the same streams, so they are additions behind seam 1, not rewrites.

### 3.5 Matching engine

The pattern is compiled to a list of items, each a set of allowed (interval from the pattern's first root, class-or-family) pairs or a wildcard; optional items and alternations expand to a small set of concrete item lists (a 3-item pattern with one `?` is two lists); `loop=True` adds the rotations. For each list the engine computes one boolean mask over the stream: position `i` matches when the family (or class) of every item equals, and the root interval from token `i` to token `i+k` equals the pattern's interval `k`. Twelve transpositions are therefore one pass (measured in section 2), `transpose=False` adds one comparison on the first root, `.` is "any chord byte", and `*` is handled by matching the pieces on either side and joining their positions within a song (a per-song pass over the few songs that have both pieces). Occurrence positions are mapped to song rows with a binary search on `offsets`, counted per song, and filtered by `scope` with a binary search on `sections`. `inversions=True` compares a bass byte from a fourth, optional stream (bass pitch class or 255), built only when asked.

The JavaScript twin is the same loop over a `Uint8Array` (section 2, `proto_scan.mjs`), so the two engines share the test vectors: a synthetic corpus of a dozen songs with known progressions in several keys, asserted in both Python and the page's test.

Music logic stays out of `app.js`: the page sends the query string to `GET /chords/compile?q=` and receives the compiled item lists (bytes), the same way it receives a chord table per key today; it never parses a chord symbol itself.

### 3.6 Ranking and popularity

**Default order:** popularity estimate descending, then occurrence count, then coverage (matched tokens / song tokens), then title; deterministic so ties are stable across refreshes [4]. `sort=` reorders the keys; reciprocal rank fusion [18] is noted as the later way to blend keys with incomparable scales, not built in v1.

**Popularity estimate.** `estimate = w · song_signal + (1 − w) · artist_prior`, with `w = n / (n + m)` (the IMDb form [17]), `song_signal` a log-scaled count from the popularity store, `n` its observation count and `m` a smoothing constant. With no song signal, `w = 0` and the song inherits its artist's number; a song kept from the web with no artist in the corpus gets 0, which is the user's "assume not popular" and is correct for the open catalogue [4]. The corpus column is exposed as `artist_popularity` (never again as song popularity) and the result rows carry both numbers with their provenance.

**Popularity store.** A second `dol` store under the data root, `popularity/<source>.jsonl`, rows `(song_key, source, source_id, value, fetched_at, url)`, append-only with a latest view; a provenance row per run. Never in the repo, never in a published artifact (Last.fm's cap and credit clause, Spotify's no-database clause). Default refresh source: **ListenBrainz** (CC0; needs a MusicBrainz id per song, a one-off title+artist mapping at 1 request/s, then batch popularity calls) [16]; optional sources `lastfm` and `deezer` behind a flag with a "private, non-commercial use only" note; Spotify not implemented. Cadence: quarterly, top decile monthly, run by `songleaf refresh-popularity --source listenbrainz`. Free secondary signal needing no network: a coverage count (how many sources on disk carry the song).

### 3.7 Surfaces

- **Core (SSOT):** `tools.chord_search(query, *, level="triads", transpose=True, scope="section", inversions=False, loop=False, sort="popularity,matches", limit=50, offset=0) -> dict` with `{"query": …, "compiled": …, "total": n, "hits": [{"key", "title", "artist", "matches", "coverage", "first_at", "section", "transposition", "popularity", "artist_popularity"}]}`; `tools.build_chord_index()`, `tools.refresh_popularity(source=...)`. Dependency injection (`index=`, `parse=`, `popularity=`) lives in `songleaf.chordseq`, hidden from the CLI.
- **CLI:** `songleaf chords "Am E F" --level tetrads --sort matches` through the existing `cw` dispatch; `songleaf build-chord-index`; `songleaf refresh-popularity`.
- **HTTP:** `GET /chords` (the same flat arguments), `GET /chords/compile`, and the index files as static assets under a content-hashed path with `Cache-Control: immutable` for phase 4.
- **Page:** a string typed into the one search box whose tokens all parse as chords (two or more) is also searched as a chord sequence and shown as a "Chord sequence" result group with the parameters as chips (level, any key, within a section); `?chords=Am+E+F&level=triads` is the URL state; each hit shows the matched passage with its lyric line (songleaf has the chart) and the hit's transposition relative to the query; a toggle flips the shown chords between the song's key and the query's key (the page already holds a chord table per key). Hooktheory's forum complaints (minor-mode confusion, unexplained partial matches) are the acceptance checklist: every hit says why it matched [5][20].
- **Browser worker (phase 4):** the Worker fetches the popular shard of the triads stream (325 KB gzip, measured) and its offsets on first use, runs the scan, and merges the long tail from the server or from the remaining shards when they arrive; the same `/chords/compile` output drives it. WAI-ARIA combobox pattern for the search-as-you-type list [3].
- **MCP and skill:** question answered, not built. The arguments are flat and serialisable, so `py2mcp` over `songleaf.tools:chord_search` would need no core change.

### 3.8 Seam table, NOT seams, one-command test

| # | Seam | v1 default (no new dependency) | Replacement you can point at |
|---|---|---|---|
| 1 | the sequence index: `index=` on `chord_search` | `StreamIndex`: the packed byte streams under the data root, scanned in one numpy pass (26-100 ms measured) | 3-gram postings as a candidate filter and browser shard selector (prototype measured, 2.3 MB); a suffix array via pydivsufsort past a few hundred thousand songs [2][10]; FTS5 phrase queries in the existing SQLite file as the no-numpy fallback |
| 2 | chord symbol → (root, class): `parse=` | `songleaf.harmony.parse_chord` extended with the 21-class vocabulary and the Brazilian spellings the corpus uses | `chordsym`, the shared package of songleaf#31 / songleaf#48 |
| 3 | song popularity: `popularity=` (song key → float) | the corpus's artist popularity, under its true name | the popularity store refreshed from ListenBrainz (CC0), Last.fm and Deezer as private-use options [4] |

```
Surfaces v1: CLI, HTTP + page (server-side search). Phase 4: the Web Worker over the same files. MCP/skill: questions answered, not built.
NOT seams: the query grammar, the byte layout, the class vocabulary and the reduction rule, the three levels, the run-length rule, the result shape, the sort keys, the "is this a chord sequence" detection rule, the shrinkage constant m (a keyword argument).
```

One-command test (the definition of v1; local, needs the corpus):

```bash
python -m songleaf build-chord-index && python -m songleaf chords "Am E F"
# -> a ranked list of songs (title, artist, key, matches) in under 0.2 s after the index loads
```

`tests/test_chordseq.py` runs the same path on a synthetic in-memory corpus in CI, in Python and (phase 4) against the JS scan with the same vectors.

### 3.9 Where the code lives

Recommended: a sub-package `songleaf/chordseq/` (`vocab.py`, `encode.py`, `index.py`, `query.py`, `rank.py`, `popularity.py`) whose only songleaf imports are `harmony` (seam 2) and the model's annotation types, so that it can be lifted into its own package without edits once a second consumer exists. The second consumer is in sight (Chordonomicon through scoreseek, accompy's chord charts), and the names `chordseq`, `chordgram`, `chordindex`, `chordsearch` were free on PyPI and npm on 2026-11-08, but a package today would be founded on one consumer; the architecture-first rule says module now, package when the consumer appears. The chord parser is the exception: songleaf#31 already names five consumers, so the build should land on `chordsym` as soon as the owner approves its name, and until then extend `harmony.py` behind seam 2.

## 4. Build plan

All work in a git worktree of songleaf (the sibling session owns the main checkout); each phase is one pull request with its tests; the research reports move into `misc/docs/research/` in PR 1 so `ir` finds them.

1. **PR 1, the engine and the CLI.** `songleaf/chordseq/` as above; the class vocabulary with the corpus's spellings; `build-chord-index` writing the three streams plus offsets, ids, sections and manifest; the query compiler (grammar of 3.2, with the `E(7)` hint); the numpy scan with every parameter of 3.3 except `inversions` and `year`; ranking by `artist_popularity` and matches; `tools.chord_search`; CLI; synthetic-corpus tests; RSS measured and recorded in the PR. Acceptance: the one-command test; "Am E F" at the triads level returns the same 1,808 songs the prototype found.
2. **PR 2, HTTP and the page.** `/chords`, `/chords/compile`; detection in the search box; the result group with chips, matched passage in context, transposition flip; labels server-side as the layout labels are; URL state. Acceptance: a phone can search a progression and open a hit's sheet in two taps.
3. **PR 3, popularity.** The store, `refresh-popularity` with the ListenBrainz source (MusicBrainz mapping cached), the shrinkage estimate, `sort=`; `artist_popularity` in every surface that showed `popularity`; a write-back to `sung` documenting what its `popularity` column is (issue filed, see section 6). Acceptance: a refreshed song moves in the order; a song with no data inherits its artist's rank; nothing from the store appears in the repo.
4. **PR 4, the browser worker.** Static shards under a content-hashed path, popular shard first, the Worker scan, merge with the server's long tail, combobox accessibility; timings on a real mid-range phone recorded in the PR. Acceptance: first results in under one second on "Fast 4G" after the shard is cached.
5. **Later, as issues:** Chordonomicon as a second corpus (680K songs; CC-BY-NC; titles need the Spotify join that Jangle made, and its ids give genre and decade facets) [21][22]; the 3-gram postings or the suffix array when the corpus grows; "songs like this one" by alignment (Hanna et al.) [9]; a trends view (next-chord frequencies, Hooktheory Trends and Peachnote style) [5]; `inversions=True` with a bass stream.

## 5. Decisions needed from the owner

1. **Notation.** Regex-shaped operators (`?`, `|`, `.`, `*`) over plain chord symbols; parentheses stay chord syntax, so `E(7)` is refused with a hint rather than accepted. Agree, or accept `E(7)` as a lenient alias for `E|E7`?
2. **Defaults.** `level=triads` (`E` matches `E7`), `transpose=True`, `scope=section`, `inversions=False`, repeats collapsed. Agree?
3. **Home and the shared parser.** `songleaf/chordseq/` now with extraction later (names free: `chordseq`, `chordgram`, `chordindex`, `chordsearch`), or a new package now? And songleaf#48: approve `chordsym` (or another name) so PR 1 builds on it, or let PR 1 extend `harmony.py` and migrate later?
4. **Browser search.** Phase 4 after the server version (recommended: same files, measured path), or in the first build?
5. **Popularity.** Accept the corpus column as an *artist* prior under its true name; ListenBrainz (CC0) as the refresh source; Last.fm and Deezer only as private-use options; no Spotify. Agree?
6. **Page behaviour.** A chord sequence typed into the one search box is detected and shown as a result group (recommended), or a separate "Chords" field?

## 6. Open questions and what was not verified

- Phone timings are extrapolated from laptop measurements (3-5×); PR 4 measures on a device.
- The class vocabulary's treatment of `aug7`, `7sus4` with extensions, and polychords is a build-time decision; the 45 suffixes that cover 99% of the corpus are the test set.
- Chordonomicon's `no3d` token is inferred to mean "no third" (a power chord); the dataset card does not say [1][22].
- Last.fm's and Deezer's numeric rate limits, ListenBrainz's batch size, and whether Deezer's terms allow caching at all are community figures or silent [4].
- Hanna et al.'s result that strict quality hurts retrieval was measured for whole-song similarity, not for exact progression lookup; the default level should be re-checked against a dozen known progressions once PR 1 runs [9].
- Write-backs found along the way: `sung.chords_index` should document that `popularity` is Spotify artist popularity, and `sung.get_spotify_client` should route key-less use to client credentials [4]; both are filed as sung issues.

## REFERENCES

[1] [Chord notation and a query language for chord-sequence search (theme report 01, this study, 2026-11-08)](./reports/01-chord-notation-and-query-language.md)
[2] [Transposition-invariant chord-sequence matching and sequence indexes (theme report 02)](./reports/02-transposition-invariant-matching-and-sequence-indexes.md)
[3] [Chord-sequence search in the browser: client-side index options (theme report 03)](./reports/03-client-side-search-in-the-browser.md)
[4] [Popularity data and ranking (theme report 04)](./reports/04-popularity-data-and-ranking.md)
[5] [Prior art: searching songs by chord progression (theme report 05)](./reports/05-prior-art-chord-progression-search.md)
[6] [Harte C, Sandler M, Abdallah S, Gómez E. Symbolic representation of musical chords: a proposed syntax for text annotations. ISMIR 2005](https://ismir2005.ismir.net/proceedings/1080.pdf)
[7] [MIREX 2020: Audio Chord Estimation (vocabularies and the largest-subset reduction rule)](https://www.music-ir.org/mirex/wiki/2020:Audio_Chord_Estimation)
[8] [mir_eval: chord comparison levels (root, thirds, triads, tetrads, sevenths, mirex, _inv)](https://mir-eval.readthedocs.io/stable/api/chord.html)
[9] [Hanna P, Robine M, Rocher T. An alignment based system for chord sequence retrieval. JCDL 2009](https://dept-info.labri.fr/~mrobine/papers/robine-HRR.JCDL09.pdf)
[10] [pydivsufsort: Python bindings for libdivsufsort (MIT)](https://github.com/louisabraham/pydivsufsort)
[11] [MDN: HTTP caching (cache busting with content hashes, immutable)](https://developer.mozilla.org/en-US/docs/Web/HTTP/Guides/Caching)
[12] [Chords and Lyrics Dataset, Kaggle](https://www.kaggle.com/datasets/eitanbentora/chords-and-lyrics-dataset)
[13] [NLP-Project-Hit-Machine: the scraper behind the dataset (artists table sorted by Spotify popularity)](https://github.com/eitanbentora/NLP-Project-Hit-Machine)
[14] [Spotify Web API changelog, February 2026 (popularity removed for Development Mode apps)](https://developer.spotify.com/documentation/web-api/references/changes/february-2026)
[15] [Spotify Developer Terms, effective 15 May 2025](https://developer.spotify.com/terms)
[16] [ListenBrainz API: popularity endpoints (CC0 data)](https://listenbrainz.readthedocs.io/en/latest/users/api/popularity.html)
[17] [IMDb weighted rating (Bayesian average) formula](https://kiwix.lema.org/stackoverflow.com_en_all_2023-11/questions/3717613/how-would-you-compute-imdb-movie-rating)
[18] [Cormack GV, Clarke CLA, Büttcher S. Reciprocal rank fusion outperforms Condorcet and individual rank learning methods. SIGIR 2009](http://cormack.uwaterloo.ca/cormacksigir09-rrf.pdf)
[19] [Hooktheory TheoryTab advanced search (Ignore Extensions & Inversions, Start of Section Only)](https://www.hooktheory.com/theorytab/advanced-search)
[20] [Hooktheory forum: TheoryTab search by chord (beta), 2019](https://forum.hooktheory.com/t/theorytab-search-by-chord-beta/2795)
[21] [de-chordis-mysteriis: Jangle's static chord-progression index over Chordonomicon](https://github.com/sanhuaaan/de-chordis-mysteriis)
[22] [Kantarelis S et al. Chordonomicon: a dataset of 666,000 songs and their chord progressions. arXiv 2410.22046](https://arxiv.org/abs/2410.22046)
