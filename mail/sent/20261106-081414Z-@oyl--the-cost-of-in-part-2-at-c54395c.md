Sent: 2026-11-06T08:14:15Z via local
Id: 29686e1d

Part 2 has a new key, `!*`, in section 10, at `c54395c` (local, not pushed yet). It takes every key a
mapping doesn't name, at every level below, and its value is a scalar type or a mapping of rules. A
key is looked up in the mapping type at its place, then in the nearest `!*`, and nowhere else, so
nesting them adds nothing per key. I chose nearest-only for that reason: searching every `!*` above
a key would let a stream pay for all of them on each key.

One question, added to the three already open: can a parser type under `!*` as events arrive, with
one rule set kept per level and nothing buffered? Below a `!*`, mappings are open, so choosing a
mapping alternative uses only required keys and literal values, and it still has to see the mapping
to do that. If either of those costs more than it looks, I would like to know before this goes to
the core team.
