# Popularity data and ranking for songleaf's chord-sequence search

Report 04 of the chordseq research set. Date: 2026-11-08. Scope: where song popularity can come from, what each number means, what may be stored and shown, how to refresh it, and how to rank when most songs have no number.

## Summary and recommendation

1. **The corpus's `popularity` column is not song popularity.** It is the Spotify *artist* popularity (integer 0-100) copied from the Kaggle "Spotify Artists" table the scraper iterated over: it is constant per artist for all 6,350 artists (0 artists have two values), every one of the 135,783 rows has it, the range is 25-100 (the scraper walked artists sorted by popularity, descending), and the row also carries the Spotify `artist_id`, `followers` and `genres` [1][2][3]. The snapshot is at latest March 2022 (dataset's last update) and undated at the source. Within an artist all songs tie, which is what the current `-popularity` tiebreaker shows.
2. **Spotify track popularity is no longer a viable backbone.** The field is marked deprecated in the reference and listed as removed for Development Mode apps in the February 2026 changelog; Get Several Tracks is removed, Search is capped at 10 results, the app owner needs Premium, and the Developer Terms forbid compiling databases of Spotify content [4][5][6][8][9][11]. Apps created before 2026-02-06 still receive the field for now (the existing-app field restrictions were postponed, not cancelled) [13]. Verdict: avoid for bulk; nothing in `sung` should depend on it.
3. **Recommended v1: a two-level prior, no network.** Rank by a song-level estimate that shrinks toward the artist popularity already on disk: `score = w·song_signal + (1−w)·artist_popularity`, with `w = n/(n+m)` (IMDb/Bayesian average form) [46], and where a song has no signal at all `w = 0`, so the song inherits its artist's number. The user's hypothesis "unknown means probably not popular" is sound at the catalogue level (86.2% of tracks on streaming services had 1,000 or fewer plays in 2023 [45]) but *not* inside this corpus, which was selected from the popular end twice (popular artists, songs someone bothered to transcribe); use the artist prior, not zero.
4. **Recommended song-level signals, cheapest first:** (a) a *coverage count*: how many of the sources on disk and in seam 4 carry the song (Kaggle, Chordonomicon via the shared Spotify `artist_id` plus title, lrclib, later others); it costs nothing and correlates with popularity; (b) **ListenBrainz** listen counts (CC0, no key, batch POST by recording MBID) [18][19]; (c) **Last.fm** `playcount`/`listeners` (free, title+artist match, non-commercial, 100 MB storage cap, credit required) [16][17]; (d) **Deezer `rank`** (0-1M, daily, no key, strong for the 29K Portuguese and 19K Spanish songs, terms say non-commercial and are silent on storage) [23][24][25].
5. **Refresh** quarterly is enough for sorting a few hundred hits; a full 135K pass costs ~4-8 hours of polite calls at Last.fm or Deezer, minutes at ListenBrainz once MBIDs are mapped (the MBID mapping is the one-off cost, ~1 req/s at MusicBrainz) [21]. Store the snapshot as `popularity(song_id, source, source_id, value, fetched_at)` under the data root, never in the repo; each row keeps its provenance.
6. **Avoid:** YouTube (Non-Authorized statistics may be stored at most 30 days; `search.list` is now 100 calls/day) [26][27]; Spotify bulk (above); Genius pageviews (unofficial endpoint, scraping is against its terms) [37][38]; AcousticBrainz (shut down 2022) [39]; Musixmatch (paid for anything useful, unverified free tier) [41]; Apple Music (no popularity attribute on songs) [42].

## 1. The number already on disk

The Kaggle page credits "The Spotify artists dataset" and "the website e-chords" [1]. The authors' repository explains the method: take the Spotify artists table (with a popularity metric and genres), look each artist up on e-chords, download all their songs [2]; the scraper sorts artists by `popularity` descending and copies `popularity` and `followers` onto each song row (`web_scraping.py`, lines 67 and 136-137). Local check of the zip: columns `artist_id` (22-char Spotify id, none missing), `followers`, `genres`, `popularity`; 135,783 songs, 6,350 artists, median 8 songs per artist (max 587); popularity integer-valued, min 25, max 100, mean 66.6; languages en 80,064, pt 29,457, es 19,269, then id/it/fr/de around 1,000-1,400 each. The Spotify Artists table is CC-BY-NC-SA-4.0 [3]; the chords dataset's licence is "unknown" and its text is scraped, which the repo already treats as "no song text in the repo".

