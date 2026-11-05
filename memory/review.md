# Review of Draft 1

*Updated 2026-11-04*

@oyl reviewed Draft 1 at the user's request (2026-11-04, against `f9727d5`). Its view:
strong, nothing changes the core design. The agent reran the probes marked **Checked**
and they hold. The user agreed to the agent's recommendations on 2026-11-04. The original wasn't
filed here, because it names private Oyl notes and reference-parser plans and this
repository is public. It stays in @oyl's `mail/sent/`, with the advice for the parser.

## Errors (**Fixed in `caece25`**)

- **Checked:** npm `yaml` 2.9.0 reads a 2.0 stream as 1.2 with only a warning:
  `port: 80`, `enabled: true` and `mode: 0755` come out typed, and `--- !job` passes. It
  refuses a first document with no `---` (`MISSING_CHAR`) and a `--- &` table. So
  "an old parser can't misread a 2.0 file" is false as a general claim. The README says
  it, published. Other parsers untested: js-yaml, SnakeYAML, ruamel, YamlDotNet, yaml-cpp,
  rapidyaml, libfyaml, the Rust crates, Symfony, go-yaml v2.
- **Checked:** section 4.2 says nothing but a comment may follow `--- &`, which the
  agent's flow tables contradict: `--- & {a: 1}` is accepted.
- **Checked:** `---` and `...` at column 0 inside a multi-line flow collection are
  accepted as strings by `draftcheck.py`, against section 12. Section 4.4 also leaves flow
  out of its reason for why a tool can split a stream. The rule is prose only.
- **Checked:** `--- !/x` and `--- !a/b` are accepted, though section 4.3 says a global name
  starts with a domain. Say that a parser doesn't check this.
- **Checked:** a table's block mapping must start at column 0, unlike a document's, and
  nothing states that.
- **Checked:** names can hold U+200C and U+200D, so section 4.3's "leaves out invisible
  controls" is wrong. Persian and some Indic words need them: fix the sentence.
- Section 10 doesn't say whether a reference counts itself, or whether `<<:` and `-<<`
  count the collection's own node, so parsers can refuse at different points. Add a
  worked example, and tests under, at and over a small limit.
- Section 2's "must not deliver the document in error" rules out event streaming.
  Suggested: must not deliver it as complete.
- Section 11 should say an emitter of typed data needs the same schema, to quote a
  string the schema would read as a number.

## Decisions (the user, 2026-11-04)

- **Drop the ban on references deep in table entries (section 8.4).** **Fixed in `caece25`.**
  References work inside entries as anywhere, backward only.
- **Invisible line breaks.** **Fixed in `caece25`**, for U+0085, U+2028 and U+2029: refused
  outside double quotes.
- **Bidirectional controls.** Allowed (the user, 2026-11-04). The user first agreed to
  refuse them, on the agent's word that it cost nothing, because 0 of 4,651 files hold one.
  That corpus has almost no right-to-left text, and real locale files do use them
  (landscape.md, Right-to-left text). Section 14 keeps a narrower rule open for the core
  team: refuse them in keys and comments only.
- **Spaces-only lines in `|`.** **Open**, in section 14. Five spaces inside `|` keep 3 of
  them in the value, and the same line in `>` is refused. Trailing-space stripping then
  changes data. The agent's earlier attempt to treat them as empty silently changed 3
  real files.
- **A minimum nesting depth.** **Fixed in `caece25`:** 256, the agent's pick, tested in block
  and flow. The deepest real file is 21.
- **Size limit per document** plus the table in scope. **Fixed in `caece25`**, with an exact
  count, and tests under, at and over a limit. The agent added one rule, **Open**: an
  interface that delivers documents together counts them together. The user questioned
  it, since plain references can share memory (see rules.md), and @oyl has been asked.
- **A "What this costs" section.** **Fixed in `caece25`**, as section 13.1.
- **Whether the first document should need `---`.** **Open**, in section 14, which now
  says the form without it is the one npm `yaml` refuses.
- **A security section for the quadratic rule, and what "column" counts.** **Open**, and
  not yet taken to the user.

## @oyl on sharing and load-all (2026-11-04, **Open: for the user**)

These are @oyl's recommendations, and the user hasn't decided. The agent reran the probes
marked **Checked**. None is in the spec yet.

- **Keep later documents out of it.** A parser may share within what it delivers together,
  but documents delivered separately share nothing an application can change. Otherwise
  document 2 no longer follows from the bytes, a test suite can't state its result, and
  on a parser that reads ahead it's a data race. State the outcome, not frozen nodes, which
  Python and Go don't have. **Checked:** PyYAML clears its object memo per document. This
  reverses the agent's advice to accept the leak.
- **Replace "delivered together".** It can't work: **Checked:** PyYAML's `load_all` is a
  generator, so the caller collects the documents and the parser can't see that. Instead:
  when a document is delivered, its written size leaves the total, and what its references
  and merges added stays until the stream ends, and `...` doesn't clear that. One total, so
  every parser and interface refuses the same file at the same point. **Checked:** with
  `a: [x, yy]` and the documents `b: *a`, `c: *a`, the table is 8, each document 9 (3
  written, 6 added), and the total is 23. Cost: a long stream heavy with references reaches
  the limit even when read one document at a time. The largest real total is 233,872, 287
  times under the limit, but 1.x anchors end with their document, so no real file shows
  this pattern. The corpus can't speak for it.
- **Merges aren't the only case.** With the rule above, a caller that collects documents
  holds real copies of plain references. So the agent's "only merges" was wrong too.
  **Checked:** go-yaml v3 copies, and refuses 100 plain references with "excessive
  aliasing".
- **"Reading can't tell them apart" is wrong.** An identity check can, and dumpers make
  one. **Checked:** PyYAML writes `&id001` and Psych `&1` for a shared node. 2.0 has no
  anchors in a document, so section 11 should have an emitter write a shared node in full.
- **"Copies a node first" should say a deep copy.** **Checked:** a merged mapping is new,
  but PyYAML and Psych share its values.
- **"Turns that one into a copy" fits only `*a`.** Under `<<:` the edit is a written key.
  `-<<` has no override, so a change expands the whole splice. A copy must be by value:
  **Checked:** after a later `b: 2`, `c: *a` gives `["1"]` and `[*b]` written at `c` gives
  `["2"]`. A change to an entry can break a later line, **Checked** in three cases, so a
  tool must read its result again. @oyl's wording: "a change at one reference replaces it
  with its value, or for a merged key, with a written key, and the tool reads the result
  again, since a change to an entry can break a later line."

Oyl's own default accepts 256 levels and refuses 257, which matches the minimum.
