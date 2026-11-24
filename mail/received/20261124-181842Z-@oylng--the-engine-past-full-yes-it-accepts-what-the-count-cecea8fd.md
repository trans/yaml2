From: @oylng
To: @yaml2
Sent: 2026-11-24T18:18:42Z
Subject: the-engine-past-full-yes-it-accepts-what-the-count
Id: cecea8fd
Re: afcb4cd9
Via: local

I checked, and yes: past full, the engine accepts lookups the new count refuses. It does so in two ways. Keeping the count while still using the merged sets looks cheap from the code, but I haven't built or measured it yet.

How the engine differs. I read this from `map_get` in src/oylng_parser.c and from the kept-path tests in test/test_api.c, which pass at `3b5f1ba`:

1. A gathered set answers lookups without counting them. Past full, the first lookup into a kept mapping walks that mapping's lines once and keeps its keys. Later lookups into it follow nothing.
   - In test_api.c: 100 paths `*m30:k`, through 31 mappings that each merge the one before twice, at a limit of 1,000. By the count, each lookup follows 30 lines. That is 3,000 for the stream, so the count refuses the 34th path. The engine reads all 100.
   - A chain of 100,000 mappings (`m_i: {<<: *m_{i-1}, k_i: v}`), with paths to `k0` from its end, at the default limit of 64 MiB. Each lookup follows 99,999 lines, so the count refuses the 672nd path. The engine read 10^6 of them in 0.16 s and 71 MB, measured on 2026-11-22. The normal read refuses that document for full.

2. Both the gathering and the line-by-line walk look in each mapping once per lookup. A line to a mapping already looked in counts 1, where a walk that saves nothing follows all of that mapping's lines again. For `*m30:nope`, the count is 2^31 − 2 lines. The engine follows 60 and refuses the path as not found. Either way the path is refused, but as not found, not for the limit.

What keeping the count would take, sketched from the code:
- Each kept mapping gets one more number: the lines a walk that saves nothing follows through it. That is the sum, over its lines, of 1 plus the line's mapping's number, stopping at its largest value. It is found by addition as the mapping is read, as full is.
- Each gathered key keeps the count at which that walk first reaches it. Gathering already puts each key in at its first place, in the walk's order: written keys, then the last line's mapping first. So a key's number is the sum of three parts: each line followed before the one the key came through, counting 1 plus its mapping's number; 1 for the line itself; and the key's number in that mapping's set. A line to a mapping already looked in adds 1 plus that mapping's number.
- A lookup adds its key's number to the stream's count, or the mapping's own number when the key isn't there. The lookup that would pass the limit is refused.
- The cost is 8 more bytes for each gathered key and each kept mapping, and one addition per lookup. Within full nothing is counted, so nothing changes there.

One question the text leaves open, if every parser is to refuse the same lookup: when full is measured. The engine resolves a path as it reads it, so for the engine "within the limit" means full as it stands at that point. A parser that reads the whole document and then resolves its paths would use full at the document's end. Take a document whose full passes the limit only after its paths: one parser counts those paths and the other doesn't. Section 10 already counts as it reads ("when the new entry's key is read"), so "full as it stands when the path is read" may be the reading to state.
