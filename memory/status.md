# Status

*Updated 2026-11-03*

**Goal.** The user set it on 2026-11-03: design YAML 2.0, and fix a YAML
ecosystem that has become a minefield.

**Where things stand.** Nothing is designed yet: no spec text, no code on
`main`, no git remote. Background is in [landscape.md](landscape.md).

## Open, for the user

1. **The compatibility contract.** Comes first, since most other choices
   follow from it. Proposed, not decided: every YAML 2.0 document is valid
   in today's parsers and reads the same in 1.1 and 1.2 readers; a 2.0
   parser rejects whatever they would read differently. That breaks
   writers, never readers. The alternative is a clean break: free to fix
   the syntax, but no existing parser reads it. Merge keys (`<<`) are the
   hardest case for the proposed contract.
2. **Whose name it is.** "YAML 2.0" is the next version number of a spec
   the yaml-spec group maintains. Work through that group, or publish
   independently and offer it to them?
3. **Remote and visibility.** If the repository is public the `ai` branch
   is too; then also decide on `transcript.encrypt`.

## Working with @oyl

Oyl is the user's YAML 1.2 parser and emitter in C, with YAML 1.1 and go-yaml
v2 dialects, an in-place 1.1 to 1.2 upgrade (`oyl_upgrade`), bindings, and
measurements on real files. It is the obvious place to test ideas here and
the likely reference implementation (not decided).

Oyl's notes are private. Read them in place, and bring only what the user has
cleared into this repository.
