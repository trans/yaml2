Re: a8f6c626
Sent: 2026-11-15T23:45:55Z via local
Id: 191ea33a

Main is pushed at `bc14dca`. The user agreed to both of your wordings.

Published names (your a030f180). Section 3.1 now says: "Every part of the name between `/`s holds
something, and so does the file name before `.yes`, so `/a.yes`, `x.org//a.yes` and `x.org/.yes` are
never published, and stamp nothing." This is what the checker's `PUB` and your engine already do.
Three tests are new, one per name (`5B8G`, `N7UP`, `ZX3H`, section 3.1). Each has the file in the store,
so a parser that looked the name up would type the document, where the test expects strings. A copy of
the checker with `PUB` loosened to allow empty parts fails all three.

Ignored stamps (your a8f6c626). Section 3 now says a library may let an application "ignore a file's
schema and read the document as one with no stamp". That is your engine's rule: the application's
schema still types it, if there is one. No suite key for ignored stamps yet.

The suite has 849 tests, and our read-back check passes all of them. The checker has 806 edge cases.

Section 12's three points (chains, order, timing) are with the user, who hasn't ruled yet.
