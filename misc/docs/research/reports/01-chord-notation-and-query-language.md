# Chord notation and a query language for chord-sequence search

Research theme 01 of the songleaf chord-sequence search study. Date: 2026-11-08. Scope: chord-symbol syntaxes and grammars, chord classes and matching levels, optional-element query syntax, enharmonics, and parser libraries. Indexing and ranking are other themes.

## Summary and recommendation

- There is one formal, implementable chord grammar in the field: Harte et al. 2005 (ISMIR), `root:shorthand(degrees)/bass` with `N` for no chord, given in BNF [1]. MIREX and mir_eval use it, with two later additions: the root is written explicitly (`C:(1,3,5)`), and `X` means "unknown chord" [2][3]. Every other notation (ChordPro, jazz lead sheets, iReal Pro, music21, MusicXML) is a surface spelling that maps onto the same model: root, interval set, bass. songleaf's planned `chordsym` should parse surface spellings into that model and emit Harte as its canonical string.
- Matching levels already have standard names and exact rules: mir_eval's `root`, `thirds`, `triads`, `tetrads`, `majmin`, `sevenths`, `mirex`, each with an `_inv` variant that also compares the bass [3]; MIREX defines class reduction as "largest subset of the input interval set that is in the vocabulary" (so `G:7(#9)` reduces to `G:maj` under majmin and to `G:7` under sevenths), with out-of-vocabulary chords such as `D:aug` or `F:sus4(9)` excluded [2]. Recommendation: name songleaf's switch after mir_eval (`level="triads"` as the default, `"tetrads"` for exact extensions, `"root"` for major/minor loosening) and use the MIREX subset rule to assign a class to each corpus chord at index time.
- `E(7)` is a bad query notation. In chord symbols, parentheses group alterations and additions (`C7(b9)`, `C(add9)`, `C(omit5)`), and `C(9)` is a common shorthand for `Cadd9`, so `E(7)` reads as "E with a 7th", the opposite of "7th optional" [4][5][6]. Parentheses also carry meaning in Harte (degree list) [1], RomanText (square brackets for alterations) [7], and iReal Pro (alternate chords) [8].
- Recommended query notation: whitespace-separated chord patterns, each a plain chord symbol; a trailing `?` makes the preceding element optional, `|` is alternation, `.` is any one chord and `*` any run of chords, all with regex, Lucene, Humdrum and Themefinder precedent [9][10][11][12]. With `level="triads"` as the default, `Am E F` already matches `Am E7 F`, so the "(7) optional" case is mostly absorbed by the level switch; `E|E7` is the explicit form, and `E7?` means "an optional E7 chord", as it would in a regex.
- Enharmonics are a solved problem: normalise to pitch class 0 to 11 (letter value plus or minus the count of accidentals, modulo 12); `Cb`, `E#` and double accidentals need no special cases; the only locale trap is German `H` = B natural and `B` = B flat, which ChordSheetJS and chord-symbol expose as a notation-system option [13][14][15]. Chordonomicon writes sharps as `s` (`Fs`, `Csmin`) and minor as `min`, and has `no3d` tokens; the dataset card documents none of this, so it must be inferred from the rows [16].
- Libraries: for the browser, chord-symbol (MIT) is the strongest parser and its `simplify: "core" | "max"` renderer option is literally a triad-only switch [15]; tonal (MIT) is the best pitch-class and enharmonic utility [13][17]. In Python, pychord (MIT) is a usable seed for a quality table but has no `min7` alias and a strict list [18]; music21 (BSD-3) is the reference for figure parsing and RomanText but far too heavy to import in a request path [19][20]; mingus is GPL-3 and last released in 2020, avoid [21][22]; ChordSheetJS is GPL-2.0-only, study only [14][23].

## Terminology

Root, quality (triad type: major, minor, diminished, augmented, suspended), extension (7, 9, 11, 13), alteration (`b5`, `#9`), added tone (`add9`), omission (`no3`, `omit5`), bass or slash chord (`C/E`), inversion (bass is a chord tone) versus upper structure or polychord (bass is not) [5]. Harte calls the interval set the degree list and the whole thing a chord label [1]. MIREX and mir_eval call a set of allowed classes a chord vocabulary, the act of assigning a class a vocabulary mapping or reduction, and the per-pair score a comparison [2][3]. Relative notations (Roman numerals, Nashville numbers) express the root as a scale degree in a key [24][7]; absolute notations (letters) do not need a key. Transposition-invariant matching compares root intervals rather than roots, what RISM calls interval search and Hooktheory calls relative ("Rel") search [25][26].

