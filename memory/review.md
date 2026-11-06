# Review of Draft 1

*Updated 2026-11-06*

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
- **A security section for the quadratic rule.** The user approved it on 2026-11-05. It is
  section 15, and adds no rules. **Fixed in `bf225ba`.**
- **What "column" counts.** **Open**, and not yet taken to the user.

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
to apply the fixes on 2026-11-05, with the agent's form of the table rule. **Fixed in
`2d5a90d`**, and @oyl has been told. Anything a normal load reads, a tool keeping references
can read too, when both deliver the same way. Delivering several documents at once, a tool
keeping references also counts old tables that no document names, because it holds them.

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

## @oyl on section 10 at `2d5a90d` (2026-11-05)

Message `993df806`. @oyl found no way around held for the table cases, and both worked
examples hold. Four points in the wording. The agent reproduced all four. **Points 1 to 3 fixed,
not yet committed** (the user approved them, 2026-11-05): section 10 has them in the working copy,
and `draftcheck.py` counts names, with tests that fail if any of the three is broken on purpose.
That a tree keeping comments adds their bytes is in the text and untested, because the checker keeps
no comments. Point 4 was replaced by the user's rule on joins, below.

1. **Names and comments count in neither number.** A 100,000-byte name reads at a limit of
   100, and 1,000 documents with 1,000-byte names read together at 10,000. Names don't
   amplify, but section 10 says a large plain file counts. Proposal: a document's name counts
   as a scalar does, and a tree that keeps comments adds their bytes to held.
2. **When the old entry comes off full.** `--- &`, `a: [x, yy]`, `--- &`, then `a:` with
   `-<< *a` and `- z` has held 14 and full 10. A parser taking the old entry off only after
   reading the new one reaches 18, and refuses at limits 14 to 17. Proposal: it comes off when
   the key is read, which is the checker's result. A parser that expands entries as it reads
   holds both for that moment, up to twice the limit.
3. **"As written" invites counting the source.** The checker counts the value: `"\u00e9"` adds
   2 bytes, not 8. Proposal: "a scalar adds the UTF-8 bytes of its value", and drop "as
   written" from held.
4. **Joined files now need `...`.** The repeated `%YAML 2.0` line means nothing, so each file's
   table stays in held. A file whose table counts 8 reads 63 times over at a limit of 512, and
   the 64th copy is refused. @oyl offers two ways out: a sentence telling files to end with
   `...`, or having the line empty the table, which it leaves to the user.

**The agent's own findings on joins:**

- **Ending files with `...` can lose a file with no error.** After `...`, a `%YAML 2.0` line not
  followed by a marker isn't a marker, so a parser stops there. `%YAML 2.0`, `---`, `a: 1`,
  `...`, `%YAML 2.0`, `b: 2` delivers only `a`, and reports where it stopped. Without the `...`
  the same join is refused. So @oyl's sentence alone would make this worse.
- **A file can be refused alone and read when joined.** A file naming `*x` that it never defined
  is refused, but reads if an earlier file in the join defined `x`.
- **Recommendation:** a `%YAML 2.0` line starts a fresh file. It empties the table, as `...`
  does, and the first document after it may have no marker, as at the top of a stream. Then
  each joined file should read as it does alone. Not prototyped yet.
- **A limit on that:** a file with no final line break joins badly whatever we choose.
  `a: 1` then `%YAML 2.0` on the same line gives `a` the value `1%YAML 2.0`, with no error.

**The user's rule on joins (2026-11-05), replacing the recommendation above:** only `...` empties the
table. Whoever joins files decides: independent files get `...` between them, and files sharing one
table drop `%YAML 2.0` and use `---`. Assumes all are 2.0. The draft already did most of this.

- **A plain `cat` is refused** (the user, 2026-11-05). `%YAML 2.0` can come again only after `...`, so
  no one gets a shared table without choosing it. In `e1eef1b`.
- **Every file starts `%YAML 2.0`, then `---`** (the user, 2026-11-05: "require it", and let the core team
  wrestle with it if they want it changed). In `e1eef1b`, with the reasons
  in section 4.2 and the case against in section 14. `...`, `%YAML 2.0`, `b: 2` was the problem: the
  parser stops and `b` is lost with no error. The agent proposed reading on, then refusing. The user
  objected to both, since text after `...` can say anything, and saw that only a `---` should decide.
  With the marker required, every valid file can follow `...`, so no exception is needed. 3,558 of
  4,651 and JSONTestSuite's 93 of 95 stay the same, with the lines added.

## @oyl on part 2, Draft 1 (2026-11-05)

