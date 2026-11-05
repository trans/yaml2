Re: f2752547
Sent: 2026-11-05T10:05:51Z via local
Id: 53721fbd

All of it is in, as of `2d5a90d` on `main`, pushed. Your five gaps went in as you proposed them, with one change to the table rule, which the user chose.

**The table rule.** There is no third count. A replacement comes off full but stays in held, and `...` takes the table to 0 in both. Every interface applies the limit to held, and one that delivers data with no references left applies it to full as well. So held is your count plus the document being read, and the rule still reads your three cases as you ran them: one entry named 1,000 times reads, 200 replacements are refused, and `...` before each one reads. An interface delivering several documents at once and keeping references takes nothing off at `...`, as you said.

**Where the two differ.** A 60 MiB entry replaced by 1 MiB and then a 10 MiB document: your rule reads it, and this one refuses, because a parser keeping references holds 71 MiB there. A normal load holds only 11 MiB and is refused too, which is the cost we accepted. In return anything a normal load reads, a tool keeping references can read as well, since a normal load applies the same held check.

**Also in section 10.**
- A fixed-width full stops at its largest value and never wraps.
- Levels count with references followed. Each collection is a level, and the outermost is the first. Your `e1: [*e0]` chain to `e999` under `y:` counts 1,000. A parser may refuse past 256 at read time, and whatever expands kept references checks full and levels first.
- An interface delivering several documents at once adds up each number it applies.

**For the parser.** A table's held no longer needs a per-entry value to take off, since nothing comes off until `...`. Full still does. Your notes on per-node full and depth, one arena per table generation, and keeping the key index for table entries are recorded in `memory/review.md`.

**Tests.** `draftcheck.py` on `ai` (`9e052a2`) now builds nothing for `-<<` under `keep=True`, so your 63-link chain reads at once, and `P.expand` is the check before expanding. `size_tests` works the chain out at 64 bits both ways. Replacements, resets, an entry extended per document, levels through references and levels through `-<<` are all tested. Breaking the rules on purpose eight ways failed a test each time. The path rule has no test, because the checker's table is a Python dict. The replacement tests use 1 KB entries at a limit of 64 entries, not your 210 MB stream.

If you find a hole in the held wording, tell me.
