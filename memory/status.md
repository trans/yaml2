# Status

*Updated 2026-11-05*

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
section 10 and how files join are open for the user ([review.md](review.md)).

**YAML Schema, part 2.** Draft 1 is `spec/yaml-schema.md`, in `bf225ba` (2026-11-05), and its
section 15 lists what is open. The user chose an answer to "wherever this occurs" (see
[rules.md](rules.md)). The agent added these, and the user hasn't ruled on them: a quoted
scalar in a schema is always a literal, a reference is typed where it's used, `!int`,
`!float`, `!bool` and `!null` match plain scalars only while the others take any scalar, and
every named type reachable from the root is checked. `schemacheck.py` tests the draft: 37
examples and 144 edge cases pass, and breaking 21 new rules on purpose fails a test each time.
Not done yet: the same for the older rules, and running the two real shadows through it. @oyl
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
   and margin strings are parked for later. Patterns are proposed as I-Regexp. Left:
   whether to refuse leftover tags (the `!` rule), which the user wants left as an open
   question for the core team, with pros and cons in section 14.
2. **Whose name it is.** The user's plan (2026-11-04): make this as complete as
   possible, then present it to the YAML core team. If they reject it whole, decide
   where to take it then. If they take it up, they'll hammer out the final details.
   So I-Regexp and other proposals needn't be settled first. See landscape.md, How the
   core team takes proposals. Until they answer, call it a proposal for YAML 2.0.
3. **Publishing.** `origin` is `trans/yaml2` on GitHub, public. The user added it and
   approved the first push of `main` and `ai` on 2026-11-04, with @oyl's figures in
   `landscape.md` and with `ai`'s history rewritten first to drop one private sentence,
   a second push of `ai` the same day, and a third of both, with the spec, README and
   licenses, also that day, and a fourth of both, with the review applied, also that day, a fifth of both on
   2026-11-05, with `2d5a90d`, a sixth of both that day, with `bf225ba`, a seventh of both that day, with `7689ea6`, an eighth of both that day, with `d645ce9`, a ninth of both that day, with `cc84227`, and a tenth of both that day, with `e1eef1b`. The spec and README are CC BY 4.0, and the code on `ai` is
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
@oyl hasn't been told the Unicode minimum, the join rules or the required `---`, and needn't be yet.
