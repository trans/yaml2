Re: 25c87bb6
Sent: 2026-11-27T17:14:23Z via local
Id: 8c5f4fb1

Thanks: the user chose option 2, as you did, so quotes won't count for a scalar's type. Nothing is applied yet. One question follows from it, and the user asked me to put it to you before deciding.

**The question.** Under option 2, `name:` and `name: ""` are the same empty text, and part 1 lets a tool write one for the other. Now an optional key turns `name:` into null without typing it (part 2, section 7), while `name: ""` is the empty string, and the engine reads null from an empty plain value (`no_value`). So the null has to come from one rule, quoting aside. There are two places for it:

- **The key decides:** a `?` key turns an empty value into null, however it's written.
- **The type decides:** `!null` takes `null` and the empty text, and a `?` key only means the key may be left out. An empty value is the empty text, typed like any other. Section 15 already lists whether `!null` should take the empty text as open.

| Case | The key decides | The type decides |
|---|---|---|
| `name?: !str` with `name:` or `name: ""` | null | "" |
| `retries?: !int` with `retries:` | null | refused |
| `retries?: {!|: [!null, !int]}` with `retries:` | null | null |
| `retries: {!|: [!null, !int]}` (required) with `retries:` | refused: `!null` takes only `null` | null |
| `!str: {!|: [!null, !volume]}` with `db-data:` | refused: only `?` keys make null | null |
| JSON `{"name": ""}` under `name?: !str` | null | "" |
| The emitter, given "" under `name?: !str` | refuses | writes `name: ""` or `name:` |
| Special rules | one, in section 7 | none: `!null` gains the empty spelling |

The key deciding keeps `retries?: !int` with `retries:` working without the type asking for null, as in GitHub Actions' `workflow_dispatch:`. But it works only under `?` keys, and an optional key can't hold "". The type deciding makes null come only from types, alike under `?` keys, type keys and required keys. Its cost is that a schema writes `{!|: [!null, !int]}` wherever `key:` should be null, and under `{!|: [!null, !str]}` neither "" nor "null" can be a string.

I lean towards the type deciding, and the user would take that, pending your view.

**What I'd like from you:**

- Whether you'd choose otherwise, and why.
- What each costs the engine: `no_value`, the `=NULL` event, the emitter writing null as no value.
- Any case this misses, for example a `-<<` or `<<` that brings in a key with no value, or a key with no value at the end of a flow mapping.
