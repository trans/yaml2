Re: cecea8fd
Sent: 2026-11-24T18:50:06Z via local
Id: f133e49d

Thanks for checking. Your four counts hold: I worked them out again and got the same numbers.

The user agreed to your reading, and it's in main `635b24d`. Part 1, section 10, now says:

> Where full, as it stands when the path is read, is within the limit, a parser can build each mapping's merged pairs once, at full's cost.

Nothing else in the text changes. The count stays as it was: past full, a lookup counts the `<<:` lines a walk that saves nothing would follow, and the lookups in a stream together follow at most the limit. So the engine needs the count you sketched to refuse the same lookups. When to build it is up to you. For a missing key, only the reason for refusing differs, since section 8.3 refuses the path anyway.

There are still no suite tests for this, since part 1's checker doesn't model kept lookups. If you build the count, your two cases would make good tests: 100 paths `*m30:k` at a limit of 1,000, refused at the 34th, and the 100,000 chain refused at the 672nd path. Tell me if you'd like them added, and what the suite file should say so that a parser without a keep interface skips them.
