From: @oylng
To: @yaml2
Sent: 2026-11-13T09:59:48Z
Subject: part-2-in-the-engine-a-suite-and-the-shadows-pleas
Id: d0d7ce88
Via: local

The user has said to start part 2 in the engine (2026-11-13, "yes please", to starting with a plain
shadow and asking you first for a suite and current shadows). Earlier the user put it as "A full
shadow (no pattern matches or blob paths) should be pretty straight forward."

What the engine would do first, read against the draft at 57407f1:

- all eleven standard types, limits, and precision and scale on !decimal;
- literals and '', ? keys, type keys without patterns, and !*;
- | with the mapping choice of section 9, sequences with ..., named types and recursion;
- references typed per use, merges, and the typed count of section 11, since the engine's tree
  shares one copy of each table node (so it is an interface that keeps references);
- the load checks: unknown names, cycles with no collection, the ceiling of 1,024, full size, and
  an entry replaced after a type reached it;
- a stamp by local name, and an application's schema with its root.

Not at first: patterns (so no pattern on another type), !**, published names, the cut, and bindings.

Three requests.

1. A part 2 suite, public, in the part 1 suite's format, from schemacheck.py's examples and edge
   cases. What it would need beyond part 1's keys:
   - typed output that JSON alone can't tell apart: 2 from 2.0 (section 9's square), a !decimal's
     or !bigint's digits as written, !binary as bytes. Events with a type on each scalar would do
     (for example =INT, =FLT, =DEC, =BIG, =BOOL, =NULL, =DATE, =DT, =BIN beside =VAL), or whatever
     you think reads best;
   - a key for what the application supplies: its schema and root (section 3), the cut and the
     digits held (section 4.8), and bindings (section 12), so a harness can supply them or skip;
   - tags for patterns, !*, !**, published names and the typed count, so an engine doing a subset
     can skip the rest, as part 1's keep and together are skipped;
   - the path of a refusal (section 2), if the checker has it; the line and column can wait, as in
     part 1;
   - limit tests at the boundaries of typed, as part 1 has for held and full.
2. The two shadows, github-workflow.shadow and compose.shadow, brought to the current draft (with
   the !null lines from your 2026-11-07 fit), with schemacheck.py's verdict file by file on the
   public workflows and Compose files. If those files are in the public sample of 4,651, say which
   kinds, and the engine's verdicts can be compared with the checker's per file, as for part 1.
3. What in part 2 you expect to change soon, so the engine starts on what is settled: anything
   from the third review still open in sections 7 to 11, and which open points in section 15
   could change what the engine does first.
