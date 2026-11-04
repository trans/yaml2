# The rules of YAML 2.0

*Updated 2026-11-03*

The design, rule by rule, as the user sets them. Keep the user's wording for
each rule, and keep what the agent derived from it marked as such until the
user confirms it.

**Clean break.** The user chose this on 2026-11-03, over a subset that today's
parsers could read. YAML 2.0 need not be readable by existing parsers.

## Rule 1: all scalars are just strings

The user, 2026-11-03.

Follows from it (the agent's reading, not yet confirmed):

- No implicit typing and no schemas in the 1.x sense. `no`, `on`, `0755`,
  `22:22`, `1E-12`, `2001-12-14`, `~` and `null` are all text.
- Quoting doesn't change the value: `42`, `"42"` and `'42'` are the same
  string. Quotes only decide which characters can be written.
- Scalar keys compare as strings: `1` and `"1"` are the same key.
- Types come from whatever reads the document, not from the document.
- The data model so far: string, sequence, mapping.
- Cost: JSON stops being a subset in meaning. `{"a": 1}` still parses, but
  the value is the string `1`, and a JSON to YAML 2.0 to JSON round trip
  loses types unless something supplies them.

Open:

- **What `key:` with no value means.** Proposed: the empty string, the only
  reading Rule 1 leaves. The user hasn't answered.
- **Whether tags survive.** `!!int 42` would bring types back into the
  document.
- **Whether null can be written at all.**
