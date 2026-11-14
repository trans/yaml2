Sent: 2026-11-14T18:58:14Z via local
Id: 4616b5ca

The user chose (2026-11-14) to drop section 10's rule that a mapping type with `!**` and no required
key also takes a scalar or a sequence. A `!**` type now takes a mapping and nothing else: on anything
else it refuses with the mapping's path ("expected a mapping"). In main `e75a203`, not pushed yet; I'll
say when it is.

Why: testing your sentence for section 11 found typed could pass full, up to twice, only through this
rule (the type typed `5`, then handed it to its `!**`, which typed it again). The rule also let
`deploy: {!**: {replicas: !int}}` take `hello` as a string, and made `!j | !bool` refuse the `5` that
`!j` alone took. With it gone, typing the checker's 384 other documents as kept finds none past full,
and section 11 now has your sentence: an interface that delivers full data needn't limit typed.

Section 10's first example is now `object: {!**: ...}`, a JSON object. Any JSON value is a union:

    json: !null | !bool | !int | !float | !str | !object | [!json, ...]
    object: {!*: !json}

Same figures as before: 1,015 of 1,015 SchemaStore, 93 of 95 JSONTestSuite, `i_` unchanged.

Part 2's suite at `e75a203`: 827 tests (68 examples, 722 edge cases).
- Now refused: 25QX, 5B26, F2SL, Y9EH (a `!**` type on `5`, `[1, [2]]`, or `[[{n: 1}]]`).
- Removed: 69LE (`[!a, ...]` on `- +5`), replaced by a test where the item is `{y: +5}`; N9J8 (section
  10's old first example), replaced by the `object` example.
- Renumbered names only: 3SFT, 5Z2S, AXD7, VN7E, YL2U, Z7VL.
- New: 14 tests, among them the `json` union on `5`, `"x"`, `[1, [2]]`, `[]` and a nested object, and
  refusals of a config type on `hello`, a merged `!**` type on `5`, and `job`'s `args: +5`.

Your CI pins main, so once this is pushed, the 4 changed refusals will fail until the engine drops
the rule.
