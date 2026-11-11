# Status

*Updated 2026-11-08*

**Goal.** The user set it on 2026-11-03: design YAML 2.0, and fix a YAML
ecosystem that has become a minefield.

**Nothing is final** (the user, 2026-11-05). Every rule is the user's current choice in a
proposal, and it's too early to carve anything in stone. Don't call a rule settled, in notes or
in mail: say "the user chose", and treat it as open to argument.

**Where things stand.** The user is setting the design rule by rule; the
rules are in [rules.md](rules.md). The user chose a clean break on
2026-11-03, so 2.0 need not be readable by existing parsers. Draft 1 of the language is
`spec/yaml-2.0.md` in the code checkout, committed on 2026-11-04. Section 14 of the draft lists
what is open; the user went through it on 2026-11-04. @oyl's review is applied in `caece25`.
The later decisions on shared nodes and the size limit, @oyl's five gaps and the limit on
shared tables are in `2d5a90d`. Section 15, Security, is in `bf225ba`. @oyl's four points on
section 10 are done: 1 to 3 in `1c1d724`, and 4 replaced by the user's rule on joins ([review.md](review.md)).

**`!*` and publishing (2026-11-06).** `!*` is in `c54395c` and publishing is in `19aad50`, both pushed.
The covering note now covers both. See [rules.md](rules.md).

**`!` outside the table (2026-11-06).** The user chose to refuse it, with a proviso that it could be
relaxed if 2.0 becomes the standard. It's in `9f6292f`. Files that read as written are now 3,418 of
4,651 (73.5%).

**@oyl's costs (2026-11-06).** The four text errors are fixed and the user chose 1,024 for the ceiling,
both in `0ba3c31`. A schema's full size, which limits load, is in `558ba6f`, and the tags changes to part
1, section 13.1, are in `a679bd6`. See [review.md](review.md).

**Independent review (2026-11-06).** Codex's seven findings are fixed in `ffe895c`, @oyl's three text
changes on event parsers in `047f547`, and `!*` split into `!**` and `!*` in `211757b`. See
[review.md](review.md) and [rules.md](rules.md). Part 2 is now YAML Easy Schema (YES), in
`spec/yaml-easy-schema.md`, and its overview opens with the shadow.

**Checks before sending (2026-11-07).** JSON with `!**` matches on 1,015 of 1,015 SchemaStore files and
93 of 95 in JSONTestSuite; the 994 in part 1 was the files under 300,000 bytes. Rerun after the precision
changes on 2026-11-08, with the same result. On the current checker the
workflow schema agrees with its JSON Schema on 131 of 131 and on 396 of 398 public files it had never been
run on, and the Compose schema on 308 of 311, all 5 disagreements being about null: see
[shadow/README.md](shadow/README.md). A second independent review found four things, and the user ruled on all four the same day: see
[review.md](review.md). They're in `ef07a4e` and `e92b1a2`. Nothing has been sent.

**Asked next (2026-11-07).** The user is more concerned about `!float` precision than limits, and asked
whether it has been worked out. The user said yes to width names and patterns on `!decimal`. Width against
digit count stays open in section 15. The user then chose patterns on `!str`, `!int`, `!float` and its
widths, `!decimal` and `!null` (part 2, section 4.5), `!decimal(38:10)` (4.6), and a precision, a limit and
a pattern together in one pair of parentheses (4.7). All of it is in `e92b1a2`. On 2026-11-08 the user
chose `!float` as short for `!float64`, with floats keeping accepted names, and left `38:10` against the
picture `28.10` open, both explained in part 2, section 15. The user also chose that a value too large or
too precise for a float type's store refuses the document rather than being no match, and kept the store
sizes, since validation before use is what a schema is for. All in `bafa4ce`. The covering note now mentions JSYNC under tags. See the end of [rules.md](rules.md). Only a comment after a repeated `%YAML 2.0` is skipped now, not one before it.

