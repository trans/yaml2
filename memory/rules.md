# The rules of YAML 2.0

*Updated 2026-11-04*

The design, rule by rule, as the user sets them. Keep the user's wording for
each rule, and keep what the agent derived from it marked as such until the
user confirms it.

**Clean break.** The user chose this on 2026-11-03, over a subset that today's
parsers could read. YAML 2.0 need not be readable by existing parsers.

**The aim.** The user, 2026-11-03: simplify YAML as much as we can. The app
then interprets the data as it sees fit, or a YAML Schema types it.

## Rule 1: all scalars are just strings

The user, 2026-11-03.

Confirmed by the user, 2026-11-03: types come from the app or a YAML Schema,
never from the document.

Tags: the user doubts they're needed, since the schema handles typing
(2026-11-03). Out unless a need turns up. `%TAG` goes with them. Apps that
use tags as syntax (CloudFormation `!Ref`, GitLab `!reference`, Home
Assistant `!include`) would have to use ordinary mappings instead.

Follows from it (the agent's reading, not yet confirmed):

- No implicit typing. `no`, `on`, `0755`, `22:22`, `1E-12`, `2001-12-14`,
  `~` and `null` are all text.
- Quoting doesn't change the value: `42`, `"42"` and `'42'` are the same
  string. Quotes only decide which characters can be written.
- Scalar keys compare as strings: `1` and `"1"` are the same key.
- The data model so far: string, sequence, mapping.
- Cost: JSON stops being a subset in meaning. `{"a": 1}` still parses, but
  the value is the string `1`, and a JSON to YAML 2.0 to JSON round trip
  loses types unless something supplies them.

Probably, the user said on 2026-11-03: `key:` is the empty string, and the app
or schema decides what that means. Watch for whether a null value turns out
to be needed.

## Reuse: merge and definition documents

All 2026-11-03. The user answered "I think so" to definition documents
replacing `&` on nodes, to no references inside them, and to `:` as the
separator.

**Merge stays**, as far as the user can see: it has proven too useful to
remove. The user's view is that YAML 1.2 dropping it is probably part of why
nobody has fully adopted 1.2.

**References are paths, not names** (the user's idea). Every node already has
an address, so `&name` is a second naming system. Anchor names go.

**Backward only** (the user chose). The consumer never waits, a bad reference
fails at its own line, and forward references could still be allowed later
without breaking any file.

**Definition documents** (the user's idea). Only a document opened with
`--- &` can be referenced:

```yaml
--- &
defaults:
  adapter: postgres
versions:
  app: 1.4
---
development:
  <<: *defaults
  image: *versions:app
```

- Every reference, not just merge, targets an earlier `--- &` document. Any
  other `&` is an error, so 1.x anchors fail loudly.
- In a `--- &` document the only reference allowed is `<<` at the top of an
  entry, merging earlier entries (the user, 2026-11-03, which refines "no
  references inside"). Nothing deeper. A merge there only combines keys already
  written, so no entry can outgrow the file, and a merge nested under a new key,
  which is what doubles, stays banned.
- **Corrected 2026-11-04:** this makes growth quadratic, not small, so "no size
  limit needed" was wrong. A 1 MB file with a 500 KB entry and 100,000 `- *a` lines
  expands to about 50 GB. A limit on expanded size, or nodes shared in memory,
  is probably still needed. The user is concerned about this and wants to revisit.
- Data documents can use `<<` anywhere: what it points at holds no nested
  references, so each use adds at most one entry.

**Path syntax** (the user chose `:`). Fewest clashes (landscape.md): keys
holding `:` in 1 of 2,995 files, `/` in 19, `.` in 160. It needs no new scanner
rule, since a plain scalar already ends at `:` plus a space. The user's
refinement: only a single `:` separates, so `Fn::Sub` is one key and only
`foo:bar` needs quoting or escaping.

Not confirmed (the agent's terms):

- Quote rather than escape: `*a:"foo:bar"`. A quoted segment is a whole key,
  with the same quotes as scalars. It also covers spaces and flow characters,
  so no second escape scheme is needed.
- A `--- &` document is a mapping and is never delivered as data, which replaces
  Compose's `x-` keys and GitLab's hidden jobs.
- It stays in scope for the rest of the stream, so several documents can share
  it, and prepending one shares definitions across files with no include
  feature.
- `<<` becomes an indicator like `-`, since in 1.1 it is an implicit type, which
  Rule 1 ends. `"<<"` is the literal key.
- A reference names exactly one node, as a copy, so the data stays a tree. A
  query (YPATH proper: wildcards, filters, many nodes) is for tools, and is a
  later question.
- Keys only, no sequence indices: `*steps:0` would still resolve after someone
  inserts a step, to the wrong one. Reuse in sequences works (`- *checkout`).
- A reference can't be a key.
- Cost: the upgrade moves text. A base that is also real data moves out and
  stays as `web: *web`.

Dropped: a bare `&` on nodes (`defaults: &`). It kept the parser's hint of what
to retain, but definition documents do that with fewer rules.

## How a file says it is 2.0

**`%YAML 2.0` is required** (the user chose, 2026-11-03), and can be relaxed
once 2.0 has taken over; dropping it then breaks no file. Without it a clean
break reopens the original mine, since an old parser reads a 2.0 file silently
and wrongly. Tested 2026-11-03 on PyYAML, libyaml and Psych: `country: NO` with
no directive reads as false in all three, and `%YAML 2.0` is refused in all
three.

Not confirmed (the agent's terms): it goes on the first line, `---` isn't needed
after it, and a 2.0 parser treats a file without it as not 2.0, refusing it or
handing it to a 1.x mode.

## Keys

Agreed by the user, 2026-11-03:

- Keys are strings only, and `?` goes.
- A duplicate key is an error, including `1` and `"1"` in one mapping.
- A Hash with non-string keys is written as a sequence of pairs, and a schema
  brings it back: `- [[1, 2], origin]`.
- A reference key (`*foo:`, the user's idea) stays an error for now. Allowing it
  later breaks no file.

Why: keys then fit every language's map. Only Ruby gained from the old form.
Tested 2026-11-03: Psych round trips such keys, PyYAML refuses them, a JS object
flattens `[1,2]` to `"1,2"`, and a JS `Map` can't find an equal array. A stray
`{{ x }}` also becomes an error instead of a mapping with a mapping for a key.
Evidence is in landscape.md.

Key order, agreed by the user, 2026-11-04 ("if it is common then why bother" with
`!omap`): 2.0 guarantees it. A parser keeps mappings in document order and an
emitter never sorts them. Proposed consequences, not yet answered:

- A native map can still lose it: a JS object moves number-like keys first, and Go
  maps are random. So the guarantee is on the parser's API (events, tree, an ordered
  map), and a conversion to a native map is the caller's choice.
- Merge needs a defined order now. Proposed: `<<` puts its keys where it is written,
  a key written locally keeps its own place and value, and in `<<: [*a, *b]` the
  earlier source wins.

## YAML Schema

The user's term, 2026-11-03: the optional layer that types the data. The user
calls it the real trick: Ruby and others still serialize, through schemas.

**A schema is a typed shadow of the document** (the user's idea, 2026-11-03,
"something to that effect"; adopted over reusing JSON Schema, the user's "sure" on
2026-11-04, to be confirmed). It mirrors the document, with each
value replaced by its type:

```yaml
a: !int
b: !str
c: ![int*]
```

Tested 2026-11-03: see [shadow/](shadow/README.md). On GitHub workflows it
agreed with the JSON Schema on all 131 real files and caught 91.9% of the damage
the schema catches, 99.3% with three small app bindings. On Compose, written
blind, it agreed on 310 of 313 and caught 99.6%. Notation below is what those
tests settled on, all the agent's proposals, not yet answered:

- **It types, and a scalar type can carry a limit.** The agent first left all
  checks to the app; the user pushed back (2026-11-04, `!int[0,100]` "or whatever")
  and was right, since an app binding works in one language and a limit in the
  schema works in all of them. Spelling, tested: `!int(0..100)`, `!float(0..1)`,
  `!str(1..)` for length, `!str(/regex/)`. It must be `..`, not a comma or
  brackets: `[int[0,100], ...]` won't parse, and `[int(0,100), ...]` silently
  splits into two items. Not all checks belong here: see the gaps below.
- **Regex is the risky part.** Dialects differ, so one pattern can match differently
  by language, and a slow pattern in a document's own `--- !` is an attack. The
  agent proposes a defined linear-time subset. Most real patterns are simple
  (`\.ya?ml$` is the commonest). The user, 2026-11-04: regex may not be needed at
  all; something simpler like PIC, or glob-like, may be enough. To explore.
- **No new syntax.** With tags out, `!` is an ordinary character, so `!int` is a
  plain string and the parser knows nothing about schemas. A value starting with
  `!` is a type expression; any other value is a literal that must match.
- **`!` marks a type on every part; bare text is a literal** (the user's `!a | !b`,
  2026-11-04): `!a | !b`, `!str | inherit`, and enums need no quotes: `read | write
  | none`. `''` is the empty literal. A literal can't contain ` | `.
- **Sequences are real sequences, and `...` means repeat** (the user's idea,
  2026-11-04, replacing `*`, which already means a reference). `[!int, ...]`, or in
  block form `- !int` then `- ...`, is any number, none included. `[!int, !str]` is
  exactly those, `[!str, !int, ...]` a string then ints. Items can be inline
  mappings. `...` must not start a line at column 0, where it ends a document.
- **Mappings are real mappings:** block, or flow as `{!str: !int}`. Inside `|` a
  mapping must be named, since `: ` can't sit in plain text, and a sequence must
  come last, since a value can't start with `[` and go on.
- **Optional is on the key, and means absent or empty:** `name?: !str` (the user:
  "might be ok", 2026-11-03). It can't go
  on the value, since an inline mapping has nowhere to put it (changed by the
  test). An empty value types as None, so null exists only through a schema: this
  mostly answers the null question. Spelled `null` is text under Rule 1, which
  failed 3 of 313 Compose files (`pgdata: null`); an upgrade rewrites it to
  `pgdata:`. Still no sign that a null value is needed.
- **Arbitrary keys:** a type as the key, `!str: !int`, with `| ''` if a value may
  be empty: `!str: !volume | ''`. Mappings are otherwise closed. `!str?:` was
  tried in the Compose run and dropped: `| ''` gave the same results on all 313
  files with no new syntax.
- **No prefix keys.** A limit on the key type does it: `!str(/^x-/): !any`. In 311
  public Compose files `x-` keys are always top level, which `--- &` replaces, so
  few 2.0 shadows should need even that.
- **An unknown type is an error in the schema**, reported when it is loaded, so
  `!stirng` is caught even if no document reaches that field. Every name is built
  in (`str`, `int`, `float`, `bool`, `any`) or in the table, so an app's own type
  is declared there (`date: !str`). This keeps a schema checkable on its own.
- **Named types** live in the schema's `--- &` document, which is a lookup table,
  as in a data file. `!flag` looks up the key `flag` there. `*flag` would paste the
  value in, and the parser would do it; `!flag` is a plain string to the parser,
  and the schema layer resolves it and keeps the name. `*` can't replace it: a
  reference is a whole value, so it can't sit in `![job*]` or `!str | job`, it
  can't nest in a `--- &` document, and recursive types would never end. Use `<<`
  to paste a shape and `!name` to use a type. A key above the `---` is a name;
  below it, a key in the document. That takes reading with care: the user read
  `flag: !str` as a key with a string value (2026-11-03), which is what it
  literally is, and found it a bit confusing.
- **Alternatives** are chosen by shape, never by how text looks: at most one
  scalar type, at most one sequence, and mappings told apart by required keys and
  literals. All 117 scalar unions in the sample include string.
- **A name is where app code attaches.** A field that is `true` or `${{ x }}` is
  two scalars, so it's a named string (`flag: !str`), and the app binds code to
  `flag`. That recovered nearly all of what patterns check, with no regex in the
  schema. An unbound name stays a string. It needs no rule of its own: it's just a
  named type.
- **Schemas name types; app code binds them to classes.** A schema must never
  name a class to build, or `!ruby/object` comes back by another door.
- **`--- !` marks a shadow** (the user asked how a schema is identified,
  2026-11-03). `--- &` is the lookup table, `--- !` a shadow, `---` data, and only
  data is delivered. A schema file is a table and a shadow; a stream can carry both
  before its data, and a shadow types the `---` documents after it. One table per
  stream: `!job` and `*defaults` look in the same place. An app can supply a schema
  directly or by prepending it, and the app's schema wins. It also eases the "above
  or below the line" wart. The prototype reads `--- !` in a schema file; a shadow
  and data in one stream isn't tested.
- **Open:** how a data file on its own points at its schema, for editors and
  generic tools. Today that's a comment or file name matching.
- **JSON Schema stays a source:** its common part could be converted to shadows
  mechanically. Not tested.

Warts: a literal key ending in `?` or starting with `!` can't be written in a
schema. 78% of the workflow shadow's keys are optional, so `?` is noisy, and
marking required keys instead may read better.

**Objects need nothing new** (`shadow/objects.py`, 2026-11-03). Named types with
app bindings rebuilt classes, a union of classes told apart by a literal, a set,
a date, binary, and a map with tuple keys from pairs. Unbound, the same document
stays plain data. This is how a language serializes through a schema.

**What JSON Schema can do that this can't** (2026-11-04; counts are keyword uses in
the five schemas in landscape.md).

Of its 214 value checks, 197 now have a spelling: ranges and non-empty scalars 59
(`!str(1..)`, all 35 `minLength` are 1), non-empty sequences 40 (`[!x, !x, ...]`,
no new syntax, all 40 `minItems` are 1), patterns 48, and formats and
`uniqueItems` 50, which need standard names (`!uri`, `!set`). Not covered, 17:
`maxItems` 7, `minProperties` 6, `dependencies` 3, `maxProperties` 1.

Still missing:

- Rules across keys: `not` 26, `if` 12. "Not both", "at least one of" and "if this
  then that" can't be written, except a literal choosing between alternatives.
- Documentation. It isn't needed to load or type anything; only editors use it
  (hover text, completion). The real problem is that a shadow gives each field one
  slot, its type, where JSON Schema gives an object. In the five schemas: 1,043
  descriptions, 162 titles, 61 defaults, 9 examples, 4 deprecations, so nearly all
  prose. A comment directly above a key is its description (the user's "sure",
  2026-11-04), as with RDoc or YARD: parsers still discard comments, and only doc
  tools keep them. No tool built.
- Defaults aren't in the schema language (the user's point, 2026-11-04: merge does
  it in most cases). An author's default is a `<<` from a `--- &` entry: local keys
  win and missing ones fill in, visibly in the file, so the same bytes give the
  same data with or without a schema. A format's own default (GitHub's 360 minutes)
  is applied by the app, and is only mentioned in a comment. Merge is shallow, so a
  nested default takes its own `<<` at that level.
- Links across files: `$ref` to another file or URL. A shadow has one stream.
- Same-shape alternatives: two sequences, or two scalars, told apart by content.

Still to decide: whether the spec defines standard names (`date`, `binary`, `set`)
with exact spellings, so that languages agree.
