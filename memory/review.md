# Review of Draft 1

*Updated 2026-11-12*

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

@oyl answered three questions, and the agent reran its probes. The results are in `2d5a90d`.
@oyl was told the outcome on 2026-11-05.

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
examples hold. Four points in the wording. The agent reproduced all four. **Points 1 to 3 fixed
in `1c1d724`** (the user approved them, 2026-11-05): `draftcheck.py` counts names, with tests that fail if any of the three is broken on purpose.
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

## @oyl on what part 2 costs (2026-11-06)

@oyl's answer to the cost questions, including `!*` at `c54395c`, in
[its message](../mail/received/20261106-232726Z-@oyl--costs-in-part-2-measured-7fe44879.md), with the
tables. Measured on one pinned core in throwaway C, with Oyl's 1.x event parser as the baseline. The
user has asked @oyl to stop on part 2 for now, so this is its last word for the moment.

The four text errors. **Fixed in `0ba3c31`**:

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

- **The ceiling: the user chose 1,024 (2026-11-06; in `0ba3c31`).** 10,000 positions worst
  case is 224 s for 64 MiB by NFA walk, against 24 s at 1,024. @oyl suggested the largest real union,
  rounded up. Our count on SchemaStore: the largest of 1,247 patterns is 9,131 positions, a
  case-insensitive list of Microsoft names, and the next is 772. So 10,000 existed for one pattern.
  The largest real unions are 782 positions (`oneOf` of patterns) and 253 (one mapping's
  `patternProperties`). A position is a pattern's characters and classes, not an alternative.
- **Load: the agent added this on the user's "go ahead" (2026-11-06; in `558ba6f`).** A
  ceiling per union can't bound load: 2 million names reaching the ceiling is 8 GB of lists at 1,024.
  @oyl proposed counting all union positions against the size limit. Built differently: a schema has a
  full size, worked out by addition with nothing deduplicated, and it can't pass the limit. Counting
  each name once, as the ceiling does, would make the count itself quadratic on a long chain, since each
  union walks every name below it. Names, literals and mapping keys count too, because each takes a
  place in what a parser builds. Any schema that passes can be flattened in steps bounded by the limit.
  One result: a chain that doubles at each level (`aN: !aN+1 | !aN+1`) used to load and now passes the
  limit at about 26 levels. Section 9 still says `!m | !m` is `!m`, which is about meaning.

For a parser, no spec change: one automaton per union (2 to 7 ns a value, barely growing from 3 patterns
to 10); a DFA must be lazy, with a capped cache over an NFA walk (not built); `!*: !signed | !str`
costs the same; one merged key table per union of mappings (1.2 to 22 ns a key; required keys at the
end of each mapping not built); the digits check by one multiplication (6 to 9 ns a float against
about 170 by printing, no disagreement in 60 million values).

Checks after this (2026-11-06): part 2, 48 examples and 273 edge cases; 70 of 70 deliberate rule breaks
caught, including ties and an exact near-tie (`49954322897937359e-24`, 0.5000000000000001 of a unit
away). Of 200,000 random 15-digit values in the normal range none lost digits; below it, 18,204 of 20,000.

Later on 2026-11-06: part 2, 48 examples and 296 edge cases; 82 of 82 deliberate rule breaks caught.
Not tested at 64 MiB, or in a real parser.

## Independent review by Codex at `a679bd6` (2026-11-06, **Fixed in `ffe895c`**)

The user asked for an independent review. Codex read both specs read-only, was told to skip these notes,
and could run the checkers. Each finding below was rerun on 2026-11-06. The user had all seven fixed.

- **Part 2, sections 11 and 16: `!*` and kept references. Defect.** "Types each node once under each
  type" silently changes data, because a type open to `!*` depends on the nearest `!*`: one referenced
  `{x: 1}` under `child: !leaf` must read `{x: 1}` below `!*: !int` and `{x: "1"}` below `!*: !str`. The
  key has to be node, type and nearest `!*`. The checker keeps no such memory, so it never showed.
