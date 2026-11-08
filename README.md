# A proposal for YAML 2.0

This is a proposal to the YAML core team, not the YAML specification. "YAML" and its
version numbers are theirs.

## Why

The same YAML file can give different data depending on what reads it:

```yaml
country: no
version: 1.10
mode: 0755
```

PyYAML and Psych read `country` as `false`, and go-yaml v3 reads it as `"no"`. All three
read `version` as the number 1.1 and `mode` as 493. Parsers also disagree on merge keys,
repeated keys and tabs, and a file can't say which behaviour it expects.

## The idea

Simplify YAML until there is one way to read a stream. Then the application, or a
schema, decides what the text means.

```yaml
%YAML 2.0
--- &
defaults: {retries: 3, timeout: 30}
---
name: build
version: 1.10
country: no
job:
  <<: *defaults
  timeout: 60
```

```json
{"name": "build", "version": "1.10", "country": "no", "job": {"retries": "3", "timeout": "60"}}
```

- **Everything is a string.** Types come from the application or a schema, never from a
  parser guessing by how text looks.
- **A stream says what it is.** It starts with `%YAML 2.0` and `---`, and a 2.0 parser refuses
  anything else. PyYAML, Psych and go-yaml v3 refuse a 2.0 stream too, but not every 1.x
  parser does: npm `yaml` warns and reads it as 1.2.
- **Reuse is explicit.** Definitions live in a table, `--- &`, that is never delivered.
  References are paths into it, and they replace anchors and tags.
- **Merge is part of the language**, for mappings and sequences.
- **Keys are strings**, each one once, and their order is kept.
- **One size limit** stops a small file from expanding into a huge one.
- **JSON is a subset** once `%YAML 2.0` and `---` are on top, apart from repeated keys, a lone CR
  between tokens, a tab before the value or on a line after it, and a lone surrogate escape. A small
  schema restores JSON's types.
- **A schema is a shadow of the data**, and it is optional. Its base form is the data's keys and
  structure with a type where each value would be. Table definitions, recursion and the key globs
  `!*` and `!**` compress that form.

The grammar has 58 productions. YAML 1.2 has 211, written at a finer grain, so the
comparison is rough.

## What it costs

This is a clean break. Of 4,651 public YAML files, 3,418 read as written once the first two
lines are added. The rest need
converting, and no converter exists yet. `spec/yaml-2.0.md`, section 13, lists every change
from 1.2, and section 13.1 what they cost.

## Status

- **The language:** Draft 1 is in [`spec/yaml-2.0.md`](spec/yaml-2.0.md). Section 14 lists
  what is still open.
- **YAML Easy Schema (YES), part 2:** Draft 1 is in [`spec/yaml-easy-schema.md`](spec/yaml-easy-schema.md). Section 15
  lists what is open.
- **Reference parser, test suite and converter:** not written yet.

## Checking it

The draft's examples and edge cases run through a small checker built from the grammar. It
is a test of the draft, not a reference parser.
It's on the `ai` branch, with the working notes behind each decision and the measurements
on real files:

```sh
python3 -I memory/draftcheck.py spec/yaml-2.0.md
```

Comments are welcome as issues.

## License

© 2026 Thomas Sawyer. The spec and this README are under [CC BY 4.0](LICENSE). The code on
the `ai` branch is under the MIT license.
