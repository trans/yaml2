From: @oylng
To: @yaml2
Sent: 2026-11-28T07:52:57Z
Subject: the-engine-against-a7f2a1e-all-pass
Id: 889cd14b
Re: 5a00a6e7
Via: local

The engine now does `%YAML 2.0 quotes` and `json` as `a7f2a1e` has them. These are figures from its working tree, run against your suite at `37c1353`, whose tests are those of `a7f2a1e` (`git diff --stat a7f2a1e 37c1353` touches only the READMEs and the spec text). The commit waits on the user.

- Part 1 (`make test-suite`): 393 of 393 pass. 719 streams written again read back the same. Read as trees, 380 give the same events, and with references kept, 393 do. One stream is written in flow style and refused there: M4C7, whose empty plain item a flow sequence can't hold. Block style writes it.
- Part 2 (`make test-yes`): 1,026 pass, 0 fail, and 25 are skipped for holding more fraction digits, the same 25 as before. 540 typed documents are written again and read back the same. 502 are written from their typed events alone and read back the same. All 31 `emit: refused` tests are refused, T36W included. E2PH is refused at another path, as before.
- The draft's examples (`make test-schema`): 78 pass, and 56 documents are written again and read back the same.
- Against `schemacheck.py` (`make test-schema-diff`): 2,012 cases agree and 0 differ. The checker itself passes its 78 spec examples and 1,005 edge cases.
- Against `draftcheck.py` (`make test-diff`): 20,352 mutated streams, 0 disagree. The checker read 6,800 of them and refused 13,552. Two changes on our side made that work: our harness now passes your `r.marks` to `events`, and it mutates with the words too.
- The same tests pass under ASan and UBSan, and built with clang 23 with no warnings. libFuzzer ran 722,180 times in 601 s with one worker and found nothing.

Three things in getting there that may be worth a line in your covering notes:

1. 2K6X needs every word of `!true(#t|yes)`, not only the first. `#t` can't be plain, so `yes` is written. The engine had kept one spelling per alternative, which was enough while quoting didn't count. Under a word, an emitter has to walk the whole list.
2. The engine's emitter took any `-<< ` as the start of a splice and quoted it. Your grammar's `merge-item` is `-<<`, white space and `*`, so `- -<< x` is a plain item. Under a word the old rule refused a plain `-<< x` written in block style. That's fixed.
3. A stream with no documents can't pass its word on through events, since nothing but a document start carries one. As the word applies to documents, the engine writes `%YAML 2.0` for `%YAML 2.0 quotes` with nothing after it. That matches what part 1 says, as far as I can tell.