Consequences: the column is a legitimate *artist prior* and should be renamed as such in the model (`artist_popularity`), it is stale (≤ 2022, and Spotify popularity is recency-weighted, so it reflects who was being streamed around 2021), and it is a Spotify number, so the Spotify Developer Terms' "do not store indefinitely" clause [11] technically applies to it too; it arrived through Kaggle, not the API, which is why the practical risk is low but a replacement by CC0 data (ListenBrainz artist counts) is the clean long-term answer.

The Chordonomicon bridge: 679,807 rows, 440,284 with `spotify_song_id`, 510,986 with `spotify_artist_id` (local count, matching the paper's Table 1) [44]. Since every Kaggle row has a Spotify `artist_id`, the two corpora join exactly at the artist level; the song level needs title matching because Chordonomicon has no titles. Chordonomicon has no popularity column; its Spotify ids are a path to Spotify popularity, which §2 closes. Licence CC-BY-NC-4.0 [43]. It does carry `main_genre`, `genres`, `release_date`, which are the inputs a genre-aware or recency-aware prior needs.

## 2. Sources compared

| Source | The number | Match key | Coverage for this corpus (estimate) | Limits | Store / show / redistribute | Verdict |
|---|---|---|---|---|---|---|
| Kaggle corpus `popularity` | Spotify **artist** popularity 0-100, snapshot ≤ 2022 [1][2] | already on the row | 100% of rows, 6,350 distinct values | none | on disk already; CC-BY-NC-SA upstream [3] | **use** as the prior; rename |
| Spotify Web API track `popularity` | 0-100, "based in the most part on the total number of plays and how recent", duplicates rated independently, lags by days [4] | Spotify track id (via Search, limit now 10) | high for en, good for pt/es, if obtainable | field removed for Dev Mode apps created after 2026-02-06; Get Several Tracks removed; Premium owner; unpublished per-account quota [5][6][8][9][10]; existing-app field cut postponed [13] | Terms IV.3.1.1: no indefinite storage, no databases of Spotify content; Policy III.13: no derived listenership metrics [11][12] | **avoid** for bulk; one-off lookups only |
| Last.fm `track.getInfo` | cumulative `playcount` and `listeners` (scrobbles) [16] | title+artist (`autocorrect=1`) or MBID | high for en, moderate for pt/es, Anglophone skew | error 29 rate limit, number unpublished (5 req/s is the community figure, unverified) [16][17] | non-commercial only; 100 MB "Reasonable Usage Cap" on stored data; credit and link back; no sublicensing [17] | **use with care** (private app yes, redistribution no) |
| ListenBrainz popularity API | `total_listen_count`, `total_user_count` per recording/artist/release; top recordings per artist [18] | MBIDs (batch POST, `MAX_ITEMS_PER_GET` = 100 or 1000, unverified) | smaller user base than Last.fm; counts split across duplicate recordings [22] | no key needed; MusicBrainz lookup for MBIDs is 1 req/s per IP with a real User-Agent [21] | data CC0 [19]; MusicBrainz core data CC0 [20] | **use**: the only source whose numbers may be redistributed |
| Deezer `rank` | 0-1M "global indicator of a song's popularity on Deezer, updated daily based on streams" [24]; present on public track JSON [25] | title+artist search, ISRC in response | strong in Brazil/France/Latin markets, so good for the pt/es third | ~50 req / 5 s (community figure, unverified); no key for public reads | terms: non-commercial, private use, no reproduction without authorisation; silent on caching [23] | **use with care** for pt/es; private only |
| YouTube Data API `statistics.viewCount` | views per video | video id (needs `search.list`) | n/a | 10,000 units/day; `search.list` and `videos.insert` 100 calls/day each; `videos.list` 1 unit [27][28] | Non-Authorized statistics stored ≤ 30 days; no aggregation, no derived metrics; branding required [26] | **avoid** |
| Wikipedia pageviews + Wikidata | daily article views since 2015-07; P2207 Spotify track id, P4404 MusicBrainz recording id [29][31][32] | Wikidata item for the song | only songs notable enough for an article: a "hit" flag, not a scale | no fixed limit, User-Agent required, blocked if abusive [29] | CC0 [29][30] | **use with care** as a notability boolean |
| Billboard Hot 100 datasets | chart position, weeks on chart | title+artist, US only | US/en hits only | static files | Kaggle copy CC-BY-NC-SA-4.0 [34]; GitHub archive MIT but scraped from Billboard, whose terms could not be fetched [35] | **use with care** as a "charted" flag; do not redistribute |
| Official Charts (UK) | chart data | licensed B2B product [36] | — | commercial only | licensed | **avoid** |
| Genius `stats.pageviews` | page views of the lyrics page | Genius song id | en-heavy | unofficial endpoint; scraping violates terms [37]; commercial use needs a licence [38] | unclear | **avoid** |
| Musixmatch `track_rating` | 0-100 popularity on Musixmatch | title+artist | — | free tier small, figures unverified [41] | paid licence for real use | **avoid** |
| Apple Music API | no popularity attribute on Song; charts only [42] | — | — | developer token, paid programme | — | **avoid** |
| Discogs `community.have/want` | collectors' counts per release, not per track | release id | album level | 60/min authenticated, 25/min not (secondary sources) [40] | terms page not fetchable | **avoid** |
| AcousticBrainz | — | — | — | shut down 2022 [39] | — | dead |
| Chordonomicon spotify ids | none; a bridge to Spotify | artist id exact, song by title | 65% of its rows have a track id [44] | — | CC-BY-NC-4.0 [43] | **use** for the join and for genre/decade |

Notes on matching. The corpus has no ISRC and no MBID, so every external source starts from `(artist_name, song_name)`; keep the *resolved* foreign id with the snapshot so the next refresh is a batch lookup, not a search. Last.fm's `autocorrect` returns the corrected names, which is a free normalisation step [16]. ListenBrainz counts are split across duplicate MusicBrainz recordings, so sum over the work's recordings or fall back to the artist total [22].

## 3. Refresh

How fast the numbers move: Spotify's popularity is recency-weighted and lags by days [4]; Deezer's rank is recomputed daily [24]; Last.fm and ListenBrainz counts are cumulative, so their *ranking* changes slowly. For sorting the few hundred hits a chord-sequence query returns, a quarterly refresh is enough; monthly if Deezer is in the mix; a trending signal is out of scope.

Cost of a full pass over 135,783 songs (estimates): Last.fm at ~5 req/s ≈ 7.5 h; Deezer at ~10 req/s ≈ 3.8 h; ListenBrainz popularity in batches of 100-1000 ≈ 136-1,360 POSTs, minutes, but the one-off MBID mapping through MusicBrainz at 1 req/s ≈ 38 h (resumable; cache the mapping forever, MBIDs are CC0). An incremental scheme (refresh the top decile monthly, the rest yearly) cuts this by 10x.

Storage: a `popularity` table or JSONL per source under the data root, `(song_id, source, source_id, value, fetched_at, source_url)`, append-only, with a `latest` view; a `provenance` row per run (source, terms version, date). This fits seam 2 as a second `dol` store. Keep it out of the repo (gitignored data dir), and out of any published artifact: Last.fm's cap and credit clause [17] and Spotify's "no databases" clause [11] both attach to the stored copy, and the YouTube 30-day rule is why YouTube is excluded [26]. The web page shows a rank, not the raw numbers, unless the source allows it (ListenBrainz, Wikipedia).

## 4. Ranking when most songs have no number

Terminology: a *popularity prior* or *static rank* is query-independent evidence added to a relevance score [49]; *shrinkage* or *empirical Bayes* pulls a thin estimate toward a prior [46][48]; *cold start* is the item with no behaviour yet [48]; *rank fusion* combines rankings from incomparable signals [51]; *long tail* is the catalogue shape that makes "unknown ≈ unpopular" true on average [45].

Standard pieces, all cheap enough for the browser:

- **Bayesian average** `WR = v/(v+m)·R + m/(v+m)·C`: the IMDb Top 250 form, where a song with few observations is pulled toward the prior `C` [46]. Here `C` is the artist prior from §1 and `R` the song signal; for count data use `log1p(count)` first, otherwise one Last.fm hit drowns everything. For binary signals (charted, has a Wikipedia article) use the Wilson lower bound rather than the raw proportion [47].
- **Priors from non-behavioural features** (Han et al., CIKM 2022: empirical Bayes priors from item attributes gave +13.5% new-item impressions at Amazon) [48]: artist popularity, language, genre and decade from Chordonomicon, number of sources carrying the song.
- **Saturating transform before adding to a match score** (Craswell et al., SIGIR 2005 [49]; Elasticsearch `rank_feature` uses `S/(S+pivot)` with pivot ≈ the geometric mean of the feature, or `log(scaling+S)`) [50]. The match score (how well "Am E F" fits, with gaps and extension penalties) stays primary; popularity breaks ties and reorders near-equal matches, never overrides a better match.
- **Reciprocal rank fusion** `Σ 1/(k + r_i)`, k = 60, for "sortable by several characteristics": rank by match, by popularity, by recency, and fuse; it needs no scale calibration and beat Condorcet fusion in Cormack, Clarke and Büttcher's experiments [51]. The URL-as-state design can carry the chosen keys as `?sort=match,pop`.
- **Deterministic multi-key sort** as the final step: `(match tier desc, popularity estimate desc, title)` so ties are stable across refreshes.

The hypothesis "unknown means probably not popular": in the open catalogue, yes (Luminate: 158.6 M of 184 M tracks had ≤ 1,000 plays in 2023, 45.6 M had none [45]), so a zero prior is the right default for a song fetched from the web by seam 4 that no popularity source knows. Inside this corpus it is wrong twice over: the artists were taken from the top of Spotify's list (minimum popularity 25), and e-chords carries what somebody chose to transcribe. There the prior is the artist number, which is already present. It fails further for: **new releases** (no cumulative counts yet, and the recency-weighted Spotify number is the one source we cannot have; use `release_date` from Chordonomicon or the web source as a recency key and let the user sort by it); **non-English markets** (Last.fm and ListenBrainz under-count Brazil and Latin America, where Deezer is strong, and Wikipedia pageviews should be read on the song's own language wiki); **classical, folk, hymns and traditional songs** (popular *works* with no canonical recording: counts are scattered across hundreds of recordings, MusicBrainz's work entity is the right aggregation unit [52]); **covers** (the chart may be filed under the cover artist while the counts belong to the original; group by normalised title plus MusicBrainz work or SecondHandSongs, show "N versions", and rank the group by its best member [52][53]).

What an expert would add. *Popularity vs frequency of the progression*: how common "I-V-vi-IV" is across the corpus is a property of the query, not the song; show it as a facet ("this progression appears in 4,120 songs"), do not rank by it. *Genre-aware ranking*: normalise the estimate within `main_genre` so a top jazz standard is not buried under mid-table pop; offer it as a toggle. *Artist-level fallback* is already free, and ListenBrainz's `top-recordings-for-artist` gives a within-artist ordering for 1 call per artist (6,350 calls) without any song matching [18]. *Dedup of covers* before ranking, or every hit list is "the same song five times". *Coverage count* as the first song-level signal: it needs no network and is a defensible proxy.

## 5. Licensing and ethics in one table

| Number | Private personal app | Redistribute (repo, public index, API) | Attribution |
|---|---|---|---|
| ListenBrainz counts, MusicBrainz ids | yes | yes (CC0) [19][20] | courtesy credit |
| Wikipedia pageviews | yes | yes (CC0) [29][30] | none required |
| Last.fm playcount/listeners | yes, non-commercial, ≤ 100 MB stored | no sublicensing | credit Last.fm and link to the track page [17] |
| Deezer rank | yes, non-commercial, private use | no | no association with marks [23] |
| Spotify popularity (any copy) | no indefinite storage, no databases [11]; show with Spotify marks and link back [12] | no | required |
| Kaggle artist popularity | already stored; CC-BY-NC-SA upstream [3] | share-alike, non-commercial | credit the dataset |
| Billboard chart presence | yes | Kaggle copy CC-BY-NC-SA; Billboard's own terms unverified [34][35] | credit |
| YouTube views | ≤ 30 days [26] | no | YouTube branding [26] |

The private deployment ("who may open the app is set in the platform repo") is non-commercial personal use, which is what Last.fm and Deezer permit; the day songleaf is public or paid, only the CC0 sources survive without a licence conversation.

## 6. The in-house angle: `sung` and Spotify auth

`sung` wraps spotipy. Its `get_spotify_client()` builds a `SpotifyOAuth` manager for a fresh client even when no scope is requested, and uses `SpotifyClientCredentials` only when rebuilding from an existing client; `get_spotify_creds()` returns a client-credentials manager directly [58]. Popularity needs no user data, so the right auth for a batch job is Client Credentials: "only endpoints that do not access user information can be accessed" [14]. That is also where the 2024-2026 restrictions bite: the November 2024 change removed Audio Features, Recommendations, Related Artists and more for new and development-mode apps but did not touch Get Track or Search [7]; the February 2026 change removed `popularity` from Track, Artist and Album for Development Mode apps created from 2026-02-11, removed Get Several Tracks, cut Search to 10 results, requires the app owner to hold Premium, and quota is now per developer account and unpublished [5][6][8][9][10]. Existing Development Mode apps keep the field for now because the field restrictions for them were postponed [13]; Extended Quota needs a registered business with 250k MAU [9]. So if the user's Spotify app predates 2026-02-06, a one-off pass at one Get Track per song (no batch endpoint) is possible but fragile and conflicts with the Terms' storage clause; it is not a foundation. `sung`'s `search_tracks` and playlist tooling are unaffected except for the Search limit.

Two small write-backs for `sung` fall out of this: expose a `client_credentials()` convenience (it exists as `get_spotify_creds`, but `get_spotify_client` does not route to it), and document in `chords_index` that the `popularity` column is artist popularity, so no consumer treats it as a song signal.

## 7. Open points (not verified)

Last.fm's numeric rate limit (community says 5 req/s); Deezer's rate limit (community says 50 req/5 s) and whether its terms allow caching at all; ListenBrainz `MAX_ITEMS_PER_GET` (100 in older docs, 1000 in a 2024 merge request) and whether `/1/metadata/lookup` can resolve artist+title to MBIDs without touching MusicBrainz search; the date of the Spotify Artists snapshot behind the corpus column; Billboard's terms (the page sits behind a paywall gateway); e-chords' terms (not fetchable; a third-party copy says tabs are "for study, skill development and scholarship only" [57]); whether Spotify will enforce the postponed field removal for pre-2026 apps.

## REFERENCES

[1] [Chords and Lyrics Dataset, Kaggle](https://www.kaggle.com/datasets/eitanbentora/chords-and-lyrics-dataset)
[2] [NLP-Project-Hit-Machine, GitHub (README and Code/WebScraping/web_scraping.py)](https://github.com/eitanbentora/NLP-Project-Hit-Machine)
[3] [Spotify Artists dataset, Kaggle (CC-BY-NC-SA-4.0)](https://www.kaggle.com/datasets/ehcall/spotify-artists)
[4] [Spotify Web API reference: Search (track object, popularity, deprecated)](https://developer.spotify.com/documentation/web-api/reference/search)
[5] [Spotify Web API changelog, February 2026](https://developer.spotify.com/documentation/web-api/references/changes/february-2026)
[6] [Spotify: February 2026 Web API Dev Mode changes, migration guide](https://developer.spotify.com/documentation/web-api/tutorials/february-2026-migration-guide)
[7] [Spotify blog, 2024-11-27: Changes to the Web API](https://developer.spotify.com/blog/2024-11-27-changes-to-the-web-api)
[8] [Spotify blog, 2026-02-06: Update on developer access and platform security](https://developer.spotify.com/blog/2026-02-06-update-on-developer-access-and-platform-security)
[9] [Spotify Web API: Quota modes](https://developer.spotify.com/documentation/web-api/concepts/quota-modes)
[10] [Spotify blog, 2026-07-23: Web API quota updates for Development Mode](https://developer.spotify.com/blog/2026-07-23-web-api-quota-updates)
[11] [Spotify Developer Terms, v10, effective 15 May 2025](https://developer.spotify.com/terms)
[12] [Spotify Developer Policy, effective 15 May 2025](https://developer.spotify.com/policy)
[13] [Spotify Community: Popularity field missing in Get Track API response](https://community.spotify.com/t5/Spotify-for-Developers/Popularity-field-missing-in-Get-Track-API-response/td-p/7384293)
[14] [Spotify Web API: Client Credentials flow](https://developer.spotify.com/documentation/web-api/tutorials/client-credentials-flow)
[15] [Spotify Web API: Rate limits](https://developer.spotify.com/documentation/web-api/concepts/rate-limits)
[16] [Last.fm API: track.getInfo](https://www.last.fm/api/show/track.getInfo)
[17] [Last.fm API Terms of Service](https://www.last.fm/api/tos)
[18] [ListenBrainz API: Popularity](https://listenbrainz.readthedocs.io/en/latest/users/api/popularity.html)
[19] [Ohri K, Kaye R. The ListenBrainz Listens Dataset. ISMIR 2024 (PDF)](https://zenodo.org/record/14877361/files/000044.pdf)
[20] [MusicBrainz: Data License](https://musicbrainz.org/doc/About/Data_License)
[21] [MusicBrainz API: Rate Limiting](https://musicbrainz.org/doc/MusicBrainz_API/Rate_Limiting)
[22] [Parachord issue 488: ListenBrainz popularity split across duplicate recordings](https://github.com/Parachord/parachord-mobile/issues/488)
[23] [Deezer Developers: Terms of Use](https://developers.deezer.com/termsofuse)
[24] [beets Deezer plugin documentation (definition of rank)](https://beets.readthedocs.io/en/stable/plugins/deezer.html)
[25] [Deezer public API, example track JSON](https://api.deezer.com/track/3135556)
[26] [YouTube API Services, Developer Policies](https://developers.google.com/youtube/terms/developer-policies)
[27] [YouTube Data API: Getting started (quota)](https://developers.google.com/youtube/v3/getting-started)
[28] [YouTube Data API: videos.list](https://developers.google.com/youtube/v3/docs/videos/list)
[29] [Wikimedia Analytics API: Access policy](https://doc.wikimedia.org/generated-data-platform/aqs/analytics-api/documentation/access-policy.html)
[30] [Wikimedia Analytics Datasets: Pageviews readme](https://dumps.wikimedia.org/other/pageviews/readme.html)
[31] [Wikidata property P2207: Spotify track ID](https://www.wikidata.org/wiki/Property:P2207)
[32] [Wikidata property P4404: MusicBrainz recording ID](https://www.wikidata.org/wiki/Property:P4404)
[33] [Wang, Pappu, Cramer. Representation of Music Creators on Wikipedia. ICWSM 2021](https://ojs.aaai.org/index.php/ICWSM/article/view/18101)
[34] [Billboard "The Hot 100" Songs, Kaggle (CC-BY-NC-SA-4.0)](https://www.kaggle.com/datasets/dhruvildave/billboard-the-hot-100-songs)
[35] [utdata/rwd-billboard-data, GitHub (MIT)](https://github.com/utdata/rwd-billboard-data)
[36] [Official Charts Company: Chart licensing](https://www.officialcharts.com/our-business-services/chart-licensing/)
[37] [LyricsGenius documentation: How it works](https://lyricsgenius.readthedocs.io/en/latest/how_it_works.html)
[38] [Genius API listing, publicapis.dev (commercial licence via API sales)](https://publicapis.dev/resource/genius/ro8ulu1u)
[39] [MetaBrainz: AcousticBrainz, making a hard decision to end the project](https://community.metabrainz.org/t/acousticbrainz-making-a-hard-decision-to-end-the-project/572828)
[40] [python3-discogs-client: Requests rate limiting](https://python3-discogs-client.readthedocs.io/en/v2.3.12/requests_rate_limit.html)
[41] [Musixmatch API listing, Jentic (third party)](https://www.jentic.com/apis/musixmatch)
[42] [Apple Music Feed: PopularityTopChartSongs rankings (charts, not per-song popularity)](https://developer.apple.com/documentation/applemusicfeed/popularitytopchartsongs/rankings-data.dictionary.md)
[43] [Chordonomicon dataset card, Hugging Face (cc-by-nc-4.0)](https://huggingface.co/datasets/ailsntua/Chordonomicon/raw/main/README.md)
[44] [Kantarelis S et al. CHORDONOMICON: A Dataset of 666,000 Songs and their Chord Progressions. arXiv 2410.22046v3](https://arxiv.org/html/2410.22046v3)
[45] [Side-Line: 86.2% of tracks receive 1,000 or fewer plays on streaming services, 25% not played at all (Luminate 2023)](https://www.side-line.com/86-2-of-tracks-receive-1000-or-fewer-plays-on-streaming-services-25-not-played-at-all)
[46] [IMDb weighted rating formula (Bayesian average), Stack Overflow mirror](https://kiwix.lema.org/stackoverflow.com_en_all_2023-11/questions/3717613/how-would-you-compute-imdb-movie-rating)
[47] [Miller E. How Not To Sort By Average Rating](https://www.evanmiller.org/how-not-to-sort-by-average-rating.html)
[48] [Han C et al. Addressing cold start in product search via empirical Bayes. CIKM 2022](https://www.amazon.science/publications/addressing-cold-start-in-product-search-via-empirical-bayes)
[49] [Craswell N, Robertson S, Zaragoza H, Taylor M. Relevance weighting for query independent evidence. SIGIR 2005](https://dl.acm.org/doi/10.1145/1076034.1076106)
[50] [Elasticsearch: rank_feature query](https://www.elastic.co/guide/en/elasticsearch/reference/current/query-dsl-rank-feature-query.html)
[51] [Cormack GV, Clarke CLA, Büttcher S. Reciprocal Rank Fusion outperforms Condorcet and individual Rank Learning Methods. SIGIR 2009](http://cormack.uwaterloo.ca/cormacksigir09-rrf.pdf)
[52] [MusicBrainz: How to Use Works](https://musicbrainz.org/doc/How_to_Use_Works)
[53] [SecondHandSongs API: Rate limits (20/min, 200/h, 1000/day without key)](https://secondhandsongs.com/page/API/RateLimits)
[54] [Spotify Community: February 2026 Spotify for Developers update thread](https://community.spotify.com/t5/Spotify-for-Developers/February-2026-Spotify-for-Developers-update-thread/td-p/7330564)
[55] [Music Business Worldwide: 152 million tracks had 1,000 plays or fewer (Luminate, alternative figure)](https://www.musicbusinessworldwide.com/152-million-tracks-1000-plays-on-streaming-services/)
[56] [ListenBrainz data dumps documentation](https://listenbrainz.readthedocs.io/en/latest/users/listenbrainz-dumps.html)
[57] [e-chords.com terms of use, third-party copy](https://tostracker.app/document/e-chordscom-tos)
[58] [sung, GitHub (sung/util.py: get_spotify_client, get_spotify_creds)](https://github.com/thorwhalen/sung)
