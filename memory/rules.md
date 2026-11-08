# The rules of YAML 2.0

*Updated 2026-11-08*

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

Measured 2026-11-06, on the 4,026 of 4,500 files PyYAML's events read: 721 tag uses in 177 files
(4.4%): MkDocs 144, Rails 17, GitLab 13, Kubernetes 2, Jekyll 1. None states a standard type. 179
are bare `!`, all in Rails, which says "a string". 542 are application marks or classes
(`!!python/name` 283, `!reference` 126, `!Ref` 43, `!ENV` 32). So a schema replaces almost nothing
tags do in these files; keys and application changes do. The sample has next to no CloudFormation
or Home Assistant, so it says little about formats built on tags.

The user asked whether naming only documents is a mistake, weighed it against a tag per node, and
chose to keep names per document (2026-11-06). For a tag per node: tagged formats keep working, a mark
can't clash with data, values of one shape can be told apart, and it is the smaller break. Against:
a nested value has nowhere to keep a name; an unregistered name needs a rule (PyYAML `safe_load` refuses
`!person`, Psych `safe_load` drops it with no error); a tag and a schema can disagree; and `!` would
become syntax, so `!int` would stop being a plain string and part 2 would need a new spelling. Adding
tags later changes nothing already written, because each file declares its version. If the core team
insists, the cheapest version is a tag delivered beside the node, a list of tags the application
accepts, refusal of any other, and a new schema spelling. The reason in part 1, section 13.1, and in
the covering note is now the data model, with MkDocs added (`a679bd6`).

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
- In a `--- &` document a reference works as it does anywhere: it looks backward, at
  earlier entries, so an entry can't name itself, and one that replaces another may
  name the old one. A `<<:` at the top of the `--- &` document itself is refused. The
  user agreed on 2026-11-04, after @oyl's review. This replaces the rule of 2026-11-03,
  which allowed only `<<` at the top of an entry: the size limit now bounds growth, and
  that rule refused GitLab's `.build:` with `script:` holding `-<< *.setup`.
