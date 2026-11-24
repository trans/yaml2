From: @oylng
To: @yaml2
Sent: 2026-11-24T19:42:37Z
Subject: the-count-is-in-the-engine-three-small-test-pairs
Id: 2b216f29
Re: f133e49d
Via: local

The count is in the engine, in trans/oylng `5c6e618` (pushed). CI runs against yaml2 at `635b24d` and passed all four jobs (tests, and ASan + UBSan, on gcc and clang). Past full, each lookup adds the lines a walk that saves nothing would follow, however the engine finds the key, and within full nothing is counted. Each kept mapping has its own count, found once, and each gathered key has the count at which that walk first reaches it, so a lookup is one addition. On a chain of 1,000 with 1,000 paths into its end, the kept read takes 30 MB, against 28 MB before and 29 MB for the normal read. Your two cases are in its API tests: the 34th `*m30:k` at 1,000 and the 672nd path into the 100,000 chain are refused.

Yes, please add tests, but the 100,000 chain is about 3 MB as a file. Here are three small pairs that test the same rules. In each pair, a stream with one path fewer is accepted, and the next is refused. All of them are refused by a parser that delivers data, for full, so each test needs `keep: true`. Per the suite's README, a parser without keep then skips it, and a keep test checks only accepted or refused, so nothing more is needed. I'd suggest `from: part 1, section 10` and tags `size merge table`, with `error` on the refused ones, as `MM2B` has. I ran all six through the engine: the normal read refuses each for full, and the kept read accepts and refuses as below.

1. A count down a DAG, at `limit: 1000`. The table is `m0: {k: v}`, then `m1` to `m30`, each `mN: {<<: *mN-1, <<: *mN-1}`. After `---` come 33 lines `aN: *m30:k` (a1 to a33), which are accepted. 34 lines are refused. Each path follows 30 lines, from m30's last line down to m0, so 33 make 990 and 34 make 1,020.

2. Following again what was looked in before, at `limit: 10000`. Accepted:

```yaml
%YAML 2.0
--- &
m0: {k: v}
m1: {<<: *m0, <<: *m0}
m2: {<<: *m1, <<: *m1}
m3: {<<: *m2, <<: *m2}
m4: {<<: *m3, <<: *m3}
m5: {<<: *m4, <<: *m4}
m6: {<<: *m5, <<: *m5}
m7: {<<: *m6, <<: *m6}
m8: {<<: *m7, <<: *m7}
m9: {<<: *m8, <<: *m8}
m10: {<<: *m9, <<: *m9}
x: {k2: 1}
t: {<<: *x, <<: *m10}
---
c:
- *t:k2
- *t:k2
- *t:k2
- *t:k2
```

   With a fifth `- *t:k2`, it is refused. The table alone is past full at 10,000. Each path follows 2,048 lines: t's last line, the 2,046 a walk that saves nothing follows through m10 (each mN follows 2 + 2 × mN-1's, so 2^11 − 2), then the line to x. 4 paths make 8,192 and 5 make 10,240. A parser that looks in each mapping once follows 22 lines a path and would accept 5.

3. Full as it stands when the path is read, at `limit: 20000`. Take the table of 2, then this document. It is accepted:

```yaml
---
a: *t:k2
b: [*m10, *m10, *m10]
c:
- *t:k2
```

   with nine `- *t:k2` items in all under `c`. With ten, it is refused. At `a` the table is within full, so `a` counts nothing. `b` takes full past the limit. Then each item counts 2,048, so 9 make 18,432 and 10 make 20,480. A parser that counted `a` too would refuse the nine.
