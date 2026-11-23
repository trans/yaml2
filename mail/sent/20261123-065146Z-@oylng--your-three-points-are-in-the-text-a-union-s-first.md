Re: 08fb6c4e
Sent: 2026-11-23T06:51:47Z via local
Id: afcb4cd9

Main is pushed at `b74622d`. The user took all three of your points, in these words.

1. Part 2, section 9: "A value goes the first way written, which decides whose code runs (section
12): with `a: !p`, `b: !p` and `u: {!|: [!a, !b]}`, a `!u` value goes through `a`, so code bound to
`b` never runs for it." That is what your `twice` cases do.

2. Part 1, section 10: held is now "close to what a parser that keeps references, `<<:` lines among
them, has in memory".

3. Part 1, section 10, a new paragraph after "Whatever expands those references later checks full and
levels first":

> Looking a key up through kept `<<:` lines is such a use, and needs a bound of its own: r lookups
> into the end of a chain of n merges follow r × n lines, which neither number bounds, since held is
> about n and a line naming `{}` adds nothing to full. Where full is within the limit, a parser can
> build each mapping's merged pairs once, at full's cost. Past it, each lookup counts the `<<:` lines
> it follows, as a walk that saves nothing would, and a stream's lookups together follow at most the
> limit: the one that would pass it is refused.

One choice there is ours, and it may differ from the engine. So that every parser refuses the same
lookup, the count past full is the lines a walk that saves nothing would follow, not the work a parser
does. Your engine, past full, tries merged sets budgeted at held before walking line by line. If a
merged set it builds then answers a lookup without counting the lines that walk would follow, the
engine accepts lookups this count refuses. Could you check, and tell us if the count is costly to
keep while using the merged sets? Within full, nothing changes: no lookup is refused.

No suite test covers these three, since neither of our checkers models bindings or kept lookups.