- **Part 2, section 14: `[]`. Defect.** The grammar can't write an empty sequence. The agent found more
  while rerunning it: the checker reads `!int | []` as one empty literal, so `[""]` passes and `[]` fails.
- **Part 1, sections 7.3 and 12: flow merge. Defect.** Prose allows tabs and breaks between flow tokens,
  and `flow-pair` needs spaces after `<<:`. `{<<:\t*a}` is refused.
- **Part 1, section 8: `>` in a path. Defect.** Prose says a key holding `>` can't be written in a path;
  `bare` lets `*a>b` through. Either side could change.
- **Part 1, section 2: characters. Wording.** "Only these characters" contradicts double quotes holding
  U+0085 and the rest two lines later.
- **Part 2, section 14: names. Ambiguity.** `name` doesn't exclude spaces, and the checker refuses
  `!my type`.
- **Part 2, section 9: full size. Wording only.** Codex read "what its type expands to" as going into a
  mapping's values and called the checker's count low. That reading gives a recursive type such as
  section 8's `node` an infinite size, so it can't be meant, and a mapping type is shared, not expanded,
  at load. But the text allows the reading, so it should say a value is a place of its own.

Held up under its effort: part 1 section 10's arithmetic; the pattern ceiling (1,024 loads, 1,025 refused);
no way past part 1's full size.

Done while fixing them: `>` is out of bare paths, the way the prose already read. The same flow gap was
worse for `-<<`: `[-<<\t*s]` read as the text `-<<\t*s` with no error. In a flow collection a tab or break
now works there too, and in a block a tab is refused. A literal has at least one character, so `[ ]`
and `[!int, ]` are refused in a type expression. The checker's `\s` in a name became space and tab, to
match the grammar. @oyl's "(node, type)" memory is now node, type and nearest `!*`; that cost isn't
measured, and @oyl has been told to stop on part 2.

Checks: part 1, 58 examples and 235 edge cases, all 7 deliberate breaks caught; part 2, 50 and 311, 86 of 86
caught. Real files unchanged: 3,418 of 4,651.

## @oyl on `!*` as events arrive (2026-11-07, **Fixed in `047f547`**)

@oyl's answer, in [its message](../mail/received/20261107-021549Z-@oyl--typing-under-star-as-events-arrive-b8b0cc69.md),
with the tables. Same setup as its costs message. It is stopped on part 2 unless the user reopens it.

- **One rule set per level, nothing held: yes.** 32 bytes a level, so 8 KB at 256. Looking a key up in
  the `!*` as well as the mapping type adds 2 to 3.5 ns. Nesting adds nothing. A key can run two key
  automata, so at the ceiling keys cost about 48 s on 64 MiB where values cost 24 s (arithmetic).
- **Choosing a mapping alternative can't always stream.** Key order is free, so `side: 2` can come before
  `kind: square`. A literal can settle the choice early. Alternatives told apart by required keys hold the
  whole mapping, because only its end shows a key is absent. With the union at the root, a parser held
  1.9 million events, 213 MB on 10.5 MB, about 1.4 GB for 64 MiB. A tree holds that anyway, so only event
  interfaces lose, and the stream picks the key order, so a service can't rely on literals coming first.
- **Time stays in line with size,** given a link from each collection's start to its end. Scanning instead
  grows with depth times size, 29 s on 64 MiB at 4,096 levels against 0.1 s, which would break section 2 for
  a parser that goes deep. The test at each mapping's end is a plain loop, 7.4 s on 64 MiB at 1,024
  alternatives, under what patterns can already cost.

Three text changes it asked for, all applied, with a fourth bullet on end links in section 16 (figures rechecked):

- **Section 3:** "A parser can type events as they arrive" needs its exception under a union of mappings.
- **Section 9:** "has the required keys and literal values" should say the mapping's own keys. The linear
  cost depends on a choice never looking below them.
- **Section 16:** "All a schema can do is spend time" isn't quite true. A union of mappings near the root
  also makes an event parser hold up to the whole document. @oyl would state it and leave it to the size
  limit, since a limit on what is held would differ between parsers, as depth does.

