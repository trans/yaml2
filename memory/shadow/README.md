# Typed shadow experiment

*Updated 2026-11-03*

Does a typed shadow carry a full real format? `github-workflow.shadow` is
GitHub's workflow format, written from SchemaStore's `github-workflow.json`.
`shadow.py` types a document with a shadow. `compare.py` runs both on real files
and on damaged copies. PyYAML's BaseLoader stands in for a 2.0 parser, since it
reads every scalar as a string; nothing here parses real 2.0 syntax.

To repeat it, with jsonschema installed:

    python3 compare.py github-workflow.json ~/Projects ~/.config

## Results (2026-11-03)

- **Real files:** 131 unique workflows (580 before removing copies). Shadow and
  schema agree on all of them: 128 accepted, 3 rejected.
- **Damaged copies:** 10,500 mutations, of which the schema rejects 7,273. The
  shadow alone catches 91.9%. With three small app bindings (`expr`, `flag`,
  `number`) it catches 99.3%. Of the 53 left, 50 are deletions (mostly the only
  job, leaving an empty mapping).
- **Stricter:** the shadow also rejects 135 the schema accepts, mostly where the
  schema is open by accident (`runs-on` as any mapping, `$ref` siblings ignored).
- **Typing:** of 8,100 scalars, 8,001 stay strings, 95 are empty and 4 are
  booleans, before bindings. This format barely needs typing at all.
- **Size:** 5.8 KB against 20.6 KB of compact schema without its documentation.
  The shadow drops the lists of activity names, which accounts for part of that.
- **Keys:** 74 optional, 21 required.

## Caveats

One format. Mostly the user's own files. Three fixes came from these runs, so
the agreement is partly fitted: `type` on an input is optional, `secrets` takes
`inherit`, and matrix `include` items are mappings. A format written blind would
be a fairer test.

## What the test changed

See rules.md, YAML Schema.
