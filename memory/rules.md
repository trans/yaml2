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
(2026-11-03). Node tags are out. The one need that turned up is a whole
document's name, `--- !name`, under YAML Schema. `%TAG` goes with them. Apps that
use tags as syntax (CloudFormation `!Ref`, GitLab `!reference`, Home
Assistant `!include`) would have to use ordinary mappings instead.

Follows from it (proposed, left open for the core team):

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
- Size limit: one total, the user's choice (2026-11-04, "set a total upper limit, and
  no matter what one stream has or is, if it passes that mem limit it errors out"),
  replacing the proposed 100 times `written`, which bounded growth but not memory: a
  1 GB file could add 100 GB. A parser counts the size of what it will deliver as it
  reads, 1 per node plus the bytes of each scalar, and a reference adds the full size
  of what it names, with no dedupe. Past the limit it stops with an error. It counts
  and refuses before allocating, since a real out-of-memory usually kills the process
  with nothing to catch; so the unit is this size, not RAM. The spec gives a default
  of 64 MiB, and an app may set it higher or lower (the user, 2026-11-04, "yes"). A refusal is loud, not
  different data, so a setting doesn't break "same bytes, same data". A big plain file
  counts too, and needs the app to raise it. A small file can reach the limit, so a
  service reading untrusted input should lower it. Shared nodes aren't the answer: a
  merge copies its key list anyway, see landscape.md. They stay a parser's choice.
  `-<<` can go at the top of a `--- &` entry too, since this stops doubling (the user,
  2026-11-04, "yes"), and nothing deeper. "Top" here means depth: it can go at any
  position among the entry's items. Several in a chain of entries can still double each
  time. The user and the agent left that to the size limit (2026-11-04): banning `-<<`
  in the table, or allowing one per entry, would stop it, but costs real use, and the
  limit refuses by adding up sizes, before allocating anything.
- Data documents can use `<<` at any depth: what it points at holds no nested
  references, so each use adds at most one entry.

**Path syntax** (the user chose `:`). Fewest clashes (landscape.md): keys
holding `:` in 1 of 2,995 files, `/` in 19, `.` in 160. It needs no new scanner
rule, since a plain scalar already ends at `:` plus a space. The user's
refinement: only a single `:` separates, so `Fn::Sub` is one key and only
`foo:bar` needs quoting or escaping.

Proposed, left open for the core team unless marked as the user's (see status.md):

- Verbatim keys, the user's idea after 1.x's `!<...>` (confirmed 2026-11-04: "works much
  better and rids us of the potential ambiguity"): `<...>` holds one key, taken
  literally, anywhere in a path. `*<a:foo:bar>` is one key,
  `*<a:foo>:bar` that key then `bar`, and `*a:<foo:bar>` `a` then that key. It replaces
  the agent's `*a:"foo:bar"`, which the user found made no sense, and doubling
  (`.deps::rocm`), which would make `*a:Fn::Sub` mean `Fn:Sub`. A ban on `:` in entry
  names was also tried and dropped ("Yuck! keys with colons"), so entry names can hold
  any key text. In GitLab, 21 of 126 real paths need it, all at the entry name:
  `*<.deps:rocm>:before_script`.
- A `--- &` document is a mapping and is never delivered as data, which replaces
  Compose's `x-` keys and GitLab's hidden jobs. Block or flow: the user preferred block
  only, but asked for a technical reason, and there wasn't one (2026-11-04), so a JSON
  object can be a table.
- A document name stays stricter than YAML's URI characters (the user, 2026-11-04): at
  the very least no `:`, which would let schemes back in and give one thing several
  names, and no `%` escapes. The agent first said escapes give one name two spellings,
  which the user rightly doubted: 1.2 decodes them (`%41` is `A`), and has them to write
  characters a tag can't otherwise hold. ASCII-only names were dropped the same day: "we
  can't do that. not fair to the chinese." So other scripts are written directly, using
  XML 1.0's name ranges (the agent's pick, no Unicode tables), which leaves escapes
  nothing to do, and `%3A` is refused "for the same reason `:` is". The other URI marks
  are open in section 14 of the draft.
