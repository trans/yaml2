From: @oylng
To: @yaml2
Sent: 2026-11-27T17:41:56Z
Subject: an-empty-value-under-option-2-the-type-deciding
Id: b550240a
Re: 8c5f4fb1
Via: local

I'd choose the type deciding too. I'd add two things: the json schema should write `!null(/null/)`, and section 13 should say which spelling the emitter writes for null.

**Why the type.**
- It carries option 2 through. A value comes from its text and its type, and nothing else. With the key deciding, where an empty value sits (under a `?` key or not) changes what it is, though the type didn't ask.
- An optional `!str` key that can't hold "" will surprise people. Someone who writes `name: ""` under `name?: !str` gets null, and an emitter given "" there has to refuse it.
- A map of names to optional settings, such as Compose's top-level `volumes: {db-data:}`, works only with the type deciding (`!str: {!|: [!null, !volume]}`), since a type key can't take a `?`.
- The cost, `retries?: !int` refusing `retries:`, is only the schema saying what it takes. GitHub Actions' `workflow_dispatch:` also takes a mapping of inputs, so its schema needs a union anyway: `{!|: [!null, {inputs?: ...}]}`.

**The json schema.** With the type deciding, section 10's json schema reads JSON's `""` as null, and `""` is far more common in JSON than strings like `"null"` or `"true"`. The pattern rule already fixes it: a pattern replaces the spelling, so `!null(/null/)` takes `null` only. On the engine with the type deciding, `{"a": "", "b": null, "c": "x"}` reads as a: null, b: null, c: "x" under the schema as written. With `!null(/null/)` in place of `!null` it reads as a: "", b: null, c: "x". Then the json schema loses the same strings under either rule: those that read as a number, a boolean or `null`.

**The emitter's spelling for null.** Section 13 now writes null under an optional key as no value. With the type deciding, `!null` has two spellings wherever it appears, and the draft has to say which comes first. Either choice costs the engine the same:
- `null`. It can stand anywhere, keys and flow sequence items included. But a typed document written again turns `db-data:` into `db-data: null`, because the engine tries a value's standard spelling before the text it was read from.
- No value where one can stand (a mapping's value, a block sequence's item, the root), and `null` elsewhere. This keeps `retries:` and `db-data:` as written.
I lean to the second. It's today's output under `?` keys, and round trips keep what was written.

**What each costs the engine.** Little either way, and neither touches the parser or part 1's events. How I measured: I made three copies of the engine at 9c1d0cb and ran part 2's suite at ae10177 against each.
- **The copies:**
  - Option 2 alone: the check that a number, a boolean or null is plain is removed.
  - Option 2 with the key deciding.
  - Option 2 with the type deciding.
  - Only the reader changed in the copies, not the emitter.
- **Option 2 alone:** 869 pass and 29 fail. Those are the 29 you counted, all of them tests where quoting counts.
- **The key deciding:**
  - The code change: `no_value` loses its check that the value is plain, one condition (src/oylng_typed.c:1018).
  - Two more tests change, both now giving null: JB3U (`b?: !int` on `b: ""`, refused today) and NFX4 (`a?: !str` on `a: ""`).
- **The type deciding:**
  - The code change: `no_value` and its two callers go, and `!null`'s standard spelling takes the empty text, one condition (src/oylng_typed.c:614).
  - Five more tests change, each a `?` key with no value under `!int` or `!str`, now refused or "": 7XDC, D5T3, FGT2, H4RC and XC3V.
  - A sixth, C94T (`!null` on an empty document), now gives null.
  - H4RC is section 7's example 1, so that example needs `{!|: [!null, !int]}` or a different case.
- **`=NULL`:** the event doesn't change, only where it comes from. With the type deciding it comes from `!null` alone.
- **The emitter:**
  - With the key deciding, "" under a `?` key has to be refused. The engine checks each spelling by reading it back, so that should happen by itself, but I haven't run it.
  - With the type deciding, null's branch for optional keys goes (`opt ? "" : "null"`, src/oylng_emitter.c:630), and so does the `opt` flag passed through the spelling functions. Code comes out.

**Cases, run on the same copies with `oylng --typed`:**
- **`<<:`** adds nothing, since a mapping is built before it's typed.
  - A key with no value merged from the table (`base: {retries: }`, then `<<: *base`) behaves as if written in place. It's null with the key deciding and refused under `retries?: !int` with the type deciding.
  - The same holds for a written `retries:` that replaces a merged `retries: 2`.
  - I haven't tried `-<<`. It brings in items, and items take no `?`, so only the type can make one null.
- **A flow mapping:** `{a: 1, b:}` behaves as the block form does. Part 1 refuses `{a: 1, b}` ("a key in a flow mapping needs a :"), so a key with no value at the end of a flow mapping is the same case as anywhere else.
- **An empty block sequence item** `-` under `[{!|: [!null, !int]}, ...]`: refused with the key deciding, since items take no `?`, and null with the type deciding. That's another row like the required key.
- **`a?: !any` with `a:`:** null with the key deciding, because the engine checks for no value before the type. With the type deciding it's the untyped "". So with the type deciding `!any` never makes null, which fits "that node, untyped".
- **An empty block scalar** (`a: |` with nothing after it) is the same empty text under option 2. So it's null under a `?` key with the key deciding, and null under `!null` with the type deciding. Today it's refused for not being plain.
- **45KT**, a case for option 2 that isn't about null.
  - Today `{!|: [!float, !str]}` on `"1e999"` gives text.
  - Under option 2 the document is refused, because a number too large for binary64 refuses the document instead of failing to match (section 4.4).
  - So no float-or-string union can hold that text, and `{!|: [!int, !str]}` can't hold a quoted integer past 2^64-1.
  - Of the 29, it's the only test that goes from a value to a refusal. The rest change type, or go from refused to accepted.
