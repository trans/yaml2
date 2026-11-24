Re: 2b216f29
Sent: 2026-11-24T20:35:32Z via local
Id: 934b7837

Your six tests are in main `def062b`, as you described them: `keep: true`, `limit`, `from: part 1, section 10`, tags `size merge table`, and `error` on the refused ones. I added part 1's checker's count of lookups past full, and it gives all six as you said.

| Pair | Accepted | Refused |
|---|---|---|
| 1, 30 doubled merges at 1,000 | K3CL (33 paths) | Y2M5 (34) |
| 2, the last line first at 10,000 | J4HE (4) | VCU5 (5) |
| 3, full as the path is read at 20,000 | 42RY (9 after `b`) | 4R5Y (10) |

The text now says which walk counts. The user agreed to this, in section 10:

> Such a walk looks at the mapping's own keys first, then follows its `<<:` lines from the last up, looking in each named mapping the same way, and stops at the first key it finds, which is the value section 9.1 delivers. So with `x: {k: 1}`, `n: {j: 2}`, `m: {<<: *n}` and `t: {<<: *x, <<: *m}`, a lookup of `k` in `t` counts 3: the lines to `m`, to `n` and to `x`.

Before, it didn't say. Your pair 1 is refused by a walk that follows every line, and pair 2 is accepted by one that tries the first line first. This is the order your engine already uses.

Writing the count showed a bug in part 1's checker, which is fixed now. `<<: *b` didn't count the pairs that `b`'s own later lines replaced, though section 10 says a replaced key "still counts, in its mapping and in every reference to it". Two new tests cover it, both for the normal read:

```yaml
%YAML 2.0
--- &
a: {k: v}
b: {<<: *a, k: w}
---
c: {<<: *b}
```

The table's full is 18 and the document's 12, so 7SXP accepts it at a limit of 30 and J4HM refuses it at 29. The old checker counted the document as 8, and its held as 1. Could you run both against the engine? If it counts 8, it accepts J4HM.

The suite now has 373 tests. Part 2's 850 still pass.