**Test suite, part 1 (2026-11-08).** The user asked for it and plans to hand it to the reference
parser, Oyl NG, when it's ready (see Working with @oyl); Oyl NG already reads it from `../yaml2`. It is `suite/` in the code checkout, first in
`b44793d`: 351 tests in yaml-test-suite's `src` format (356 now), with a README and `bin/suite-to-data`. They are
the draft's 59 examples, the 250 edge cases that were in `draftcheck.py` (its 253, less 4 repeats, plus 1
it skipped for want of an answer, `a: [x]` then `- -<< *a` in a table, which it refuses), and 42 new ones:
each size boundary and one under it, 256 levels, CR LF, the stop offset, and key order. `draftcheck.py`
now reads `suite/src` in place of its own lists (with PyYAML), checks that every example in the draft is
a test tagged `spec` with the same result, and exits 1 on any failure. Before, a failing edge case only
printed. `suitenew.py` adds a test. Breaking the checker on purpose can make it build toward 2^64
nodes (with the default limit removed, it reached 5 to 6 GB on 2026-11-08 and slowed another project's
job: `mail/received/20261109-021824Z-@oyl--memory-on-this-machine-1b3d249d.md`), so run such checks under
a memory cap, one heavy job at a time. The changes from yaml-test-suite's format are the agent's, and the
user hasn't ruled on them: `=VAL :` for every string, `+DOC !name`, `rest` for a stop, `limit`, `keep`
and `together`, a fixed list of escaped characters, and IDs from a hash of each test. The user left two
questions to the agent on 2026-11-08, and it chose: the suite is under MIT, as yaml-test-suite is, so a
parser can copy it in; and section 4.4's offset counts bytes, with a CR LF as two (`b44793d`). The checker
now reports that offset (`P.offset()`) and the suite's `rest` is checked against the bytes after it; an
offset in characters, or one that drops the CRs, fails a test. yaml-test-suite's `⇔` mark unescapes to
the text `x{FEFF}`, not U+FEFF (a missing backslash in `bin/YAMLTestSuite.pm`), and none of its tests
uses it.