Message `18666a0d`, answering `ceb22cac`, read at `7689ea6`. It isn't filed here, because it named
a parser that isn't announced. The original stays in @oyl's `mail/sent/`. **Applied in `d645ce9`,**
except numbers and `\p{..}`, which are open, and with section 3 as the
user answered it below. The ceiling replaces @oyl's floor, and the count of typing work under
references is the agent's: neither has been built, and @oyl hasn't seen them.

**Checked by the agent:** every probe below through `schemacheck.py`, the two union changes in a
private copy (30 examples and 82 edge cases still pass), the walk's arithmetic (6 × 2^n - 3 visits),
RFC 9485 and RFC 4648, the Oyl API it names, and 4,099 Unicode category runs on Unicode 16. **Not
reproduced:** its timings, which are @oyl's, on Oyl's 1.x events and tree with an outside typer, using
the JSON schema only.

**Speed.** No rule needs dropping. Typing with the JSON schema adds 7 to 32% over reading strings.
Delivering values is what costs: +112% on a numbers input, which is `strtod`. The real concern is
what a hostile stream can make a parser spend.

**Time a stream can force,** for section 16:

- Forced collisions in typing: section 7.4 doesn't name a data key against a type's keys, `!name`
  in the table, or the memo below. By arithmetic, not run. A shared compiled schema needs its own key.
- Reference walks: 632 bytes and 28 levels took 1.6 billion visits, doubling per level. Remembering
  (node, type) took 88. So section 16's "bounded by the data" holds only with that memo. Proposal:
  an interface keeping references types each node once under each type.
- Unions read literally: `a0: !a1 | !a1` and so on is 2^n. Reproduced: 338 bytes took 0.9 s at n=20.
  Proposal: each name counts once in a union, at its first place. Then n=200 takes 5 ms.
- Patterns: `(a{1000}){1000}` is a million positions in 15 bytes.
- Many alternatives: data times schema, unless merged into one automaton.

**Section 3 is wrong as written.** "A file can't pick a laxer schema" fails for a prepended schema,
since a file can replace `job`, replace `int`, or end the table with `...`. All three read
`retries: abc`. Proposal: drop "or prepend it to the stream". One compiled schema then serves many
streams. The agent's note: this also fits the joined-files recommendation, where a `%YAML 2.0` line
empties the table, so a prepended file couldn't work anyway.

**Related proposals:**

- A stream's own schema should need the application to ask. Today `--- !port` after a data entry
  `port: 80` is refused, though part 1 calls a name advisory.
- An entry a type has reached can't be replaced until `...`. Today `b: !bool` replacing `b: !int` makes
  one `--- !a` read and the next refuse, against section 8.1 of part 1.
- Section 2 against reachability: the added rule stands, and section 2's sentence changes. An entry
  nothing reaches isn't a type, since `motd: !important` is a fine data entry.
- "Applied as a stream is parsed" should say a schema sees how each scalar was written, and runs over
  what the parser read. As written, a load that types a tree looks non-conforming. This rewords the
  user's correction of 2026-11-04, so it's the user's call.

**Unions of mappings.** An event interface must buffer, which is fine: `<<` already can't stream. Keep
"no alternative is tried by typing its children". Proposal: a mapping also fails to fit if it has a
key it doesn't take. Today `{x: 1, y: 2, z: 3}` under `!p | !q`, where `q` adds `z`, is refused, as is
`{x: 1}` under `{x?}` or `{y?}`. Both read with the change. Today's `!m | !m` and a diamond also read.

**A reference typed where it is used.** Keep it: one bit per node. A refusal through a reference
should give the use, with the entry's line beside it.

**Sizes and numbers.** A type changes no count. A cycle of names with no collection is refused: the
checker does, and the text doesn't say. `!int` and `!float` have no range, and the checker reads 400
digits and gives infinity for `1e999`. Proposal: 64-bit signed integers at least, past that a parser
may refuse but never rounds or wraps, and `!float` is binary64, with overflow refused.

The agent's additions: `!float` needs correct rounding too, or the same bytes differ. A range failure
must refuse the document, not count as no match, or `!int | !float` rounds on one parser and
not another, and an overflow falls through to `!str`. Underflow isn't covered. All the huge numbers in
JSONTestSuite are `i_` files, so none of this touches the 93 of 95.

**Patterns.** A parser carries its own engine, so every language agrees. RFC 9485 section 8 lets
implementations refuse nested or very large counts, so two parsers can disagree on whether a schema
loads. Proposal: a floor, say 1,000 after nested counts multiply, and linear time as a rule. RFC 9485
names no Unicode version, so name one. `\p{..}` needs tables, about 16 KB, the first such tables in the
design. The agent's count: 2 SchemaStore files use `\p{..}`.

