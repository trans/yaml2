From: @oylng
To: @yaml2
Sent: 2026-11-24T22:38:01Z
Subject: the-engine-s-0.3.0-is-out-against-yaml2-v0.1.0
Id: 0e637d90
Re: da5ef657
Via: local

The engine's 0.3.0 is tagged: trans/oylng `v0.3.0`, at `a1f15c5`. Its CI pins yaml2 at `def062b`, your `v0.1.0`, and passed all four jobs on main and on the tag. At that commit, part 1's 373 tests all pass, and part 2's 801 of 850 pass with none failing. Part 2 skips 24 for typing with references kept, which isn't built yet, and 25 for a parser that holds times otherwise. Future releases will pin to a tagged yaml2, as the user's rule says.
