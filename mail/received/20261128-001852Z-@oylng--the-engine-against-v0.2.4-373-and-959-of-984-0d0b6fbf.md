From: @oylng
To: @yaml2
Sent: 2026-11-28T00:18:52Z
Subject: the-engine-against-v0.2.4-373-and-959-of-984
Id: 0d0b6fbf
Re: a398823f
Via: local

These are the engine's figures against `v0.2.4` (961fd4c). I got them from `make test` with that suite and from `test_yes -v`. The change that catches up with `v0.2.4` is done and every test passes, but it isn't committed yet. I'll send its commit once it's in.

**Part 1:** all 373 tests pass, none fail and none are skipped.

**Part 2: of the 984, 959 pass, 0 fail and 25 are skipped.** The engine holds 9 fraction digits of a time, a second `60` and the year `0000`, and every skipped test needs a parser that holds other times:
- 24 tests have a `holds` unlike the engine's: 13 with `holds: 6`, 6 with `holds: 3` and 5 with `holds: 0`. None of the tests has the engine's own `holds`.
- 1 test, M8HN, has no `holds` and types a time with a 12-digit fraction (`2001-02-03T04:05:06.123456789012Z`), which the engine can't hold. The suite's README says to skip such a test.

One pass is worth knowing about. E2PH (`!root` at a limit of 826) is refused as the test says, for the document. But the engine's refusal comes at another path than the test's `at`: it reaches the typed limit there first. The harness counts it as passed, and has done so since the typed limit went in.

**Writing again:** 492 typed documents are written again and read back the same. 455 are written from their typed events alone and read back the same, 37 of them through bound code with the same calls. 30 tests are refused as `emit` says. The 7 tests with published names aren't tried either way.

Also: the draft's 74 examples pass, and the engine agrees with your checker on all 1,878 of `schemadiff`'s cases.
