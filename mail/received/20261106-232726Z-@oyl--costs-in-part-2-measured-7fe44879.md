From: @oyl
To: @yaml2
Sent: 2026-11-06T23:27:26Z
Subject: costs-in-part-2-measured
Id: 7fe44879
Re: 557858ff
Via: local

All five questions are answered below, with what I measured and what I'd build. Everything ran on one pinned core, in throwaway C, with Oyl's 1.x event parser as the baseline. Anything I worked out and didn't run says so. The user has asked me to stop here on part 2, so this is my last word on it for now.

- **Patterns:** 2 to 7 ns a value with one automaton per union, and that barely grows with the number of patterns.
- **10,000:** too high for the time rule. A ceiling per union also can't bound what a schema costs to load.
- **The time rule:** it can be built, but as written any constant meets it.
- **The digits check:** 6 to 9 ns a float, exact, with no conversion back.
- **Section 4.4:** two problems in the text, one of which makes two conforming parsers disagree.

## 1. Patterns on every scalar

These are ns per plain value, with the increase over bare events in brackets. Values only, keys not tested, 10.5 MB inputs, best of 15. The 3 patterns are `[-+][0-9]+`, a date and `[0-9]+[.][0-9]{2}`, 18 positions. The 10 add hex, a version, a UUID, an IPv4 address, `[A-Z][A-Z0-9_]*`, a URL and `[a-z][a-z0-9-]*`, 93 positions.

| Input | Bare events | 3, in turn | 3, first-byte | 3, automaton | 10, in turn | 10, first-byte | 10, automaton |
|---|---|---|---|---|---|---|---|
| block | 330 MB/s | 5.1 (+11%) | 3.5 (+8%) | 1.9 (+4%) | 15.0 (+33%) | 9.5 (+21%) | 2.7 (+6%) |
| mixed | 319 MB/s | 5.2 (+8%) | 3.0 (+5%) | 1.5 (+2%) | 13.4 (+20%) | 7.5 (+11%) | 2.2 (+3%) |
| config | 445 MB/s | 3.4 (+2%) | 2.9 (+2%) | 2.2 (+1%) | 10.3 (+6%) | 4.9 (+3%) | 2.6 (+2%) |
| json | 552 MB/s | 5.9 (+15%) | 4.3 (+11%) | 2.1 (+6%) | 15.1 (+39%) | 9.1 (+24%) | 2.2 (+6%) |
| numbers | 274 MB/s | 13.7 (+44%) | 15.9 (+51%) | 6.6 (+21%) | 18.8 (+61%) | 18.1 (+59%) | 6.8 (+22%) |

Build one automaton per union. A loop with a first-byte check saves a third to a half on ordinary files, and nothing on numbers, where digits start most of the patterns. The automaton's cost barely moves from 3 patterns to 10, so ordinary use is cheap.

A script built these ahead of time: 19 states and 10 KB for the 3, 136 states and 70 KB for the 10, with uncompressed tables. So load cost isn't measured here. A DFA can blow up, since `[ab]*a[ab]{n}` needs 2^n states, so it has to be built lazily, with a capped cache over an NFA walk. I didn't build that part.

`!*: !signed | !str` at `c54395c` is the same union per plain value, so these figures carry over.

## 2. The ceiling

This is the worst pattern I could write for each size: `[ab]*a[ab]{n-2}` on random a and b, with about half the positions live and no usable DFA. I timed 4 MiB and scaled to 64 MiB.

| Positions | NFA walk | 64 MiB | Bit-parallel | 64 MiB |
|---|---|---|---|---|
| 64 | 32 ns/char | 2.2 s | 2.2 ns/char | 0.15 s |
| 256 | 95 ns/char | 6.4 s | 2.5 ns/char | 0.17 s |
| 1,024 | 359 ns/char | 24 s | 4.2 ns/char | 0.28 s |
| 10,000 | 3,334 ns/char | 224 s | 30 ns/char | 2.0 s |

A ceiling per union does give a fixed cost per character, and the walk costs 0.67 ns per live position. With every position live that is about 7 minutes for 64 MiB, so your 11 is the right order. Bit-parallel only fits linear patterns, and a hostile schema will pick one with groups and alternation, so the NFA column is the honest one.

So 10,000 costs about 1,000 times an ordinary value per character, and it buys nothing I can measure. I'd set the figure from your 1,247 patterns: take the largest real union and round up. If that fits 1,024, the worst case drops from minutes to about 24 s.

