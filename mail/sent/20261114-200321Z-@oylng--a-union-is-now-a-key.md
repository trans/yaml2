Sent: 2026-11-14T20:03:22Z via local
Id: a4eb283a

The user chose (2026-11-14) to write a union as YAML, not as a small language in a plain scalar. In
main `0b88244`, on top of `e75a203` (my last mail); neither is pushed yet, and I'll say when.

The rule (part 2, sections 9 and 14):
- A union is a mapping whose only key is `!|`. Its value is a sequence of one or more alternatives:
  `{!|: [!int, !str]}`, or the block form. Section 9's choosing is unchanged.
- An alternative is any node a schema holds at a value: a type, a literal (a quoted one too, so
  `"none"` and `''` are plain literals now), a sequence, a mapping written in place, a nested `!|`
  (flattened, as a named union is), or a reference (`*m`).
- Refused when the schema loads: ` | ` in a plain scalar outside a type's parentheses (so `!int | !str`
  and `x | y` fail loudly; `!str(/x|y | z/)` is still one type); `!|` beside another key, which includes
  a `<<` that pastes a union into a mapping; a value that isn't a non-empty sequence; `...` in `!|`.
- A `!|` mapping as a `!**`'s value is a union, not a mapping of rules: `!**: {!|: [!signed, !str]}`.
  A union whose alternatives include a mapping is still refused there.
- Full size (section 9): a union adds what its alternatives add, and nothing for itself.
- A pattern holding `, [ ] { }` can't sit in the flow form, so such a union is written in the block
  form.

Section 10's JSON schema is one entry again:
`json: {!|: [!null, !bool, !int, !float, !str, {!*: !json}, [!json, ...]]}`. Same figures: 1,015 of
1,015 SchemaStore, 93 of 95 JSONTestSuite, `i_` unchanged.

Part 2's suite: 842 tests (69 examples, 736 edge cases). A test's id follows its stream, so every test
whose schema held a union has a new id. I rewrote each old test's unions and matched it to the new
suite: 817 give the same answer, path and tags; 10 are gone (tests of the old spelling: `[ ]`,
`[!int, ]`, `[, !int]` inside a union, a mapping or a quoted literal inside `|`, `[!a, !b] | [!c]`, the
old JSON example and two splitter tests, all replaced); 25 are new. The tag `union` now also marks a
test whose schema holds ` | `, so a parser without unions skips the refusals of the old spelling.

The two shadows on our `ai` branch (`memory/shadow/`, ai `92e8331`) are converted the same way. The
verdict and path came out the same on all 801 files, so `verdicts-*.tsv` are unchanged.
