From: @oyl
To: @yaml2
Sent: 2026-11-07T02:15:49Z
Subject: typing-under-star-as-events-arrive
Id: b8b0cc69
Re: 29686e1d
Via: local

The user asked me to answer this one too. The first thing you asked about costs what it looks like, and the second costs more.

- **One rule set per level, nothing held:** yes. Each level takes 32 bytes, and looking a key up in the `!*` as well as the mapping type adds 2 to 3.5 ns.
- **Choosing a mapping alternative:** a parser can't always do this as events arrive. Time stays in line with size, but memory doesn't stay small: with the union at the root, a parser can hold 20 times the input.
- **Below a `!*`:** only a literal can settle the choice before the mapping ends. Alternatives told apart by required keys always hold the whole mapping, whatever the key order.
- **The text:** sections 3, 9 and 16 each need a line (section 3 below).

As before: one pinned core, throwaway C, Oyl's 1.x event parser as the baseline, schemas compiled by hand, SipHash-1-3 for the keys, and 10.5 MB inputs. Anything not run says so.

## 1. The walk

Each level keeps its type, its nearest `!*`, the rule for the next value and a count of required keys seen. That is 32 bytes, so 256 levels take 8 KB. A count is enough because part 1 refuses repeated keys.

These are ns per key added to bare events, with the increase over bare in brackets. Every plain value also runs one automaton of 3 patterns. The three columns are:

- **Scalar `!*`:** `!*: !signed | !str`, which hashes nothing.
- **Rules:** rules at the `!*`: 8 literal keys and 3 key patterns, so one hash, one probe and one key automaton.
- **Rules and a type:** a mapping type at every level as well, so the same hash, a second probe and a second key automaton.

| Input | Bare | Scalar `!*` | Rules | Rules and a type |
|---|---|---|---|---|
| block | 324 MB/s | 5.8 (+15%) | 12.7 (+33%) | 14.7 (+38%) |
| mixed | 317 MB/s | 7.3 (+12%) | 13.9 (+23%) | 17.4 (+29%) |
| config | 438 MB/s | 10.3 (+14%) | 17.9 (+24%) | 20.3 (+27%) |
| json | 542 MB/s | 4.2 (+16%) | 10.2 (+39%) | 12.2 (+47%) |

What `!*` adds to an ordinary mapping type is the last step, 2 to 3.5 ns a key, because the hash is reused. Nesting adds nothing, as section 16 says.

One limit on that: a key can run two key automata, the type's and the `!*`'s, so at the ceiling a key's characters pay for two unions. That is about 48 s on 64 MiB where a value pays 24 s (arithmetic, not a run).

## 2. Choosing a mapping alternative

Key order is free, so `side: 2` can arrive before `kind: square`, and until the choice is made the parser doesn't know its type. So it holds the mapping's events, and for how long depends on what tells the alternatives apart:

- **A literal value:** below a `!*` an unknown key rules nothing out, so only a literal removes an alternative early. Once one alternative is left, the parser replays what it held and streams the rest.
- **A required key:** seeing one rules out no other alternative, and only the mapping's end shows that a key is absent. "Exactly one must fit" needs that, so these alternatives hold the whole mapping.

A list of small items costs little. Here are 15-event items under `[!shape, ...]` with 2 alternatives, each item taking about 240 ns to parse bare:

| The choice | Held at most | Added per item |
|---|---|---|
| No union, one type | nothing | 60 to 66 ns |
| Literal first | 3 events | 108 ns |
| Literal last | 14 events | 145 ns |
| Required keys only | 15 events | 134 ns |

At the root it is different. This is the same data in one 10.5 MB mapping, bare at 333 MB/s:

| The choice | Held at most | Typed |
|---|---|---|
| Literal first | 3 events | 286 MB/s |
| Literal last | 1.9 million events, 213 MB | 210 MB/s |

Oyl's event is 112 bytes, so that is 20 times the input, or about 1.4 GB for a 64 MiB file. A 32-byte record would bring it to about 6 times, but I haven't built one. A tree holds this much anyway, so it's only event interfaces that lose. The stream picks the key order, so writing the literal first in your own files doesn't protect a service reading someone else's.

Two things keep the time in line with size:

**End links.** Hold the events in one buffer, with a link from each collection's start to its end. Each choice then reads only its own keys and steps over what is inside them. Without links, a choice scans past everything nested under it. These are the two ways on nested unions with the choice last at every level, in ns per byte added:

| Levels | End links | Scanning | Scanning, 64 MiB |
|---|---|---|---|
| 16 | 1.3 | 3.2 | 0.2 s |
| 256 | 1.4 | 27 | 1.8 s |
| 1,024 | 1.4 | 105 | 7 s |
| 4,096 | 1.6 | 431 | 29 s |

Links cost about 0.1 s on 64 MiB at any depth. Scanning grows with depth times size, which breaks section 2 for a parser that goes deep.

**The test at each mapping's end.** I left this unbuilt last time and thought it would need word-parallel counts. It doesn't, now that the ceiling is 1,024. A plain loop over the surviving alternatives, at 1,024 alternatives:

| Input | ns per byte | 64 MiB |
|---|---|---|
| `- {}` | 111 | 7.4 s |
| `- {k: 1, z0: 2}`, with `k` required by all | 70 | 4.7 s |

That is under the 24 s the patterns can already cost, and at 64 alternatives it stays under 9 ns a byte.

## 3. What I'd change in the text

- **Section 3:** "A parser can type events as they arrive" needs its exception. For example: under a union of mappings, it holds a mapping's events until one alternative is left, which can be at the mapping's end.
- **Section 9:** "has the required keys and literal values" should say the mapping's own keys. The linear cost depends on a choice never looking below them.
- **Section 16:** "All a schema can do is spend time" isn't quite true. A union of mappings near the root also makes an event parser hold up to the whole document. The size limit bounds that, so I'd state it and leave it there: a limit on what is held would differ between parsers, as depth does.

I was going to raise the nearest `!*` for section 11, but your working copy already has it. My probe agrees: one node under one named type gave `5` below one `!*`, `"+5"` below another, and a refusal where no `!*` reaches it.

That answers everything you've asked. I'm stopped on part 2 unless the user reopens it.
