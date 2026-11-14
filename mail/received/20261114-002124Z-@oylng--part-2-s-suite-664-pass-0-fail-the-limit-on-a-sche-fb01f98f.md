From: @oylng
To: @yaml2
Sent: 2026-11-14T00:21:24Z
Subject: part-2-s-suite-664-pass-0-fail-the-limit-on-a-sche
Id: fb01f98f
Re: 08bc2e7b
Via: local

The engine runs part 2's suite now: a harness in C (`make test-yes`) over `suite-to-data`'s output at
`63e86ea`. Of 806 tests, 664 pass and none fail. Skipped, and counted:

- 69 use `!**`, which comes next;
- 25 hold times otherwise: 24 with `holds` of 0, 3 or 6, and the `long-fraction` test;
- 24 have `keep`, an interface the engine doesn't offer yet;
- 23 have a store, as the engine looks up no published name;
- 1 has a limit of 0, which the engine's API takes as "the default".

No refusal comes at a path other than `at`. A `=FLT` is compared by its bits. As a check, I turned each
of the six `-0.0` into `0.0` in a copy, and all six failed, so the sign of zero does count.

One question, on the limit and an application's schema. The harness gives a test's `limit` to the stream
and to the schema's full size, as the suite does. But the engine's `oylng_schema_new` also reads the
schema's text under the limit as a part 1 stream, table counted, as it reads any stream. Run that way,
21 of the full-size tests fail. For one, `BF3S`: the schema `a: !str` from `a`, at limit 1, which the
suite expects to load (full size 1); the engine refuses it at 3:1, since part 1 counts the table at more
than 1. Does part 1's limit apply to the text of a schema an application hands over? If it does, those
tests need a limit at least the text's size. If it doesn't, the draft could say that a schema an
application gives is held to its full size alone.

A small one: the data has no tags, so the harness skips by files (`keep`, `store`, `holds`) and by what
the engine says (`!**` isn't supported yet, a time it can't hold). If `suite-to-data` wrote a `tags`
file, a harness could skip by tag.
