# Review of Draft 1

*Updated 2026-11-05*

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

## @oyl on sharing and load-all (2026-11-04, decided 2026-11-05)

@oyl answered three questions, and the agent reran its probes. The results are in the
working copy of the spec, **not committed yet**. @oyl was told the outcome on 2026-11-05.

- **Later documents.** @oyl would limit sharing to what is delivered together. The user's
  rule replaced that: nothing is writable while parsing (rules.md).
- **Load-all.** @oyl showed "delivered together" can't see a caller's own loop, and proposed
  counting growth across the stream. The user chose two numbers instead, held and full
  (rules.md), because that stream holds almost nothing and should read.
- **Fixes taken.** A deep copy to change one place. An emitter writes a shared node in full,
  since which nodes are shared isn't data. In section 11, a change at one reference replaces
  it with its value, or for a merged key with a written key, and the tool reads the result
  again, since a change to an entry can break a later line.
- **Blind spot.** 1.x anchors end with their document, so no real file shows a table named
  across many documents. The corpus can't speak for that pattern.

Oyl's own default accepts 256 levels and refuses 257, which matches the minimum.

## @oyl on held and full, and a limit on shared tables (2026-11-05)

Two messages, `a5d4f5e5` and `f2752547`, in `mail/received/`. @oyl found no hole in the two
decisions, and five gaps in the text. The agent reran the first two and the replacement
stream, built as the messages describe, and checked the third by arithmetic. The user said
to apply the fixes on 2026-11-05, with the agent's form of the table rule. **Fixed, not yet
committed.** @oyl hasn't been told which form was chosen.

- **Full wraps.** `a0: [x, x]`, then each link naming the last twice: 63 links in 1,672
  bytes, `a62` has a full size of 2^64 + 1. A wrapping 64-bit count reads 1, so "checks full
  first" passes. Only interfaces applying held reach it; a normal load refuses at `a24`.
  Proposal: full stops at its largest value and never wraps.
- **Depth through references.** `e1: [*e0]` up to `e999` is 13.8 KB of written depth 2, and
  the checker delivered depth 1,000. A chain of 11,500 levels in 185 KB fits the default
  limit. Proposal: levels count with references followed, by addition, and whatever expands
  checks them too. `oyl_parser_set_max_depth` already applies to expanded events.
- **Following a path.** Section 7.4 limits only finding repeated keys. 100,000 keys and
  100,000 `*a:k123` references is 2.4 MB, and scanning is about 5 billion comparisons, by
  arithmetic. Proposal: widen the sentence to following a path.
- **Builds across documents.** Section 8.3's "built afterwards" leaks if a per-document loop
  keeps its memo. Proposal: data built one document at a time shares nothing between
  documents, and sharing across documents takes one build, after the stream is read.
- **Several documents and held.** "Adds up their full sizes" leaves out a tree of several
  documents. Proposal: it adds up whichever number applies.

**A limit on shared tables.** @oyl reports the user said a reset has to happen every so
often in a stream, and that the wording is unruled. The hole: section 10 takes a replaced
entry off held, but an interface keeping references has to keep every version a document
names. Scaled to 1/16, 200 replacements of a 64 KiB entry read at a 4 MiB limit with
`keep=True, together=True`, with table held near 64 KiB and 200 distinct versions delivered.

@oyl's rule is a third count: what `--- &` documents add since the last `...`, counted as held
does, never taken off, refused on every interface. The agent's variant has no third count: a
replacement stops coming off held, full keeps its take-off, and every interface applies the
limit to held, with full on top for data with no references left. In a model of the two,
both read 1 MiB named 1,000 times, both read a one-item-per-document log, and both refuse
200 replacements unless each has `...` before it. They differ on one case: 60 MiB replaced by
1 MiB and then a 10 MiB document, which @oyl's rule reads and the variant refuses, since a
parser keeping references does hold 71 MiB there. Either way a 100-byte entry gets about
620,000 replacements, a 1 MiB entry 63, so emitters should write `...` before replacing an
entry in a long stream.

An interface that delivers several documents at once and keeps references takes nothing off
at `...` either, because its documents still name the old tables.

**For the parser.** Keep full and depth per table node, not per entry, since a path names
nested nodes: 12 bytes each. One arena per table generation, freed at `...` once the documents
naming it are gone. Keep the key index for table entries.

**Cost, @oyl's estimates** (20 MB inputs, counting in a loop outside the parser): 2 to 5% in
all. Following a reference by hash takes 11 to 21 ns, about one parsed event. A scan takes
120,000 ns at 100,000 keys, the only real problem.

**Checker.** With `keep=True` it now builds nothing for `-<<`, so the 63-link chain reads at
once. Python integers don't wrap, so `size_tests` works the chain out at 64 bits both ways, and
`P.expand` is what a tool checks before expanding. Breaking each new rule on purpose, eight
ways, fails a test each time. The path rule has no test, because the checker's table is a
Python dict.
