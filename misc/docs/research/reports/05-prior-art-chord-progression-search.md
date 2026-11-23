# Prior art: searching songs by chord progression

Research date: 2026-11-08. Scope: products, sites, open-source projects and academic systems that let a user find songs from a chord progression, assessed against songleaf's planned chord-sequence search. Harmony theory is out of scope (covered in-house).

## Summary and recommendation

Only one mainstream product does real progression search over a large annotated corpus: Hooktheory's TheoryTab (about 82K songs, relative Roman-numeral notation, up to four chords in the search bar, a Trends explorer, and a documented API) [1][2][7]. Everything else is either a chord-*set* search ("songs you can play with G, C, D": Chordify, Chord Genome Project, and what Ultimate Guitar hints at but does not deliver) [12][18][17], a research corpus without a search surface (Chordonomicon, McGill Billboard, ChoCo) [26][29][46], or a hobby project with no users [21][22][23][24].

The pattern songleaf should borrow is already proven in two small projects: encode each chord as (semitone distance from the first chord's root, quality family), index sliding windows of 3 and 4 chords, and ship the index as static JSON chunks that a browser fetches on demand. "Jangle" does exactly this over Chordonomicon with no server at all (title search 20-100 KB, one song 40 KB) [19]; chord-explorer normalises to intervals and matches bigrams [23]. Hooktheory's own data model (scale degree + figured-bass inversion + "b" for borrowed + "/" for applied chords, with an "Ignore Extensions & Inversions" switch) is the best-tested query grammar and maps cleanly onto the exact-vs-triad switch the user asked for [3][7].

The gaps are consistent across every tool and are songleaf's opportunity: none ranks results by popularity (Hooktheory's API orders by artist, then song, then section [7]; Jangle deliberately drops Spotify popularity [19]; Chord Genome does not say [18]); none offers wildcards or gaps; none shows the matched passage in context on the result row; none lets the user flip between absolute and key-relative display of the same hit; and the two biggest (Hooktheory, Chordify) are closed and either four-chord-limited or set-only. Recommendation: build the Jangle/Hooktheory hybrid (transposition-invariant n-gram index in static chunks, Hooktheory-style grammar with a looseness switch), add popularity-first ranking and the lyric context songleaf already has, and treat Hooktheory's forum complaints [8][9][10] as the acceptance checklist for mode handling and partial matches.

## Comparison table

