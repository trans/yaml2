# Status

*Updated 2026-11-24*

**Tags.** The user, 2026-11-24: "nothing should be released on an untagged commit". So a commit of
main that a release (Oyl NG's, say) runs against gets an annotated tag, pushed with it. The user chose
`v0.x.y`, Oyl NG's pattern; the first is `v0.1.0`, on main `def062b`.

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

**Third independent review, of part 2 (2026-11-11).** A fresh agent found 14 issues, 6 of them silent. The
user took the agent's recommendations, and they are applied in `bc5491f`. Three were held for review with the
user. On dates the user chose RFC 3339's grammar (2026-11-11), and then precision in the schema: `round`, a
date's level and an application's own, applied in main `6c74755`, with the checker in step. On big integers
the user chose a fixed `!int` and a new `!bigint` (2026-11-12), in main `300f554`. The count a kept
reference adds to is now typed, a third number (2026-11-12, main `56210d7`). See [rules.md](rules.md), "From the third review".

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
it"). **Committed on main** (checked 2026-11-12).

**YAML Easy Schema (YES), part 2.** Draft 1 is `spec/yaml-easy-schema.md`, first in `bf225ba` (2026-11-05), and its
section 15 lists what is open. The user chose an answer to "wherever this occurs" (see
[rules.md](rules.md)). The agent added these. The user took the first two on 2026-11-12 ("all are
fine"), and section 15 no longer lists the second: a quoted scalar in a schema is always a literal, a
reference is typed where it's used. The user hasn't ruled on the rest: `!int`,
`!float`, `!bool` and `!null` match plain scalars only while the others take any scalar, and
every named type reachable from the root is checked. `schemacheck.py` tests the draft: 68
examples and 756 edge cases pass (2026-11-12, after floats and dates were simplified in `4d7f934` and `7989372`). Breaking 152 rules on purpose failed it each time, though 6 of
those only by a crash or a time-out, not a failing test. Not done yet: tests that catch those 6, and the same
for any older rules not covered. `\p{..}` is read since the third review. @oyl
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
v0.1.0 (`077a031`, 2026-11-09) was the streaming event parser for part 1. **v0.2.0 (2026-11-12)**, tagged
on `45cc586` with CI passing, adds the emitter and the tree, one document per call with a referenced node
made once and shared (`207d43b`), and the faster scans with `make bench-files` (`1591e05`). Part 2 is to
come. Its agent read part 1's changes up to `0e2e6b3` and found none asks anything new of a parser; it
stops at the first error, which section 2 still allows. Before tagging it ran, under ASan and UBSan with
clang 18: the tests; the 4,651 real files as 2.0, block and flow, plus two mutants of each, through its
fuzz harness, which compares events with trees and round-trips through the emitter; and 490,323
libFuzzer runs. All clean (`mail/received/20261112-180136Z-@oylng--oyl-ng-0.2.0-is-released-26a49c1d.md`). Its CI runs this suite pinned at `213471d`, and it passes the 347
tests an event interface can run (the 9 others need `keep` or `together`). On 2026-11-09 the user called
it "a working fast parser", and then "even faster now". Its speed figures, sent at the user's request
(`mail/received/20261111-070212Z-@oylng--speed-figures-4a9a93ac.md`), are from its `make bench` on
generated 8 MB inputs, as ratios, since absolute MB/s moved by up to 2x on the shared machine: against
libyaml 0.2.5, events 3.7 to 8.3 times as fast at `077a031`, read and written again 2.9 to 4.6, trees
against `yaml_parser_load` 4.1 to 7 at `207d43b`; against Oyl, events, 0.94 to 1.22 at `1758ec9`. Its own
caveat: the figures don't isolate the language. Most of the gap over libyaml is engineering Oyl has too
(SSE2 scans, fast paths), and against Oyl it is about even, while also refusing repeated keys and
applying section 10's limit. The event parser holds nothing measurable beyond the input (`b1a354a`).
The user had expected it to beat 1.x parsers on speed, given the simplifications. The agent suggested
the 1.2-to-2.0 converter sit in Oyl beside `oyl_upgrade`; not decided.

**Real files (2026-11-11).** The user asked Oyl NG to follow up with real files, and its agent's figures,
at `1591e05`, are in `mail/received/20261111-200634Z-@oylng--speed-and-size-on-real-files-2ea21726.md`.
The sample was the 4,651 public files, with `%YAML 2.0` added, `---` where needed and any BOM dropped,
which added 0.37% to their size. libyaml refuses 487 of them. Of the other 4,164, the engine reads 3,409
as written (3,388 of them give exactly libyaml's events) and refuses 755 for what 2.0 cut. The speed
figures cover only the 3,409:
- against libyaml, events are 4.1 times as fast (3.3 to 5.4 by kind) and trees 4.5 (3.9 to 6);
- against Oyl at `e6e38b5`, events are 0.92 (0.77 to 1.17 by kind) and trees 0.95. Before
  `1591e05` they were 0.77 and 0.83; that commit scans plain values 16 bytes at a time with SSE2, as Oyl
  does.

Peak heap: events take a fixed 15 KB (Oyl 28 KB, libyaml 69 KB). Trees take 1.6 bytes per input byte
from 16 KB up (Oyl 2.05, libyaml 9.2). The same caveat holds: the figures don't isolate the language, and
no file is over 200 KB. **Cross-check, the same day:** `draftcheck.py` also reads 3,409 of the 4,164
(3,418 of 4,651). Where its messages name the same rule, its first-refusal counts match: tags 160,
repeated keys 57, `>` 42. It also reads 9 of libyaml's 487, all with a `%` or `@` placeholder starting a
value (`tag: %%VERSION%%`), which section 13 allows. **File by file** (@oylng's lists, in its notes'
`real-files/`, `mail/received/20261111-233800Z-@oylng--real-files-the-lists-and-a-final-newline-ddb9104c.md`):
the engine and the checker read the same 3,418 files and refuse the same 755, and the engine reads the 9 too.
The README now gives the real-file figures, at the user's go-ahead (**Done in `c1a436c`**), and so do both
covering notes.

Of the 3,418, 21 don't give libyaml's events:
- **17 end in a `|` scalar with no line break after its last line.** 2.0 gives `|` exactly one final newline
  (the user's rule, 2026-11-04, in rules.md), and 1.2's clip gives none at the end of input, so the value is
  one character longer in 2.0. That is intended. But section 13 lists only what was removed and added, not
  this change, and a converter would have to write `|-` there. The user told @oylng "ok do it" (2026-11-12,
  `mail/received/20261112-052203Z-@oylng--a-line-in-section-13-for-the-final-newline-c9555dcf.md`), and the line,
  covering `>` too, is **Done in main `0e2e6b3`**. Recounted here with PyYAML 6.0.3: of the 3,418, 536 have no final
  line break, and 17 of those change under 1.2 when one is added, 13 of them workflows.
- **4 hold only comments.** libyaml gives no document, and with `---` put in front, 2.0 gives one empty
  document. That comes from the conversion, not the language.

Oyl's notes are private. Read them in place, and bring only what the user has
cleared into this repository, which is public.

**What goes to @oyl for now** (the user, 2026-11-05): only what its insight into performance might help
with. Asked in `mail/sent/20261106-021824Z-@oyl--two-costs-in-part-2-at-1c1d724.md`: patterns on every
scalar and the digits check on `!float`, with the three cost questions from `c422281e` still waiting.
@oyl answered all of it on 2026-11-06 and has been told to stop on part 2 for now, so nothing more goes there on it; see [review.md](review.md).
@oyl hasn't been told the Unicode minimum, the join rules or the required `---`, and needn't be yet.

**Part 2 is marked a work in progress (2026-11-12).** The user asked, through @oylng, for a bold notice at
the top of part 2 "so it is clear that is not done yet. and we will mention it in the letter"
(`mail/received/20261112-221957Z-@oylng--a-work-in-progress-notice-on-part-2-36efb35d.md`). It is in main
`d78e55b`, and both covering notes now say so where they list part 2. @oylng's view, which isn't a ruling:
part 1 is close to ready to show, and part 2 isn't, since no parser implements it, the third review found 6
silent issues, section 15 has about 17 open points (16 since `4d7f934`), and 6 of 152 broken rules are caught only by a crash or
a time-out. The user is weighing more work on part 2 before showing it.

**Floats simplified (the user, 2026-11-12: "yes").** `!float` is the nearest binary64; one too large
refuses the document, after the limit; the width names and `round` on floats are gone; `!decimal` is
delivered as written, for money or a bigfloat. In main `4d7f934`; the reasons are in rules.md, "Floats
simplified". Dates followed (the user, 2026-11-12: "yes"): a parser refuses a time it can't hold,
unless the application turns on a cut to its language's fraction digits; `!datetime(3)` and `round` are
gone. In main `7989372`; see rules.md, "Dates simplified". The user chose to keep `!bigint` beside
`!decimal` (2026-11-12), as the agent recommended; 4.4 says why, in main `57407f1` (rules.md).

**Oyl NG starts part 2 (2026-11-13).** The user told @oylng "yes please" to starting part 2 in the engine,
with a plain shadow first, and to asking this project for a suite and current shadows
(`mail/received/20261113-095948Z-@oylng--part-2-in-the-engine-a-suite-and-the-shadows-pleas-d0d7ce88.md`).
Its first scope leaves out patterns, `!**`, published names, the cut and bindings. Asked for: (1) a public
part 2 suite in part 1's format, with typed output JSON can't tell apart, keys for what the application
supplies, tags for subsets, and refusal paths; (2) both shadows at the current draft, with per-file
verdicts: done, see [shadow/README.md](shadow/README.md); (3) what may change soon: answered from section
15, since the third review has nothing left open (mail `20261113-100746Z`).

**Part 2's suite (2026-11-13). In main `63e86ea`, the user said do it (2026-11-13).** `suiteyes.py` writes
`suite/yes/src` from the checker's own tests: 806 tests (67 examples, 724 edge cases, 15 of typed), in part
1's format with `typed` events (`=INT`, `=BIG`, `=FLT`, `=DEC`, `=BOOL`, `=NULL`, `=DATE`, `=DATETIME`,
`=BIN`), keys for what the application supplies, tags from what each root reaches, and `refused` and `at`.
`suiteyes.py --check` reads it back and passes all 806. Writing it found two shortcuts in the checker:
- **A table with no document.** `typed()` loads every entry, which section 2 doesn't: an entry nothing
  reaches isn't a type. 152 checker tests rely on it, and the suite gives each a stamped document. Two
  examples in part 2, in 4.3 (`tag: !str(/^[a-z]+$/)`) and 9 (`a: !str(/(a{1000}){1000}/)`), had no
  document, so a parser would accept them. **Fixed in main `8514686`** (the user said do it, 2026-11-13):
  each has a document that would fit if its schema loaded, so only the schema is at fault.
- **The limit.** `typed()` applies a test's limit to the schema and to typed, not to the stream, so
  its typed tests sit below the stream's held size (the table counts in held: 74 for section 11's
  `[*s, *s, *s]` stream, whose typed is 10). The suite leaves those 17 out and has 15 scaled ones.

**Oyl NG against the checker (2026-11-13)**
(`mail/received/20261113-105601Z-@oylng--the-engine-on-the-shadows-and-the-checker-6c5df137.md`). The
engine logged each stream the checker's tests type, as `suiteyes.py` does, and agrees on 526 of 526, types
and refusal paths included. It skipped 265 for patterns or `!**` and didn't run 20 with a store. It found the
limit shortcut above too. It applies one limit to held, full and typed, and its typed count matches the
checker's at every limit and one under. For `!binary` in a block, the checker delivers the text without its
breaks and the engine the bytes; the suite writes bytes. Its fuzzer now types streams too. Its first run
found an engine bug (a union picking a literal or `!any` left a field unset), which is fixed. A second run,
of 187,909 cases, was clean. Two points for the user:
- **The path of a key's refusal.** **Fixed in main `5398fe7`.** The user left it to the agent
  (2026-11-14), and section 2 now gives an unknown or missing key the mapping's path, naming the key
  (rules.md). The suite has 7 tests of it below the root (815 tests).
- **Unions as a reserved key** (the user, 2026-11-14). **Fixed in main `0b88244`** (rules.md). The user
  chose `!|`. Checks: 70 examples and 799 edge cases pass; 817 earlier suite tests, unions rewritten, keep
  their answers and tags, and the 10 left were tests of the old spelling; both shadows give the same
  verdict and path on all 801 files; JSON's one entry matches on 1,015 and 93 of 95. Converter and checks
  in scratchpad `unionkey/` (`conv.py`, `cmpsuite.py`, `verd2.py`).
- **Typed on a data interface.** **Fixed in main `e75a203`.** @oylng's point: each type that reaches a
  node comes down a path of its own, so typed never passes full, and only an interface that keeps
  references needs to limit it. Testing the sentence (2026-11-14) found typed could pass full, up to
  twice, through section 10's rule that a `!**` type with no required key also takes a scalar or a
  sequence. The user asked for that rule's ramifications in detail (rules.md lists them) and chose to
  drop it. With it gone, typing the checker's 384 other documents as kept finds none past full, and
  section 11 has the sentence. Measured with scratchpad scripts `nokey/probe.py` and
  `nokey/jsonfigs.py`, and `typedfull/typedfull.py`.

**Oyl NG with patterns (2026-11-13)**
(`mail/received/20261113-153724Z-@oylng--patterns-and-a-stream-with-no-document-2b7d9854.md`). The engine
now has sections 4.3, 4.5 and 9's count. It gives `verdicts-compose.tsv`'s verdict and path on all 311
Compose files (255 accept, 2 refuse, 54 the grammar refuses), and still 490 of 490 workflows. Against the
checker: 716 of 791 agree and none differ, and the 75 left use `!**`, which is next. A pattern generator
compared the engine with `pattern()` and `re.fullmatch`: none differ on 50,000 patterns and 199,553 strings
(seed 7). The engine doesn't backtrack: `(a*)*b` against 100,000 `a`s takes 2 ms. On a table with no
document, the engine checks only what a document reaches. Its comparison tool had copied the checker's
shortcut, and now does so only with `--every-entry`. Without it, 141 of the 791 cases differ, each one a
stream the checker refuses and the engine loads (the suite counts 152, after dropping repeats in another
way). Two points for the user, both since answered:
- **How deep a pattern's groups go.** The user chose a limit of 256 (2026-11-13), which every
  parser refuses past. In main `a8a4420` (section 4.3) and the checker, with two edge cases. Of SchemaStore's
  1,287 patterns, the deepest nests 7.
- **What the count bounds.** Section 16 says the ceiling limits a pattern's size, but a part that counts 0
  (`x{0}`, an empty branch) still has to be matched. `(|||...)` with 100,000 bars counts 0 and loads, and a
  plain matcher steps through 100,000 states per character. The engine drops parts that count 0 and folds
  nested counts of 1 (`((a?)?)?`, `(a+)*`) into one, so its steps per character stay within the count.
  10 of SchemaStore's 1,287 patterns have an empty branch, and none has `{0}`. The text could require
  what the engine does, or count each group and branch as at least 1.
  **Measured 2026-11-14** (the user asked), on SchemaStore at `1e82d8a` with section 9's counter as an
  ECMAScript reader (anchors, `\b` and lookarounds dropped, as conversion drops them). Two rules:
  - *least1*: each part counts at least 1 after its count, and so does an empty alternative.
    `x{0}` 1, `(|||)` 4. 28 of 1,287 patterns change, by 2 at most. Section 9's figures don't move
    (11,831, 772, 782). But nesting stays free: `((a?)?)?` counts 1, so 1,024 alternatives each nested
    256 deep cost about 262,000 states per character.
  - *group1*: least1, and a group adds 1. `((a?)?)?` 3, `(a{1000}){1000}` 1,001,000. 814 patterns
    change, by 64 at most (the IPv6 one, 322 to 386). Figures: 11,832, 773, and the largest union
    782 to 813. Nothing new passes 1,024. Each state of a plain NFA is then within a small multiple of
    the count. **Fixed in main `c6ba341`:** the user took group1 (2026-11-14; rules.md).

**Oyl NG runs part 2's suite (2026-11-14)**
(`mail/received/20261114-002124Z-@oylng--part-2-s-suite-664-pass-0-fail-the-limit-on-a-sche-fb01f98f.md`).
A C harness (`make test-yes`) over `suite-to-data`'s output at `63e86ea`: 664 of 806 pass and none fail.
It skips 69 with `!**`, 25 that hold times otherwise (`holds`, `long-fraction`), 24 with `keep`, 23 with a
store, and 1 with a limit of 0, which its API reads as the default. No refusal comes at a path other than
`at`, and `-0.0` counts: all six fail when made `0.0`. Two points:
- **Part 1's limit on an application's schema.** The engine reads the schema an application hands over
  as a part 1 stream, under the limit, table counted; the draft didn't say, and the suite held it to its
  full size alone, so 23 tests sat below the text (held 7 to 38 against limits of 0 to 10). The user took
  the agent's recommendation (2026-11-14): the limit applies (rules.md). In main `425db57` (section 3).
  The checker now reads an application's and a published schema under the limit, and its typed test
  across documents moved to 18 and 17. The suite (`a7e2df6`, 808 tests) leaves out the checker's 22
  full-size tests and has 22 in their place, each schema reached beside a mapping that names a 20-key
  mapping 40 times, so full size (about 1,010) passes the text (about 510); and 2 tests of `a: !str`
  at limits 7 and 6.
- **A `tags` file per test.** `suite-to-data` now writes one, for both parts, so a harness can skip by
  tag. Doing it found `tags: null` in `RP5Q`, which PyYAML reads as no tags. `suiteyes.py` now quotes a
  tag line YAML would read as other than a string; that fix is in `a7e2df6`. The `tags` file itself is
  **Fixed in main `590d0a7`** (the user: "commit", 2026-11-14).

**Oyl NG with `!**` (2026-11-14)**
(`mail/received/20261114-093223Z-@oylng--is-in-the-engine-part-2s-suite-736-pass-0-fail-c7337088.md`).
Section 10 is in the engine (its main `ee7508a`, not pushed then). Over the suite at `a7e2df6`: 736 pass
and none fail, all 69 `!**` tests included. It still skips 25 that hold times otherwise, 24 with `keep` and
23 with a store; published names and `keep` are what part 2 still lacks there. Its harness now hands a
test's schema to the library's public constructor, which reads it under the limit (`425db57`). Against the
checker: 798 cases agree, none differ, with 20 store cases and the limit-0 case not run. The one difference
before that, `a: !str` at limit 6, was its comparison not reading the application's schema under the limit.
All 68 examples give their JSON or the refusal the text gives. Its reading of `!**` matches the checker
everywhere the tests reach; the mail lists it rule by rule. This mail crossed ours on the refused key's
path, so the 7 new tests (815) weren't in its run.

**Oyl NG with the new count (2026-11-14)**
(`mail/received/20261114-110513Z-@oylng--section-9-s-new-count-is-in-the-engine-e1aabe57.md`). The
engine counts as main `c6ba341` says, in its working tree. It gives all 14 of `counts3`. Over the suite
at `c6ba341`: 743 pass and none fail, `E6UA` and `LZL6` included. Against the checker: 805 agree, none
differ. Over 20,000 generated patterns (79,810 cases), its counts and matches agree with the checker's
reading under Python's `re`. It still drops `x{0}`, by the repeat rather than the count, and what loads
is decided by the count alone. **Waiting on our push:** its CI pins our main at `590d0a7`, whose `K8BW`
(`(a|b){512}`) the new count refuses, so its push waits for ours of `c6ba341`, and it asked for a word
when that is pushed.

**Oyl NG with `!|` and mapping-only `!**` (2026-11-14)**
(`mail/received/20261114-205336Z-@oylng--the-engine-has-both-unions-and-a-mapping-only-51154408.md`). Both
of main `0b88244` are in the engine's working tree, not committed then. Over the suite at `0b88244`: 770
pass, none fail (skipped: 25 times, 24 `keep`, 23 store). Against the checker: 832 agree, none differ. All
70 examples pass, and the converted shadows give the same verdict and path on all 801 files. It found no
test of a name that only names itself through a nested or pasted union (its engine passed the suite with
that check broken); both of its cases are refused as `a only names itself`, in the checker's `cycles`
(section 8), and **in the suite since main `e8fe146`**. It also noted that a union pasted into itself
level on level doubles at each level; the engine drops literals it meets again, and loads what the checker
loads. The checker expands it in full (20 levels of two literals: 11 s), bounded by part 1's full size.
**Fixed in main `e8fe146`:** section 9 said "Each name counts once in a union", and section 14 makes a
standard type a name, but the checker counts a repeated standard type each time (`!str(/a{1023}/)`,
`!int`, `!int` is refused at 1,025) and a repeated entry once, and the engine agrees with the checker. The
user agreed (2026-11-14) that the text say an entry's name counts once; the ceiling paragraph now says a
type counts each time it is written (`{!|: [!int, !int]}` holds 2). Two tests pin it, in the checker's
`ceiling` (refused at 1,025) and `unions` (an entry's name twice, 1,024, loads). Suite: 846 tests (69
examples, 740 edge cases, 158 with a document added).

**Section labels, fixed in main `25bfb66`** (the user asked, 2026-11-15). `suiteyes.py`'s `section()`
guesses a test's section from the types it holds when its list names none, checking scalars before unions
and never giving 5, 6 or 8. All about 370 guessed tests were read against their refusal or result; 51 were
wrong (a `!|` form error said 4.4, `a: !a` said 14, the ceiling said 4.3, `!int(5:2)` said 4.4). They are
corrected by ID in `CORRECT`, and the writer stops if an entry there isn't written, isn't guessed, or
matches the guess. A test inside `!**`, `!*` or `<<` keeps that section. Only `from:` lines changed. Kept
as they are, on purpose: `{!|: [!float, !str]}` and the like, where the union only wraps a number test.
**Lesson:** `--check` must come first (`suiteyes.py --check SPEC SUITE`); written last, it was read as
nothing and the suite was rewritten instead of checked. The script now refuses that. The real check:
846 tests, none fail.

**Oyl NG: published names, stamps ignored, application types (2026-11-15).** Three of its mails, each
pushed with CI passing on all four jobs, each with the suite at `e8fe146` 797 pass, 0 fail (24 `keep`, 25
holding more, skipped):
- **Published names** (Oyl NG `d435018`; `mail/received/20261115-051810Z-@oylng--published-names-in-the-engine-a030f180.md`).
  The application gives the parser a lookup, by address or hash; all 23 store tests agree, and the checker
  at ai `eebafbf`, 859 cases, all agree. **Fixed in main `bc14dca`** (the user: "that's fine", 2026-11-15):
  the text now says every part between `/`s holds something, as the checker does; three tests, one per odd
  name, deliver strings with the file in the store (a `PUB` loosened to allow empty parts fails all three).
  It was: part 1 takes `x.org//a.yes`, `/a.yes` and
  `x.org/.yes` as global names. The checker's `PUB` needs every part, and the file name before `.yes`,
  non-empty, so none is published, and the engine agrees. Section 3.1 says only "a global name that ends
  in such a file name"; `/a.yes` would give `https:///a.yes`, with no host.
- **Section 3's two "may" options** (Oyl NG `7b4ff48`; `...-151653Z-@oylng--ignoring-a-stamp-and-the-table-handed-over-a8f6c626.md`).
  Stamps can be switched off, and the stream's table handed over as a tree. **Fixed in main `bc14dca`**
  (the user: "ok", 2026-11-15): the text now says "as one with no stamp". It was:
  "ignore a file's schema and read the document as it is" can mean strings only or as a document with no
  stamp, typed by the application's schema if there is one. The engine does the second: under strings
  only, a file stamped `loose: !any` gets past the application's schema, which section 15's "Ways past a
  stamp" is about. It suggests "as one with no stamp". No suite test covers either option; one would need
  a key, as `keep` marks its interface.
- **Section 12, application types** (Oyl NG `8c56408`; `...-172347Z-@oylng--application-types-section-12-in-the-engine-f91d052e.md`).
  `oylng_parser_bind`; code runs once per use, never on trial. **Open, for the user**, three points the
  draft doesn't settle, as the engine answers them: (1) through a chain `alias: !point`, only the nearest
  entry's code runs, so binding `alias` does nothing, and a union runs the chosen alternative's code, never
  the union's. **Fixed in main `6a116a6`:** the user chose
  the outermost bound name (2026-11-15: "the outer name takes precedence ... they choose a spot, not a
  point"); if it isn't bound, the next one in runs, and a bound union's name takes the place of its
  alternatives'. The engine does the opposite, so it needs changing; @oylng not told yet. (2) innermost first, in the order written.
  **Fixed in main `1a2815f`** (2026-11-24): the user had raised, 2026-11-16, that parts first might make a
  spot a point first; the agent answered that a chain is one value and a line three, and the user took
  that as settled ("I thought we just went thru this", 2026-11-24). Section 12 now says code runs for the
  values inside a value first, in the order the data has them, with `line: {a: !point, b: !point}`, and
  that `spot: *point` makes a spot shaped like a point without being one. Lesson: the agent asked "does
  that settle it?", the talk moved on, and the agent kept listing the item as open for eight days without
  asking again. (3) When code runs: **fixed in main `b2ae1b8`** (the user: "yes", 2026-11-24). The engine
  runs it once the whole document is typed. The agent first recommended requiring that, so a refused
  document runs no code; the user objected that it "effectively kills streaming" for a large document.
  Part 1, section 2, already lets an event interface deliver before reporting an error, and part 2,
  section 3, lets a parser type events as they arrive, so the agent changed its recommendation: section
  12 now fixes which calls and their order (the same everywhere for an accepted document), and lets code
  run once a value's type is fixed (read, and every union around it chosen) or once the document is
  typed. A parser may have run code for a document it then refuses, as with events; the root's code runs
  last, so all-or-nothing work goes there (`orders: [!order, ...]`). The engine's way is allowed. It suggests a suite key naming entries to bind with counting
  code, `calls: {point: 2}`, and says nothing needs it.
- **Section 13, emitting** (Oyl NG `8e1bdd0`; `mail/received/20261116-000932Z-@oylng--emitting-typed-data-section-13-in-the-engine-2d6b216e.md`).
  Its CI runs the suite at `25bfb66`; at `bc14dca` 800 of 849 pass, none fail. The emitter types each
  document with the schema and writes each scalar in the first spelling that reads back as the same type
  and value; checked by writing again every typed document of the draft (49) and the suite (395), block
  and flow. **Open, for the user**, from what it found: (1) under `{!|: [!date, !str]}` the string
  `2001-02-03` has no spelling, nor does `abcd` under `{!|: [!binary, !str]}`, since both types match a
  quoted scalar (section 4.1; the agent checked the text, as the checker delivers dates and binary as text);
  **fixed in main `36517b9`**: the user first called it "a given" (2026-11-24), then asked for the warning
  ("I would do that though. yes."). Section 9, after the `1.10` example, now says quotes don't keep
  `!date`, `!datetime` or `!binary` away, so a date-first union can't hold the string `2001-02-03` and an
  emitter refuses it, while `!str` first reads every date as a string; (2) "it refuses if it has none" (section 13)
  needs a search of the pattern to promise in full (`1.5` under `!float(/[0-9]+e-[0-9]+/)` needs `15e-1`);
  it suggests naming the spellings an emitter must try; (3) a scalar decides nothing above it except
  through an all-literal field, so an emitter needs no backtracking, which section 13 could say; (4) an
  object under `!any` can't come back, and is refused; (5) `t`/`z` in a time come back as `T`/`Z`, the
  same value. Section 13 writes `"3"` where the engine writes `'3'`; both read back. Suite idea: emitting
  tests (schema, typed events, the YAML expected or refused), and every typed test run as "written
  again, reads back the same".

**Oyl NG: chains, `!` names and part 1 of keep (2026-11-23)**
(`mail/received/20261123-062923Z-@oylng--chains-the-rule-and-keep-part-1-are-in-the-engine-08fb6c4e.md`).
CI runs the suite at `c5203b6`: part 1 365 of 365, part 2 801 pass, 0 fail (24 `keep`, 25 times held
otherwise). Chains by the outermost bound name are in (`11f6c4c`); in the Oyl NG session the user was asked
again and agreed ("this makes sense", 2026-11-23), and "the most specific bound name wins" was set aside,
since `shape` → `point` → `base` with `point` unbound has no ranking. `!` names are refused (`71051bf`).
Keep and together for part 1 (`6ed5628`, `3b5f1ba`); part 2's 24 keep tests wait on typing kept trees.
**Fixed in main `b74622d`** (the user: "go with your recommendations on all three", 2026-11-23); no
suite test, since neither checker models bindings or kept lookups:
- **A union reaching one entry through two names.** With `p` a mapping, `a: !p`, `b: !p` and
  `u: {!|: [!a, !b]}`, section 9 says the union "is `!p`", counted at its first place; the engine types a
  `!u` value through `u`, `a` and `p`, so `a`'s code can run and `b`'s never does. Section 9 now says a
  value goes the first way written.
- **Held, part 1, section 10.** "Close to what a parser that keeps references has in memory" holds only
  if `<<:` lines are kept as written: a chain of n merges holds about n, while resolving each mapping's
  merged pairs holds n²/2, which is full's count. Section 10 now says "keeps references, `<<:` lines
  among them".
- **Lookups through kept `<<:` lines.** r paths into the end of a chain of n cost r × n steps, which
  neither held (about n) nor full (about n², and 0 for a line naming `{}`) bounds. The engine builds the
  normal read's merged sets while full is within the limit, and past it budgets the stream's lookups at
  the limit in steps. Section 10 now says it is such a use: within full a parser can build the merged
  pairs once; past it, each lookup counts the `<<:` lines it follows "as a walk that saves nothing would",
  and a stream's lookups follow at most the limit. The agent chose that count so every parser refuses the
  same lookup.
  **Open: the engine past full** (`mail/received/20261124-181842Z-@oylng--the-engine-past-full-yes-it-accepts-what-the-count-cecea8fd.md`,
  read from Oyl NG `3b5f1ba`). It accepts lookups the count refuses, two ways. (1) A mapping's gathered
  keys answer later lookups for nothing: 100 paths `*m30:k` through 31 mappings that each merge the one
  before twice, at a limit of 1,000, count 30 each, so the count refuses the 34th; the engine reads all
  100. A chain of 100,000 with paths to `k0` counts 99,999 each, so the count refuses the 672nd at
  64 MiB; the engine read 10^6. (2) It looks in each mapping once per lookup, where the walk follows a
  mapping's lines each time it reaches it. For a missing key, `*m30:nope` counts 2^31 − 2 against the
  engine's 60, but a missing key is refused anyway (part 1, section 8.3), so only the reason differs. For
  a found key the count can differ too. @oylng's sketch, not built or measured: each kept mapping keeps the
  walk's lines through it, worked out by addition as full is; each gathered key keeps the count at which
  the walk first reaches it; a lookup adds its key's number, or the mapping's when the key is missing.
  8 bytes per gathered key and per kept mapping, one addition per lookup, nothing within full. The agent
  checked the four counts above and they hold.
  **When full is measured: fixed in main `635b24d`** (the user: "I agree", 2026-11-24). Section 10 now
  says "Where full, as it stands when the path is read, is within the limit". It was: the text didn't say
  when, so a parser resolving paths after reading the whole document would use full at its end, and differ
  from the engine on a document whose full passes the limit only after its paths. @oylng suggested it, as
  section 10 already counts replacements "when the new entry's key is read"; full is worked out by
  addition in reading order, so a parser that resolves late can still note full at each path.
  **The count is in Oyl NG `5c6e618`** (`mail/received/20261124-194237Z-@oylng--the-count-is-in-the-engine-three-small-test-pairs-2b216f29.md`),
  CI passing against main `635b24d`. @oylng sent three small pairs, each `keep: true`, `from: part 1,
  section 10`, tags `size merge table`: (1) 33 paths `*m30:k` through `mN: {<<: *mN-1, <<: *mN-1}` at
  1,000 accepted, 34 refused; (2) `t: {<<: *x, <<: *m10}`, 4 paths `*t:k2` at 10,000 accepted, 5 refused;
  (3) pair 2's table, `a: *t:k2` before `b: [*m10, *m10, *m10]` takes full past 20,000, then 9 items
  accepted, 10 refused. `draftcheck.py` now counts lookups (full as it stands; written keys, then lines
  from the last up, stopping at the first key found) and gives all six as @oylng says; the normal read
  refuses each for full. **The walk's order: fixed in main `def062b`** (the user: "I agree",
  2026-11-24). Section 10 now says the walk looks at a mapping's own keys, then its `<<:` lines from the
  last up, and stops at the first key found, with `t: {<<: *x, <<: *m}` counting 3 for `k`. It was: no
  order, so a walk following every line refuses pair 1 (2^31 − 2 a path) and one trying the first line
  first accepts pair 2 (1 a path). The six are K3CL/Y2M5, J4HE/VCU5, 42RY/4R5Y.
  **Checker bug, fixed in `draftcheck.py`, committed with this note:** `<<: *b` added only `b`'s remaining pairs, not those `b`'s
  own later lines replaced, though section 10 says a replaced key "still counts, in its mapping and in
  every reference to it". With `a: {k: v}`, `b: {<<: *a, k: w}`, `c: {<<: *b}`, the document's full is
  12, not 8, and held 5, not 1. 7SXP (limit 30) and J4HM (29) test it. The old checker fails J4HM and
  the four refused lookup tests. `draftcheck.py` now also checks, at each collection's end, that what it
  counted while reading equals the collection's size. 373 tests; part 2's 850 still pass.
  **The engine agrees** (`mail/received/20261124-203641Z-@oylng--7sxp-and-j4hm-pass-the-engine-counts-the-document-ffd3816f.md`):
  at main `def062b` and Oyl NG `5c6e618`, part 1's 373 pass, and read the same kept; part 2 801 pass, 49
  skipped, as before. J4HM is refused at 29 and 7SXP accepted at 30, so the engine counts the document as
  12; kept, it is accepted at 29, as only held applies. Oyl NG's CI still runs against `635b24d`.
  **Main `def062b` is pushed and tagged `v0.1.0`** (2026-11-24), for Oyl NG's 0.3.0
  (`mail/received/20261124-214114Z-@oylng--the-engine-s-0.3.0-waits-on-def062b-reaching-githu-225dfc42.md`).
  **Oyl NG `v0.3.0` is out** (`a1f15c5`; `mail/received/20261124-223801Z-@oylng--the-engine-s-0.3.0-is-out-against-yaml2-v0.1.0-0e637d90.md`),
  CI pinned to yaml2 `def062b` (`v0.1.0`), all four jobs passing on main and the tag: part 1 373 of 373,
  part 2 801 of 850 with none failing (24 skipped for typing kept trees, not built; 25 for a parser that
  holds times otherwise). Its future releases pin to a tagged yaml2.

**Two silent schemas, found 2026-11-16** (the user asked what `!spot: !point` means). (1) A table key
starting with `!`, plain or quoted, made an entry whose name has the `!`: with `!spot: !point`,
`--- !spot` looks for `spot`, finds nothing, and the document stays strings. **Fixed in main `c5203b6`:**
part 1, section 8.1, refuses a name that starts with `!` (the user: "ok", 2026-11-16), in
`draftcheck.py`'s `tableflow` and `tablemap`; part 1's 8THU and X65G became V4W4 and RQK6 with the `!` key
inside an entry, and QVU4, JDM9, 3GJP refuse it (365 tests). Part 2, section 8, now has the user's example:
the table isn't a document's schema, and an unstamped document whose keys are the table's names stays
strings (850 tests). The user first leaned to marking names with `!` where defined; the agent advised
against it once it checked that the table is part 1's and holds data too (`port: 80`, `*port`), and that
`!spot:` at the table's top would read as a type key, more so if the core team keeps `?` keys. (2) A type key whose type is a mapping, `m: {!point: !int}` with `point` a
mapping, loads, and no key can ever fit it. **Fixed in main `bd5f8ed`** (the user: "ok, I agree",
2026-11-24). Section 7 now says a type key's type must be one a scalar can fit, so `!point: !int` as a
key, and a union as a key with a mapping or sequence among its alternatives, are refused when the schema
is read; `schemacheck.py`'s `keytype` checks it, type keys under `!**` too. It was: `!point: !int` beside
`!*: !str` gave `{"a": "1"}` through `!*`, and `{!|: [!int, !point]}` as a key gave `{"5": "1"}`.
Five tests (25F7, JR6M, L4RX, ZZ27 refused; 4CT4 loads), 855 in all; the old checker accepts three of
the four refused. If the core team keeps `?` keys, that sentence goes, and `!point: !int` would mean keys
that are points. Inside a mapping, `!spot: !point` is an ordinary type key (section 7): any key that fits `!spot`
takes a `!point`.

**Covering note for the core team** (the user asked for a draft, 2026-11-05). It stays local until the
user says otherwise, in `Outtake/covering-note.md`, which git ignores. On 2026-11-11 the user asked for a
shorter one as a separate document: `Outtake/covering-note-short.md`, under 1,000 words against 2,667,
with the cut table and other details left to the long one. Its list of what is essential is
the agent's draft: the user hasn't ruled on it. The talk is confirmed, and the org's schema language
and plugin work bear on the ask and on part 2's name: see landscape.md, What the YAML org is doing now.
