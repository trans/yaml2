# The rules of YAML 2.0

*Updated 2026-11-03*

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
- No references inside a `--- &` document. Without chains there is no billion
  laughs: output is at most quadratic and no size limit is needed. Layered
  bases are written at the use site: `<<: [*rails, *base]`.

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

## YAML Schema

The user's term, 2026-11-03: the optional layer that types the data. The user
calls it the real trick: Ruby and others still serialize, through schemas.

**A schema is a typed shadow of the document** (the user's idea, 2026-11-03,
"something to that effect"; the user isn't sure it's enough; the agent
recommends it over reusing JSON Schema; not decided). It mirrors the document,
with each value replaced by its type:

```yaml
a: !int
b: !str
c: ![int*]
```

The agent's proposals, not yet answered:

- **It types; it doesn't validate.** Real JSON Schemas are 86% shape and 6%
  validation (landscape.md), so dropping validation is most of the
  simplification. Ranges and patterns stay the app's job.
- **No new syntax.** With tags out, `!` is an ordinary character, so `!int` is a
  plain string and the parser knows nothing about schemas. In a schema, a value
  starting with `!` is a type; any other value is a literal that must match,
  which gives discriminators (`kind: circle`).
- **Many or fixed:** `[int*]` is any number, `[int, str]` is exactly those two.
- **Optional:** `!int?`.
- **Arbitrary keys:** a type as the key, `!str: !int`.
- **Named types** live in the schema's `--- &` document and are written
  `!service`. The schema layer resolves them, not the parser, so recursive types
  work although `--- &` documents can't hold references.
- **Alternatives** (`!str | ![str*]`) are chosen by shape or by a literal, never
  by how text looks, and at most one may be a scalar. All 117 scalar unions in
  the sample include string, so each is simply `!str` in 2.0.
- **Schemas name types; app code binds them to classes.** A schema must never
  name a class to build, or `!ruby/object` comes back by another door.
- **Delivery:** `--- !` carries a shadow for the documents after it, and an app
  supplies one by prepending it, as with `--- &`. The app's schema wins.
- **JSON Schema stays a source:** its common part could be converted to shadows
  mechanically, so SchemaStore's work isn't lost.

Still to design: dates and other exact spellings, null, pairs back to a map,
set, ordered map, binary.
