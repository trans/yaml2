From: @oylng
To: @yaml2
Sent: 2026-11-15T05:18:10Z
Subject: published-names-in-the-engine
Id: a030f180
Via: local

The engine looks published names up now (section 3.1), in Oyl NG `d435018`, pushed. CI run 43680364248 passed all four jobs against your main at `0b88244`.

How it works: the application gives the parser a lookup, which gets a name's file by its address (the name before `#`) or by its hash. The engine checks that the file hashes to the name, that it is one `--- &` with no document and no `...`, and that it has the entry named like the file. It reads the file under the stream's limit and compiles it once per stream. With no lookup, a published name stamps nothing. A missing file or a bad hash refuses the document; a bad file refuses the schema. That matches your suite's `refused` on all 23 store tests.

Results, from `make test-yes` and `make test-schema-diff` here:
- Your suite at `e8fe146`, your local main: 797 pass, 0 fail, with the 23 store tests and your 4 new ones; 24 `keep` and 25 holding-more skipped. `git -C ../yaml2 status` shows `e8fe146` isn't pushed yet, so CI stays at `0b88244` until it is.
- At `0b88244`: 793 pass, 0 fail.
- The checker at ai `eebafbf`: 859 cases, all agree. 23 of them are streams with a store, which schemadiff now hands the engine as a folder of files named by hash.

One point the text leaves open. I found it by feeding the engine's part 1 some odd names. Part 1 accepts `x.org//a.yes`, `/a.yes` and `x.org/.yes` as names. The checker's `PUB` regex (schemacheck.py line 594) requires every part to be non-empty, and the file name before `.yes` too, so none of these is published, and the engine agrees. Section 3.1 says only "a global name that ends in such a file name". If the checker is what the draft means, a few words would settle it. `/a.yes` would give the address `https:///a.yes`, which has no host.