- It stays in scope until the next `...`, so several documents can share it, and
  prepending one shares definitions across files with no include feature.
- Several `--- &` documents: the user chose, 2026-11-04. A stream's table starts empty,
  and `...` empties it (the user's idea, instead of per-document tables). Between `...`
  lines a later `--- &` replaces an entry it repeats, as a later `<<:` line does, and a
  repeat inside one `--- &` is refused, as in any mapping. References copy as they are
  read, so a replacement never changes an earlier document or entry. An entry may name
  the one it replaces, which extends it (the agent's addition, the user agreed the same
  day: it needs no rule, since references look backward and the old entry is still there).
  Two other ways were dropped: refusing every repeat, and each `--- &` replacing the
  whole table. `read_stream` in the prototype still gathers one table per stream.
- `<<` is an indicator like `-`, not a key: the user, 2026-11-04, "It's not really a
  key, is it." A parser never delivers it. So Rule 1 has no exception here: an
  indicator isn't a scalar, so quoting one changes nothing about any value.
- It keeps its colon: `<<: *a` (the user, 2026-11-04, reversing `<< *a` of the same
  day: "It's just makes it more obvious, even if it is not an actual key."). So one
  spelling. A plain `<<:` always merges and takes one reference, `<<: [*a, *b]` is an
  error, and `"<<":` is the literal key. CircleCI's `<< parameters.x >>` stays text.
- Sequence merge: `-<< *s`, raised by the user, accepted 2026-11-04 ("perfect", then
  "yes"). It replaces itself with the items of `s`,
  which must be a sequence. One token, a space, then a reference, so anything else
  stays text. Any position, any number: nothing can clash, and position is the point.
  Plain concatenation, no dedupe. No colon (the user, 2026-11-04), since items have none, and
  `- <<: *a` (an item that is a mapping with merged keys) then differs from `-<< *a`
  by more than a space. A shape check also tells them apart: `<<:` needs a mapping,
  `-<<` a sequence.
  In a `--- &` entry it goes at the top of the entry, as `<<:` does. Two `-<<` of the
  entry before double each time, unlike `<<:`, whose keys collapse, so the size limit
  above is what stops that.
- Flow collections, **proposed** (the user asked, 2026-11-04): both work, by the same
  rules, if flow stays, as proposed below. `{<<: *a, x: 1}` with `<<:` first, and
  `[-<< *s, x]` at any position. A reference ends at `,`, `]` or `}`, so a path key
  holding those needs `<...>` inside flow. `[<<: *a, x]` is
  a one-pair mapping item, as in 1.x, unless that form is cut below. Real use of either
  in flow: none (landscape.md).
- A reference names exactly one node, as a copy, so the data stays a tree. A
  query (YPATH proper: wildcards, filters, many nodes) is for tools, and is a
  later question.
- Keys only, no sequence indices (the user, 2026-11-04: fine for now, "it can alwasy
  be revisted"): `*steps:0` would still resolve after someone inserts a step, to the
  wrong one. A path through a sequence is an error, so allowing indices later changes
  no working file. Reuse in sequences works (`- *checkout`).
- A reference can't be a key: `*foo: x` stays an error for now, as agreed under Keys
  (2026-11-03). Real use: none in 4,164 public files parsed, 161 of them using
  references (2026-11-04). 1.x allows `*foo : x`.
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

Proposed, left open for the core team: it goes on the first line, `---` isn't needed
after it, and a 2.0 parser treats a file without it as not 2.0, refusing it or
handing it to a 1.x mode.

## Keys

Agreed by the user, 2026-11-03:

- Keys are strings only, and `?` goes.
- No limit on key length (the user, 2026-11-04). 1.x's 1024 limit only bounded lookahead,
  which flow keys needed. A 2.0 key is one line.
- A duplicate key is an error, including `1` and `"1"` in one mapping.
  Finding repeats must not grow with the square of the keys, even in a stream written to
  force it (the user, 2026-11-04). This limits growth, not technique: a parser may scan
  a short list and change method as a mapping grows, and a fixed-seed hash doesn't pass.
  The user asked on 2026-11-04 whether the cost of checking argues for replacing instead.
  It doesn't: replacing needs the same lookup, and merges need it anyway. Of 4,163 public
  files, 64 repeat a key, 51 of those with different values, one of them on purpose: see
  [landscape.md](landscape.md). PyYAML and Psych keep the last and go-yaml refuses, and
  that disagreement is the reason.
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
emitter never sorts them. Proposed consequences, left open for the core team:

- A native map can still lose it: a JS object moves number-like keys first, and Go
  maps are random. So the guarantee is on the parser's API (events, tree, an ordered
  map), and a conversion to a native map is the caller's choice.
- Merge order. The user on `<<` as the first key of a mapping: "I think so"
  (2026-11-04), replacing "where it is written". "Top" had two meanings: depth (the
  `--- &` rule) and position (this one). Why: a late `<<` already gives different
  values, see landscape.md. The user expects this to be debated, since it may be stricter
  than needed if the rule for each place is clear. It stays the proposed rule, and
  section 14 of the draft says so (2026-11-04).
  - Override in place: the user's "I am good with it" (2026-11-04). `<<: *base` (x,
    y), `name: a`, `y: 3` gives `x, y, name`. A mapping with `<<` is ordered as if the
    merged keys were pasted at the top and each local key then assigned. So merged
    keys always come before local ones, and a file can't say "name, then the
    defaults". Around it: merge a `head` entry first, or no merge.
  - Several sources: repeated `<<` lines, the user's choice (2026-11-04, "I think it
    makes more sense"). One reference each, all before any other key, no list form.
    Read top to bottom: a later line replaces a key in place, as a local key does.
    With a (p, q) and b (q, r) that gives `p, q` from b, `r`. Layering is `<<: *base`
    then `<<: *prod`. Two written keys that are the same are still an error; only a
    merged key can be replaced. This replaces `<<: [*a, *b]`, "the earlier source
    wins" and "a key in two sources is an error", all dropped the same day.