| Tool | Corpus | Query language | Transposition-invariant | Extensions / slash | Wildcards / gaps | Ranking, popularity shown | Verdict |
|---|---|---|---|---|---|---|---|
| Hooktheory TheoryTab search bar [1][2] | ~82K user-analysed songs, section-level | Relative only: `[mode:] 1 5 6 4`, figured bass for inversions (`16`), `/` for applied chords, `b7` borrowed; max 4 chords | Yes by construction (relative) | Extensions in the grammar; advanced search has "Ignore Extensions & Inversions" [3] | None | Not documented; API orders by artist, song, section [7] | **Study** (grammar, switch, section scope) |
| Hooktheory Trends / "Chord Progression Explorer" [4][5][6] | same | Click a chord, see next-chord percentages; key or "Rel" notation | Yes with "Rel", else per key | Only "most common chords" appear (popularity threshold) [9][10] | None | Markov next-chord percentages; song list, order unstated | **Borrow the idea** (next-chord chips, song list that updates per click) |
| Hooktheory Trends API [7] | same | `cp=4,1` scale degrees; `scale=` mode filter (new in 2026) | Yes | `27` = ii7, `16` = I6 | None | 20 per page, ordered by artist/song/section; needs account, 10 req/10 s | **Study** (as a data model); do not depend on |
| Chordify "search by chords" [12][13] | ~36M auto-transcribed songs | Pick the chords you can play (set, not sequence) | Absolute (blog describes "which chords can you play") | Unverified (page behind bot wall) | None | Unverified | **Ignore** (set search over machine transcriptions) |
| Ultimate Guitar [15][16][17] | millions of user tabs | Filters: key, capo, tuning, tab type "Chords"; a "chord finder" landing page exists but did not load | No | No | No | Rating, hits, "most popular" sort | **Ignore** for search; **borrow** sort options |
| Chord Genome Project [18] | "500K+" songs linked to YouTube and tab sites | Type 3+ chords you know (set); paid "Force Last Chord", "Wildcard" (one unknown chord allowed), "All Keys" | Only with paid "All Keys" | Not stated | "Wildcard" = one extra chord allowed | Title, artist, year; genre and decade filters; 10 results free | **Borrow** the "one chord you don't know" relaxation and decade/genre facets |
| Jangle / de-chordis-mysteriis [19][20] | 385,664 Chordonomicon songs with parts, titles via a Spotify join | Progression; signature = (semitones from first root, quality family M/m/d/a/s/5), bass ignored | Yes | Quality collapsed to family; bass dropped | Windows of 3 and 4 chords give partial matches | None (popularity deliberately excluded); counts per signature | **Study closely** (static chunked index, browser-only) |
| HarmonyDB [21] | club libraries, user chords (muzland links) | Progression or pick one from a song; "key-insensitive" | Yes | Not documented | Not documented | "percentage of coverage" per song | **Borrow** coverage percentage |
| chordverse [22] | Hooktheory 75K (section-level), POP909, curated Mandopop | Scale degrees `1564`; minor read against relative major; matches any rotation of the stored loop | Yes | Degrees only | None; rotation matching | Counted next-chord model; CLI, web, MCP | **Borrow** rotation matching and "counted, with per-song tallies" |
| chord-explorer [23] | McGill Billboard (sample) | Progression → bigram Jaccard; intervals 0-11 from key | Yes | Not stated | Implicitly (bag of bigrams) | Similarity score; Louvain clusters, "bridge" songs | **Borrow** the interval-normalised bigram idea; ignore the rest |
| Progressions (2018) [24] | top-1000 UG tabs | Click a song or type a progression; Euclidean distance of transition matrices | Heuristic key estimate, then shift to C | sus/aug/7 stripped | N/A | Distance only | **Ignore** (unmaintained, no licence) |
| Music Corpus Search [25] | McGill Billboard | Roman-numeral progression, "inclusion of repeats is optional"; artist, title, chart date | Yes (Roman) | Not stated | Repeat toggle | Chart date | **Borrow** the repeats toggle |
| Chordonomicon [26][27][28] | 666K UG-scraped songs | None (dataset); 749 chord types, 3,577 with inversions; repeats collapsed; no key assigned, transposition scripts provided | N/A | Single-token and root/quality/bass forms | N/A | No popularity field; CC-BY-NC-4.0 | **Study** the normalisation; the corpus is already on disk |
| McGill Billboard tools [29][30] | 890-1,300 expert annotations | Parsers only (billboard-parser, JAMS) | N/A | Harte syntax | N/A | N/A | **Ignore** for product; reference for chord syntax |
| Peachnote [31][32] | scanned scores | Melody or chords as rising note sequences; n-gram viewer | Interval n-grams | N/A | N/A | Frequency per year | **Borrow** the n-gram-viewer framing for a "trends" page later |
| Musipedia, Themefinder [33][34] | folk/classical melodies | Melodic (Parsons code, intervals, scale degrees) | Yes (melodic) | N/A | Themefinder has regex-like fields | N/A | **Ignore** (no harmony) |
| iReal Pro, Chordbot, ChordChord, Oolimo, Yamaha Chord Tracker [35][36][37][38][39] | own charts / generators / audio | Title search, progression builders, audio-to-chords | N/A | N/A | N/A | N/A | **Ignore** (claims of "find songs by progression" in listicles could not be verified on the vendors' pages) |
| Academic: TPSD, cyclic patterns, LSH cover-ID, LHARP/Harmory [40][41][42][44][45] | small annotated sets | Whole-sequence similarity, not query search | Yes (relative to key) | Varies | Alignment-based | Similarity rank | **Study** for a later "similar songs" feature, not for v1 search |

## What each one does, and what it gets right or wrong

### Hooktheory (TheoryTab search, Trends, advanced search, API)

Query language. The 2019 beta post defines the search-bar grammar: `[mode:] chord, chord, chord, chord`, mode defaulting to major (major, minor, dorian, lydian, mixolydian, phrygian, locrian), roots as Arabic numerals "not Roman numerals", figured bass for inversions (`16` = I6, `542` = V42), `/` for applied chords (`5/6` = V/vi), per-chord borrowed-mode prefixes (`minor:4`), and "chords after the 4th chord in the progression will be ignored" [2]. The API documents the same path syntax (`b7` = bVII, `27` = ii7) and, as of 2026, a `scale` filter [7]. The advanced-search form adds "Chord String", "Start of Section Only", "Ignore Extensions & Inversions", Key, Scale, Meter, Genre, BPM range and complexity metrics, but requires a login [3]. Absolute chord names are not accepted anywhere; Trends offers a per-key view instead [4][6].

What it gets right. Relative notation makes every match transposition-invariant and lets one progression "transfer instantly to all 12" keys [1]. Section scope ("Start of Section Only") and the extensions/inversions switch are exactly the knobs the user asked for [3]. Trends' click-a-chord interaction, where "any time you click a chord, a list of all songs that use the chord/progression gets updated to the right", is the best search-as-you-type pattern found [6]. The API's song object (artist, song, section, URL) shows that a hit is a *section*, not a song [7].

What it gets wrong, in users' words. Searches "are always in perspective of a major mode", so minor-key songs are missed or mis-matched [8]; "many of the found progressions are only partial matches" after an update [8]; Trends "only allows searching for the most common chords" because it is "thresholding on popularity", so borrowed chords vanish [9][10]; "the spelling of the chord progression is left to the discretion of the user(s) performing the analysis", so I-bVII-IV in major and I-VII-IV in mixolydian are different strings [9]; the four-chord cap and no 7th/sus specification in Trends [9]; no way to search for a song that merely *contains* one unusual chord [10]. A 2015 analysis of the API also found it "does not distinguish minor from major for 6" [11]. Results are ordered alphabetically, not by popularity [7].

Verdict: study. Copy the grammar shape and the two switches; design the mode handling and partial-match display so the forum complaints cannot recur.

### Chordify

Its blog introduces "search songs by chords" as a way to find songs from "the chords you can already play" over a catalogue of "almost 36 million songs", and suggests users "play around with random chord progressions and see what songs emerge" [12]; the Android release notes date the feature to app version 1758 [13]. The chords come from automatic transcription, which a reviewer notes the app does not disclose well [12]. The blog page sits behind a bot wall, so the exact matching rule (set vs sequence, capo handling) could not be verified; the App Store listing mentions only title search [14]. Verdict: ignore for search mechanics; its "which chords can you play" framing is the beginner-facing set search, which songleaf could offer as a looser mode, not as the default.

### Ultimate Guitar

A landing page titled "Chord finder - search music by chord progressions and guitar notes" exists but returned "Access denied" to every fetch [15]. The help centre documents only key, capo ("With capo, No capo"), tuning and tab-type filters, plus sorts by rating, "Most popular of all time", "Today's most popular", recently added and alphabetical [16]. A 2024 community thread says that on UG "I can't see a way to search for eg all songs with only chords G, C, D and Em" [17]. Verdict: ignore the search; borrow the sort vocabulary (rating, hits, recency), which songleaf's popularity column can serve.

### Chord Genome Project

"To run a search, add 3+ chords (e.g. C, F, G, Am)"; results are songs playable with only those chords, with instrument filters (guitar, ukulele, banjo, mandolin), beta genre and decade facets, and paid "Gold" filters: "Force Last Chord", "Wildcard" (songs needing just one chord you don't know) and "All Keys", which "searches your chords in all 12 keys, no capo" [18]. Ten results free, 100 with an account, "All 500K+ Songs" for Gold. Data source is not named; links go to YouTube and tab sites. Verdict: borrow the "one chord I don't know" relaxation (a natural `max_extra_chords=1` parameter), the decade/genre facets, and the honesty of showing the count ("3,970 Songs" for G, C, D).

### Jangle and its data repo "de-chordis-mysteriis"

The repo holds the static data for a chord-progression app: 385,664 songs from Chordonomicon with parts, titles and artists from a join with a Spotify tracks dataset, "no Spotify-owned fields" such as popularity, and the indices needed to search them [19]. The signature of a progression "does not depend on key or colour": per chord, the semitone distance from the first chord's root plus a family (M, m, d, a, s, 5); bass is ignored; Am F C G and Bm G D A share a signature. The indices are sliding windows of four and three chords, so a song containing part of a progression still matches. There is no server: "the app downloads the chunk it needs and caches it", a title search is 20-100 KB and a song 40 KB. Licence CC BY-NC 4.0, inherited from Chordonomicon [19][20]. The app's own repository (UI) was not located. Verdict: study closely; this is the architecture that satisfies "computed in the browser" and "fast sequence index" at once, and it already runs over the corpus songleaf has on disk. Its two weaknesses (no popularity, quality collapsed to family with no exact mode) are exactly what songleaf would add.

### HarmonyDB

A personal .NET/Blazor project with "a (key-insensitive) song search based on progressions", searching the offline library by progression "with the percentage of coverage displayed", and a planned public harmonic index API; LGPL-2.1, 798 commits, last push 2025-08 [21]. The playground domain did not resolve on the research date. Verdict: borrow "coverage": the fraction of a song's chords (or of a section) explained by the query is a useful secondary sort key.

### chordverse, chord-explorer, Progressions

chordverse (AGPL-3.0, 1 star, pushed 2026-10) searches Hooktheory's 75K section-level Roman-numeral annotations plus POP909 and a Mandopop corpus with scale-degree queries like `1564`; "scale degrees are always relative to the major key", a minor song is analysed against its relative major, "search matches any rotation" of a song's main loop, and next-chord probabilities "are counted, not written by hand" with per-song tallies; it ships CLI, static web dashboard and an MCP server [22]. chord-explorer (no licence, 1 commit, 2026-06) normalises keys to intervals 0-11 and compares bigram Jaccard over McGill Billboard [23]. Progressions (no licence, 2018 data, last push 2022) estimates key heuristically, shifts to C, strips sus/aug/7 and compares transition matrices by Euclidean distance; its README admits the key heuristic "by no means will give you the correct key every time" [24]. Verdict: borrow rotation matching and the "counted, with evidence" posture from chordverse; ignore the other two as code, keep them as confirmation that interval normalisation plus n-grams is the folk consensus.

### Music Corpus Search

"The site's primary function is to search the McGill-Billboard corpus for chord progressions analyzed with Roman numerals", also by artist, title and chart date; "inclusion of repeats is optional" [25]. Its TLS certificate is misconfigured (only reachable over plain HTTP). Verdict: borrow the repeats toggle (a `collapse_repeats=True` default, as Chordonomicon also collapses "A G G A" to "A G A" [26]).

### Chordonomicon, McGill Billboard, ChoCo

Chordonomicon scraped Ultimate Guitar, kept "the best-rated version, determined by a weighted average of user rating and vote count percentage", collapsed consecutive repeats, removed N.C., and holds 749 unique chords (3,577 with inversions) in FHO syntax with a Harte conversion; "each song's tonal key was excluded as its assignment is a globally interpretive judgment", and "transposition scripts are provided"; no popularity field; the paper does not discuss search [26]. The HF card lists two Spaces using it, neither a search demo, and the licence cc-by-nc-4.0 [27]; the GitHub repo is Apache-2.0 benchmark code, pushed 2026-05 [28]. McGill Billboard offers expert annotations and parsers (billboard-parser, JAMS), no search UI [29][30]. ChoCo integrates 18 harmonic sources into a knowledge graph; its full text was behind a verification wall and was not read [46]. Verdict: study Chordonomicon's normalisation (it is the corpus on disk); the NC licence means its derived index cannot ship in a commercial product, which matches songleaf's private-app posture but should be recorded.

### Melody search engines and the rest

Peachnote searches melodies or "a sequence of chords", with "chords represented as rising note sequences" and an n-gram viewer over scanned scores [31][32]; Musipedia and Themefinder are melodic (Parsons code, intervals, scale degrees) with no harmony mode [33][34]. iReal Pro searches by title only [35]; Chordbot is a progression builder and backing-track maker [36]; Oolimo's progression pages are lessons, not a song database [37]; Yamaha Chord Tracker extracts chords from audio on the device [38]. The listicle that credits Oolimo, Hookpad and others with "find songs by progression" [39] is not borne out by the vendors' own pages. Verdict: ignore; Peachnote's year-by-year n-gram chart is a nice later "trends" view.

### Academic similarity work

Tonal Pitch Step Distance (ISMIR 2008) ranks whole songs by chord-sequence distance [40]; cyclic-pattern retrieval (ISMIR 2011) handles repetitions and structural change [41]; Khadkevich (ISMIR 2013) uses locality-sensitive hashing over chord profiles for large-scale cover identification [42]; an ISMIR 2021 late-breaking dataset argues time-aware similarity beats averaging [43]; Harmory (MIT code, ChoCo data) segments progressions in Tonal Pitch Space and links patterns by temporal and similarity edges, with no search UI [44], and LHARP is Polifonia's recurrent-pattern similarity (MIT, 2021) [45]. Verdict: study for a later "songs like this one" feature; none is a query-by-progression search, and all need a key estimate songleaf does not yet have.

## Synthesis

### Features every serious tool has

- Transposition-invariant matching, done one of two ways: relative notation at annotation time (Hooktheory, chordverse, Music Corpus Search) [1][22][25], or interval-from-first-root normalisation at index time (Jangle, chord-explorer) [19][23]. The second needs no key estimate and is the right fit for a corpus with no keys (Chordonomicon excluded keys on purpose [26]).
- A quality vocabulary reduced to a few families for matching (Jangle's M/m/d/a/s/5 [19]; Progressions stripping sus/aug/7 [24]), with the full symbol kept for display.
- Collapsed consecutive repeats, optionally re-enabled (Music Corpus Search's repeats option [25]; Chordonomicon's "A G G A" to "A G A" [26]).
- Partial matching through short windows (Jangle's 3- and 4-chord windows [19]; Hooktheory's four-chord cap [2]).
- Section as the unit of a hit (Hooktheory returns artist, song, *section* [7]; Chordonomicon and Jangle keep parts [19][26]).
- Result counts shown up front (Chord Genome's "3,970 Songs" [18]; Trends' percentages [4]).

### Features none has (opportunities)

- Popularity-first ranking: Hooktheory orders alphabetically [7], Jangle excludes popularity [19], Chord Genome and HarmonyDB do not say [18][21]. songleaf has a popularity column already.
- Wildcards and gaps: nothing beyond Chord Genome's "one chord you don't know" [18] and bag-of-bigram similarity [23].
- A user-controlled looseness ladder (exact extension, triad, major/minor-agnostic root motion) exposed as one switch; Hooktheory has only "Ignore Extensions & Inversions" behind a login [3].
- Honest minor-mode handling and showing *why* a song matched: the top Hooktheory complaints are relative-major confusion and unexplained partial matches [8][9].
- The matched passage in context: no tool shows the chords around the hit, let alone the lyric line under them, which songleaf's charts make possible.
- Flipping a hit between absolute and key-relative display; Hooktheory is relative-only and Chordify absolute-only.
- Open index over an open corpus in the browser: Jangle is the only one, and it is a three-commit hobby project [19].

### UI patterns worth borrowing for a phone page

- Search-as-you-type on the progression itself: Trends updates the song list on every chord click [6]; combine with songleaf's existing one-field search so "Am E F" in the search box is detected as a progression.
- Chord chips with next-chord suggestions sized by frequency (Trends' bubbles, "the chords that are more likely to follow will be bigger" [4]); tapping a suggestion appends a chip, as in chordverse's counted next-chord panel [22].
- Chip-level looseness: a tap on a chip cycles E7 → E → E(any) rather than a global setting, giving the user Hooktheory's switch without the form [3].
- Key-relative display as a toggle on the result list (Hooktheory's "Rel" [9]), with the song's key or first chord shown on each row, as a Hooktheory user asked for so that exact-key and transposed hits can be told apart [8].
- Coverage or match-span on each row (HarmonyDB's percentage [21]; Jangle's window counts [19]) and the section name, so a chorus-only match reads differently from a whole-song loop.
- Result count and facets (decade, genre, language) before the list, Chord Genome style [18], with the URL as the state so a progression search is shareable.

## Could not be verified

Chordify's matching rule and result order (blog and site behind a bot wall; only search-engine excerpts and release notes seen) [12][13]. Ultimate Guitar's chord-finder page content (access denied) [15]. Hooktheory's search-bar result ordering and whether the 2019 beta limits still apply (no current doc; the API order is documented) [2][7]. HarmonyDB's playground (domain did not resolve) [21]. Jangle's user interface (only the data repo was found) [19][20]. ChoCo's paper text (verification wall) [46]. "ChordSeqer" returned nothing and may not exist. Licences were read from the GitHub API or repository pages: HarmonyDB LGPL-2.1, chordverse AGPL-3.0, Harmory and jchord MIT, chordonomicon code Apache-2.0, dataset and Jangle data CC BY-NC 4.0, chord-explorer and Progressions none [19][21][22][23][24][27][28][44][48].

## REFERENCES

1. [Hooktheory TheoryTab](https://www.hooktheory.com/theorytab)
2. [Theorytab search by chord (beta), Hooktheory forum, June 2019](https://forum.hooktheory.com/t/theorytab-search-by-chord-beta/2795)
3. [TheoryTab advanced search](https://www.hooktheory.com/theorytab/advanced-search)
4. [Hooktheory Trends Tool: Free Resource (blog)](https://www.hooktheory.com/blog/trends-tool/)
5. [Hooktheory Trends / Chord Progression Explorer](https://www.hooktheory.com/trends)
6. [Chord progression search, patterns and trends (Hooktheory blog)](https://www.hooktheory.com/blog/chord-progression-search-patterns-and-trends/)
7. [Hooktheory Trends API documentation](https://hooktheory.com/api/trends/docs)
8. [Incorrect results from TheoryTab Trends search, Hooktheory forum, 2022](https://forum.hooktheory.com/t/incorrect-results-from-theorytab-trends-search/5262)
9. [Ability to search a chord progression more than just the key, Hooktheory forum, 2022](https://forum.hooktheory.com/t/ability-to-search-a-chord-progression-more-than-just-the-key-of-the-music-itself-for-theorytabs-and-or-projects/5991)
10. [Finding theorytabs that use a specific chord, Hooktheory forum, 2024](https://forum.hooktheory.com/t/finding-theorytabs-that-use-a-specific-chord/8232)
11. [Chord progressions of 5,000 songs (R-bloggers, 2015)](https://www.r-bloggers.com/2015/03/chord-progressions-of-5-000-songs/)
12. [Search songs by chords: what do you think? (Chordify blog)](https://chordify.net/pages/search-songs-by-chords/)
13. [Chordify release notes on APKMirror (feature added in 1758)](https://www.apkmirror.com/apk/chordify-b-v/chordify/chordify-1782-release/)
14. [Chordify on the App Store](https://apps.apple.com/us/app/chordify-song-chords-tuner/id1073624757)
15. [Ultimate Guitar chord finder](https://www.ultimate-guitar.com/chords)
16. [Ultimate Guitar search: filters and tab types](https://help.ultimate-guitar.com/en/articles/6741297-ultimate-guitar-search-filters-tab-types)
17. [Searching for songs by chord (JustinGuitar community)](https://community.justinguitar.com/t/searching-for-songs-by-chord/277023)
18. [The Chord Genome Project](https://www.chordgenome.com/)
19. [sanhuaaan/de-chordis-mysteriis (Jangle data and indices)](https://github.com/sanhuaaan/de-chordis-mysteriis)
20. [De Chordis Mysteriis site](https://sanhuaaan.github.io/de-chordis-mysteriis/)
21. [pavel-zhur/HarmonyDB](https://github.com/pavel-zhur/HarmonyDB)
22. [vecyang1/chordverse](https://github.com/vecyang1/chordverse)
23. [k4sud0n/chord-explorer](https://github.com/k4sud0n/chord-explorer)
24. [Ljfernando/Progressions](https://github.com/Ljfernando/Progressions)
25. [Music Corpus Search](http://musiccorpussearch.com/)
26. [Chordonomicon: A Dataset of 666,000 Songs and their Chord Progressions (arXiv 2410.22046)](https://arxiv.org/html/2410.22046v4)
27. [ailsntua/Chordonomicon on Hugging Face](https://huggingface.co/datasets/ailsntua/Chordonomicon)
28. [spyroskantarelis/chordonomicon](https://github.com/spyroskantarelis/chordonomicon)
29. [The McGill Billboard Project](https://ddmal.music.mcgill.ca/research/The_McGill_Billboard_Project_(Chord_Analysis_Dataset))
30. [billboard-parser (Hackage)](https://hackage.haskell.org/package/billboard-parser)
31. [Peachnote](https://www.peachnote.com/)
32. [Peachnote: Music Score Search and Analysis Platform (ISMIR 2011)](https://ismir2011.ismir.net/papers/PS3-1.pdf)
33. [Musipedia](https://www.musipedia.org/)
34. [How to use Themefinder](https://themefinder.org/help/general.html)
35. [iReal Pro: find a song in your music library](https://technimo.helpshift.com/hc/en/3-ireal-pro/faq/327-find-a-song-in-your-music-library/)
36. [Chordbot](https://chordbot.com/)
37. [Oolimo chord progressions](https://www.oolimo.com/en/chord-progressions)
38. [Yamaha Chord Tracker](https://usa.yamaha.com/products/musical-instruments/keyboards/apps/chord_tracker)
39. [10+ apps to find songs by progression (Gemtracks, 2024)](https://www.gemtracks.com/resources/guides/view.php?title=apps-to-find-songs-by-progression&id=7423)
40. [Tonal Pitch Step Distance (ISMIR 2008)](https://archives.ismir.net/ismir2008/paper/000252.pdf)
41. [Music similarity retrieval based on chord progressions and cyclic patterns (ISMIR 2011)](https://ismir2011.ismir.net/papers/PS1-4.pdf)
42. [Large-scale cover song identification using chord profiles (ISMIR 2013)](https://archives.ismir.net/ismir2013/paper/000067.pdf)
43. [A novel dataset for time-dependent harmonic similarity between chord sequences (ISMIR 2021 LBD)](https://archives.ismir.net/ismir2021/latebreaking/000011.pdf)
44. [smashub/harmory (The Harmonic Memory)](https://github.com/smashub/harmory)
45. [polifonia-project/harmonic-similarity (LHARP)](https://github.com/polifonia-project/harmonic-similarity)
46. [ChoCo: a Chord Corpus and a Data Transformation Workflow (Scientific Data, 2023)](https://pmc.ncbi.nlm.nih.gov/articles/PMC10511441/)
47. [hooktheory-mcp get_songs_by_progression](https://glama.ai/mcp/servers/@gabguerin/hooktheory-mcp/tools/get_songs_by_progression)
48. [jonathangjertsen/jchord](https://github.com/jonathangjertsen/jchord)
