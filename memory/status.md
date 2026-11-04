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
   and margin strings are parked for later. Left: patterns (the user wants to revisit
   them), then quote versus escape for `:` in paths and keys-only references.
2. **Whose name it is.** "YAML 2.0" is the next version number of a spec
   the yaml-spec group maintains. Work through that group, or publish
   independently and offer it to them? Can wait for a draft.
3. **Publishing.** `origin` is `trans/yaml2` on GitHub, public. The user added it and
   approved the first push of `main` and `ai` on 2026-11-04, with @oyl's figures in
   `landscape.md` and with `ai`'s history rewritten first to drop one private sentence.
   So the `ai` branch is public: write nothing private here. Ask before pushing
   again. No transcripts are kept in this repository yet, so `transcript.encrypt` can
   wait.

## Working with @oyl

Oyl is the user's YAML 1.2 parser and emitter in C, with YAML 1.1 and go-yaml
v2 dialects, an in-place 1.1 to 1.2 upgrade (`oyl_upgrade`), bindings, and
measurements on real files. It is the obvious place to test ideas here and
the likely reference implementation (not decided).

Oyl's notes are private. Read them in place, and bring only what the user has
cleared into this repository, which is public.