## YAML Schema

The user's term, 2026-11-03: the optional layer that types the data. The user
calls it the real trick: Ruby and others still serialize, through schemas.

**What it is** (the user, 2026-11-04): not needed to use YAML. Apps can take
responsibility for interpretation, and no schema is necessary. A schema is a shared
common means of interpretation and constraints, and nothing more.

**A schema is a typed shadow of the document** (the user's idea, 2026-11-03,
"something to that effect"; confirmed 2026-11-04 over reusing JSON Schema, with work
still to do on it). It mirrors the document, with each
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
tests settled on, all proposals, left open for the core team:

- **It types, and a scalar type can carry a limit.** The agent first left all
  checks to the app; the user pushed back (2026-11-04, `!int[0,100]` "or whatever")
  and was right, since an app binding works in one language and a limit in the
  schema works in all of them. Spelling, tested: `!int(0..100)`, `!float(0..1)`,
  `!str(1..)` for length, `!str(/regex/)`. It must be `..`, not a comma or
  brackets: `[int[0,100], ...]` won't parse, and `[int(0,100), ...]` silently
  splits into two items. Not all checks belong here: see the gaps below.
- **Regex is the risky part.** Dialects differ, so one pattern can match differently
  by language, and a slow pattern in a document's own table is an attack. The user,
  2026-11-04: regex may not be needed at all; something simpler like PIC, or
  glob-like, may be enough. See **Patterns** below.
