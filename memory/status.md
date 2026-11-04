# Status

*Updated 2026-11-04*

**Goal.** The user set it on 2026-11-03: design YAML 2.0, and fix a YAML
ecosystem that has become a minefield.

**Where things stand.** The user is setting the design rule by rule; the
rules are in [rules.md](rules.md). The user chose a clean break on
2026-11-03, so 2.0 need not be readable by existing parsers. No spec text,
no code on `main`. Background is in
[landscape.md](landscape.md).

## Open, for the user

1. **The design's open points:** marked as such in [rules.md](rules.md). Merge, the
   size limit, the syntax cuts and how schemas are named were settled on 2026-11-04,
   and margin strings are parked for later. Patterns are proposed as I-Regexp. Left:
   quote versus escape for `:` in paths, and keys-only references.
2. **Whose name it is.** The user's plan (2026-11-04): make this as complete as
   possible, then present it to the YAML core team. If they reject it whole, decide
   where to take it then. If they take it up, they'll hammer out the final details.
   So I-Regexp and other proposals needn't be settled first. See landscape.md, How the
   core team takes proposals. Until they answer, call it a proposal for YAML 2.0.
3. **Publishing.** `origin` is `trans/yaml2` on GitHub, public. The user added it and
   approved the first push of `main` and `ai` on 2026-11-04, with @oyl's figures in
   `landscape.md` and with `ai`'s history rewritten first to drop one private sentence,
   and a second push of `ai` the same day. So the `ai` branch is public: write nothing
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