## 1. Chord-symbol syntaxes and their grammars

### Harte 2005, the only formal grammar

Table 1 of the paper, verbatim [1]:

```
<chord>       ::= <note> ":" <shorthand> ["(" <degree-list> ")"] ["/" <degree>]
                | <note> ":" "(" <degree-list> ")" ["/" <degree>]
                | <note> ["/" <degree>]
                | "N"
<note>        ::= <natural> | <note> <modifier>
<natural>     ::= A | B | C | D | E | F | G
<modifier>    ::= b | #
<degree-list> ::= ["*"] <degree> ["," <degree-list>]
<degree>      ::= <interval> | <modifier> <degree>
<interval>    ::= 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12 | 13
<shorthand>   ::= maj | min | dim | aug | maj7 | min7 | 7 | dim7 | hdim7
                | minmaj7 | maj6 | min6 | 9 | maj9 | min9 | sus4
```

Rules stated in the text: note modifiers follow the letter (`Ab`), degree modifiers precede the interval (`b7`); `*` before a degree removes it; the bass is a degree relative to the root, not a note (`D#:(b3,5,b7,9)/5`); `N` is no chord; the syntax is case-sensitive because `b` is both a flat and a letter [1]. Shorthand definitions: `maj=(3,5)`, `min=(b3,5)`, `dim=(b3,b5)`, `aug=(3,#5)`, `maj7=(3,5,7)`, `min7=(b3,5,b7)`, `7=(3,5,b7)`, `dim7=(b3,b5,bb7)`, `hdim7=(b3,b5,b7)`, `minmaj7=(b3,5,7)`, `maj6=(3,5,6)`, `min6=(b3,5,6)`, `9=(3,5,b7,9)`, `maj9=(3,5,7,9)`, `min9=(b3,5,b7,9)`, `sus4=(4,5)` [1]. Two later changes: MIREX writes the root explicitly (`C:(1,3,5)`; `C` and `C:maj` stay equivalent) [2], and mir_eval adds `X` (unknown), the shorthands `sus2, aug7, min11, 11, maj13, min13, 13, 1, 5`, and a validation regex anchored `^((N|X)|(([A-G](b*|#*))...$` where a root takes flats or sharps but not both; omissions require a quality (`C:(*3)` is rejected, `C:maj(*3)` is not) [3]. Chordonomicon's own Harte conversion writes `SOL5` as `G:(*3)` [27].

A practical regex for the surface form, derived from the BNF (an implementation sketch, not from a source): `^(?P<root>[A-G][b#]*)(?::(?P<sh>maj|min|dim|aug|maj7|min7|7|dim7|hdim7|minmaj7|maj6|min6|9|maj9|min9|sus4|sus2|1|5)?(?:\((?P<deg>\*?[b#]*(?:1[0-3]|[1-9])(?:,\*?[b#]*(?:1[0-3]|[1-9]))*)\))?)?(?:/(?P<bass>[b#]*(?:1[0-3]|[1-9])))?$|^[NX]$`.

### The other notations