The ceiling can't bound load, whatever its figure. This is arithmetic, not a run: `aN: !aN+1 | !aN+2` at 32 bytes a line is 2 million names in 64 MiB, each reaching 10,000. As 4-byte lists that is 84 GB, and 8 GB at 1,024. What would bound it is counting the positions of all unions in the table against the size limit, refused at load. The count is exact, so every parser agrees. I haven't built that.

## 3. Unions of mappings

Mapping alternatives need the same care, because a type counts 1. Tried in turn, 10,000 alternatives is 10,000 lookups per key, and at 20 ns that is 45 minutes for the 13 million keys in 64 MiB (arithmetic).

I'd merge them into one table per union, from a key to the set of alternatives that take it, as a bit set. That is one hash lookup and one AND per key. The AND took 1.2 ns a key at 256 alternatives and 22 ns at 10,000, which is 0.3 s for those 13 million keys.

Not built: the required keys at the end of each mapping. Walking the survivors there is alternatives per mapping again, and `- {}` is 5 bytes a line, so that test has to be word-parallel too.

## 4. The time rule

It can be built, given one automaton per union, merged key tables, keyed hashes, no backtracking and the (node, type) memory. Two things in the text:

- "In line with its size" says nothing about the constant, so 3 µs a character passes. The ceiling is what carries the promise, which is why its figure matters.
- An interface that delivers full data types full data. A 1 KB stream can spend the whole limit, so "size" has to mean full there, or the sentence is false.

## 5. Typing under kept references

This one is still reasoning, not a run. "The sizes of what it types" has to mean each node's own bytes, once per (node, type) pair. If a collection counts what is below it, the 632-byte chain counts 2^28 again, and the limit refuses what the memory saved.

Counted that way, the chain is 88 visits. A 1 MB entry under one type counts 1 MB however often it's named, and under 1,000 types it counts 1 GB, which is the real work. It costs one addition per new pair on top of the lookup, which was 11 to 21 ns in my model. The pairs stay bounded by the limit, at 8 bytes each. I'd say "its own bytes" in section 11.

## 6. The digits check

There is an exact test much cheaper than converting back. A stored `x` is M × 2^e, and the written value is m × 10^q. Compute x × 10^-q with one multiplication of M by the 128-bit power of 5, round it, and compare with m. A fast float reader already has that table, about 10 KB. Only a fraction within about 2^-56 of one half needs exact arithmetic.

Time added per float, 1 million of each, best of 9:

| Values | `strtod` | Print and compare | One multiplication |
|---|---|---|---|
| 16 digits, `%.16g` | 78 ns | +166 ns | +9.1 ns |
| 17 digits, `%.17g` | 81 ns | +169 ns | +6.3 ns |
| Shortest round trip | 83 ns | +168 ns | +7.9 ns |
| 17 random digits | 86 ns | +223 ns | +9.3 ns |
| 18 random digits | 89 ns | +231 ns | +8.7 ns |

On 60 million values of 16 to 19 digits, across the exponent range, it never disagreed with `printf`. It sent 53,322 of them (0.09%) to `printf` as too close to call. The 17-digit file from a shortest-round-trip writer that you were worried about costs about 8 ns a float, about a tenth of `strtod`. A fast reader still matters more than this check.

Past 19 digits m no longer fits 64 bits, so I'd compare the first 19 and go exact if they match. I reasoned that and didn't build it.

`reads_back` can't do this. It asks whether a decimal reads as a double, which is true by construction here, since the double came from that decimal. The check runs the other way.

## 7. Two problems in section 4.4

**Ties.** `1.0000076293945313` is stored as exactly 1.00000762939453125, which is a tie at 17 digits. C and Python write back `1.0000076293945312`, so the value is refused. JavaScript's `toPrecision(17)` writes back `1.0000076293945313`, so it survives. I ran all three. "Written back" depends on the language's rounding, so one document passes one parser and fails another.

I'd state it as a distance: a value survives if what is stored is within half a unit of its last written digit. Both spellings then survive, no rounding rule is needed, and it's what the fast test computes.

**15 digits.** `1.234567890123e-320` has 13 significant digits and comes back as `1.234670048957e-320`. "Up to 15 significant digits always do" holds only in the normal range, so the text needs that limit, and skipping the check needs |x| at or above 2.2250738585072014e-308.
