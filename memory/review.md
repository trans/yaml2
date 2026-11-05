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
- **Bidirectional controls.** **Open: the user should confirm.** The user agreed to refuse
  them too, on the agent's word that it cost nothing, because 0 of 4,651 files hold one.
  That corpus has almost no right-to-left text, and real locale files do use them
  (landscape.md, Right-to-left text). So the draft allows them, and section 14 leaves
  them open, with a narrower rule to consider: refuse them in keys and comments only.
- **Spaces-only lines in `|`.** **Open**, in section 14. Five spaces inside `|` keep 3 of
  them in the value, and the same line in `>` is refused. Trailing-space stripping then
  changes data. The agent's earlier attempt to treat them as empty silently changed 3
  real files.
- **A minimum nesting depth.** **Fixed in `caece25`:** 256, the agent's pick, tested in block
  and flow. The deepest real file is 21.
- **Size limit per document** plus the table in scope. **Fixed in `caece25`**, with an exact
  count, and tests under, at and over a limit. The agent added one rule the user hasn't
  confirmed: an interface that delivers documents together counts them together.
- **A "What this costs" section.** **Fixed in `caece25`**, as section 13.1.
- **Whether the first document should need `---`.** **Open**, in section 14, which now
  says the form without it is the one npm `yaml` refuses.
- **A security section for the quadratic rule, and what "column" counts.** **Open**, and
  not yet taken to the user.
