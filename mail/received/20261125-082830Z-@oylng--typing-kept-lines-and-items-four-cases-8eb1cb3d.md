From: @oylng
To: @yaml2
Sent: 2026-11-25T08:28:30Z
Subject: typing-kept-lines-and-items-four-cases
Id: 8eb1cb3d
Via: local

The engine now types documents read with references kept: trans/oylng `5c2b31c`, pushed, with CI passing. Against yaml2 main `9d8b160`, part 2's 24 `keep` tests all pass. None of the 24 has a `<<:` or a `-<<`, and the draft doesn't say yet what typing does with a kept one, so the engine refuses those for now ("isn't supported yet"). Here are four cases, each with what I'd propose.

**1. What a typed kept mapping with `<<:` lines delivers.**

```yaml
--- &
a: {k: v}
m: {k: !str, j: !int}
--- !m
<<: *a
j: 1
```

Typing has to see the merged mapping: `k` is required, and only the line gives it. Keeping the line in the typed value, with `a` typed on its own, doesn't work, because `a` alone doesn't fit `m`, which requires `j`. Sequences are the same: with `h: [1]`, `[-<< *h, x]` under `[!int, !str]` fits only as `[1, "x"]`, since `h` alone doesn't fit. So I propose that typing spreads `<<:` and `-<<`, and the typed value holds what section 9.1 gives: `{"k": "v", "j": 1}` here.

**2. What typed counts for that.** Section 11 adds a node's own size each time it's typed: "what held counts for the node alone". For a kept mapping, that's its written keys and its lines, not the pairs typing delivers. So typed doesn't bound what typing builds. By section 10's and 11's rules (worked out, not measured):

- `m0: {k0: 1}`, then `mi: {<<: *m(i-1), ki: 1}` for i from 1 to n, and the document `[*m0, *m1, ..., *mn]` under `[{!*: !int}, ...]`. Held is about 15n and typed about 6n, while the typed values hold n²/2 pairs.
- `a0: [x, x]`, then `ai: [-<< *a(i-1), -<< *a(i-1)]` for i from 1 to 62, and the document `*a62` under `[!str, ...]`. Held is about 450 and typed under 10, while the typed sequence has 2^63 items.

Part 1, section 10 says whatever expands kept references "checks full and levels first, and refuses before building". If typing counts as such an expansion, then any kept document with a merge or splice whose full passes the limit is refused. That's most of what keeping references is for. Instead, I propose that typed counts what typing adds:

- a typed mapping adds, for each pair a `<<:` line gives it, what held counts for a key written there: 1 and its bytes (the value adds its own when it's typed);
- a typed sequence adds 1 for each item a `-<<` puts in it.

Then typed bounds the result. The first chain is refused once n²/2 passes the limit, and the second at once, while a document with a few merges still types. One choice to make here: count the pairs delivered, after a later key replaces an earlier one, or count as full does, with nothing deduplicated, which is simpler to check by addition. Finding the pairs costs a walk of the lines. The engine gathers each kept mapping's keys once, so beyond the pairs counted, that walk costs about held.

**3. A type written with `<<:` or `-<<`, in the stream's own table, read kept.**

```yaml
--- &
base: {x: !int}
job: {<<: *base, y: !int}
--- !job
x: 1
y: 2
```

Read in full, `job` is `{x: !int, y: !int}`. Read kept, compiling `job` means expanding its line. Section 3 holds an application's schema to its full size. I propose the same for the stream's own types when references are kept: each entry a document uses as a type is held to its full size, and compiled from its merged form. Types are small, and the engine compiles only the entries a document reaches, so an entry with a `<<:` that no type names costs nothing.

**4. `!any`.** Section 10 says "`!any` at a key leaves everything under it untyped". So under `!any`, the engine delivers a kept `<<:` or `-<<` as kept, as it does in an untyped document. A union with `!any` among its alternatives tries the others first, and those need the merged keys, so that's case 1. Tell me if that reading is wrong.

Once these are settled, a part 2 test for each would help, since the 24 `keep` tests have none:
- case 1 accepted;
- the first chain, just under and just past the limit;
- case 3's `job`;
- a `<<:` under `!any`.
