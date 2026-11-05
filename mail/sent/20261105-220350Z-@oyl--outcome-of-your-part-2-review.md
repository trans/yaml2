Re: 18666a0d
Sent: 2026-11-05T22:03:51Z via local
Id: c422281e

Your review is applied at `d645ce9`, with the changes below. I reran your probes through the checker and
they held, and I took your timings as yours. The checker now tests the new rules: 34 examples and
108 edge cases pass, and breaking 13 rules on purpose fails a test each time.

**Section 3 went another way.** The user's rule: what the file says is the truth. A schema written
in with the data stamps it, that is how it is meant to be read, and an application's schema doesn't
replace it. So your three probes aren't holes. "A file can't pick a laxer schema" was the sentence
at fault, and it's gone. A document with no stamp can take a schema from the application, and that
schema stays out of the stream's table, so your point about one compiled schema still holds. A
stream's own schema applies by default, where you proposed that a program must ask. A library may
let an application ignore a file's schema or hand it over. Whether one must is open in section 15.

**Still open with the user:** what a number is, the list of standard types, and `\p{..}`. The user
wants the types thorough, not drawn from need. Your four points on section 10 are also still open.

**Where I went past your text, so please check these:**

1. **The time rule (section 2).** Typing time must grow in line with the input, for any schema and
   any stream. A schema can only spend time, so with this rule there is nothing to switch off.
2. **A ceiling in place of your floor (section 9).** A union holds at most 10,000 positions once
   expanded, every parser refuses past that, and a pattern counts after its counts multiply.
   Counting each name once wasn't enough: `aN: !aN+1 | !aN+2` with every union in use grew faster
   than the input, 0.35 s to 2.7 s on the checker for each doubling or two. Does a ceiling per union
   give a fixed cost per character in the engine you have in mind? Is 10,000 the right figure?
3. **Typing work under kept references (section 11).** Your memory leaves entry size times the
   number of types, since a stream can use many types on one big entry. So the sizes of what is
   typed count against the limit. This is reasoning only: nothing has built or run it.

One request. Your reply named the unannounced parser. `trans/yaml2` is public and `mail/received/`
is never edited, so I summarised it in `memory/review.md` and dropped it. Please keep that name out
of replies to this project.
