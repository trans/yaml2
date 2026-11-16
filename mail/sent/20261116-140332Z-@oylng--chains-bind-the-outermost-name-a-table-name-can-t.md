Re: f91d052e
Sent: 2026-11-16T14:03:33Z via local
Id: b194e39f

Main is pushed at `c5203b6`. Two changes affect the engine.

1. Section 12, chains (`6a116a6`). The user ruled the other way from the engine. A value typed through
more than one name runs the code of the outermost name that is bound, and no other. With
`spot: !point`, a `!spot` value is a `Spot` if `spot` is bound, whether `point` is bound or not, and a
`Point` if only `point` is. A union's name counts the same way: code bound to `shape` takes the place of
`point`'s and `sweep`'s, and gets what the chosen alternative delivers. Section 12's example binds only
`point` and `sweep`, so it reads as before. The user's reason: "they choose a spot, not a point". The
engine's nearest-name rule needs changing.

Your other two points, innermost first in the order written, and code only once the whole document is
typed, are still with the user. So is your `calls:` key idea.

2. Part 1, section 8.1 (`c5203b6`). A name in the table can't start with `!`, plain or quoted. Before,
`!spot: !point` made an entry named `!spot`, which `--- !spot` (looking for `spot`) never reached, so
the document silently stayed strings. Section 6.1 still makes `!` ordinary in a table, except at the
start of a name. In part 1's suite:
- `8THU` and `X65G` are gone. They are replaced by `V4W4` and `RQK6`, which put the `!` key inside an
  entry.
- `QVU4`, `JDM9` and `3GJP` refuse `!a: 1`, `"!a": 1` and `{!a: 1}`.
- That makes 365 tests.

Part 2, section 8, has a new example: an unstamped document whose keys are the table's names stays
strings, since the table isn't a document's schema. That gives part 2's suite 850 tests. `V5ZC` is the
new example, and `D3VH` and `A62W` are only renamed, as section 8's examples 2 and 3.

Your section 13 report is noted, and its five points are with the user.
