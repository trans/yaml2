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
inside Oyl, and the Oyl project builds it, applying what it learned. The user will set
that up. The user expects it to beat 1.x parsers on speed, given the simplifications:
measure speed and size for the proposal. It needs the spec draft, or at least
[rules.md](rules.md), to build from. The agent suggested the 1.2-to-2.0 converter sit
in Oyl beside `oyl_upgrade`; not decided.

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