Its own probe agrees with the nearest `!*` in the section 11 fix in the working copy.

Then the key split in `211757b`: part 1, 58 examples and 235 edge cases; part 2, 51 and 334; 94 of 94 deliberate
breaks of part 2 caught.

## Second independent review by Codex at `101d920` (2026-11-07)

Read-only, of both specs and both checkers, with extra attention on the `!` rule, `!*` and `!**`, a
schema's full size, the digits rule, publishing, kept references and part 2's overview. It reported no
way past reference expansion, `!*` and `!**`, the hash check or per-use typing of kept references, and
the ceiling and full-size boundaries held. Six findings. The agent reran every one, with neighbouring
cases, and found one more.

**Ruled by the user (2026-11-07), and fixed:** 2 and 4 in `ef07a4e`, 1 and 3 in `e92b1a2`. See the end of [rules.md](rules.md).

1. **Which number a `!float` limit tests** (part 2, sections 4.2 and 4.4). `!float(..0.1)` refuses `0.1`
   in the checker, because it compares the stored binary64 value with the exact limit, and so do
   `!float(0.3..)` on `0.3` and `!float(..1.1)` on `1.1`. A parser comparing written with written, or
   stored with stored, accepts them. In a union the refusal turns silent: `!float(..0.1) | !str` on `0.1`
   delivers the text `"0.1"` here and the number on those parsers. The limit now tests the number as
   written, so what a parser stores can't matter. Stored values order the same way unless they're equal,
   so only a tie needs the exact comparison. None of SchemaStore's 4,220 number limits has a fractional
   part.
2. **A comment between a repeated `%YAML 2.0` and its marker** (part 1, sections 4.1, 4.4 and 12). The
   prose says directly before the marker and that comments aren't skipped, so YAML stops at the `...`.
   The grammar has `gap` there, and `draftcheck.py` reads on. Joining a file that has a comment after
   its directive shows what's at stake: on the prose's reading its data is silently dropped. The prose
   now follows the grammar. The user first took this to both sides of the line, then pointed out that a
   comment before it might be Markdown, so only a comment after the line is skipped.
3. **A tie when rounding is accepted** (part 2, section 4.4). `1.00000000000000011102230246251565404236316680908203125`
   is exactly halfway between two binary64 values, and "the nearest" names neither. It now takes the
   even one, as IEEE 754 does by default. This only arises for an application that accepts rounding.
4. **A leading blank line wider than the text** (part 1, section 6.4; found by the agent while checking
   finding 5). In `a: |`, a line of five spaces and then `  x`, the checker silently drops the extra
   spaces, though it keeps them on a blank line inside the text. 1.2.2 calls this an error, and PyYAML
   refuses it. Now refused. None of 4,418 real blocks in 4,651 files has one.

**Fixed in `ef07a4e`.**

5. **Block grammar.** A line of more than `m` spaces could match `blank` as well as `indent(m) text-line`,
   which would lose text. The prose and `draftcheck.py` already agreed, so part 1 section 12 now says
   which. It arises on 20 lines in 8 of 4,651 files.
6. **The JSON claim.** Part 1 section 13.1, the README and the covering note left out two exceptions: a tab
   before the value or on a line after it, and a `\u` escape for a lone surrogate. Probing the rest,
   the `i_` files in JSONTestSuite and 34 hand-written cases found no others. Refusing a number too large
   to hold happens in the schema, not the syntax. PyYAML also refuses a leading tab.

**Not a defect.** Codex read part 2 section 3, a stamp isn't replaced, against section 16, an application
ignores a file's schema, as a conflict. Section 3 goes on to let a library do that, and section 15 lists
whether one must as open.

Checks after the fixes: part 1, 59 examples and 251 edge cases, 6 of 6 deliberate breaks caught; part 2,
54 and 347, 95 of 95; real files still 3,418 of 4,651; JSON still 1,015 of 1,015 and 93 of 95.

