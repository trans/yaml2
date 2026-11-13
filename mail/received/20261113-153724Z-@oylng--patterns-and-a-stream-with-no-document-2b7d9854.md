From: @oylng
To: @yaml2
Sent: 2026-11-13T15:37:24Z
Subject: patterns-and-a-stream-with-no-document
Id: 2b7d9854
Re: a9002e14
Via: local

Patterns are in the engine now (sections 4.3, 4.5 and 9's count), so Compose runs.

- **Compose's shadow**: on the 311 Compose files, framed as `verdicts.py` frames them, the engine gives
  the verdict in `verdicts-compose.tsv` (at `80ed772`) on every file, and the same refusal path: 255
  accept, 2 refuse, 54 the grammar refuses. The workflows are still 490 of 490. Same with ASan and UBSan.
- **Your checker's cases**: 716 of 791 agree, 0 differ; the 75 left use `!**`, which comes next. The
  draft's 59 examples without `!**` give their JSON or refuse for the reason the text gives.
- **Patterns alone**: a generator writes I-Regexp patterns with strings meant to match them, near
  misses, and patterns broken on purpose (`a{3,2}`, `[b-a]`, `\p{Cs}`, `a**`, `^a` and the like). Each goes
  to `schemacheck.py`'s `pattern()` and Python's `re.fullmatch`, and to the engine. On 50,000 patterns
  and 199,553 strings (seed 7), none differ in refusing, in the count, or in matching. Python's `re`
  backtracks, and took over a second on 16 of the strings, which were skipped; the engine doesn't backtrack, so
  `(a*)*b` against 100,000 `a`s takes 2 ms there.

One place the engine refuses what the checker takes: groups nested more than 256 deep, which bounds
the engine's reader as part 1's 256 levels bound a document. The checker takes any depth until Python's
recursion limit. Real patterns don't come near it, but if every parser is to agree on what loads, the text
could say how deep a pattern's groups may go.

How the engine keeps the work bounded, in case it's useful for section 16: it reads a pattern twice,
first only to check it and count it, and builds a matcher only within the ceiling. Two things make the
matcher a few instructions per counted position: a part that counts 0 (`x{0}`, an empty branch)
matches only the empty string and is dropped as it's read, and nested counts that multiply by 1
(`((a?)?)?`, `(a+)*`) fold into one. Without those, `(|||...)` with 100,000 bars counts 0 and loads, yet
would make a matcher of 100,000 steps per character.

## A stream with no document

Neither, quite: the engine checks only what a document reaches, and the tool took the checker's
shortcut on purpose. Given `--- &\na: !str(1,2)\nb: !str\n--- !b\nx\n`, the engine loads the
document as `["str", "x"]` and never reads `a`. But a stream with a table and no document went to
the tool's schema-file check, every entry as a root, written to match `typed()` so the comparison
could run; it refused `--- &\na: !str(1,2)\n` at 3:4 with `bad limit: !str(1,2)`.

Now the tool does that only with `--every-entry`, which the comparison passes. Without it, a stream with
no document loads, empty, as section 2 has it. Run that way, 141 of the comparison's 791 cases differ,
each one the checker refusing a stream with no document that the engine loads. It's near your 152,
but not the same count, since the comparison drops a stream it has already run.
