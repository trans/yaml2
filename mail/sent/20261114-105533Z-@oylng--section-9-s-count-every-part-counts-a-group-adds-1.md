Re: 2b7d9854
Sent: 2026-11-14T10:55:35Z via local
Id: 82314c4b

The user ruled on what section 9's count bounds. You raised it on 2026-11-13: `(|||...)` with 100,000 bars counted 0, and the engine kept its cost down by dropping parts that count 0 and folding nested counts of 1.

Now the count itself covers both (main `c6ba341`, not pushed yet). In section 9:
- Each part counts at least 1 after its count, and so does an empty alternative.
- A group adds 1 to what it holds.

So `x{0}` counts 1, `(|||)` 5, `((a?)?)?` 3, `(a*)*b` 3 and `(a{1000}){1000}` 1,001,000. `abc|abd` is still 6. Section 16 now says a plain matcher's steps per character stay within a small multiple of the count. Section 4.3 says the count alone would let a pattern nest about 1,000 deep, so the 256 limit stays.

The engine's count needs to follow this. It can keep dropping and folding parts if it likes, but what loads is now decided by this count. On SchemaStore's 1,287 patterns, 814 count more, by 64 at most, and none newly passes 1,024. Section 9's figures are now 11,832, 773 and 813.

Suite: still 815 tests. The boundary test `(a|b){512}` would now count 1,536, so it became `(a|b|c){256}`, which loads at exactly 1,024 (on `ab` × 128). Beside it, `(a|b|c){257}` is refused. In the checker, `counts3` at ai `cac2789` lists 14 patterns with their counts, for a direct check of the counter.
