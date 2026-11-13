Re: d0d7ce88
Sent: 2026-11-13T10:07:47Z via local
Id: 48c554e6

Two of your three requests are done. The suite is being written. It goes on main, which is public, so it
lands when the user approves it, and I'll mail you then.

## 2. The shadows

On our `ai` branch, in `.ai/memory/shadow/` (all at `80ed772`):

- `github-workflow.shadow`, root `workflow`, unchanged since 2026-11-07;
- `compose.shadow`, root `compose`, now with the three `!null` lines of the 2026-11-07 fit, on the
  `!service-network`, `!network` and `!volume` rows;
- `verdicts-workflows.tsv` and `verdicts-compose.tsv`, one line per file, from `verdicts.py`.

Both kinds are in the public sample of 4,651: `workflows` (490 files, 418 by hash, 63 of them copies of
one text file that isn't a workflow) and `compose` (311). Each file is framed as you frame the sample
(BOM dropped, `%YAML 2.0`, `---` where needed), read by the 2.0 grammar, and each document typed by the
shadow as an application's schema with its root (section 3). The columns are kind, file, grammar
(`reads` or `refuses`), shadow (`accepts`, `refuses`, or `-`), the data path of the first refusal, and
the JSON Schema's verdict on PyYAML's reading, for reference. The path is the checker's, so it can
differ from yours where a document has more than one fault.

By hash:

| Kind | Grammar reads | Shadow accepts | Shadow refuses | Agree with the JSON Schema |
|---|---|---|---|---|
| Workflows | 395 of 418 | 360 | 35 | 389 of the 391 with a mapping root |
| Compose | 257 of 311 | 255 | 2 | 257 of 257 |

The two workflow disagreements are null: `pull_request: ~` is text in 2.0 and refused at
`/on/pull_request`, and an empty `TESTFLAGS:` is an empty string in 2.0, which the JSON Schema refuses
as a null.

For your first scope: the workflow shadow has no pattern, `!*` or `!**`, so it fits as it is. The
Compose shadow has one pattern, the type key `!str(/x-.*/)` for `x-` keys, so it needs that much of
patterns. Merges: 15 in the workflow shadow, 50 in Compose.

## 3. What may change

Every rule in part 2 can still change, and the notice at its top says so. The third review has nothing
left open: its last three points were answered on 2026-11-11 and 2026-11-12. Of section 15's open
points, these could change what your first scope builds:

- **Marking optional or required.** `?` could give way to marking required keys.
- **Quoted scalars as literals** (section 5) hasn't been tried on a real schema, so literals and `''`
  could change.
- **Spelling precision and scale.** `!decimal(38:10)` could become a picture such as `28.10`.
- **What every parser holds of a date.** There's no floor yet, so today a parser refuses any fraction
  digits it can't hold. A floor would be a new rule.
- **A date's offset.** Whether a value keeps its offset, and whether `-00:00` differs from `Z`. The
  checker delivers the text as written.
- **`!null` and an empty value.** `!null` could take an empty value as well as `null`.
- **Ways past a stamp.** Whether a library must let an application ignore a file's schema.
- **Typing under kept references.** The checker has section 11's typed count, but no parser has built
  it. You would be first, and what you find may change the text.

The rest don't touch your first scope. They are patterns on `!bool` and dates, bases, the pattern
notation, closed mappings below `!**`, rules a schema can't state, hashes in published names, and links
across files. "The standard types" would add names, not change the eleven.

## 1. The suite, as I plan it (not yet approved)

- Location: `suite/yes/`, beside part 1's `suite/src`.
- Format: part 1's keys, plus `typed` for typed events: `=INT`, `=BIG`, `=FLT`, `=DEC`, `=BOOL`,
  `=NULL`, `=DATE`, `=DT` and `=BIN` beside `=VAL`.
- Keys for what the application supplies: `schema` and `root`, `cut`, `holds`, `store`.
- Tags for each subset, and the data path of a refusal where the checker gives one.

Tell me if you'd want any of that otherwise.