**The checker against the reference parser (2026-11-08).** Oyl NG's agent ran 100,319
generated and mutated streams through the parser and `draftcheck.py`, and reported the two where they
differed. In both the parser followed the draft's text and the checker was wrong. (1) A reference to a
merged mapping whose merged key a later line replaced: the checker counted the replaced pair where the
mapping was written, but not at a reference to it, so `m: {<<: *s, a: y}` then `k: *m` needed a limit of
26, not 30. Section 10 says full is "worked out by addition" and "nothing is deduplicated". (2) A tab
after the `>` of `*<a:b>` was refused, though the grammar's `eol` allows it and a tab after a bare step
was accepted. Both are fixed in the checker; the old one fails 4 of the 5 new tests (`M6Q8`, `T38H`,
`6AHS`, `AKB8`, `X3AR`). Sections 8.2 and 10 each gained a few words to say so (a reference ends at "a
space, a tab or the end of the line"; a replaced key counts "in its mapping and in every reference to
it"). **Not committed on main yet:** the spec and suite changes wait for the user.

**YAML Easy Schema (YES), part 2.** Draft 1 is `spec/yaml-easy-schema.md`, first in `bf225ba` (2026-11-05), and its
section 15 lists what is open. The user chose an answer to "wherever this occurs" (see
[rules.md](rules.md)). The agent added these, and the user hasn't ruled on them: a quoted
scalar in a schema is always a literal, a reference is typed where it's used, `!int`,
`!float`, `!bool` and `!null` match plain scalars only while the others take any scalar, and
every named type reachable from the root is checked. `schemacheck.py` tests the draft: 64
examples and 621 edge cases pass, and breaking 152 rules on purpose fails it each time, though 6 of those
only by a crash or a time-out, not a failing test. Not done yet: tests that catch those 6, `\p{..}` in
patterns (the checker can't read it, though section 4.3 allows it), and the same for any older rules not
covered. @oyl
reviewed Draft 1 on 2026-11-05, and the review is applied in `d645ce9`, with the user's answers: see
[review.md](review.md). The list of standard types stays open in section 15: the user
judged on 2026-11-05 that the draft is far enough along for the core team to work out final details
such as this, if they take it up. Numbers and `\p{..}` with Unicode 16 or later (the user, 2026-11-05) are in
`cc84227`.

**In `7689ea6`** (the user, 2026-11-05): patterns in flow collections (part 2, sections 4.3 and 14),
a parser builds nothing from a name (part 2, sections 12 and 16), and what 2.0 costs object data
(part 1, section 13.1). See [rules.md](rules.md).
Background is in [landscape.md](landscape.md).

## Open, for the user

1. **The design's open points:** marked as such in [rules.md](rules.md). Merge, the
   size limit, the syntax cuts and how schemas are named were chosen on 2026-11-04,
   and margin strings are parked for later. Patterns are proposed as I-Regexp. The
   user chose to refuse leftover tags (the `!` rule) on 2026-11-06, with a proviso in section 6.1.
2. **Whose name it is.** The user's plan (2026-11-04): make this as complete as
   possible, then present it to the YAML core team. If they reject it whole, decide
   where to take it then. If they take it up, they'll hammer out the final details.
   So I-Regexp and other proposals needn't be settled first. See landscape.md, How the
   core team takes proposals. Until they answer, call it a proposal for YAML 2.0.
3. **Publishing.** `origin` is `trans/yaml2` on GitHub, public. The user added it and
   approved the first push of `main` and `ai` on 2026-11-04, and has approved each one since. The spec and README are CC BY 4.0, and the code on `ai` is
   MIT (the user, 2026-11-04). So the `ai` branch is public: write nothing
   private here. Ask before pushing again. No transcripts are kept in this repository yet, so `transcript.encrypt` can
   wait.

## Working with @oyl

Oyl is the user's YAML 1.2 parser and emitter in C, with YAML 1.1 and go-yaml
v2 dialects, an in-place 1.1 to 1.2 upgrade (`oyl_upgrade`), bindings, and
measurements on real files. It is the obvious place to test ideas here.

**The reference parser** (the user, 2026-11-04): a standalone 2.0 parser, not a dialect
inside Oyl, applying what Oyl learned. It is **Oyl NG** (the user gave its name for use here on
2026-11-09), a C11 library at https://github.com/trans/oylng (public, MIT), address `@oylng`.
By its README (v0.1.0, `077a031`, 2026-11-09) it has the streaming event parser, the tree and the
emitter for part 1; part 2 is to come. Its CI runs this suite pinned at `213471d`, and it passes the 347
tests an event interface can run (the 9 others need `keep` or `together`). On 2026-11-09 the user called
it "a working fast parser", and then "even faster now". Its speed figures, sent at the user's request
(`mail/received/20261111-070212Z-@oylng--speed-figures-4a9a93ac.md`), are from its `make bench` on
generated 8 MB inputs, as ratios, since absolute MB/s moved by up to 2x on the shared machine: against
libyaml 0.2.5, events 3.7 to 8.3 times as fast at `077a031`, read and written again 2.9 to 4.6, trees
against `yaml_parser_load` 4.1 to 7 at `207d43b`; against Oyl, events, 0.94 to 1.22 at `1758ec9`. Its own
caveat: the figures don't isolate the language. Most of the gap over libyaml is engineering Oyl has too
(SSE2 scans, fast paths), and against Oyl it is about even, while also refusing repeated keys and
applying section 10's limit. The event parser holds nothing measurable beyond the input (`b1a354a`);
trees' memory isn't measured. The user had expected it to beat 1.x parsers on speed, given the
simplifications; speed and size on real files, which would first need converting to 2.0, are still to
measure. The agent suggested the 1.2-to-2.0 converter sit in Oyl beside
`oyl_upgrade`; not decided.

Oyl's notes are private. Read them in place, and bring only what the user has
cleared into this repository, which is public.

**What goes to @oyl for now** (the user, 2026-11-05): only what its insight into performance might help
with. Asked in `mail/sent/20261106-021824Z-@oyl--two-costs-in-part-2-at-1c1d724.md`: patterns on every
scalar and the digits check on `!float`, with the three cost questions from `c422281e` still waiting.
@oyl answered all of it on 2026-11-06 and has been told to stop on part 2 for now, so nothing more goes there on it; see [review.md](review.md).
@oyl hasn't been told the Unicode minimum, the join rules or the required `---`, and needn't be yet.

**Covering note for the core team** (the user asked for a draft, 2026-11-05). It stays local until the
user says otherwise, in `Outtake/covering-note.md`, which git ignores. Its list of what is essential is
the agent's draft: the user hasn't ruled on it. The talk is confirmed, and the org's schema language
and plugin work bear on the ask and on part 2's name: see landscape.md, What the YAML org is doing now.