- **No new syntax.** With tags out, `!` is an ordinary character, so `!int` is a
  plain string and the parser knows nothing about schemas. So a leftover 1.x tag reads
  as text, in 137 of 3,544 public files. The agent proposed refusing a plain scalar
  starting with `!` outside the table. **Open:** the user is undecided (2026-11-04), and
  asked for it to go to the core team as an open question, so section 14 of the draft
  gives the case each way. The user's point against: people have to convert, not just add
  `%YAML 2.0`. A value starting with `!` is a type expression; any other value is a
  literal that must match.
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
- **How a stream is marked** (the user accepted this, 2026-11-04). `--- &` is the
  lookup table, `--- !name` a named document, `---` a plain one, and only data is
  delivered. Bare `--- !` goes: a shadow's root is a table entry, so a schema file is
  a table and nothing else. One table per stream: `!job` and `*defaults` look in the
  same place. An app can supply a schema directly or by prepending it. Moving both
  shadows' roots into named entries changed no result.
- **A document names its interpretation with `--- !name`** (the user asked for a
  whole-document tag so any app reading a file knows what it is meant to be, and
  accepted this, 2026-11-04). It is also how a lone file points at its schema. It is
  per document, optional, delivered beside the data and not in it. A parser looks
  nothing up and never fetches: it is a name, not an address, and reading a file must
  not touch the network. It is advisory. The app's schema wins, so a hostile file
  can't pick a laxer one, and an app may refuse a name it didn't expect. Node tags
  stay out. A name with a `/` is global, domain first (`github.com/actions/workflow`);
  one without is local to the stream or app. No `tag:` form and no year: that date
  only shows who held the domain (RFC 4151), and a name is advisory, so a domain
  changing hands does no harm. A format with versions puts one in the path
  (`.../workflow/v1`). If the stream's table has that name, it types the document;
  otherwise it is only a name for the app. `read_stream` in the prototype does this,
  tested on small examples only, not on real files.
- **No `!` versus `!!`** (the user asked, and accepted this, 2026-11-04). Inside a
  schema every name is built in or in the table, which already separates standard
  from app. If the standard later adds a name a table defines, the table wins. An app
  type is a table entry plus app code, so `!ruby!int` isn't needed.
- **Standard names are exact** (the user accepted this, 2026-11-04), since a schema
  exists to be a shared standard. `!bool` is `true` or `false`. `!int` and `!float`
  take JSON's spellings, so `0755` is refused; that changed no result in either
  comparison. `!date`, `!datetime` and `!binary` are added (RFC 3339 and base64). Not
  `!uri`, which is a pattern question, nor `!set`, which an app can bind.
- **Patterns: I-Regexp (RFC 9485) is the proposed scheme** (the user, 2026-11-04: "the
  proposed pattern matching scheme", not settled in stone). Measured (see landscape.md,
  Patterns in real schemas): PIC and glob write 15% of real patterns, and neither can
  say one or more of a class. Proposed with it: the whole string always matches, and
  `^` and `$` are refused outside a class. The rest goes to a named type and app code.
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

## Syntax cuts