- Structure alone doesn't bound growth: a 1 MB file with a 500 KB entry and 100,000
  `- *a` lines expands to about 50 GB. Hence the size limit.
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
- **Size limit, two numbers.** The user chose this on 2026-11-05 ("why not track actual
  memory? and maybe enve what it would cost to fully instantiate"). Held is the data as
  written, with a reference, `<<:` and `-<<` each counting 1. Full is the size with no
  references left, worked out by addition, so nothing is built: a 702-byte doubling chain
  came to 3.3 trillion in under a millisecond. Both cover the table in scope and the
  document being read, and a delivered document leaves both. Every interface applies the
  limit to held, and a normal load also applies it to full, refusing up front, because its
  program will usually walk the data. An interface that keeps references applies it to held
  alone, and whatever expands them later checks full and levels first. An interface
  delivering several documents at once adds up each number it applies. It is still one
  setting. This replaces the count per stream and then per document,
  and @oyl's count on the stream. A reference costs one node in Oyl's tree, so a stream
  naming a 1 MB entry 1,000 times holds almost nothing and should read. Held stands in for
  real memory so that every parser gets the same number: Oyl could track real memory,
  since every allocation in a parse goes through `oyl_arena.c`, but another parser's figure
  would differ.
- **Shared tables need a reset.** The user asked for this through @oyl (2026-11-05), and
  chose the agent's form over @oyl's third count ("apply the fixes", 2026-11-05). A
  replacement comes off full but stays in held, and `...` takes the table to 0 in both, so a
  stream that keeps replacing entries has to write `...` now and then. An interface keeping
  references and delivering several documents takes nothing off at `...`, since its documents
  still name the old tables. Held stays linear: an entry grown by one item per document adds
  a few units each time. A fixed-width full stops at its largest value
  and never wraps. In `2d5a90d`. See [review.md](review.md).
- `-<<` can go anywhere in a `--- &` entry. A chain of entries can still double each
  time, and the user and the agent left that to the size limit (2026-11-04), which
  refuses by adding up sizes, before allocating anything.
- Nesting: every parser must accept 256 levels and may refuse past that, but never crash.
  Levels count with references followed, by addition, the outermost collection being the
  first (the user, 2026-11-05, in `2d5a90d`).
  The user agreed to a minimum on 2026-11-04. 256 is the agent's pick, and the user
  accepted it as a minimum (2026-11-04): the deepest of the 4,241 real files that parse is 21.

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
  repeat inside one `--- &` is refused, as in any mapping. References take what the
  entry holds as they are read, so a replacement never changes an earlier document or entry. An entry may name
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
  In a `--- &` entry, two `-<<` of the entry before double each time, unlike `<<:`,
  whose keys collapse, so the size limit above is what stops that.
- Flow collections, **proposed** (the user asked, 2026-11-04): both work, by the same
  rules, if flow stays, as proposed below. `{<<: *a, x: 1}` with `<<:` first, and
  `[-<< *s, x]` at any position. A reference ends at `,`, `]` or `}`, so a path key
  holding those needs `<...>` inside flow. `[<<: *a, x]` is
  a one-pair mapping item, as in 1.x, unless that form is cut below. Real use of either
  in flow: none (landscape.md).
- A reference names exactly one node, and a parser may share it or copy it, so an
  application that changes delivered data can't assume either. The user chose this on
  2026-11-04 ("I would not forbid that"): a write through a shared node is how the
  document is spelled, may be wanted, and copying first is easy. It replaces "a copy, so
  the data stays a tree" and "share memory only if no application can tell". A writable
  tree can offer both kinds of edit. In `2d5a90d`. Nothing is writable while
  parsing (the user, 2026-11-04: a writable structure "should not be wriable until it is
  manifest -- not while it is parsing"), so a change can't reach a later document. Data
  built one document at a time shares nothing between documents, and sharing across them
  takes one build after the stream is read (2026-11-05). Oyl already works this
  way: `oyl_parse_tree` gives a read-only tree per document, with no write functions, and
  an alias is a 32-byte node holding its target's index. Its aliases stay inside one
  document's tree today, so references into a table that spans documents are new work.
  Part 2
  will need to allow for it too: a reference under two schema types can't share its
  typed result.
- A query (YPATH proper: wildcards, filters, many nodes) is for tools, and is a
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
  `!str(1..)` for length, `!str(/regex/)`. It must be `..`, not a comma or brackets,
  because a plain scalar in a flow collection ends at `, [ ] { }`. That is part 1,
  section 6.1, and 1.2 alike: first seen through PyYAML, and rerun on the 2.0 grammar and
  Psych on 2026-11-05, when the user asked. `[!int(0,100), ...]` splits in two, and the
  draft refuses it, since `!int(0` is a bad type. Patterns hit the same rule: **Patterns
  and flow**, below. Not all checks belong here: see the gaps below.
- **Regex is the risky part.** Dialects differ, so one pattern can match differently
  by language, and a slow pattern in a document's own table is an attack. The user,
  2026-11-04: regex may not be needed at all; something simpler like PIC, or
  glob-like, may be enough. See **Patterns** below.
- **The parser uses the schema to parse** (the user, 2026-11-04, correcting the agent,
  who had written that a schema works on what the parser delivers). So a schema can see
  how a scalar was written while parsing, as 1.2's schemas do. The prototype still
  applies a schema afterwards, to strings, and doesn't show this. Every schema can see
  quotes: the agent proposed only a standard JSON reading, and the user said that "could
  never work". Instead part 2 needs a way to say "wherever this occurs, interpret it this
  way", so a JSON reading is an ordinary small schema. **Open:** the form of that rule.
  Goal (the user, 2026-11-04): make JSON a subset; "It shouldn't take much." The schema
  covers types, and three language changes went into the draft for the syntax, see
  landscape.md, JSON against the draft. Section 13 now claims a subset once `%YAML 2.0` is
  on top, apart from repeated keys and a lone CR between tokens.
- **No new syntax.** With tags out, `!` is an ordinary character in a table, so `!int` is a
  plain string to the grammar. A value starting with `!` is a type expression; any other value
  is a literal that must match.
- **`!` outside the table (the user chose this, 2026-11-06; in `9f6292f`).** A plain scalar can't start with `!` outside the table, so a
  leftover 1.x tag is refused. The user's proviso: this could be relaxed if 2.0 becomes the go-to
  standard, which is section 6.1's last paragraph. Relaxing only accepts more, so no file breaks.
  Before this the user was undecided (2026-11-04) and it sat in section 14; that item is gone. The
  case against, kept here: no file gets here by accident, since a 1.x file has no `%YAML 2.0`;
  the same text is fine in a table and refused in a document; and a tag in a table entry still reads
  as text, which a reference delivers. A 1.x file has no table, so a tag only gets there by moving.
  - Cost, measured 2026-11-06: 3,558 of 4,651 files read as written before, 3,418 (73.5%) after. Of
    the 140 lost, MkDocs 128 (92.8% to 67.2%), Rails 7, GitLab 5. 165 files now stop at this rule,
    25 of which stopped later anyway. Those 140 only read because tags passed as text. First-refusal
    counts moved too: duplicate keys 60 to 58. A quoted value costs nothing, since 60 strings in 36
    of 4,241 files start with `!` and are quoted already.
  - Checks: part 1, 58 examples and 217 edge cases; part 2, 48 and 262. All 5 deliberate breaks of
    the rule caught (no refusal; refused in tables; not reset after a table; keys; flow).
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
  reference is a whole value, so it can't sit in `![job*]` or `!str | job`,
  and recursive types would never end. Use `<<`
  to paste a shape and `!name` to use a type. A key above the `---` is a name;
  below it, a key in the document. That takes reading with care: the user read
  `flag: !str` as a key with a string value (2026-11-03), which is what it
  literally is, and found it a bit confusing.
- **Alternatives** are chosen by shape, never by how text looks: at most one
  scalar type, at most one sequence, and mappings told apart by required keys and
  literals. All 117 scalar unions in the sample include string. Among scalars, the user
  changed this on 2026-11-05: see "Wherever this occurs" just below.
- **"Wherever this occurs" (the user accepted this, 2026-11-05; replaced by `!*` on 2026-11-06,
  below).** The rule is a recursive named type, which needs no new construct. Two changes make it work: a union
  may hold several scalar types, tried in the order written, and a quoted scalar matches
  string types only. JSON is then four lines of ordinary schema (`shadow/schema2.py`):
  `json: !null | !bool | !int | !float | !str | !array | !object`, `array: [!json, ...]`,
  and `object:` with `!str: !json`. Read by the real grammar, that matched a JSON parser
  exactly on all 994 SchemaStore files under 300,000 bytes and on 93 of 95 in JSONTestSuite, the other 2 being
  repeated keys. It needs a `!null` standard name. The same form gives "every `timeout` key
  at any depth is an int" in five lines. The cost: `!float | !str` reads `1.10` as 1.1, the
  old Norway problem, but only where a schema's author asks, and the same on every parser.
  Quoted-means-string changed no verdict on 408 workflows and 311 Compose files, which is
  weak evidence: those two shadows use non-string types in 9 places, and no quoted value
  reached one. It matches what a 1.2 parser with JSON Schema does today.
- **Universal matchers (the user chose this, 2026-11-05).** "any value matching `/[+-][0-9]+/` is an
  `!int`". The reach already existed: a recursive type (above), and since 2026-11-06 `!*`. What was missing was the claim, since
  only `!str` took a pattern. So `!int(/pattern/)` replaces the standard spelling with the pattern
  (part 2, section 4.5), and section 10 shows it applied to every value. Not a separate rule, which
  would need a precedence against the type at a key: each node has one type, so `image: !str`
  holding `+5` stays a string. Plain scalars only. Text is read as a sign and base-10 digits, so `007`
  is 7. Text the pattern matches and that can't be read refuses the document rather than falling
  through to a string. An emitter writes a spelling the type reads back, or refuses (section 13;
  no emitter in the checker, so untested). `!float`, `!decimal`, `!null`, `!bool` and other bases are
  open points in section 15, left out because the user was asked about `!int` only.
- **`!*`, anywhere (the user chose this, 2026-11-06).** The user asked whether a schema should be
  rules from general to specific (`*: !int /.../`, `address:name: !str 40`, `*:ts_*: !date`), then
  saw the nested form is nearly the shadow, short of one `*` being both a type and a mapping. So
  there is one `!*` key, and the scalar default sits inside it as a second `!*`. It replaces section
  10's `free`, `list` and `map`, and the shadow stays. Measured before choosing: the two real shadows
  have 701 lines, 8 give a standard non-string type, and at most 82 say anything about type; in 721
  SchemaStore families the median schema has 35 property declarations and about 6 `*:key` rules cover
  its non-string keys; of 947 schemas 74% use `required`, 68% close a mapping, 37% choose between
  shapes, none of which rules can say. Flat rules were dropped because one form did two jobs (`*`
  selected, `address:name` constrained), and a key can't start with `*`.
  - The closest rule wins, with no ranking and no dependence on order: the mapping type at the key's
    place, then the nearest `!*`, and nowhere else. A `!*` replaces any above it for everything below.
    Searching every `!*` above would let a stream nest thousands and pay for them on each key, so
    "nearest only" is what keeps the time rule.
  - `!*`, not `"*"`, because a quoted key is literal (section 7). `!str(/ts_.*/)`, not `ts_*`, so there
    is one pattern language. Its type is scalars only. A `!*` inside a `!*` is the default for scalars,
    and holds no rules. A rule is never required.
  - Consequences the user accepted: below a `!*` every mapping is open, so a typo in a key passes
    (open point in section 15), and alternatives there are chosen by required keys and literals only.
  - Two rules added while building it, not put to the user one by one: a type with `!*` and no required
    keys takes a scalar or sequence too (JSON's `5` needs it), though not inside a union; a key under
    `!*` that an alternative doesn't name no longer rules that alternative out.
  - JSON is now two lines. It matched `json.loads` on all 1,015 SchemaStore files and 93 of 95 in
    JSONTestSuite, the other 2 being repeated keys. Part 2: 46 examples, 245 edge cases, 53 of 53
    deliberate rule breaks caught. Not tested: speed, or an emitter under `!*`.
- **`!**` and `!*` (the user chose this, 2026-11-06; in `211757b`).** The user doubted the spelling: in a
  file glob `*` stops at one level and `**` goes down. They also read `!*: {Rev: !int}` as a "skip level",
  `Rev: !int` here and anywhere below, which is what the key already did. So the meaning stayed and the
  spelling split: `!**` is rules here and at every level below, and `!*` is any other key here. That
  removes the special rule for the inner `!*`: it is the same key, and a `!**` walks every collection, so
  it only sees scalars. Cost: outside `!**`, `!*: T` and `!str: T` overlap, though `!*` always comes after
  type keys. `!ts_*` is still refused, for one pattern language. Everything above about `!*` as the deep
  key now applies to `!**`.
- **Publishing a schema (the user proposed this, 2026-11-06; in `19aad50`).** The user asked for `!<url>` to a `.yes` file. The agent objected to a
  parser fetching on read (a stranger's file sends requests from the reader's machine) and to a
  published file changing (same bytes, different data). The user answered the second by naming the
  file for its own hash, then chose 40 hex digits of SHA-256 (160 bits) over 32 and 64, and put the
  version in the path: `tabcomputing.com/address/v1/<hash>.yes`.
  - No new grammar: a global name holds it, and names keep their ban on `:`, so `!<url>` isn't needed.
    `https://` before the name is the address, and no other name has one.
  - A parser never fetches, so every parser delivers strings and the name. An application that opts
    in gets a stamp as from a local entry, and the file's table stays out of the stream's. A file that
    doesn't hash to its name is refused, and so is a document whose file can't be had.
  - Why "no hash, no lookup": pinning by hash is rare where it's optional, 9.1% of 2,332 workflow
    `uses:`, 1.6% of 1,161 Compose `image:`, 2.1% of 427 Kubernetes `image:`. Only 8 of 4,651 files
    name a schema by URL today, 7 with no version in it and none pinned.
  - JSON Schema's core, 2020-12, sections 8.2 and 9.1.2, also treats a URI as an identifier and not a
    download. The agent's proposal, not yet decided: the last entry is the root.
  - 17 edge cases added, and 64 of 64 deliberate breaks of part 2 caught, the last 11 on publishing.
- **A name is where app code attaches.** A field that is `true` or `${{ x }}` is
  two scalars, so it's a named string (`flag: !str`), and the app binds code to
  `flag`. That recovered nearly all of what patterns check, with no regex in the
  schema. An unbound name stays a string. It needs no rule of its own: it's just a
  named type.
- **Joining files** (the user, 2026-11-05). Only `...` empties the table. Whoever joins files chooses:
  independent files get `...`, and files sharing a table drop `%YAML 2.0` and use `---`. A plain `cat` is
  refused. Every file starts `%YAML 2.0` then `---`, which closes section 14's open point for now.
- **Numbers** (the user, 2026-11-05). `!int` and `!float` have no size. A parser delivers the number
  written, or refuses. Digits lost are an error, not a warning, unless an application accepts rounding
  on `!float`. `!decimal` says the application keeps it exact or errors. A width is a limit, and byte
  order doesn't arise in text. The user first asked whether names like `uint32` were needed at all.
  A float that specifies a minimum precision is the one loose end, left in section 15 of part 2 for
  the core team (the user, 2026-11-05).
- **The file is the truth** (the user, 2026-11-05, replacing "the application's choice wins"). A
  schema written in with the data stamps it: that is how it is meant to be read, and an
  application can't make the file lie. Normal use is a data-only file, with the application
  or library applying a schema from elsewhere, known from the file's name or extension or
  simply by knowing it. An application can strip a file's schema if it chooses, and whether
  a library offers such ways out is another matter. A stream's own schema applies by default.
  So "a file can't pick a laxer schema" was wrong, not prepending: @oyl's three probes aren't
  holes, and passing and prepending do the same job. The cost: an application checking files
  it didn't write has to ignore or refuse a file's schema.
- **Schemas name types; app code binds them to classes.** A parser builds nothing from
  a name, and only a name the application bound does anything, so the bindings are an
  allow-list, like Psych's `permitted_classes`. The user challenged the agent's first
  wording, "a schema must never name a class" (2026-11-05): nothing is wrong with
  `!ruby/object` for serializing Ruby, only with the file choosing the class. Part 1,
  section 13.1, now says what 2.0 costs object data, and the user accepted that the same
  day: no class on a nested node without a schema, no cycles, no shared identity. The
  real-file sample is config files, so it can't show how much Ruby data depends on these.
- **How a stream is marked** (the user accepted this, 2026-11-04). `--- &` is the
  lookup table, `--- !name` a named document, `---` a plain one, and only data is
  delivered. Bare `--- !` goes: a shadow's root is a table entry, so a schema file is
  a table and nothing else. One table at a time: `!job` and `*defaults` look in the
  same place. An app can supply a schema directly or by prepending it (but see **The file
  is the truth**, below). Moving both
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
- **Patterns, an idea for later (the user, 2026-11-05, "just a thought").** Everything in a
  pattern is literal except what sits in rare Unicode brackets: `⦃0-9⦄` a class, `⟦A999⟧` a
  PIC, perhaps `⦅ ⦆` a glob, with an ASCII way to type them. I-Regexp stays the proposal.
  Measured: none of the six characters appears in 1,015 SchemaStore schemas or 4,651 YAML
  files, and 341 of 1,271 unique patterns escape punctuation, which this would end. The
  agent's view: the gain comes from literal-by-default, not from Unicode. One bracket pair
  with a count and `|` would cover what the table in landscape.md shows is needed, and an
  ASCII form `{0-9}`, with `{{` for a literal brace, costs little: 17 patterns hold a
  literal brace. One point for Unicode, found later that day: `⦃0-9⦄` could sit in a flow
  collection, which `[0-9]` and `{0-9}` can't. A literal comma still couldn't.
- **Patterns and flow** (the user accepted this, 2026-11-05). A type expression is a plain
  scalar first. So in a flow collection a pattern can't hold any of `, [ ] { }` and must be
  named in the table, and in a block a space before `#` or after `:` is written `[ ]`.
  Quoting can't help, because a quoted scalar in a schema is a literal. The failures are all
  loud. The draft's examples always named a pattern first, which hid this.
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
- Links across files: `$ref` to part of another file. A shadow has one stream, and publishing, above,
  only covers a whole schema.
- Same-shape alternatives: two sequences, or two scalars, told apart by content.

Still to decide: whether the spec defines standard names (`date`, `binary`, `set`)
with exact spellings, so that languages agree.

## Syntax cuts

Measured with `syntax.py`. On 2026-11-04 the user took the nine cuts below ("I pretty
much agree with those"): `|+` and `>+`; `|1` to `|9`; everything but UTF-8; tabs outside
strings; one-pair `[a: b]`; escapes JSON doesn't have; multi-line plain; multi-line
quoted; more-indented lines inside `>`.

The user chose these details on 2026-11-04, reading section 14. A tab after the last
content on a line is ignored, as a space is (their point; the draft had refused it), and
a tab on a line with no content stays refused, except inside flow. `%YAML 2.0` may repeat before a marker.
Another version on the first line counts as no directive: refuse, or pass it to that
version's parser if the caller asked ("it can switch parsers, dealer choice"). A block
scalar with no text is the empty string. A plain key and its `:` stay on one line in
flow, and a quoted key may have a line break before `:`, for JSON (the user first agreed
to one line, then chose the JSON goal, the same day).
**Characters outside double quotes** (the user agreed on 2026-11-04, after @oyl's review):
U+0085, U+2028 and U+2029 are refused, and a double-quoted string can hold them, which
keeps JSON. They are a real same-bytes-different-data case: PyYAML and go-yaml read
`- a`, U+2028, `- b` as two items, and a 1.2 parser as one. **Bidirectional controls stay
allowed** (the user, 2026-11-04). They first agreed to refuse them, on the agent's word
that it cost nothing, which the agent then measured false (see landscape.md, Right-to-left
text). Every parser reads them alike, so they aren't the root problem. Section 14 keeps a
narrower rule open for the core team: refuse them in keys and comments only.

`{a}` is refused, which leaves room for sets later, and section 14 says so. U+FEFF outside double quotes is left as an
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

## From the second review (the user, 2026-11-07)

- **A `!float` limit tests the number as written.** The user's reading: `!float(..0.1)` is simply the
  maximum allowed, so `0.1` passes. It no longer depends on what a parser stores.
- **Comments after a repeated `%YAML 2.0` are skipped, and comments before it aren't.** The agent first
  applied both sides. The user then pointed out that a comment before the line might be Markdown, so only
  the side after it stands. The first non-blank line after `...` decides: a marker or `%YAML 2.0` carries
  on, and anything else ends the YAML, so `# Heading` stays Markdown and a parser needn't read ahead
  through comments. Nothing is lost in joining files, because a 2.0 file's first line must be the
  directive, so no file brings a comment ahead of it. A comment written by hand between the `...` and the
  line ends the YAML at the `...`, and the parser reports that offset.
- **Rounding takes the even value on a tie**, where an application accepts rounding.
- **A leading blank line wider than a block scalar's text is refused**, as in 1.x. The user asked whether
  an escape for a space exists. No `\s` does, in 1.x or 2.0. In double quotes a space needs none and
  `\u0020` also works; a block scalar has no escapes.
- **A minimum precision on `!float` is still open** (part 2, section 15). `!float` never loses digits
  silently, but its verdict depends on the parser: `3.14159265358979323846` is refused on binary64 and
  delivered on binary128. The agent proposed width names, `!float32`, `!float64` and `!float128`, each
  meaning that a value keeps its digits in that width and a parser that can't work in it refuses. The
  user hasn't ruled.
- **A digit count is a separate question from a width** (the user, 2026-11-07). The user asked what
  separates `!float32` from `!float(32)`: the first is the store, the second 32 digits. The agent had said
  a digit count matches nothing a program stores, which was wrong: SQL `NUMERIC(p,s)`, Avro and Parquet
  `decimal`, and XSD `totalDigits` all count digits, and Ada and Fortran ask for digits and pick the store.
  What holds is that a binary store has no round number of decimal digits. By exact arithmetic on 4,000
  random values per count, every value of 6, 15 and 33 digits keeps its digits in binary32, 64 and 128, and
  the next digit up starts to lose: 3,994, 3,631 and 3,732 of 4,000 keep. `16777216` keeps in binary32 and
  `16777217` doesn't, with 8 digits each, so no count can tell them apart. `1234.5678` loses and
  `0.0012345678` keeps, also 8 digits each. A float counts significant digits, not places after the point.
- **`!decimal` already answers part of it.** It keeps every digit on every parser, whatever the count, so
  a value that needs 32 digits is `!decimal` today. The agent missed this when first answering. Today
  `!float(15)` is refused as a bad limit and `!decimal(/pattern/)` is refused, with patterns on other types
  open in part 2, section 15. The agent's view: a digit cap belongs on `!decimal`, as `!decimal(32)` or a
  pattern, not on `!float`, since `!float32` and `!float(32)` would be one typo apart and mean bits and
  digits. The user hasn't ruled.
- **Width names and patterns on `!decimal` are in `e92b1a2`** (the user, 2026-11-07). The user first
  said they weren't keen on `!float32` and would rather have SQL's `!float(38,10)`, because `!float32` has to
  cite a standard, and floats of one size can have different layouts: IEEE binary16 and bfloat16 are both 16
  bits and hold 11 and 8 bits of mantissa. They then answered yes to adding both, and said they may be
  thinking about floats wrong. So the draft names IEEE 754 binary32, binary64 and binary128 outright, and
  part 2, section 15, keeps width against digit count open for the core team.
- **SQL's form.** In SQL, two numbers go on `NUMERIC`, with precision the total digits and scale the digits
  after the point, and `FLOAT(p)` takes one, counted in bits. MySQL's `FLOAT(M,D)` is a nonstandard extension,
  deprecated as of 8.0.17. `12345678901234567890.1234567890` has 30 digits and 10 places: under `!float` it's
  refused on binary64 and delivered on binary128, and `!decimal` keeps it on every parser.
- **A pattern is not a minimum precision** (the user, 2026-11-07). The user pointed out that
  `!decimal(/[0-9]{1,28}(\.[0-9]{1,10})?/)` only says how to read the text. The agent had called it the same
  as `NUMERIC(38,10)`, which was wrong. Three things were run together: spelling (which text reads as a
  number), a cap (how many digits a value can have) and a minimum (what a reader must be able to hold,
  whatever the value). An application holding 15 digits takes `1.5` under that pattern and only fails on the
  first long value. **Fixed in `e92b1a2`:** section 4.5 no longer says it, and section 15 says "minimum
  precision" again.
- **A pattern says which text is the type (the user, 2026-11-07),** and the user chose to allow one on
  `!str`, `!int`, `!float` and its widths, `!decimal` and `!null`, under one rule: it replaces the spelling
  the type matches. The agent's earlier idea of taking the pattern off `!decimal` is dropped. `!bool`,
  `!date`, `!datetime`, `!binary` and `!any` take none: a pattern can't say which text is true, which digits
  are the month, or which encoding. **In part 2, section 4.5, in `e92b1a2`.**
- **Precision and scale on `!decimal` (the user chose, 2026-11-07),** as in SQL: `!decimal(38:10)` has at
  most 28 digits before the point and 10 after, tested on the exact value and refused rather than rounded,
  and an application that can't always keep 38 digits refuses every value of that type, even `1.5`. A
  parser can't check that second half, because it keeps digits as written: it falls to the application.
  `!float128` is already a minimum, since a parser without it refuses; `!float32` and `!float64` are only
  caps. The user asked why SQL's comma couldn't stay: a type is a plain scalar, and in a flow collection
  `[!decimal(38,10), ...]` is read as the items `!decimal(38`, `10)` and `...`. The agent suggested `38:10`,
  since a colon ends a plain scalar only before a space or one of `, [ ] { }`, and the user agreed. **In
  part 2, section 4.6, in `e92b1a2`.** The user then asked whether the comma problem is PyYAML's: it is
  YAML's own, in every version (1.2.2, section 7.3.3), and PyYAML 6.0.3 and Psych 5.2.2 both read
  `[f(38,10), x]` as three items. 2.0 keeps it because JSON writes `[1,2]` with no space. The user also
  raised a picture of the number, `10.38` (2026-11-08); for `NUMERIC(38,10)` that would be `28.10`. The
  agent's view: it reads as a number and isn't one, since `28.10` and `28.1` would differ. The user then
  noted COBOL's `PIC 9(28).9(10)`: the same values as `S9(28)V9(10)`, except that COBOL drops a sign
  without `S`, `.` makes an edited text field where `V` is the value's point, and a `MOVE` cuts extra
  digits off silently. **Left open (the user, 2026-11-08),** because the choice seems subjective: part 2
  keeps `38:10` and section 15 explains both spellings.
- **A precision, a limit and a pattern together (the user agreed, 2026-11-07).** The user asked how a type
  carries a range and a pattern, and whether it would ever need two ranges, which "can get pretty hairy if
  we let it". The agent's proposal, which the user took: one pair of parentheses, at most one of each, one
  space between them, in the order precision (`!decimal` only), range, pattern, as in
  `!decimal(5:2 0.. /[0-9]+\.[0-9]{2}/)`. The pattern last keeps "a pattern ends at the first `/)`". Two
  ranges as alternatives are a union, `!int(1..10) | !int(20..30)`; two on one type are refused. Too many
  digits is no match, as a range is: the agent's choice. Anything more, such as a multiple of 5 or a bound
  that excludes its value, stays application code. **In part 2, section 4.7, in `e92b1a2`.**
- **Arguments as YAML structure, dropped.** The user asked about `["!decimal", [38,10], "/.../"]`, then
  noted it would affect every type. In a schema a sequence already stands for a sequence in the data, and a
  quoted scalar for that literal text, so that line is already a schema for a three-item sequence. The
  arguments stay inside the type's scalar.
- **`!float` is short for `!float64` (the user, 2026-11-08),** binary64 on every parser, and floats keep
  accepted names. The user first asked whether `!float(11.52)`, binary64's exponent and fraction bits, could
  be `!float`; the agent offered `!float(64:52)` to match `38:10`. The user asked whether two sizes cover
  every float, and they don't: they describe a format only under IEEE 754's rules. E4M3 reaches 448, not
  240; some hardware has no subnormals; IBM's floats are base 16; double-double has no fixed precision. So
  the user chose names. Whether to add `!float16` and `!bfloat16`, as C++23 names them, is open (part 2,
  section 15). **In `bafa4ce`.**
- **What the agent chose in writing them, which the user hasn't ruled on.** A width is a test and delivers
  a number, not one rounded to its store, because a binary32 value widened to binary64 would read
  `0.10000000149011612`, not `0.1`. Accepted rounding goes to the nearest value in the named store. A parser without binary128 refuses any `!float128` value spelled as a number,
  even `0.1`. `!decimal(/pattern/)` also reads `.5` and `5.`, and a match that isn't a number refuses the
  document, as on `!int`.
- **A store too small for a value refuses the document (the user chose, 2026-11-08),** for every float
  type, and isn't no match. The agent had made a width failure no match, and once `!float` was `!float64`
  that made `1e999` under `!float | !str` the text `"1e999"`, and 7 of JSONTestSuite's `i_` files, such as
  `[1.5e+9999]`, text under part 1's JSON schema. The agent's case, which the user took: a limit is a rule
  about the data and a store isn't, so a number shouldn't become text because of how many digits it has.
  `16777217` under `!float32 | !str` and `!float32 | !float64` are refused too. The store is tested before
  any limit, so `!float(0..1) | !str` refuses `1e999`: the agent's choice. A decimal's precision stays no
  match, since it's a rule the schema states. **In `bafa4ce`.**
- **Store sizes stay (the user, 2026-11-08).** The user asked whether to drop the widths and a decimal's
  precision, leaving a number the program can't hold to fail on its own, since no schema is complete. The
  agent called it safe, because a store failure now refuses and so can't change the data, and said what it
  loses: the same check in every program, and a minimum that fails on the first value, not on the first
  long one, perhaps in production. The user chose to keep them: validation before use is what a schema is
  for. Part 2, section 4.4, now says so. **In `bafa4ce`.**
- **The stop offset counts bytes (the agent chose, when the user left it to the agent, 2026-11-08).**
  Section 4.4 said "the offset of the line after the `...`" with no unit, and the test suite found it. A
  stream is UTF-8 with no byte order mark (section 3), so every parser can count bytes, and an application
  takes the rest by cutting its buffer there. Characters would give a different number after any text
  outside ASCII. A CR LF counts as two, because the offset is into the stream as written. **In part 1,
  section 4.4, in `b44793d`;** the suite's `N7ZD` and `9JN7` fail an offset in characters or without the
  CRs.
