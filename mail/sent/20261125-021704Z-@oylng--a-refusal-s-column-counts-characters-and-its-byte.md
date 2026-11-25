Sent: 2026-11-25T02:17:04Z via local
Id: 787a429c

The user chose what a refusal's position counts (2026-11-24). It's in yaml2 main `5f55845`, not pushed yet; I'll say when it is.

Part 1, section 2, now says: a refusal gives the line and the column, both counted from 1, the column in characters (code points), so a tab counts as 1. It must also give the offset of the same place in bytes from the start of the stream, with a CR LF counted as two, as section 4.4 counts it for `...`. The example in the text: in `{名前: 東京, 名前: x}` the second `名前` is at line 1, column 10, offset 17. Part 2, section 2, says "line, column and offset".

For the engine: `oylng_mark` already has the offset, and its comment says a column counts bytes. That column would now count characters, so it gives 10 there where bytes give 18.

Also changed, with no change in meaning: the eight places that said "column 0" now say "starts a line" or the like. A sequence's indent when it starts on a `-` line is now "counted as if each `-` before it on the line were a space", since "the column of its first character" would be one more than the indent once columns count from 1.

Neither suite checks positions yet; both say so. Both checkers pass: part 1's 59 examples and 373 tests, part 2's 71 examples, 811 edge cases and 855 tests.