Measured with `syntax.py`. On 2026-11-04 the user took the nine cuts below ("I pretty
much agree with those"): `|+` and `>+`; `|1` to `|9`; everything but UTF-8; tabs outside
strings; one-pair `[a: b]`; escapes JSON doesn't have; multi-line plain; multi-line
quoted; more-indented lines inside `>`.

The user settled these details on 2026-11-04, reading section 14. A tab after the last
content on a line is ignored, as a space is (their point; the draft had refused it), and
a tab on a line with no content stays refused. `%YAML 2.0` may repeat before a marker.
Another version on the first line counts as no directive: refuse, or pass it to that
version's parser if the caller asked ("it can switch parsers, dealer choice"). A block
scalar with no text is the empty string. A key and its `:` stay on one line in flow.
`{a}` is refused, which leaves room for sets later, and section 14 says so. U+FEFF is left as an
open question there.

A lone CR stays refused (the user, 2026-11-04, "But okay"). The reason is that a line
break tools can't see lets a viewer and a parser disagree. The user expects most parsers
to ignore this rule, so it needs a case in the test suite.

- Multi-line plain scalars go: a plain scalar is one line. The user's earlier idea
  (yaml/YAML2#5, 2016) was to keep their line breaks, since an app can remove lines
  but can't get them back. The user retracted it on 2026-11-04. Real files rely on
  folding, so keeping breaks would silently change them, and a dropped `- ` or `:`
  would still be swallowed. Cutting makes both an error.
- `|` always ends in exactly one newline, whether or not the file does (the user, "I
  guess", 2026-11-04). Blank lines after it are layout. Otherwise an editor's final
  newline changes the value.
- `...` ends the YAML unless the next non-blank line is `---`, which starts another
  document, as in 1.2. A parser stops at any other `...`, whatever follows isn't YAML,
  and it reports where it stopped so an app can take the rest. Raised by the user's
  "what about `...`?" (2026-11-04), and the restart is the user's point. In 1.2 `...`
  only ends a document, and what follows is still read as YAML, which is why Markdown
  can't follow it. Blank lines are skipped, comments aren't: `# Heading` then `---` is
  Markdown. Bare documents after `...` go. This covers front matter, the user's case in YAML2#5,
  and replaces `--- |`, a text document proposed the same day, which needed a new
  string type and a rule that it comes last. The user agreed, `--- |` dropped
  (2026-11-04). An ordinary `--- |` with indented text is still a block string.
- The rare forms are each under 0.5% of 4,026 public files, each a loud error with an
  easy fix: `|+` and `>+`; indentation indicators (`|2`); UTF-16, UTF-32 and a BOM, so
  UTF-8 only; tabs outside strings; one-pair `[a: b]`; escapes JSON doesn't have.
- Without `|2` the first non-blank line sets a block's indent, as it does in all but 3
  of 4,213 real block scalars. Text whose first line starts with spaces has to be
  written double-quoted; in a block, a shorter later line is an error, as it is today.
- Multi-line quoted scalars go too: an unclosed quote then fails on its own line, not
  at the next quote. `\`-newline and `\ ` go with them.
- A more-indented line inside `>` becomes an error. Its special folding rule is hard to
  implement and to predict; silently folding it instead would change values.
- `%`, `@` and `` ` `` are freed at the start of a plain scalar (the user, 2026-11-04:
  "free them. the YAML team can decide otherwise if they have a reason too"). They were
  only inherited, and forced quotes on 1,530 public values starting with `%` alone. A
  line starting with `%` at column 0 stays reserved for directives. 1.x refuses these
  today, so no existing file changes meaning.
- Comments are never data, and no interface that delivers data shows them. A parser may
  also offer a syntax tree that keeps them, and the spec gives one attachment rule so
  tools agree (the user, 2026-11-04): a comment at the end of a line belongs to the last
  node on it, and a run of comment lines to the key or item on the next line, with no
  blank line between. Uses: tools that rewrite files, documentation, tool directives.
- Indentation means nothing inside a flow collection (the user, 2026-11-04: "I think
  that has to be true"), though 1.2's grammar says otherwise and its parsers don't.
- Staying: flow (34.5%, and JSON needs it), `>` (8.3%), `|-` and `>-` (5.9%), several
  documents (27.8% of Kubernetes files), trailing commas (they cost nothing), and
  `- - x` (3 files, but `- key:` stays, so cutting it would add a rule, not remove one).
- Margin strings, the user's idea from a Ruby literal (2026-11-04). **Parked** as a
  proposal to work out later: not in 2.0 for now, so `|text` stays an error (the user,
  2026-11-04, on the agent's recommendation). Section 14 of the draft shows it. The idea:
  `a: |this is the text` then `   |  more`. The first `|` sets a column, each later line
  has `|` there, and all after it is literal, so a `|` in the text or a leading space is
  fine, and `#` isn't a comment. Line breaks fall between lines, so an empty last `|`
  line gives a final newline. What you see is the exact value, with no chomping or
  indent detection. `|` followed by the end of the line, or by spaces and `#`, stays the
  ordinary header (103 of 4,213 real blocks have that comment). A key rename shifts the
  column unless the string starts on its own line. It would be an addition, it can't
  replace `|-` (real ones run to 594 lines), and pasted text needs every line touched.
  The header rule means a margin string can't start with spaces and `#`, which the user
  sees as a possible reason to allow no comment on a `|` line at all (2026-11-04).