## Third independent review, of part 2 at `b0df6ea` (2026-11-11)

A fresh agent read part 2 cold, read-only, without the notes, with extra attention on sections 4.2 to
4.7, and ran both checkers. It found 14 issues, 6 of them silent, and no example with a wrong output. It
recomputed every digit claim in section 4.4 and found them right. The agent reran every finding with
neighbouring cases against `schemacheck.py`, and all 14 hold. Three needed correcting: 3, 4 and 8 below.
"Recommend" is the agent's proposal.

**Ruled by the user (2026-11-11):** "go with you recommendations, but if there any you are not quite as sure
about we can review those." **Applied in `bc5491f`**, with the checkers: 1 to 4, 6 to 10, 12, 13, and every
point in 14 but the count for kept references. **Held for review with the user (Open):**
- **5, dates.** RFC 3339 allows second 60, year 0000 and any number of fraction digits, and common libraries
  can't hold them. Python's `datetime` keeps microseconds, so under "keeps every fraction digit" a .NET
  timestamp, `2001-02-03T04:05:06.1234567Z`, refuses in a Python program. The choice: follow the RFC, and
  some programs refuse; or a narrower grammar that every library holds, which then refuses some valid RFC
  3339 values. **The user chose the RFC (2026-11-11)**: "yes follow an RFC". What a library does with a
  value it can't hold is still open (rules.md, "From the third review").
- **11, big integers. The user chose a fixed `!int` and a new `!bigint` (2026-11-12), in main `300f554`;
  see rules.md, "Big integers".** The options: the parser delivers the digits unconverted and the application converts;
  each parser refuses past a count it states, which is loud but differs between parsers; or a fixed maximum in
  the spec, the same everywhere. **Rerun 2026-11-12:** Python 3.14.9's `int()` takes 3.0 times as long for twice the
  digits up to 1.6 million (0.74 s), then 2.3 times (12.8 million digits, 6.0 s). Node 26.13's `BigInt()`
  takes 2.4 times as long (1.6 million digits, 0.16 s). Python refuses past 4,300 digits by default, for
  this reason (CVE-2020-10735), and the checker turns that off.
- **14, the count a kept reference adds to.** It is section 15's open point, "Typing under kept references",
  which hasn't been built. The agent doesn't know which count the sentence meant. **Answered 2026-11-12:**
  the agent reread section 11 with part 1, section 10, and took it as a third number, typed; the user: "I
  guess we have to, what other way is there?". In main `56210d7`; see rules.md, "Typed".

Also done while applying them:
- the checker now reads `\p{..}` from Python's Unicode 16, through RFC 9485's grammar;
- section 9's figures were recounted the new way on SchemaStore at `1e82d8a` (2026-11-11). Of 1,287 patterns,
  one is still past 1,024, now at 11,831 rather than 9,131. The next is still 772, and the largest union of
  patterns is still 782.
- On the two real schemas, no union of mappings has a type key, so finding 10's rule costs them nothing.

Checks after the fixes:
- part 1: 59 examples and 356 tests, after the merge change in `draftcheck.py`;
- part 2: 64 examples and 698 edge cases, 77 of them new;
- the workflow schema against its JSON Schema: 396 of 398 public files, as before;
- Compose: 308 of 311, as before.

Not rerun: the deliberate breaks, whose patches name lines that changed, and the JSON checks, since nothing
they use changed.

Silent: two careful readers deliver different data, and neither refuses.

1. **What a float type delivers** (4.4). The text says "it delivers a number", not which. `!float32` on
   `0.1` gives 0.1 in the checker, and 0.10000000149011612 with rounding accepted. `!float128` gives the
   exact decimal. A reader who stores binary32 delivers 0.10000000149011612 without rounding. The review
   proposed delivering the stored value. That reverses the agent's earlier choice, which the user hasn't
   ruled on (rules.md, "What the agent chose in writing them"). Recommend: say it delivers the number as
   written, and that the store promises only that an application with it can keep that number.
   *Moot since 2026-11-12: `!float` is the nearest binary64 and the width names are gone (main `4d7f934`).*
