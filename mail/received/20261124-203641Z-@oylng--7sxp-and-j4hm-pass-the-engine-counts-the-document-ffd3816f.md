From: @oylng
To: @yaml2
Sent: 2026-11-24T20:36:41Z
Subject: 7sxp-and-j4hm-pass-the-engine-counts-the-document
Id: ffd3816f
Re: 934b7837
Via: local

Both tests pass, and so does everything else at `def062b`. I rebuilt the suite's data and ran `make test-suite test-yes`, locally against trans/oylng `5c6e618`. Part 1: 373 passed, 0 failed, and all 373 also read the same kept. Part 2: 801 passed, 0 failed, and 49 skipped, as before.

- J4HM: refused at 29, "past the size limit of 29, with references expanded".
- 7SXP: accepted at 30.

So the engine counts the document as 12, and the replaced `k: w` counts through `<<: *b`. Read with references kept, the same stream is accepted at 29, since only held applies there. The six keep tests give what you listed, and the walk order section 10 now states is the one the engine counts with.

CI still runs against `635b24d`. Moving it to `def062b` waits on the user.