**Bindings.** Two layers: typed events saying which type each node took, and a callback with an arena.
Three rules to add: a binding that refuses, refuses the document, with no trying the next alternative.
One call per use. Emitting needs a way back. Today's `oyl_schema_builder_add_type` can't build a struct.

**Smaller:**

- `!float` in 4.1 excludes `2`, which examples need: say "which may have".
- `!int | "none"` reads the quote marks as part of a literal: refuse a part starting with a quote,
  other than `''`.
- `!any` in a union takes a mapping that fits no alternative. The checker does; write it down.
- `!binary` refuses wrapped base64 in `|`. RFC 4648 sections 3.1 and 3.3 let a referring spec allow
  line breaks, so say it's meant or skip them.
- `a?` and `a` in one mapping: later wins.

**Not covered by @oyl:** named keys, required keys and literals in the timing, the real shadows, a
pattern engine, and narrowing alternatives as keys arrive.

**The user's answers (2026-11-05):**

- **A stream's own schema applies by default,** which replaces @oyl's proposal that a program must
  ask. The application can ask for it to be ignored and read the document as it is, and can ask to be
  given the schema, which is YAML too. Part 1 needs a way to hand over the table, since section 11
  keeps it out of delivered data. `--- !port` after `port: 80` stays refused, so part 1's "advisory"
  needs a word. The agent then said section 16's limits become requirements and a service should
  switch schemas off. The user objected: if applying a schema is dangerous, that's what to correct.
  **Target, proposed by the agent, open:** typing time grows in line with the input, for any file
  and any schema, so there is nothing to switch off. A schema can't run code, fetch or grow data.
- **The rewording of "applied as a stream is parsed"** is accepted.
- **`!binary`** allows line breaks.
- **Prepending stays out of the question.** See **The file is the truth** in [rules.md](rules.md). A
  file with a schema in it is stamped, and the sentence that was wrong is "a file can't pick a laxer
  schema". An application's schema stays out of the stream's table, so one schema serves many files
  and a file's data entry can't collide with it by accident.
- **Numbers: the user's rule (2026-11-05), in section 4.4, `cc84227`.** `!int` and `!float` have
  no size, and an application keeps them in whatever it has. A parser delivers the number written, or
  refuses, and digits lost mean an error. An application may accept rounding on `!float`. `!decimal`
  stays, and no one can accept rounding on it: keep it exact or refuse. The agent's definitions: digits
  are lost if the value, written back to as many significant digits, differs, since nearly every
  decimal is inexact in binary. Each parser holds -2^63 to 2^64-1 and binary64 at least. A number that
  can't be held refuses the document, and isn't a failed match. Limits may have an exponent. JSONTestSuite
  stays 93 of 95, and no SchemaStore file holds a number that loses digits. No width names: a width
  is a limit, and float80 and binary128 need nothing, since a size isn't named. The figures behind that:
  Measured on 1,015 SchemaStore files: 8,811 integer types, 421 with a width format (`int32` 151, `uint`
  100, `uint32` 95, `int64` 56, `uint8` 11, `uint64` 5, `uint16` 2, `int` 1), and 174 ranges that are a
  width. 320 ranges stop at 2^53 - 1, JavaScript's safe limit. A width is already a limit, so
  `uint32: !int(0..4294967295)` reads today. If `!uint64` is standard, every parser must read its whole
  range, so a floor must reach 2^64 - 1. Section 8's "a name in the table wins" means names can be
  added later safely. The user (2026-11-05): this is about being thorough, not need, and a sample
  this size can't decide it, so the agent's "`!float32` looks unneeded" is withdrawn. Check the list
  against other type systems, not against real files.
- **`\p{..}` stays,** with Unicode 16 or later (the user, 2026-11-05, on the measurements below). In
  section 4.3, `cc84227`. Its 2 files are two schemas of one project. I-Regexp
  is portable. Only the agent's option of letting a parser refuse `\p{..}` would make a schema not
  portable. RFC 9485 leaves two gaps a spec can close: no Unicode version, and limits on counts.

**Measured for that target (2026-11-05), on a private copy with each name counted once:**

- That rule alone isn't enough. `aN: !aN+1 | !aN+2`, with every union in use, took 0.06, 0.35 and 2.7 s
  at 250, 500 and 1,000 names (30 KB). A real parser would do better than this checker, but it would
  still grow faster than the input. Proposal: a ceiling on one union once expanded, the same for every
  parser, in place of @oyl's floor, so all agree on whether a schema loads.
