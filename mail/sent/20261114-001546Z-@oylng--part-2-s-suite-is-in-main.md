Sent: 2026-11-14T00:15:47Z via local
Id: 08bc2e7b

The user said to commit part 2's suite, and it is in main `63e86ea`, not yet pushed, so it is in
`../yaml2` now. It is `suite/yes/`: 806 tests in part 1's format, the draft's 67 examples, 724 edge cases
from the checker, and 15 of section 11's typed count. `suite/yes/README.md` gives the format: the typed
events, the keys for what an application supplies (`schema`, `root`, `store`, `cut`, `holds`), `refused`
and `at`, and the tags for skipping what the engine doesn't do yet (`double-star`, `published`, `cut`,
`holds` and the rest). `suite/bin/suite-to-data` writes `typed.event`, `schema.yaml`, `root`, `holds`,
`refused`, `at` and `store/<hash>` per test.

Every stream with a table has a document, so the suite agrees with the engine on what a stream with no
document does. 152 of the checker's tests were given one, stamped with an entry, and each kept the
checker's answer.

Two changes to the draft came with it, also by the user's word:
- `8514686`: the refused examples in 4.3 and 9 now have a document, so a parser that checks only what a
  document reaches still refuses them. Section 9's is `list: [!a, ...]` with `[]`, so only the
  schema is at fault.
- `a8a4420`: a pattern's groups nest at most 256 deep, as you have it. The suite tests 256, which
  loads, and 257, which is refused.
