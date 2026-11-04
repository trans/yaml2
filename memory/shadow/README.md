# Typed shadow experiments

*Updated 2026-11-04*

Does a typed shadow carry a full real format? `github-workflow.shadow` is
GitHub's workflow format, written from SchemaStore's `github-workflow.json`, and
`compose.shadow` is Compose, written blind from `compose-spec.json`. `shadow.py`
types a document with a shadow. `compare.py` runs both on real files and on
damaged copies. PyYAML's BaseLoader stands in for a 2.0 parser, since it reads
every scalar as a string; nothing here parses real 2.0 syntax.

To repeat it, with jsonschema installed:

    python3 compare.py workflows github-workflow.json ~/Projects ~/.config
    python3 compare.py compose compose-spec.json DIR

## Results: GitHub workflows (2026-11-03)

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

Caveats: mostly the user's own files. Three fixes came from these runs, so the
agreement is partly fitted: `type` on an input is optional, `secrets` takes
`inherit`, and matrix `include` items are mappings.

## Results: Compose, written blind (2026-11-03)

No Compose file was looked at before the run, and the shadow wasn't changed
after it. Reading the schema forced two additions first: prefix keys (`x-*`) and
any key with an empty value (`!str?`). The second was later replaced by
`!str: !x | ''`, with the same results.

- **Real files:** 313 unique, 311 of them public, from GitHub code search (not
  committed; a search sample, not a random one). 310 agree with the schema: 308
  accepted, 2 rejected. All 3 others are `pgdata: null`, which the schema takes
  and the shadow doesn't, since `null` is text under Rule 1.
- **Damaged copies:** 10,500 mutations, 6,962 rejected by the schema, 99.6%
  caught. All 26 misses are inside `x-` blocks, probably a harness quirk:
  aliases are shared in one tree and copied in the other. Not checked.
- **Merge syntax:** on 2026-11-04 the two list merges became two lines each, and all
  65 lines in both shadows became `<< *a`. Output is identical before and after, on
  the workflows and the 311 public Compose files. The prototype now refuses `<<:`,
  and a `<<` that isn't first.
- **Typing:** 26,083 strings, 500 empty, 4 booleans. The schema allows a string
  wherever it allows a number, so agreeing with it is easier than for workflows.
- **Mines:** YAML 1.1 changes 22 values in these files: `0755` to 493, `OFF` to
  false, `0.50` to 0.5. All stay as written under Rule 1.
- **Size:** 9.4 KB against 22.0 KB of compact schema without its documentation.
- **Merge:** 63 uses of `<<` across both shadows, all at the top of an entry.

## Notation since (2026-11-04)

Both shadows were converted to `!a | !b`, bare literals and `[!x, ...]`, and
limits (`!int(0..100)`) were added, with `x-*` replaced by `!str(/^x-/)`. Every
result above came out the same. The schema language in `rules.md` is current;
results above were first produced with the older notation.

## What the tests changed

See rules.md, YAML Schema.
