Sent: 2026-11-24T23:13:03Z via local
Id: c3b521b1

One more change to part 2, in main `bd5f8ed`, not yet pushed or tagged. The user agreed to it. Section 7 now says:

> A key is always a scalar (part 1, section 7.4), so a type key's type must be one a scalar can fit. With `point: {x: !int, y: !int}`, `!point: !int` as a key is refused when the schema is read, and so is a union as a key with a mapping or a sequence among its alternatives, since that alternative could never take a key.

Before, such a schema loaded, and the type key took nothing. Next to `!*`, that was silent: with `!point: !int` and `!*: !str`, the document `a: 1` read as `{"a": "1"}`. With `{!|: [!int, !point]}` as a key, `5: 1` read as `{"5": "1"}`.

Five new part 2 tests, 855 in all, each with `point: {x: !int, y: !int}` or a sequence type in its table:

| Test | Schema | Result |
|---|---|---|
| ZZ27 | `m: {!point: !int, !*: !str}` | refused: schema |
| JR6M | a union of `!int` and `!point` as a key | refused: schema |
| L4RX | `list: [!int, ...]`, then `!list: !int` | refused: schema |
| 25F7 | `!point: !int` among a `!**`'s rules | refused: schema |
| 4CT4 | a union of `!int` and `!str(/[a-z]+/)` as a key | loads, `{"7": true, "ab": false}` |

The checker allows `!any` as a key, and any standard type, since every one can fit a scalar. If the core team keeps `?` keys, this rule is the one sentence that goes.
