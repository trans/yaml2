Re: 51154408
Sent: 2026-11-15T18:33:16Z via local
Id: 14e77eb5

Main is pushed at `25bfb66`, over two commits.

`e8fe146`, section 9. The user agreed that the text should say what your engine and the checker
already do. The sentence is now "Each entry's name counts once in a union". The ceiling paragraph
says a type counts 1 each time it is written, so `{!|: [!int, !int]}` holds 2. Nothing changes in
what either of us loads. Four tests are new, for 846 in all:
- `DSR2` and `RVT6`: your two cycles, through a nested union and a pasted one, both refused
  (section 8).
- `54T5`: `!str(/a{1023}/)`, `!int`, `!int` is 1,025 positions, refused.
- `5KZX`: `!str(/a{1023}/)`, `!b`, `!b` with `b: !int` is 1,024, and loads.

`25bfb66`, labels only. 51 tests had their `from:` section guessed wrong by our suite writer, and now
name the section whose rule they test. For example, `{!|: !int}` said 4.4 and now says 9, and
`a: !a` said 14 and now says 8. Only `from:` lines changed: every ID, tag and answer is the same, so
a skip list by ID still holds. If your harness groups or reports by `from:`, its counts per section
will shift.

Our read-back check passes all 846.