| Notation | Root | Quality / extension | Slash and bass | Suspension, add, omit | Grammar? | Verdict for songleaf |
|---|---|---|---|---|---|---|
| Harte 2005 / MIREX [1][2][3] | `A-G` + `b*`/`#*` | 16 to 25 shorthands plus explicit degree list | `/degree` relative to root | degrees, `*` omits, `sus4`/`sus2` shorthands | BNF and regex | canonical internal string |
| ChordPro [4] | letter (A-G, German H), Roman I-VII, or Nashville 1-7, spellings set in config (`Bb`, `Bes`, `B♭`) | optional qualifier (`m`, `mi`, `min`, `-`) then extension from a built-in list (`sus`, `add`, `maj7`/`^7`, `dim`, `aug`, `+`, `alt`) | `/` + root | via extension list; `[*text]` is an annotation, not a chord | informal: root, qual, ext, bass, strict or relaxed | the shape of a lead-sheet token; parse to Harte |
| Chordonomicon [16][27] | letter with `s` for sharp, `b` for flat (`Fs`, `Bb`) | `min`, `7`, `maj7`, `add9`, `sus2`, `sus4`, `no3d` | `/` + note (`D/Fs`) | `no3d` (undefined on the card) | none published; sections as `<verse_1>` | needs a tiny adapter (`s` to `#`, `min` to `:min`, `no3d` to `(*3)`), then Harte |
| Nashville numbers [24] | scale degree 1-7, chromatic `b7` (written `7b` in some charts) | `-` or `m` for minor, otherwise pop symbols | `1/5` = 1 chord over 5 | pop symbols | none | the relative form for transposition-invariant display |
| Roman numerals: RomanText [7], Humdrum `**harm` [28] | `I-VII`, case = major/minor, `o`/`+`, `b`/`#` or `-`/`#` before the numeral | figured-bass inversions `6`, `64`, `7`, `65`, `43`, `2`; `9`, `11`, `13` | applied chords `V/V`, chains `V7/V/V` | RomanText: `[b5]`, `[no5]`, `[add#6]`, one per bracket; `**harm`: `M`/`m` interval letters | prose spec plus music21 parser; `**harm` informal | analysis export only; square brackets conflict with ChordPro |
| Jazz lead sheet / iReal Pro [5][8] | letter | `-`, `m`, `min`; `^7`, `maj7`, `Δ`; `o`, `dim`; `h7`, `ø`, `m7b5`; `+`, `aug`; `7alt`; `sus`, `7sus`, `9sus` | `F/C` | parentheses group alterations; iReal uses parentheses for alternate chords | spelling table, app rewrites to its own symbols | the spellings a user will type; alias table for `chordsym` |
| MusicXML `harmony` [29][30]; music21 `CHORD_TYPES` [19] | `root` element; music21 figure `[A-Ga-g][#-]*`, flat is `-` in roots, `b` only in alterations | 33 `kind` values (`major`, `dominant`, `half-diminished`, `power`, `pedal`, `Tristan`, `none`, `other`); music21 maps 50 kinds to abbreviation lists (`m`/`min`, `maj7`/`M7`, `ø7`/`m7b5`, `o7`/`dim7`, `7sus`/`7sus4`, `N6`, `It+6`) | `bass` element; `/B-` | `degree` element = `degree-value` + `degree-alter` + `degree-type` (add, alter, subtract) | XSD | the cleanest data model: kind + degree changes + bass; mirror it in the index schema |

Jazz conventions worth encoding: a plain major triad is a bare letter; `Δ` is ambiguous (triad for some writers, major 7th for others); `sus` alone means `sus4`; `C13` implies 7, 9 and 11; `add9` implies no 7th; a non-chord-tone bass (`C/Ab`) is an upper structure, not an inversion [5]. Brandt and Roemer's *Standardized Chord Symbol Notation* (1976) is the usual citation for these conventions but its rules on parentheses could not be verified from an online source.

## 2. Chord classes and matching levels

mir_eval encodes every label as (root pitch class, 12-bit interval bitmap, bass pitch class) and compares at a named level [3]:

| Level (mir_eval name) | Exact rule [3] | What it means for a query `E` | Verdict |
|---|---|---|---|
| `root` | roots equal | matches any chord on E (`Em`, `E7`, `Esus4`, `E5`) | songleaf's "major/minor loosening" |
| `thirds` | root equal and bitmap bit 3 (minor third) equal | `E`, `E7`, `Emaj7`, `Eaug` match; `Em`, `Edim` do not; `A:7`/`A:maj` and `A:min`/`A:dim` are documented matches | major-vs-minor only; sus and power chords fall on the "major" side |
| `triads` | root equal and bitmap bits 0-7 (root to fifth) equal | `E`, `E7`, `E9`, `Emaj7`, `Eadd9` match; `Esus4`, `Eaug`, `Em` do not | the default "triad only" switch |
| `tetrads` | root equal and all 12 bits equal (extended chords not reduced; `A:7` and `A:9` share a bitmap) | `E7` and `E9` match each other, `E` and `E7` do not | "exact extension" switch |
| `majmin` | reference must be `maj`, `min` or `N`, else the pair is ignored (score -1); compares bits 0-7 | like `triads`, but sus/aug/dim/power references are dropped | the historical MIREX vocabulary |
| `sevenths` | reference must be `maj`, `min`, `maj7`, `7`, `min7` or `N`, else ignored; full bitmap | `E7` matches only `E7` family after reduction | MIREX "Sevenths" |
| `*_inv` variants | the above plus bass equal | `E/G#` is distinct from `E` | slash-chord switch |
| `mirex` | at least 3 pitch classes in common (bass included); references with fewer than 3 tones (`5`, `1`) ignored | `E` matches `C#m7` (shares E, G#, B) | too loose for search; useful as a "similar chord" relaxation |

MIREX 2020's vocabularies are sets of Harte classes: root only; `{N, maj, min}`; `{N, maj, min, maj7, min7, 7}`; the first two with inversions (`maj/3, min/b3, maj/5, min/5`; the sevenths set adds `maj7/3 ... 7/b7`) [2]. Its reduction rule is the one to copy at index time: a mapping exists if root and bass match and "the structure of the output label is the largest possible subset of the input label given the vocabulary"; `G:7(#9)` reduces to `G:maj` under majmin and to `G:7` under sevenths; `D:aug` or `F:sus4(9)` have no class and are excluded from the ground truth or counted as a mismatch in an estimate [2]. The same wiki justifies the vocabularies from the Billboard corpus: pure major and minor are 65 percent of chords, the five-quality sevenths set 86 percent, augmented and diminished 0.2 percent each, and suggests power, suspended and added-sixth/ninth chords as future classes [2]. For a search corpus of guitar charts, that argues for a vocabulary of `{maj, min, 7, maj7, min7, sus4, sus2, 5, dim, aug}` with everything else reduced to the largest-subset class. Burgoyne, de Haas and Pauwels (ISMIR 2014) list the same levels as I (root) to V (sevenths with inversions) plus segmentation [31]; the paper itself was not opened.

Tool precedents for a "triad only" switch: Hooktheory's TheoryTab advanced search has an "Ignore Extensions & Inversions" toggle and a "Start of Section Only" toggle, behind a login, with no published semantics [32]; its older search-by-chord syntax is relative (`1`, `16` for I6, `511` for V11, `542/4` for V42/IV, `minor:6` for bVI) with a mode prefix, 1 to 4 chords, and no adds, omits, suspensions or alterations [26]; its Trends API encodes chords the same way (`b7`, `5/6`) and offers "Rel" search over all keys [25]. A Hooktheory user request for "rotate over all notes" matching (`Am C F G` matching `Bbm Db Gb Ab`) shows the feature does not exist there for letter-name queries [33]. chord-symbol's renderer option `simplify` is the only library-level switch found: `"core"` keeps the vertical quality and drops suspensions, extensions, alterations, adds and omits; `"max"` keeps only the minor third [15]. tonal's `Chord.reduced` / `Chord.extended` (subset and superset chord types) are the set-theoretic equivalent [17].

## 3. Optional parts of a token: query-language precedent

| System | Optional element | Any one element | Any run | Alternation | Grouping | Source |
|---|---|---|---|---|---|---|
| Regular expressions (Python `re`) | `x?` | `.` | `.*` | `a|b` | `( )`, `(?: )` | [9] |
| Lucene classic query parser | none (optional terms are the default OR) | `?` one character | `*` zero or more characters; not allowed as first character | `OR`, `||` | `( )`; reserved: `+ - && || ! ( ) { } [ ] ^ " ~ * ? : \ /` | [10] |
| Humdrum `pattern` | `regex<TAB>?` zero or one record | regex per record | `<TAB>*` records | regex `|` | regex `( )` | [11] |
| Humdrum `patt` | one regex per template line, consecutive records must match; `-s` skips barlines | | | | | [34] |
| Themefinder (interval field) | `?` after an interval | `.` any one interval | `*` in examples (meaning not confirmed from the page) | | | [12] (page not fetchable directly; summary via search index) |
| themax (Humdrum Extras) | full extended regex over contour and pitch strings, e.g. `u{4,}.*d{4,}` | | | | | [35] (manpage not reachable at research time) |
| RISM incipit search | none; searches are right-truncated prefix matches in interval (transposition-invariant), exact-pitch or contour mode | | | | | [36] |
| Hooktheory TheoryTab | none; 1 to 4 chords, exact in-mode match | | | | | [26] |
| RomanText | not a query language; `[ ]` holds alterations (`V65[no5][add#6][b3]`) | | | | | [7] |

Is `E(7)` a bad idea? Yes, for three independent reasons. In chord symbols, parentheses enclose alterations and additions: chord-symbol parses `Cm7(b9,#9)`, `C(add9)`, `C(omit5)` [6]; Sibelius and Dorico render alterations in parentheses by default, and Dorico documents parentheses around a whole symbol as "an alternative set of changes or an optional chord" [4]; some jazz systems put every altered note in parentheses (`C7(b9)(b13)`) [37]. In Harte, `( )` is the degree list [1]. In iReal Pro's chart protocol, `(Db^7/F)` is an alternate chord [8]. A musician reading `E(7)` will most likely read "E with an optional or added 7th", so the chord `E7`, and a parser built on any of these libraries will do the same.

Recommended notation (a proposal; the components are standard, the combination is this report's):

- A query is whitespace-separated chord patterns. A pattern is a chord symbol in lead-sheet spelling (`Am`, `E7`, `Bbmaj7/D`, `F#m7b5`, `N.C.`), parsed by `chordsym` to Harte.
- `?` after a pattern makes that chord optional: `Am E7? F` (regex, Humdrum `pattern`, Themefinder precedent).
- `|` between patterns is alternation: `Am E|E7 F` (regex, Lucene `OR`).
- `.` is any one chord and `*` is any run of chords, giving gaps and skips: `Am . F`, `Am * F` (regex, Themefinder `.`, Lucene `*`).
- Parentheses stay part of the chord symbol and are never a query operator. If `E(7)` must be accepted, treat it as lenient input for `E|E7` only after `chordsym` fails to parse it as a chord, and say so in the help text.
- The match level is a global switch, not per-token syntax: `level=triads` (default) makes `E` match `E7`, `E9`, `Emaj7`; `level=tetrads` makes `E7` match only the dominant family; `level=root` makes `E` match `Em`. `inversions=False` (default) ignores the bass, matching mir_eval's non-`_inv` levels [3]. Per-token exactness, if ever wanted, can be a prefix such as `=E7`, a free character in every system surveyed; this is an invention, not precedent.
- Transposition invariance is a search mode, not a notation: the engine rewrites the query and the corpus to (root interval from the previous chord, class) tuples, as RISM's interval mode does for melodies [36] and Hooktheory's relative mode does for scale degrees [25]. Nashville numbers or Roman numerals are then only a display option.

## 4. Enharmonics and pitch-class normalisation

Pitch class = letter value (`C=0, D=2, E=4, F=5, G=7, A=9, B=11`) plus the signed count of accidentals, modulo 12; `Cb` is 11, `E#` is 5, `Bb` and `A#` are 10, `C##` is 2 [13][17]. Harte roots take flats or sharps but not both [3]. German usage: `H` is B natural and `B` is B flat in Germany, Czechia, Slovakia, Poland, Hungary, Norway, Denmark, Finland and Iceland [38]. ChordSheetJS's `Chord.parse` has a `notation: "german"` option under which `B` means B flat and `H` means B natural, and by default treats `H` as an alias for B [14]; chord-symbol's parser tries English, German and Latin (`Do`, `Ré`) systems by default and can be restricted [15]; Chordonomicon mapped `hmin` to `B:min` and `SOL5` to `G:(*3)` [27]. Spelling, not pitch class, is what differs between libraries: music21 writes flats as `-` in roots and basses (`B-/D`), keeps `b` for alterations, treats enharmonics as unequal in `==` (`isEnharmonic()` compares), and offers `getEnharmonic`, `simplifyEnharmonic(mostCommon=True)` (G flat to F#, A# to B flat) [20]; tonal's `Note.chroma` gives 0-11, `Note.simplify("C###")` gives `D#`, `Note.enharmonic("C#")` gives `Db`, double accidentals are supported [13]; pychord's `Chord("C#") == Chord("Db")` is `True` and transposition defaults to flat spelling unless a key is given [18]; ChordSheetJS `normalize()` rewrites `E#/B#` as `F/C` and `useAccidental("#"|"b")` switches spelling [14]. For the index store pitch class and class only; keep the original spelling for display and transposition (songleaf's `harmony.transpose_chord` already handles spelling).

## 5. Parser libraries, licences and verdicts

Licences were read from the npm or PyPI registry record, or the repository LICENSE file, as noted.

| Library | Language | Licence (source) | Version, date | Parses | Enharmonics | Verdict |
|---|---|---|---|---|---|---|
| pychord [18][39][40] | Python, pure | MIT (PyPI `license_expression`) | 1.4.3, 2026-11-03, Python >= 3.11 | ~120 qualities as a dict (`''`, `maj`, `m`, `min`, `-`, `dim`, `aug`, `7`, `M7`, `maj7`, `m7`, `m7b5`, `dim7`, `sus4`, `add9`, `7(b9)`, `no5`, `m(no5)` ...), slash and `/N` inversions; no `min7` or `-7`; unknown quality raises | equal across spellings | study: copy the quality table as the seed for `chordsym`; depending is acceptable (no dependencies) but the strict list will reject real corpus tokens |
| music21 [19][20][41][42] | Python | BSD-3-Clause (PyPI, LICENSE text) | 10.5.2, 2026-10-28, Python >= 3.11 | `ChordSymbol` figures with a 50-kind `CHORD_TYPES` table aligned to MusicXML kinds, `add`/`omit`/`alter` keywords, bare `b9`/`#11`; RomanText reader/writer; flats in roots must be `-` | `getEnharmonic`, `simplifyEnharmonic`, `isEnharmonic` | study: the kind table and the figure parser are the reference; avoid importing it anywhere near a request (size, import time); never a `chordsym` dependency |
| mingus [21][22][43] | Python | GPL-3.0 (repo, PyPI `GPLv3`) | 0.6.1, 2020-12-31 | `from_shorthand` with a fixed abbreviation list (`m`, `M`, `dim`, `m7b5`, `7#9`, `6/9`, `sus4b9`, `5`, `NC`, `hendrix`), slash and polychord `|` | not documented | avoid: GPL-3 is incompatible with an MIT package and the project is stale |
| tonal (`@tonaljs/chord`, `note`, `chord-type`) [13][17][44][45] | JS/TS | MIT (npm) | 6.5.1 | `Chord.get("Cmaj7/B")` via `tokenize` to `[tonic, type, bass]`; 107 chord types with alias lists (`maj7, Δ, ma7, M7, Maj7, ^7`; `m7b5, ø, -7b5, h7, h`; `7no5`); unknown type returns `empty: true`; no parenthesis handling | `chroma`, `enharmonic`, `simplify`, double accidentals | depend (vendor a bundle) for pitch-class and transposition in the page; not sufficient alone as a parser of corpus spellings |
| chord-symbol [6][15][46] | JS | MIT (npm) | 4.0.0, depends on lodash | "more than 100 modifiers": `M, Maj, m, minor, Δ, ^, b5, o, -, ø, #9, b13, +, dim, 69, add11, omit3`, parentheses groups `Cm7(b9,#9)`, `C(omit5)`, `alt` with configurable intervals; English, German, Latin roots; output has `intervals`, `semitones`, `quality`, `extensions`, `alterations`, `adds`, `omits`, `isSuspended`; renderer `simplify: none|core|max`, `accidental: original|flat|sharp`, `transposeValue`, `notationSystem` | by notation system and accidental option | depend (vendor) for the browser parser, or study: port its modifier dictionary into `chordsym` so Python and JS agree |
| ChordSheetJS [14][23] | JS/TS | GPL-2.0-only (npm) | 18.0.0 | `Chord.parse("Ebsus4/Bb")`, Nashville numeric `b1sus4/#3`, Roman numerals, solfège; `toNumeral`/`toNumeric` in a key; `normalize`; parsers for ChordPro, Ultimate Guitar and chords-over-lyrics | `normalize`, `useAccidental`, German notation option | study only (licence): its symbol-to-Nashville conversion and its chords-over-lyrics parser are the closest prior art to songleaf's chart parser |
| teoria [47][48] | JS | MIT (npm) | 2.5.0; last publish about 2017 (inferred from the tarball timestamp, not stated) | `teoria.chord("F#(#11b5)")`, qualities major/minor/augmented/diminished/half-diminished/dominant | `enharmonics()`, `chroma()` | avoid: unmaintained; tonal covers it |

## 6. Not asked, but important

- Chordonomicon's chord strings are undocumented. The card declares `cc-by-nc-4.0`; the sample rows show `s` for sharp, `min`, `no3d`, `<verse_1>` tags; the paper reports 736 unique chords and 3,526 unique inverted chords, N.C. removed, consecutive duplicates collapsed, songs with fewer than four chords removed, and a Harte conversion notebook (`convert_mirex.ipynb`) [16][27][49]. Its internal data model (`tetrad = [root_id, quality_id, extension_id, bass_id]`) is a sound shape for a chord index [49]. The exact meaning of `no3d` (probably "no 3rd", so a power chord or `(*3)`) is an inference, not documented.
- Suspended chords are not triads in any MIREX vocabulary, so decide explicitly whether `E` should match `Esus4` at the default level (mir_eval `triads` says no, `root` says yes) [2][3]. Power chords (`E5`, `no3d`) have no third and fall to `thirds` as "major"; mir_eval's `mirex` level drops them entirely [3].
- Harte's `N` versus the corpus's `N.C.`, RomanText's `NC`, mingus's `NC`: normalise all to `N` and decide whether `N` is a wildcard or a token in a query [1][7][22].
- Harte is case-sensitive (`B` vs `b`) and MIREX assumes enharmonic equivalence of roots at evaluation time [1][2]: do the same, and never fold case on roots.
- RomanText's bracket syntax and ChordPro's bracket delimiters both use `[ ]`; a future "paste a RomanText or ChordPro line as a query" feature must pick one [4][7].
- music21 writes flats as `-`; Chordonomicon writes sharps as `s`; Harte uses `b`/`#`; the `chordsym` input alphabet should accept all three plus `♭`/`♯` (ChordPro's `truesf` setting emits Unicode accidentals) [16][19][50].

## REFERENCES

1. [Harte, Sandler, Abdallah, Gómez. Symbolic representation of musical chords: a proposed syntax for text annotations. ISMIR 2005](https://ismir2005.ismir.net/proceedings/1080.pdf)
2. [MIREX 2020: Audio Chord Estimation (wiki)](https://www.music-ir.org/mirex/wiki/2020:Audio_Chord_Estimation)
3. [mir_eval chord module source (mir_eval/chord.py)](https://github.com/mir-evaluation/mir_eval/blob/main/mir_eval/chord.py)
4. [Dorico 4 manual: Parenthesized chord symbols](https://steinberg.help/dorico/v4/en/dorico/topics/notation_reference/notation_reference_chord_symbols/notation_reference_chord_symbols_parentheses_c.html)
5. [Wikipedia: Chord names and symbols (popular music)](https://en.wikipedia.org/wiki/Chord_names_and_symbols_(popular_music))
6. [chord-symbol README](https://github.com/no-chris/chord-symbol/blob/master/packages/chord-symbol/README.md)
7. [Tymoczko, Gotham, Cuthbert, Ariza. The RomanText format. ISMIR 2019](https://archives.ismir.net/ismir2019/paper/000012.pdf)
8. [iReal Pro: Chord symbols](https://www.irealpro.com/learn/chord-symbols)
9. [Python `re` module documentation](https://docs.python.org/3/library/re.html)
10. [Apache Lucene classic query parser syntax](https://lucene.apache.org/core/9_0_0/queryparser/org/apache/lucene/queryparser/classic/package-summary.html)
11. [Humdrum Toolkit: pattern command](https://www.humdrum.org/Humdrum/commands/pattern.html)
12. [Themefinder search form help: interval](https://www.themefinder.org/help/interval/)
13. [tonal: @tonaljs/note README](https://github.com/tonaljs/tonal/tree/main/packages/note)
14. [ChordSheetJS Chord class documentation](https://martijnversluis.github.io/ChordSheetJS/classes/Chord.html)
15. [chord-symbol API documentation](https://github.com/no-chris/chord-symbol/blob/master/packages/chord-symbol/API.md)
16. [Hugging Face dataset card: ailsntua/Chordonomicon](https://huggingface.co/datasets/ailsntua/Chordonomicon)
17. [tonal: @tonaljs/chord README](https://github.com/tonaljs/tonal/tree/main/packages/chord)
18. [pychord repository](https://github.com/yuma-m/pychord)
19. [music21 harmony.py source (CHORD_TYPES, ChordSymbol)](https://github.com/cuthbertLab/music21/blob/master/music21/harmony.py)
20. [music21 pitch module reference](https://www.music21.org/music21docs/moduleReference/modulePitch.html)
21. [python-mingus repository](https://github.com/bspaans/python-mingus)
22. [mingus.core.chords reference](https://bspaans.github.io/python-mingus/doc/wiki/refMingusCoreChords.html)
23. [npm registry: chordsheetjs](https://www.npmjs.com/package/chordsheetjs)
24. [Wikipedia: Nashville Number System](https://en.wikipedia.org/wiki/Nashville_Number_System)
25. [Hooktheory Trends API documentation](https://www.hooktheory.com/api/trends/docs)
26. [Hooktheory forum: TheoryTab search by chord (beta)](https://forum.hooktheory.com/t/theorytab-search-by-chord-beta/2795)
27. [Chordonomicon: a dataset of 666,000 songs and their chord progressions (arXiv HTML)](https://arxiv.org/html/2410.22046v1)
28. [Humdrum **harm representation](https://www.humdrum.org/rep/harm/)
29. [MusicXML 4.0 reference: kind-value data type](https://www.w3.org/2021/06/musicxml40/musicxml-reference/data-types/kind-value/)
30. [MusicXML 4.0 reference: degree element](https://www.w3.org/2021/06/musicxml40/musicxml-reference/elements/degree/)
31. [Burgoyne, de Haas, Pauwels. On comparative statistics for labelling tasks: what can we learn from MIREX ACE 2013? ISMIR 2014](https://archives.ismir.net/ismir2014/paper/000250.pdf)
32. [Hooktheory TheoryTab advanced search](https://www.hooktheory.com/theorytab/advanced-search)
33. [Hooktheory forum: more flexible chord search, rotate over all notes](https://forum.hooktheory.com/t/more-flexible-chord-search-option-search-by-chord-names-but-rotate-over-all-notes/10618)
34. [Humdrum Toolkit: patt command](https://www.humdrum.org/Humdrum/commands/patt.html)
35. [themax manpage, Humdrum Extras](https://extras.humdrum.org/man/themax/)
36. [RISM Online: incipit search documentation](https://rism.online/docs/api/incipit-search/)
37. [Dobrian: jazz chord symbols](https://music.arts.uci.edu/dobrian/f14/music16D/dobrianchordsymbols.htm)
38. [Wikipedia: B (musical note)](https://en.wikipedia.org/wiki/B_(musical_note))
39. [pychord default qualities table](https://github.com/yuma-m/pychord/blob/main/pychord/constants/qualities.py)
40. [PyPI: pychord](https://pypi.org/project/pychord/)
41. [PyPI: music21](https://pypi.org/project/music21/)
42. [music21 LICENSE](https://github.com/cuthbertLab/music21/blob/master/LICENSE)
43. [PyPI: mingus](https://pypi.org/project/mingus/)
44. [tonal chord-type dictionary (data.ts)](https://github.com/tonaljs/tonal/blob/main/packages/chord-type/data.ts)
45. [npm registry: tonal](https://www.npmjs.com/package/tonal)
46. [npm registry: chord-symbol](https://www.npmjs.com/package/chord-symbol)
47. [teoria repository](https://github.com/saebekassebil/teoria)
48. [npm registry: teoria](https://www.npmjs.com/package/teoria)
49. [Chordonomicon GitHub repository README](https://github.com/spyroskantarelis/chordonomicon)
50. [ChordPro configuration: generic settings](https://www.chordpro.org/chordpro/chordpro-configuration-generic/)

Verification notes: Harte 2005 and RomanText 2019 were read from the PDFs; mir_eval, music21, pychord and tonal from source files; licences from registry metadata or LICENSE files as stated per row. The Themefinder interval help page and the themax manpage could not be fetched directly (host unreachable at research time), so their wildcard syntax rests on the search index summary of those pages and is marked accordingly. The MIREX wiki was read despite an expired TLS certificate. Brandt and Roemer (1976) was not available online. Chordonomicon's `s`, `min` and `no3d` conventions are inferred from dataset rows, not documented.
