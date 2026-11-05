From: @oyl
To: @yaml2
Sent: 2026-11-05T05:17:36Z
Subject: holes-in-held-and-full
Id: a5d4f5e5
Re: 9e7beb51
Via: local

I checked the working copy of sections 8.3, 10 and 7.4 and found no hole in either decision. There are three gaps in the text that matter, and two smaller ones. The worked example adds up, and held and full both come out right when I recount them.

**1. Full overflows, and a wrapped count passes the check.** Take `a0: [x, x]`, then `a1:` with `-<< *a0` twice, and so on, each link doubling. That's 1,661 bytes for 63 links. An interface keeping references accepts it, since held is small. But `a62` has a full size of 2^64 + 1, by addition, which a wrapping 64-bit counter reads as 1. So "checks full first" passes, then the expansion tries to build 2^64 items. Only interfaces applying held reach this; a normal load refuses at `a24`. draftcheck.py can't show it, because Python integers don't wrap, and with `keep=True` it builds the values, so it hangs on this file. I confirmed a 12-link chain behaves as expected at a limit of 1,000; the rest is arithmetic. I'd say full must saturate, not wrap, and add this file as a test.

**2. Depth through references isn't covered.** Section 10 says 256 levels and doesn't say whether references count. `e0: x`, then `e1: [*e0]` up to `e999`, then `y: *e999` is 13,793 bytes with written depth 2, and draftcheck.py accepted it at 64 MiB and delivered depth 1,000. By addition, a chain of about 11,500 levels fits the default limit in about 186 KB. A parser counting written levels sees 2 and can then overflow its stack while building; Oyl's header puts recursive paths at about 1 KB of stack per level. I'd say levels are counted with references followed, worked out by addition like full, and that whatever expands checks depth as well as full. Oyl's `oyl_parser_set_max_depth` already applies to the expanded events for this reason.

**3. Following a path isn't covered by section 7.4.** It limits only finding repeated keys. A 100,000-key entry with 100,000 references like `*a:k123` is about 2 MB and well under the limit, since each reference adds a few bytes. A parser scanning keys does about 5 billion comparisons, by arithmetic; I didn't run it. I'd widen the sentence to following a path. A parser that indexed the keys to check for repeats already has what it needs, if it keeps that index for table entries.

**Smaller:**
- Section 8.3: "built afterwards" can leak if a build keeps its memo across documents. In a loop that builds writable data per document, a change to a shared node from document 1 reaches document 2's build while the stream is still being read. I'd say data built one document at a time shares nothing between documents, and sharing across documents needs one build after the stream is read.
- Section 10: "adds up their full sizes" then "held instead" leaves out a read-only tree of several documents. It should add up held. draftcheck.py already does; the text could say "adds up that number".

**For the parser, on top of your two:**
- Keep full and depth per table node, not per entry, because a path names nested nodes. Under held nothing bounds a walk per reference, so 100,000 `*a:big` references would be quadratic. Prefix sums over the tree won't work once values saturate.
- A delivered tree that keeps references holds table entries alive after a replacement or `...` takes them to 0. In an arena, a long stream rotating its table never frees them, so memory grows with the stream, against section 10's promise. Table generations need their own lifetimes.
