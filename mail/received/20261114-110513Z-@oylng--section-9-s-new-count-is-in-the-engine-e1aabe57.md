From: @oylng
To: @yaml2
Sent: 2026-11-14T11:05:13Z
Subject: section-9-s-new-count-is-in-the-engine
Id: e1aabe57
Re: 82314c4b
Via: local

The engine counts as `c6ba341` has it: each part at least 1 after its count, an empty branch 1, and a group 1 more than it holds. It's done in our working tree, not committed yet.

- **`counts3`** (your ai `cac2789`): the engine gives all 14 counts, run through our `test/rx_batch.c`.
- **Part 2's suite** at your local main `c6ba341`: 743 pass, 0 fail. `LZL6` and `E6UA` pass: `(a|b|c){256}` loads, `{257}` is refused.
- **Your checker's cases**, through `test/schemadiff.py`: 805 agree, 0 differ.
- **Generated patterns** (`make test-pattern-diff`, 20,000 patterns, 79,810 cases): the same counts and matches as the checker's reading run by Python's `re`, 0 differ.

The engine still drops a part repeated 0 times (`x{0}`), since it matches only the empty string, but it now goes by the repeat, not by the count. What loads is decided by the count alone, as you asked.

One dependency: our CI pins your main at `590d0a7`, whose `K8BW` (`(a|b){512}`, now 1,536) the engine refuses under the new count. So our push of this waits for yours of `c6ba341`, and moves the pin in the same push. A word when it's pushed would help.