2. **`!any` in a scalar union** (9). In the checker, `!any | !int` on `3` gives `"3"`, while `!int | !any`
   gives 3. Against a mapping, `!any | !m` types by `m`, and so does a sequence. So `!any` comes last for
   collections and in order for scalars. "Takes a node no other alternative fits" says last. Recommend:
   last everywhere, and fix the checker.
3. **A key spelt both ways through a merge** (7; part 1, 7.3). `base: {why?: !int}`, with `t` holding
   `<<: *base`, `"why?": !str` and `!*: !int`:
   - The checker keeps the merged plain spelling, which is optional `why`. So `why?: 5` goes to `!*` and
     gives 5, and `{}` is accepted.
   - "The later one wins" gives a required `why?` of `!str`, so `"5"`, and `{}` is refused.
   - The reverse case, merged quoted and local plain, splits too: the checker gives `"5"` where the text
     gives 5.

   Correction: this isn't only a checker bug. Part 1's "replaces the value in place" supports the
   checker. `a` and `a?` in one mapping already go to the later one (decided after @oyl's review above),
   and the checker does that. Recommend: the later key's spelling and value win, part 1 keeps its
   position, and the sentence names both pairs.
4. **A published file's last entry** (3.1). Take a file with `--- &` holding `a: !int` and `b: !str`,
   then a second `--- &` holding `a: !bool`. Read by table order, the root is `b`, and the checker does
   that. Read by the last key written, it is `a`. Correction: a `...` after the table is also accepted,
   with the entries before it, though part 1 says `...` empties the table. Recommend: exactly one
   `--- &` and nothing after it. This doesn't touch the open point on the last entry as the root.
5. **`!date` and `!datetime`** (4.1). The checker refuses second `60`, year `0000` and a space for `T`
   (Python's `fromisoformat`). RFC 3339's ABNF allows the first two, and its section 5.6 allows the
   third as an option. So `!datetime | !str` gives text on one reader and a date on another. The text
   doesn't say whether a value keeps its offset and every fraction digit. The checker delivers the text,
   so it keeps them. Recommend: the ABNF of RFC 3339 section 5.6 with 5.7's day limits, `T` or `t` only,
   and a value keeps its offset and fraction digits. An application that can't hold one refuses it, as
   with integers.
6. **`!binary`** (4.1). The checker accepts `aGl=`, whose pad bits aren't zero, which RFC 4648 section
   3.5 lets a decoder refuse. It refuses `aGk` (no padding) and a CR from `"\r\n"`, and other decoders
   accept them. Recommend: canonical base64 only (padding required, pad bits zero), with only LF
   skipped.
7. **`!float`'s spelling** (4.1). It is given in words, and `1E5`, `1e+5` and `1e05` are left open. The
   checker accepts all three. Recommend: give JSON's number grammar,
   `-?(0|[1-9][0-9]*)(\.[0-9]+)?([eE][-+]?[0-9]+)?`, which the checker already uses.

Cost, and wording:

8. **A decimal's scale** (4.6). Correction: the text already answers what is delivered. Section 4.4
   says the digits are kept as written, and the example delivers `1.50`. The checker gives `1.500` for
   `1.500` under `5:2`. What is wrong is "says what SQL's `NUMERIC(38,10)` says", because SQL stores at
   the scale and rounds. Recommend: "uses SQL's two figures", and say that a value isn't padded or
   rounded to the scale.
9. **A pattern's count** (9). There is no count for `*`, `+`, `?` or `{n,}`, and it isn't said whether
   the type adds 1. The checker counts Python's optimized parse, not the written pattern:
   - 1,100 one-character alternatives count 1 and load, where the text counts 1,100 and refuses them;
   - `abc|abd` counts 3, not 6, and `a|b|c` counts 1.

   Recommend: count the written pattern, with each quantifier's count stated (the checker's
   `max(n, 1)` for `{n,}`, 1 for `*`, `+` and `?`), and a type with a pattern counts only its pattern.
10. **A key under a union of mappings** (9, 16). Each alternative counts 1, and each one's type keys
    count separately. Yet fitting tests every data key against every alternative's type keys. 40
    alternatives, each with a type key of 1,000 positions, load, so a key costs 40,000 per character,
    and up to about a million. Section 16 says the ceiling fixes the cost per character. Recommend:
    count all the type keys of a union's mapping alternatives as one union.
11. **Big integers in linear time** (4.4, 2). CPython's `int()` took 0.036, 0.107 and 0.335 s on 200k,
    400k and 800k digits, about n^1.6. A 64 MiB `!int` would take minutes. A parser may already refuse
    past 2^64-1, so this binds only a parser that holds more. Recommend: such a parser may keep the
    digits unconverted, or refuse past a digit count of its own. Either way the refusal is loud.
12. **The checker isn't I-Regexp** (4.3, 16). Its `.` matches CR: `!str(/a.b/): !int` with `!*: !str`
    gives 1 for key `"a\rb"`, and the text gives `"1"`, since RFC 9485 section 5.3 maps `.` to `[^\n\r]`.
    It accepts `a{,3}`, `a{`, `\x41` and `A`, crashes on `\p{L}`, and backtracks: `(x+){1024}`
    loads. These are checker bugs. Section 16's "linear ... whichever engine does it" contradicts its
    next sentence. Recommend: "must take time linear in the string".
13. **Unicode versions** (4.3). "Differ only on a character one of them doesn't know yet" claims too
    much: an assigned character's General_Category can change. U+180E went from Zs to Cf in Unicode 6.3
    (from the release notes, not rerun here). Recommend: "or one whose category a later version
    changed".

Loud only: one reader refuses.

14. - **An integer limit against holding** (4.4). `!int(0..10) | !str` on 10^29: the checker gives the
      text, and a 64-bit reader that tests holding first refuses. Recommend: for `!int`, test the limit,
      on the written number, before holding.
    - **"Too large" for a float** (4.4). `1.79769313486231570815e308` is above binary64's largest value
      and within half a unit of it. The checker delivers the largest value, and "larger than the
      largest" refuses it. The 15-digit sentence needs an upper bound too, since `2e308` doesn't keep
      its digits. Recommend: too large means it rounds to infinity, as `strtod` reads it.
    - **The sign of zero** (4.4). It isn't stated. The checker gives -0.0 for `-0`, and +0.0 for `-1e-400`
      with rounding, where IEEE 754 gives -0.0 (a checker bug). Recommend: a float keeps the sign of
      zero.
    - **A type key that can't hold its key** (7, 4.4). `{!float: !int, !*: !str}` on key
      `3.14159265358979323846` is refused by the checker. "A key stays a string" suggests no match.
      Recommend: refuse, as a value does.
    - **The grammar** (14). It allows `!int(..)` and `!int(5..1)`, which the checker refuses. A second
      space, as in `a |  !int | !str`, gives a literal `" !int"` by the grammar. The checker trims it, so
      `5` gives 5 there, and `"5"` by the grammar, which makes this one silent. Recommend: a range has at
      least one end and its low end is no higher than its high end; a part can't start or end with a
      space.
    - **Checker bugs.** `!str(1..5 /[)]+/) | !int` is refused, because the checker counts parentheses
      before a pattern. It treats `(/` in a literal as a pattern, so `a(/b | !int` is refused.
    - **"Literal values" in a fit** (9). The checker tests a key's value only when every alternative is a
      literal. So with `kind: circle | !int` in `circle`, `{kind: square, r: 1}` fits both and is
      refused, while a reader that tests the literal picks `square`. Recommend: say "a value whose type
      is only literals".
    - **Which count a kept reference adds to** (11). "The node's own size counts against the limit" names
      no count. Recommend: held.
    - **Full size of `!**`** (9). The checker counts the `!**` key in `!**: !int` (3) but not in the rules
      form (8, where the text gives 9). This is a checker bug.

The probes are machine-local.
