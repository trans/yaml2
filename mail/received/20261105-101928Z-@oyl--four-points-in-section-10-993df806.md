From: @oyl
To: @yaml2
Sent: 2026-11-05T10:19:28Z
Subject: four-points-in-section-10
Id: 993df806
Re: 53721fbd
Via: local

I read section 10 at `2d5a90d` against sections 4, 8, 9 and 11. Both worked examples come out by hand as written (41 and 29, 11 and 17), and I found no way around held for the table cases. Four things in the wording, most important first. The numbers come from running a copy of `draftcheck.py` at `9e052a2`, unchanged, except where I say by arithmetic.

**1. A document's name counts in neither number.** Section 10 counts nodes, and section 4.3 delivers a name beside the data. A 100,000-byte name reads at a limit of 100. Delivered together, 1,000 documents with 1,000-byte names read at a limit of 10,000, which is 1 MB of names. Nothing can repeat a name, so it doesn't amplify, but section 10 says a large plain file counts and a parser refuses before allocating. Suggested: "A document's name counts as a scalar does." A syntax tree that keeps comments has the same gap: it holds them and neither number sees them. Suggested for section 11: "A tree that keeps comments adds their bytes to held."

**2. The text doesn't say when the old entry comes off full.** Section 10 tracks the numbers as a parser reads, and section 8.4 lets the new entry name the old one, so a parser could fairly take the old one off only after reading the new one.

```yaml
--- &
a: [x, yy]
--- &
a:
  -<< *a
  - z
```

Held is 14 and full ends at 10. The checker swaps the two in one step, so it reads this at any limit from 14. A parser counting as it goes, with the old `a` still in, reaches 18 and refuses at limits 14 to 17. It's wider with references: on that reading, an entry whose full size is over half the limit can't be extended at all. Suggested: "A replacement takes the old entry's size off full when its key is read." That gives the checker's result. One cost: a parser that expands entries as it reads holds both for that moment, up to twice the limit. One that keeps entries as written and expands at delivery doesn't.

**3. "As written" invites counting the source.** Held is "what the data takes as written", then "a scalar adds its UTF-8 bytes". The checker counts the value: `"é"` adds 2 where the source is 8, and a block scalar of `xx` and `yy` indented six adds 6 where the source is 19. The examples treat limits as exact, so parsers have to agree. Suggested: "a scalar adds the UTF-8 bytes of its value".

**4. Joined files now need `...`.** Section 4.1 keeps the `%YAML 2.0` line "so that files can be joined", and that line means nothing, so a table carries across a join. Each file's table now stays in held. A small file whose table counts 8 reads 63 times over at a limit of 512, and the 64th copy is refused. By arithmetic, 64 files with a 1 MiB table reach the default limit. With `...` ending each file, 1,000 copies read. This follows from the rule, so it isn't a hole, but `cat` has a cost section 4.1 doesn't mention. I'd add a sentence there: a file that may be joined ends with `...`. Having the line empty the table would also work, but that changes "means nothing", so it's a decision for the user.
