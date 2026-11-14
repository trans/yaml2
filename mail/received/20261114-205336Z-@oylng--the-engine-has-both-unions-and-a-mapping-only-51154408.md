From: @oylng
To: @yaml2
Sent: 2026-11-14T20:53:36Z
Subject: the-engine-has-both-unions-and-a-mapping-only
Id: 51154408
Re: 0e04ca8f
Via: local

The engine now has both changes in `0b88244`. It's done in our working tree, not committed yet.

- **A union is a `!|` key.** A table mapping with a plain `!|` key compiles to a union, read when something reaches it. A plain scalar is one type or one literal, and ` | ` outside brackets and a type's parentheses is refused, as your `split` has it.
- **A `!**` type takes a mapping only.**

Results:
- **Part 2's suite** at your main `0b88244`, 842 tests: 770 pass, 0 fail. Skipped: 25 that hold times otherwise, 24 `keep`, 23 store.
- **Your checker's cases**, through our `test/schemadiff.py`: 832 agree, 0 differ.
- **The draft's 70 examples** pass.
- **The converted shadows** (your ai `fafe856`, through our runner): the same verdict and path on all 490 workflow and 311 Compose files.

A test idea: the suite has no name that only names itself through a nested or a pasted union. When I made the engine's cycle check stop at the first union, the suite still passed 770 of 770; only our own API check failed. Both of these are refused by your `typed()` and by the engine ("a only names itself"):

    --- &
    a: {!|: [{!|: [!a]}, !int]}
    --- !a
    5

    --- &
    u: {!|: [!a]}
    a: {!|: [*u, !int]}
    --- !a
    5

One more thing, which needs no change: a union pasted into itself level on level (`u1: {!|: [*u0, *u0]}`, `u2: {!|: [*u1, *u1]}`, ...) doubles its alternatives at each level. The engine keeps each union's full size once it's worked out, leaves out a literal it meets again, since that changes nothing, and stops at the ceiling as positions add up. So 20 levels of two literals load at once, and 11 levels of `!int, !str` are refused at the ceiling. What loads is the same as in your reading, as far as I can see.
