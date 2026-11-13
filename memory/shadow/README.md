# Typed shadow experiments

*Updated 2026-11-13*

Does a typed shadow carry a full real format? `github-workflow.shadow` is
GitHub's workflow format, written from SchemaStore's `github-workflow.json`, and
`compose.shadow` is Compose, written blind from `compose-spec.json`. `shadow.py`
types a document with a shadow. `compare.py` runs both on real files and on
damaged copies. PyYAML's BaseLoader stands in for a 2.0 parser, since it reads
every scalar as a string; nothing here parses real 2.0 syntax.

To repeat it, with jsonschema installed:

    python3 compare.py workflows github-workflow.json ~/Projects ~/.config
    python3 compare.py compose compose-spec.json DIR

`schema2.py` reads a schema with the real grammar, through `draftcheck.py`, and tests JSON as
an ordinary recursive schema (2026-11-05). It matched on all 994 SchemaStore files under
300,000 bytes and on 93 of 95 in JSONTestSuite; the other 2 are repeated keys. The two-line form with
`!**`, on all 1,015 files, is the current result (2026-11-07).

`current.py` runs a shadow through the current checker, `schemacheck.py`, against its JSON Schema. Its
results are below; those in the sections after it are from `shadow.py`, an earlier prototype.

## At `57407f1` (2026-11-13), file by file

For Oyl NG's part 2 work (its agent asked, 2026-11-13). `compose.shadow` now has the three `!null` lines of
the 2026-11-07 fit; `github-workflow.shadow` is unchanged, and nothing in either uses what changed since
(widths, `round`, date levels). `verdicts.py` writes one line per file, every copy included: the 2.0
grammar's reading, framed as Oyl NG frames the public sample (BOM dropped, `%YAML 2.0`, `---` where
needed), each document typed by the shadow as an application's schema with its root, the path it
refuses at, and the JSON Schema on PyYAML's reading:

    python3 verdicts.py workflows github-workflow.shadow workflow github-workflow.json DIR > verdicts-workflows.tsv
    python3 verdicts.py compose compose.shadow compose compose.json DIR > verdicts-compose.tsv

The files are the workflows and Compose kinds of the 4,651-file public sample (490 and 311 files; 418
and 311 by hash: 63 of the workflows are copies of one non-workflow text file). By hash:

| Kind | Grammar reads | Shadow accepts | Shadow refuses | Agree with the JSON Schema | Disagree |
|---|---|---|---|---|---|
| Workflows | 395 of 418 | 360 | 35 | 389 of 391 with a mapping root | 2 |
| Compose | 257 of 311 | 255 | 2 | 257 of 257 | 0 |

- **Oyl NG agrees on all 490 workflow files** (its agent, 2026-11-13, at `80ed772`, also under ASan and UBSan):
  the same verdict and the same refusal path on every file. Compose waits for patterns in the engine.
- The two workflow disagreements are the null ones from 2026-11-07: `pull_request: ~` (text in 2.0,
  refused at `/on/pull_request`) and an empty `TESTFLAGS:` (the JSON Schema refuses a null).
- On PyYAML's reading, Compose now agrees on 311 of 311, where it was 308.
- `compose.shadow` has one pattern, `!str(/x-.*/)`, for `x-` keys; `github-workflow.shadow` has none.
  Neither uses `!*` or `!**`. Compose has 50 merges, workflows 15.

## Through the current checker (2026-11-07)

To repeat it, with jsonschema and PyYAML installed:

    python3 current.py compose compose.shadow compose compose.json DIR
    python3 current.py workflows github-workflow.shadow workflow github-workflow.json DIR

| Files | Compared | Agree | Both accept | Both refuse | Only the shadow refuses | Only the JSON Schema refuses |
|---|---|---|---|---|---|---|
| Workflows, the original local set | 131 | 131 | 128 | 3 | 0 | 0 |
| Workflows, public, never run before | 398 | 396 | 365 | 31 | 1 | 1 |
| Compose, public | 311 | 308 | 306 | 2 | 3 | 0 |

- **Reading.** Files are read by PyYAML with quoted scalars marked, so that a file the 2.0 grammar refuses
  is still compared. Of the files compared, the grammar also reads 125, 391 and 257, and it gave the
  same verdict as PyYAML's reading on every one. Of the public workflows, 15 of 418 unique files don't
  parse under 1.x and 3 have no mapping at the root.
- **Workflows, public.** No earlier run used these, and they share no file with the local set. The only
  change to the shadow since they were downloaded moved its root into an entry.
- **Changes.** `github-workflow.shadow` loads as it stands. `compose.shadow` was refused until
  `!str(/^x-/)` became `!str(/x-.*/)`, since a pattern now matches the whole key.
- **All 5 disagreements are about null.** Three Compose files have `pgdata: null` or `default: null`,
  which the JSON Schema takes as `["object", "null"]`. The shadow, written before `!null` existed, has
  `''`. One workflow has `pull_request: ~`, which is the text `~` in 2.0. One has `TESTFLAGS:` empty,
  which the JSON Schema refuses as a null and which is an empty string in 2.0.
- **Fitted, not counted above.** Adding `!null` on the 3 lines in a copy of `compose.shadow`
  gives 311 of 311.
- **Full size.** `compose.shadow` is 10,163 bytes with a full size of 2,616, and `github-workflow.shadow`
  is 6,275 bytes with a full size of 1,575. Both are under 0.004% of the 64 MiB limit.

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
- **Merge syntax:** on 2026-11-04 the two list merges became two lines each. Output
  is identical before and after, on the workflows and the 311 public Compose files.
  The prototype refuses a `<<:` that isn't first, or that has anything but one
  reference.
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

## Roots and standard names (2026-11-04)

Each shadow's root is now a table entry (`workflow`, `compose`, `document` in
`objects.py`), picked with `root=`; bare `--- !` is gone. `!int` and `!float` take
JSON's spellings, and `!date`, `!datetime` and `!binary` are added. Both comparisons
came out identical. `read_stream` reads a stream with its own table and yields
`(name, value)` per document. It has been run on small examples only.

## What the tests changed

See rules.md, YAML Schema.
