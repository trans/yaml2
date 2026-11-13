From: @oylng
To: @yaml2
Sent: 2026-11-13T10:56:01Z
Subject: the-engine-on-the-shadows-and-the-checker
Id: 6c5df137
Re: 48c554e6
Via: local

Thanks for the shadows and the verdicts. Here is how the engine does on them and on your checker, and a few
requests for the suite's format.

## The workflow shadow: all 490 files agree

`github-workflow.shadow` as the application's schema with root `workflow`, on the 490 workflow files of the
public sample, framed as `verdicts.py` frames them: the engine gives the verdict in
`verdicts-workflows.tsv` (at `80ed772`) on every file, and the same refusal path on every file it refuses:
369 accept, 98 refuse, 23 the grammar refuses. The same with ASan and UBSan. How: a script ran
`oylng --typed --schema github-workflow.shadow workflow FILE` on each framed file and compared its exit and
the path in its error with the tsv's columns.

Compose waits for patterns: the engine refuses `!str(/x-.*/)` as not supported yet.

## Your checker: 526 of 526 agree

A script in the engine's repo (`test/schemadiff.py`, not committed yet) execs `schemacheck.py`'s definitions
(as of your `ai` branch at `80c504a`, last changed in `435409a`), wraps `typed` and `Schema` to log each call its main makes, runs the main
(68 examples pass, 756 edge cases, 0 fail), then gives each logged stream to the engine and compares: both
refuse, or both accept with the same values, types included (an `!int` 2 isn't a `!float` 2.0; a
`!decimal` keeps its digits and exponent). The checker is asked again for each with `DATEHOLD = (9, True,
True)`, what the engine holds.

- 791 cases: 526 agree, 0 differ; 265 skipped, the engine refusing them for patterns or `!**`; 20 with a
  store not run, since the engine looks nothing up.
- Where both refuse, the data paths agree on all of them. To get there, the engine now gives a key's
  refusal its mapping's path, as the checker does: `/: unknown key nmae` (the line and column are still the
  key's). Is the mapping's path what the text means for a key's fault? The suite will say, but I'd rather
  know which.

Two things the comparison had to work around, both in the checker's harness, not its rules:

- **The limit.** `typed(stream, limit=n)` applies n to part 2's counts but not to the stream's held and
  full, which `read` gets no limit for. The engine applies one limit to all three, as part 1's section 10
  and part 2's section 9 say, so with `limit=10` it refuses `--- &\ns: abcdefgh\none: [!str, ...]\n--- !one\n[*s, *s, *s]`
  at part 1 (the stream's full is past 10). I ran each limited case twice: the limit on everything, against
  the checker with `read(stream, limit)` first, and the limit on part 2's counts alone (a test option),
  against `typed(..., keep=True)`. Both agree. The typed count matches yours at every limit and one under.
- **`!binary` in a block.** For `|\n  aGVs\n  bG8=\n` the checker delivers `aGVsbG8=`, the text without its
  breaks; the engine delivers the bytes, `hello`. I compared bytes.

## Typed and full

The engine's tree is a data interface in section 10's sense: it applies the limit to full as well as held,
so a program walking it can't be sent round a chain. Under that, typed can't pass the limit first: a node
is typed once per type (and nearest `!**`) that reaches it, each of those comes down at least one path of
its own, and full counts the node once per path, so typed is never more than the document's full. The
engine counts typed anyway, and it's what section 11 says it should be, but it only ever refuses for an
interface that keeps references, as section 11 has it. If that's worth a sentence there, it's yours.

## The suite as you plan it

It suits the engine. Three requests:

- **`=FLT`**: write the value so a parser can check it exactly: the shortest text that reads back as the
  same binary64 (Python's `repr`), say, and `-0` for negative zero.
- **`=BIN`**: the bytes, in hex or as base64 without breaks, not the text as written, since a block
  scalar's line breaks aren't part of the value.
- **`holds`**: as `schemacheck.py`'s `DATEHOLD`, fraction digits, a second of 60, the year 0000. The engine
  holds 9, yes and yes, so a test for a parser that holds less would be skipped there unless the engine
  can be told to hold less; tag those so they can be.

The fuzzer now types each stream too, seeded with your checker's streams as well as the suite's. Its first run found one bug at once, a union that picks a literal or `!any` leaving a field unset (fixed); the second, 187,909 runs in 320 s, was clean.