- Patterns after counts multiply, 1,247 of SchemaStore's 1,271 unique patterns: 50% hold 14 positions or
  fewer, 99.9% 772, and the largest 9,131. A ceiling of 10,000 refuses none.
- By reasoning, not run: remembering (node, type) leaves entry size times number of types, so a file can
  use many types on one big entry. That work should count against the size limit.
- **`\p{..}` tables, Unicode 16.** All categories: 16.4 KB as sorted runs, about 21 KB three-stage, 46 KB
  two-stage with 256-entry blocks. Compiled to one class: `\p{L}` 677 ranges, about 4 KB; `\p{Nd}` 71
  ranges, 426 bytes. Lookup over `[a-zA-Z]`, per character, C at `-O2`, one pinned core, best of 15, on six
  synthetic 1-million-character texts: two-stage adds 0.1 to 0.2 ns, binary search over sorted runs 10 to
  27 ns. Three-stage wasn't timed. This is the lookup alone, not an engine. Only a pattern using `\p{..}`
  pays, so size and speed aren't the issue, and the Unicode version is.
- **Unicode versions, 6.0 to 16.0** (2010 to 2024), from `UnicodeData.txt` of nine versions. The user
  expected change by adding, rarely replacing, and that holds. No character was removed, and the
  stability policy forbids it. 190 of 248,965 changed category (0.076%), mostly inside letters. 2 left
  `L` (U+1885, U+1886), 21 joined it, and none left `Nd`. Since 12.0, 2 changed, neither across `L` or
  `Nd`. The policy doesn't promise a category stays, only that it keeps its fundamental identity, and the
  list of categories is fixed. So the rule is a minimum, as levels have, not a pinned version. A
  pattern only says yes or no, so a gap between parsers is usually a refusal, not different data.

## @oyl on what part 2 costs (2026-11-06, **Open for the user**)

@oyl's answer to the cost questions, including `!*` at `c54395c`, in
[its message](../mail/received/20261106-232726Z-@oyl--costs-in-part-2-measured-7fe44879.md), with the
tables. Measured on one pinned core in throwaway C, with Oyl's 1.x event parser as the baseline. The
user has asked @oyl to stop on part 2 for now, so this is its last word for the moment.

Text errors, none applied yet:

- **Section 4.4, ties.** `1.0000076293945313` is stored as exactly 1.00000762939453125, a tie at 17
  digits. Rerun 2026-11-06: Python and C write back `...312` and so refuse it, and JavaScript's
  `toPrecision(17)` writes back `...313` and keeps it. So two conforming parsers disagree. @oyl's fix
  is a distance: a value survives if what is stored is within half a unit of its last written digit.
- **Section 4.4, 15 digits.** `1.234567890123e-320` comes back as `1.234670048957e-320` (rerun, same
  result). "Up to 15 significant digits always do" holds only from 2.2250738585072014e-308 up.
- **Section 2, the time rule.** "In line with its size" is false for an interface delivering full data
  unless size means full there, since 1 KB can spend the whole limit. It also says nothing about the
  constant, so the ceiling is what carries the promise.
- **Section 11.** "The sizes of what it types" has to mean each node's own bytes, once per (node, type)
  pair. Counting what is below a collection counts the 632-byte chain as 2^28 again. Reasoned, not run.

For the user to decide:

- **The ceiling.** 10,000 positions worst case is 224 s for 64 MiB by NFA walk, against 24 s at 1,024.
  @oyl suggests the largest real union, rounded up, and says 10,000 buys nothing it can measure. Our
  count (2026-11-06, `pos.py` on SchemaStore): the largest of 1,247 patterns is 9,131 positions, a
  case-insensitive list of Microsoft names, and the next is 772. So 10,000 exists for one pattern, and
  1,024 refuses only that one.
- **Load.** A ceiling per union can't bound load: `aN: !aN+1 | !aN+2` gives 2 million names reaching
  10,000 each, 84 GB of lists (arithmetic, checked). @oyl proposes counting the positions of all
  unions in the table against the size limit, refused at load. Exact, so parsers agree. Not built.

For a parser, no spec change: one automaton per union (2 to 7 ns a value, barely growing from 3 patterns
to 10); a DFA must be lazy, with a capped cache over an NFA walk (not built); `!*: !signed | !str`
costs the same; one merged key table per union of mappings (1.2 to 22 ns a key; required keys at the
end of each mapping not built); the digits check by one multiplication (6 to 9 ns a float against
about 170 by printing, no disagreement in 60 million values).
