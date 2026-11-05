# Review of Draft 1

*Updated 2026-11-05*

@oyl reviewed Draft 1 at the user's request (2026-11-05, against `f9727d5`). Its view:
strong, nothing changes the core design. The agent reran the probes marked **Checked**
and they hold. These are recommendations until the user decides. The original wasn't
filed here, because it names private Oyl notes and reference-parser plans and this
repository is public. It stays in @oyl's `mail/sent/`, with the advice for the parser.

## Errors, the agent would just fix (**Open**)

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

## Decisions for the user (**Open**)

- **Drop the ban on references deep in table entries (section 8.4).** **Checked:** a
  GitLab-style `.build:` with `script:` holding `-<< *.setup` is refused, and `-<<` chains
  in the table already double, so the ban no longer protects anything now the size limit
  exists. The agent agrees. This also corrects its advice of 2026-11-04: the 38 of 123
  GitLab list reuses inside definitions are mostly refused by this ban already.
- **Invisible line breaks.** **Checked:** raw U+0085, U+2028 and U+2029 are accepted in
  plain values, keys and comments, and U+202E in comments. It's the lone CR argument again.
  They could be refused outside double quotes, which keeps JSON. Refusing them inside too
  would cost 2 of the 93 JSONTestSuite files. Bidirectional controls need a sentence.
- **Spaces-only lines in `|`.** **Checked:** five spaces inside `|` keep 3 of them in the
  value, and the same line in `>` is refused. Trailing-space stripping then changes data.
  The agent's earlier attempt to treat them as empty silently changed 3 real files.
- **A minimum nesting depth** every parser must accept, with a test at that depth.
- **Size limit per document** plus the table in scope, rather than per stream, so a long
  stream can be read one document at a time.
- A security section for the quadratic rule, and what "column" counts.
- A "What this costs" section: JSON's line and schema, YAML-to-JSON consumers such as
  sigs.k8s.io/yaml, and a 2.0 spelling for CloudFormation, GitLab `!reference`, Home
  Assistant `!include` and Ansible `!vault`.
- Whether the first document should need `---`: the form without it is the one npm `yaml`
  refuses, which argues for keeping it optional.
