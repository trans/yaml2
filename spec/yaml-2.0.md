# A proposal for YAML 2.0: the language

*Draft 1, 2026-11-04*

This is a proposal to the YAML core team, not the YAML specification. "YAML" and
its version numbers are theirs. Part 2 is [YAML Schema](yaml-schema.md). Section 14
lists what is still open.

## 1. Overview

YAML's central problem is that the same bytes can give different data, depending on
which parser reads them. YAML 2.0 is a clean break that removes the causes:

- **Everything is a string.** A stream holds strings, sequences and mappings, and
  nothing else. Types come from the application or from a YAML Schema, never from a
  parser guessing by how text looks.
- **There is one way to read a stream.** Whatever this document doesn't allow is an
  error. A loud refusal is acceptable; a silent difference isn't.
- **Reuse is explicit.** Definitions live in a table that is never delivered, and
  references are paths into it.

```yaml
%YAML 2.0
--- &
defaults:
  adapter: postgres
  pool: 5
---
development:
  <<: *defaults
  database: dev
  ports: [80, 443]
```

```json
{"development": {"adapter": "postgres", "pool": "5", "database": "dev", "ports": ["80", "443"]}}
```

Each example shows a stream, then what it delivers, one line of JSON per document.
Examples leave out the `%YAML 2.0` line, except where it matters. An example marked
`refused` must be refused.

## 2. Conformance

A parser must refuse any stream that the grammar (section 12) doesn't produce or that
breaks a rule in this document. There is no error recovery and no lenient mode.

A refusal must give the line and column. A parser reading a stream incrementally may
already have delivered earlier documents, but must not deliver the document in error as
complete: an event interface reports the error before the document's end.

The one setting is the size limit (section 10). It can only cause a refusal, so it
can't make two parsers give different data.

## 3. Characters and lines

A stream is UTF-8. Any other encoding, invalid UTF-8, and a leading byte order mark are
refused.

A stream may contain only these characters, the printable characters of YAML 1.2 without
U+FEFF and the line breaks YAML 1.1 had:

| Characters | What they are |
|---|---|
| U+0009, U+000A, U+000D | tab, line feed, and carriage return as part of a line break |
| U+0020 to U+007E | printable ASCII |
| U+00A0 to U+D7FF, except U+2028 and U+2029 | |
| U+E000 to U+FFFD, except U+FEFF | |
| U+10000 to U+10FFFF | |

That refuses the other control characters (U+0000 to U+001F and U+007F to U+009F,
including next line U+0085), the line and paragraph separators U+2028 and U+2029, the
byte order mark U+FEFF, and U+FFFE and U+FFFF. U+0085, U+2028 and U+2029 are refused
because YAML 1.1 parsers still read them as line breaks: `- a`, U+2028, `- b` is two items
to PyYAML and go-yaml, and one item to a 1.2 parser. A double-quoted scalar can hold all of
these except U+0000 to U+001F directly, as a JSON string can, and can produce those with
an escape.

Bidirectional controls, U+202A to U+202E and U+2066 to U+2069, are allowed, because
translated text uses them (section 14).

A line ends with LF or CR LF, and either one reads as LF. A lone CR is refused. The
last line needn't end with a break.

Indentation is spaces. A tab is allowed inside a scalar or a comment, between tokens in
a flow collection, and after the last content on a line. Outside a scalar or a comment
it is ignored, as a space is. It is refused anywhere else, including on a line with no
content outside a flow collection, and a plain scalar must not start with one.

A comment starts with `#`, at the start of a line or after a space or a tab, and runs
to the end of the line. It can follow any complete line of YAML, but it can't sit
inside a block scalar, where `#` is text. A blank line is empty or holds only spaces.
Neither is data, and section 11 says how tools can keep comments.

## 4. Streams and documents

### 4.1 The directive

The first line of a stream must be `%YAML 2.0`. Without it, or with any other version
there, including a later 2.x, a stream isn't 2.0: a 2.0 parser must refuse it, or pass
it to a parser for that version if its caller asked for that. It must never read it as
2.0. Any other directive is refused.

The line may appear again directly before a marker line, where it means nothing, so
that files can be joined. Any other version there is refused.

### 4.2 Markers

| Marker | Starts |
|---|---|
| `---` | a document |
| `--- !name` | a named document |
| `--- &` | entries for the table (section 8) |

A marker starts at column 0, and `---` is followed by a space, a tab or the end of the
line.

The first document may follow the directive with no marker. Every later document needs
one.

After `---` or `--- !name`, a document may start on the same line if it is a scalar, a
flow collection, a reference or a block scalar header. A block collection starts on
the next line. After `--- &`, only a comment or a flow mapping may follow.

A document with no content is the empty string.

```yaml
%YAML 2.0
title: first
---
second
--- [third]
--- |
  fourth
---
```

```json
{"title": "first"}
"second"
["third"]
"fourth\n"
""
```

### 4.3 Document names

`--- !name` says what a document is meant to be. A name is letters and digits in any
script, and `.`, `_`, `-` and `/`, so `--- !配置` is a name. The characters beyond ASCII
are the ones XML 1.0 allows in a name (section 12): a short list of ranges, which needs
no Unicode tables and leaves out spaces and bidirectional controls. It keeps U+200C and
U+200D, which can't be seen, because Persian and some Indic words need them.

A parser compares names by code point, with no normalization, as it does keys. A name
has no `:`, which keeps URI schemes out, so `github.com/a/b` and `https://github.com/a/b`
can't both name one thing. It has no `%` escapes: any character a name may hold can be
written directly, and `%3A` is refused for the same reason `:` is.

A name with a `/` is global. By convention it starts with a domain, which a parser doesn't
check: `github.com/actions/workflow`.
There is no `tag:` form and no year. A format with versions puts one in the path:
`github.com/actions/workflow/v1`. A name without a `/` is local to the stream or the
application.

A name is delivered beside the data, not in it. A parser looks nothing up and never
fetches anything, because a name isn't an address, and reading a file must not touch
the network. A name alone is advisory: an application may refuse a name it didn't expect.
A name that is an entry in the file's own table stamps the document with that entry, and
YAML Schema says what that means.

```yaml
--- !github.com/actions/workflow/v1
on: push
--- !job
name: build
--- !配置
端口: 80
---
plain: yes
```

```json
{"on": "push"}
{"name": "build"}
{"端口": "80"}
{"plain": "yes"}
```

Names are the only tags. A tag on any other node is an ordinary plain string, since
`!` means nothing else to a parser.

### 4.4 Ending

A line of `...` at column 0, followed by a space, a tab or the end of the line, ends
the YAML, unless the next non-blank line is a marker, in which case another document
starts. A `%YAML 2.0` line directly before that marker counts as part of it, and the
table starts empty again (section 8.1).

A parser stops at any other `...`, and reads nothing after it. It reports the offset
of the line after the `...`, so an application can take the rest. Blank lines are
skipped when looking for a marker, and comments aren't, so `# Heading` after `...` is
not YAML.

```yaml
%YAML 2.0
---
title: Hello
...
# Heading

Body text: this isn't YAML, so it can say anything.
```

```json
{"title": "Hello"}
```

This gives front matter a specified form. Today it is only a convention: a tool finds
the closing `---` itself and cuts the file in two before any parser sees it. Here the
parser reads the whole file, stops at `...`, and reports where the body starts.

A line starting a marker or `...` at column 0 is never inside a node: block scalar text
is always indented, other scalars are one line, and a flow collection can't hold such a
line. So a tool can split a stream into documents without parsing it.

## 5. Data model

A stream delivers documents in order. Each is a node and, optionally, a name.

A node is a **string**, a **sequence** (ordered nodes) or a **mapping** (ordered pairs
of a string key and a node, each key once).

With no schema, the value of a scalar doesn't depend on how it is written. `42`, `"42"`
and `'42'` are the same string, so a file alone can't say "this is really a number": that
takes a schema (section 11). Quotes only decide which characters can be written.

```yaml
a: no
b: 0755
c: 22:22
d: null
e: "no"
f:
```

```json
{"a": "no", "b": "0755", "c": "22:22", "d": "null", "e": "no", "f": ""}
```

A key or item with no value, and an empty document, is the empty string. An
application or a schema decides what that means.

## 6. Scalars

Every scalar except a block scalar is one line.

### 6.1 Plain

A plain scalar ends at the end of the line, at a `#` after a space or tab, or at a `:`
followed by a space or the end of the line. In a flow collection it also ends at any
of `, [ ] { }`, and at a `:` followed by one of them. Spaces after it aren't part of
the value. Spaces inside it are.

It can't start with any of `, [ ] { } # & * | > ' "`. Each of those has a meaning of its
own, except `&`, which is refused so that a 1.x anchor fails loudly. `-`, `?` and `:`
can't start it if a space or the end of the line follows.

`!`, `%`, `@` and `` ` `` are ordinary characters, except that a line starting with `%`
at column 0 is reserved for directives.

```yaml
a: %{count} items
b: @home
c: `code`
d: !important
```

```json
{"a": "%{count} items", "b": "@home", "c": "`code`", "d": "!important"}
```

```yaml refused
a: b: c
```

```yaml refused
key: value
  more text
```

```yaml refused
%reserved: a
```

```yaml refused
&a b
```

### 6.2 Double-quoted

As in JSON. The escapes are `\"`, `\\`, `\/`, `\b`, `\f`, `\n`, `\r`, `\t` and
`\uXXXX`. Any other backslash is refused. Two `\u` escapes forming a surrogate pair
are one character, and a lone surrogate is refused. A double-quoted scalar is the way
to write text that needs escapes or starts with spaces.

```yaml refused
a: "\x41"
```

```yaml refused
a: "open
  close"
```

### 6.3 Single-quoted

No escapes, except that `''` is one `'`.

```yaml
a: 'it''s \n'
b: "  two spaces"
```

```json
{"a": "it's \\n", "b": "  two spaces"}
```

### 6.4 Block scalars

A block scalar starts with a header on its key's line, or on a line of its own:

| Header | Line breaks | Final newline |
|---|---|---|
| `\|` | kept | exactly one |
| `\|-` | kept | none |
| `>` | folded | exactly one |
| `>-` | folded | none |

A comment may follow the header. Anything else is refused, including `|+`, `>+`, `|2`,
`|0` and `|text`.

The first non-blank line sets the indent, which must be deeper than the parent node's.
A later non-blank line that is less indented ends the scalar. The value is the text
with that indent removed.

A block scalar that is a whole document has no parent, but its text must still be
indented by at least one space. Without that, a line of `---` in the text, such as a
Markdown rule, would silently end the document.

A blank line inside the text is kept as an empty line. If it holds more spaces than
the indent, the extra spaces are text, as in 1.x, and it counts as a line of text.
Blank lines after the text are layout, and never part of the value. A block with no
text is the empty string.

In a folded scalar, one line break between lines of text becomes a space, and each
blank line between them becomes a line break. A line of text must not start with a
space or a tab after the indent.

```yaml
a: |
  one
    two

b: |-
  three
c: >
  four
  five

  six
d: >-
  seven
e: |  # a comment here is fine
  # this is text
```

```json
{"a": "one\n  two\n", "b": "three", "c": "four five\nsix\n", "d": "seven", "e": "# this is text\n"}
```

```yaml refused
a: |+
  text
```

```yaml refused
a: |2
    text
```

```yaml refused
a: |text
```

```yaml refused
a: >
  one
    two
```

```yaml refused
--- |
top level text must be indented
```

## 7. Collections

### 7.1 Block mappings

A block mapping is one or more lines of `key: value` at the same indent. Spaces may
come before the `:`, and a space or the end of the line must follow it.

A value is on the key's line if it is a scalar, a flow collection, a reference or a
block scalar header, or on the following lines, more deeply indented. A block sequence
may also sit at its key's own indent. With nothing there, the value is the empty
string. A block collection can't start on its key's line.

```yaml
a:
  b: 1
c:
- x
- y
d:
  next line
```

```json
{"a": {"b": "1"}, "c": ["x", "y"], "d": "next line"}
```

```yaml refused
a: - x
```

### 7.2 Block sequences

A block sequence is one or more lines of `- value` at the same indent. A value follows
the same rules as in a mapping, except that a block collection may start on the `-`
line. Its indent is then the column of its first character.

```yaml
- a: 1
  b: 2
- - x
  - y
-
- z
```

```json
[{"a": "1", "b": "2"}, ["x", "y"], "", "z"]
```

### 7.3 Flow collections

`[a, b]` is a sequence and `{a: 1, b: 2}` is a mapping. A trailing comma is allowed.

Inside one, line breaks, tabs and comments may go anywhere between tokens, and
indentation means nothing. A scalar stays on one line, and so does a plain key with its
`:`. A value may be left out, giving the empty string. A quoted key may be followed
directly by `:`, or by a line break before it, so JSON reads as it should. Anything else
after a `:` needs a space, a tab, a line break, or `,` or `}`.

```yaml
a: [1, two, "three",]
b: {c: 1, "d":2, e: }
f: [
  x,  # a comment
  y
]
```

```json
{"a": ["1", "two", "three"], "b": {"c": "1", "d": "2", "e": ""}, "f": ["x", "y"]}
```

```yaml refused
[a: b]
```

```yaml refused
{a}
```

```yaml refused
{a:1}
```

```yaml refused
[a, , b]
```

### 7.4 Keys

A key is a plain or quoted scalar on one line, of any length. A key is a string, so `1`
and `"1"` are the same key, and two keys that are the same are refused. Keys are
compared by code point, with no normalization.

The time to find repeated keys, and to follow references through keys, must not grow with
the square of the number of keys and references, even in a stream written to force it.

An empty key must be quoted. A collection or a reference can't be a key, and `?` isn't
an indicator. A Hash with non-string keys is written as a sequence of pairs, and a
schema can bring it back: `- [[1, 2], origin]`.

```yaml refused
1: a
"1": b
```

```yaml refused
? a
: b
```

```yaml refused
[a]: b
```

```yaml refused
--- &
a: b
---
*a: c
```

## 8. The table and references

### 8.1 The table

A stream's table starts empty. Each `--- &` document adds entries to it: its top-level
keys. A `--- &` document is a mapping, block or flow, or empty, and it is never
delivered. A block mapping there starts at column 0.

A key repeated inside one `--- &` document is refused, as in any mapping. A key that an
earlier `--- &` document defined replaces that entry. A `...` empties the table, so the
documents after it start fresh. A replaced entry still counts against the size limit until
that `...` (section 10).

An entry stays in scope until the next `...`, so several documents can share it.
Putting a `--- &` document ahead of a file shares definitions without any include
feature.

A reference takes what its entry holds when it is read, so a replacement never changes a
document or an entry that came before it.

```yaml
--- &
port: 80
---
a: *port
--- &
port: 8080
---
b: *port
...
--- &
port: 443
---
c: *port
```

```json
{"a": "80"}
{"b": "8080"}
{"c": "443"}
```

```yaml refused
--- &
port: 80
port: 8080
```

```yaml refused
--- &
port: 80
...
---
a: *port
```

```yaml
--- &
{"port": 80, "hosts": {"main": "a.example"}}
---
a: *port
b: *hosts:main
```

```json
{"a": "80", "b": "a.example"}
```

### 8.2 References

`*` starts a reference, which is a path into the table: keys separated by a single
`:`. The first key names an entry, and each later key is looked up in the mapping
reached so far. A run of two or more colons is part of a key, so `Fn::Sub` is one key.

A key holding anything a path can't say goes inside `<` and `>`, which hold one key,
taken literally, anywhere in the path:

| Reference | Means |
|---|---|
| `*a:foo:bar` | `a`, then `foo`, then `bar` |
| `*<a:foo:bar>` | one key, named `a:foo:bar` |
| `*<a:foo>:bar` | the key `a:foo`, then `bar` |
| `*a:<foo:bar>` | `a`, then the key `foo:bar` |
| `*a:Fn::Sub` | `a`, then the key `Fn::Sub` |

A key starting with `<` also needs this form. A key holding `>` can't be written in a
path, and neither can the empty key, though copying the mapping holding them still
brings them along.

A reference ends at a space or the end of the line, and in a flow collection also at
any of `, ] }`.

```yaml
--- &
versions:
  app: 1.4
  Fn::Sub: x
  foo:bar: y
  foo:
    bar: z
.deps:rocm:
  before_script: [install]
---
a: *versions:app
b: *versions:Fn::Sub
c: *versions:<foo:bar>
d: *versions:foo:bar
e: [*versions:app, *versions:foo]
f: *<.deps:rocm>:before_script
```

```json
{"a": "1.4", "b": "x", "c": "y", "d": "z", "e": ["1.4", {"bar": "z"}], "f": ["install"]}
```

### 8.3 Resolving

A reference names exactly one node, and delivers its value. Nothing can loop, so the data
always reads as a tree.

What a parser delivers while it is reading can't be changed, so nothing an application
does can reach what is still to be read. Writable data is built from that afterwards, and
there a reference may stay one shared node or become a copy. A change to a shared node
reaches every place that names it, so to change one place only, a program takes a deep
copy of it first. Data built one document at a time shares nothing between documents, so a
change can't reach a document still to be read. Sharing across documents takes one build,
after the stream has been read.

A reference is allowed as a value, a sequence item or a whole document, and never as a
key. It must name an entry already in the table: references only look backward, so a
bad one fails at its own line. A key that isn't there is refused, and so is a step
through a string or a sequence. A path has no sequence indices.

Any `&` other than `--- &` is refused, so a 1.x anchor fails loudly.

```yaml refused
a: *later
--- &
later: 1
```

```yaml refused
--- &
a: {b: 1}
---
c: *a:missing
```

```yaml refused
--- &
steps: [x, y]
---
c: *steps:0
```

### 8.4 Inside the table

A reference inside an entry works as it does anywhere else: it looks backward, at earlier
entries. An entry that replaces another may name the one it replaces, which extends it.
An entry can't name itself, so nothing can loop, and the size limit bounds what
references can build. A `<<:` at the top of the `--- &` document itself isn't in an
entry, and is refused.

```yaml
--- &
a: {p: 1}
b:
  <<: *a
  q: 2
s: [x]
t:
  -<< *s
  - y
---
b: *b
t: *t
```

```json
{"b": {"p": "1", "q": "2"}, "t": ["x", "y"]}
```

```yaml
--- &
.setup: [apt-get update]
.build:
  script:
    -<< *.setup
    - make
---
build: *.build
```

```json
{"build": {"script": ["apt-get update", "make"]}}
```

```yaml refused
--- &
a:
  b: *a
```

## 9. Merge

### 9.1 Mappings

`<<: *ref` at the top of a mapping copies in the keys of the mapping it names. Its
lines come before any other key, and there can be several, with one reference each.

`<<` is an indicator, not a key, and is never delivered. Plain `<<:` always merges, and
`"<<":` is the literal key.

A parser builds the mapping from the top. Each merged key is added at the end, or, if
it is already there, replaces the value in place. Each written key does the same. Two
written keys that are the same are still refused: only a merged key can be replaced.
So merged keys always come before local ones. A merge is shallow.

```yaml
--- &
base: {x: 1, y: 2}
a: {p: 1, q: 2}
b: {q: 3, r: 4}
---
m:
  <<: *base
  name: a
  y: 3
n:
  <<: *a
  <<: *b
```

```json
{"m": {"x": "1", "y": "3", "name": "a"}, "n": {"p": "1", "q": "3", "r": "4"}}
```

```yaml
"<<": x
run: << parameters.x >>
```

```json
{"<<": "x", "run": "<< parameters.x >>"}
```

```yaml refused
--- &
a: {p: 1}
---
m:
  x: 1
  <<: *a
```

```yaml refused
--- &
a: {p: 1}
b: {q: 1}
---
m:
  <<: [*a, *b]
```

```yaml refused
m:
  <<: x
```

### 9.2 Sequences

`-<< *ref` is replaced by the items of the sequence it names, as a plain
concatenation. It can go at any position in a block sequence, any number of times.
`-<<` is one token, followed by a space and a reference, and it is refused anywhere
but a sequence item, as `- x` is. Anything else that starts that way is a plain
scalar, so `-<<x` is text.

`- <<: *a` is a different thing: an item that is a mapping with merged keys.

```yaml
--- &
common: [a, b]
m: {k: v}
---
steps:
  - first
  -<< *common
  - last
items:
  - <<: *m
    extra: 1
  -<< *common
```

```json
{"steps": ["first", "a", "b", "last"], "items": [{"k": "v", "extra": "1"}, "a", "b"]}
```

### 9.3 Shapes and flow

`<<:` must name a mapping, and `-<<` a sequence. Both work in flow collections:
`{<<: *a, x: 1}`, with `<<:` first, and `[-<< *s, x]`, at any position.

```yaml
--- &
a: {p: 1}
s: [x]
---
m: {<<: *a, q: 2}
n: [-<< *s, y]
```

```json
{"m": {"p": "1", "q": "2"}, "n": ["x", "y"]}
```

```yaml refused
--- &
s: [x]
---
m:
  <<: *s
```

```yaml refused
--- &
a: {p: 1}
---
- x
-<< *a
```

```yaml refused
--- &
a: {p: 1}
---
[<<: *a, x]
```

## 10. The size limit

A parser tracks two numbers as it reads, and refuses the stream when one that applies
passes the limit. It must refuse before allocating, because running out of memory usually
kills a process with nothing to catch.

**Held** is what the data takes as written, which is close to what a parser that keeps
references has in memory. Each node counts 1, and a scalar adds its UTF-8 bytes. A key
counts as a scalar does. A reference, a `<<:` and a `-<<` each count 1.

**Full** is what the data would take with no references left. A reference adds the size of
the node it names, and nothing for itself. `<<:` adds the size of the pairs it names, and
`-<<` of the items, without the collection's own 1. Nothing is deduplicated, so a merged
key that a later line replaces still counts. Full is worked out by addition, so finding
it builds nothing. A short chain of references can pass 2^64, so a fixed-width sum must stop
at its largest value and never wrap.

Both cover the table in scope and the document being read. An entry adds its key and value
to both. A replacement takes the old entry's size off full, where nothing can reach it
again, but not off held, because a delivered document that keeps references can still name
it. `...` takes the table to 0 in both. A delivered document leaves both numbers, so a long
stream can be read one document at a time.

Every interface applies the limit to held. So a stream that keeps replacing entries has to
write `...` now and then, and an emitter should write one before replacing an entry in a
long stream.

An interface that delivers data with no references left also applies the limit to full,
because a program that loads a file usually walks it, and a chain of references that fits
in a kilobyte can take terabytes to walk. An interface that keeps references, such as a
syntax tree (section 11), applies it to held alone. Whatever expands those references later
checks full and levels first, and refuses before building.

An interface that delivers several documents at once adds up their sizes in each number it
applies. If it keeps references, `...` takes nothing off held either, because its documents
still name the old tables.

```yaml
--- &
a: [x, yy]
m: {k: v}
---
b: *a
c:
  -<< *a
  - z
d:
  <<: *m
```

```json
{"b": ["x", "yy"], "c": ["x", "yy", "z"], "d": {"k": "v"}}
```

The entry `a` counts 8 in both numbers: 2 for the key, 1 for the sequence, 2 for `x` and 3
for `yy`. The entry `m` counts 7, so the table is 15. The document's full size is 26: 1 for
the mapping, 8 for `b`, 10 for `c` and 7 for `d`. Its held size is 14: 1 for the mapping, 3
for `b`, 6 for `c` and 4 for `d`. So full is 41, which a limit of 41 allows and a limit of
40 refuses, and held is 29, which an interface keeping references allows at a limit of 29.

```yaml
--- &
a: [x, yy]
--- &
a: [z]
---
b: *a
```

```json
{"b": ["z"]}
```

The second `a` replaces the first, so the table counts 5 in full and 13 in held. The
document counts 6 in full and 4 in held. So full is 11 and held is 17, and every interface
refuses this stream at a limit of 16.

The default limit is 64 MiB. An application may set it higher or lower.
A large plain file counts, and needs its application to raise the limit. A small file
can reach it through references, so a service reading untrusted input should lower it.

The size limit doesn't bound nesting: a few kilobytes of `[` can be deeper than a parser
can go, and so can a chain of references written two levels deep. So levels count with
references followed, worked out by addition as full is. Each collection is a level, the
outermost being the first. Every parser must accept 256 levels. Past that it may refuse,
and it must refuse rather than crash, so parsers can differ on how deep they go, but only
by refusing.

## 11. What a parser delivers

For each document, a parser delivers its value and its name, if it has one. After the
last, it reports where it stopped, if a `...` stopped it.

A parser keeps mappings in document order, and its interface must show that order,
through events, a tree or an ordered map. Converting to a native map that loses it is
the caller's choice.

The table, `<<`, `-<<`, comments and the way a scalar was written are not data, and no
interface that delivers data may show them, so an application can't behave differently
because of a comment. A schema is the one exception for scalars: a parser applying a
schema lets it see how a scalar was written, so a schema can read `1` and `"1"`
differently. With no schema, they are the same value.

A parser may also offer a syntax tree that keeps all of them, with their exact
positions, for tools that edit files. It isn't required, and it is separate from the
delivered data. Because it keeps references, it can offer both kinds of edit. A change to
an entry reaches every reference to it. A change at one reference replaces it with its
value, or for a merged key, with a written key. The tool then reads the result again,
since a change to an entry can break a later line.

So that such tools agree, a comment at the end of a line belongs to the last node on
that line. A run of comment lines belongs to the key or item on the next line, if no
blank line comes between. Any other comment belongs to no node.

An emitter writes `%YAML 2.0` first and never sorts keys. It writes a shared node in full
at each place, because which nodes are shared isn't data. An emitter of typed data needs
the same schema, so that it can quote a string the schema would read as something else.
With no schema, changing how a scalar is quoted is always safe. With one, it can change
the data.

## 12. Grammar

The notation is W3C EBNF, as in YAML 1.2. `(n)` is a number passed down, `indent(n)` is
exactly `n` spaces, and `A - B` is A but not B. `[> x]` means x must follow, and is not
consumed, `[!> x]` means it must not, and `[< x]` means x must come before. `EOF` is
the end of the stream.

Rules the grammar can't state: a `<<:` at the top of a table, duplicate keys,
reference resolution, and the size limit. A line starting a marker or `...` at column
0 is only matched by `document`, `table`, `later` and `finish`, and a line starting
with `%` at column 0 only by `directive`.

### Characters

```ebnf
printable  ::= #x9 | [#x20-#x7E] | [#xA0-#x2027] | [#x202A-#xD7FF] | [#xE000-#xFEFE]
             | [#xFF00-#xFFFD] | [#x10000-#x10FFFF]
break      ::= #xA | #xD #xA
space      ::= #x20
ws         ::= space+
white      ::= space | #x9
comment    ::= "#" printable*
eol        ::= (white+ comment?)? (break | EOF)
gap        ::= (space* comment? break)* (space* comment? EOF)?
```

### Streams

```ebnf
stream     ::= directive gap (first gap)? later* finish?
directive  ::= "%YAML 2.0" eol
first      ::= node(-1)
later      ::= ("..." eol blank*)? (directive gap)? (document | table) gap
finish     ::= "..." eol
document   ::= "---" (ws "!" name)? (ws line-node(0) | eol gap node(-1)?)
table      ::= "---" ws "&" (ws flow-map eol | eol gap (map(0) | space* flow-map eol)?)
name       ::= name-char+
name-char  ::= [A-Za-z0-9._/-] | #xB7 | [#xC0-#xD6] | [#xD8-#xF6] | [#xF8-#x37D]
             | [#x37F-#x1FFF] | [#x200C-#x200D] | [#x203F-#x2040] | [#x2070-#x218F]
             | [#x2C00-#x2FEF] | [#x3001-#xD7FF] | [#xF900-#xFDCF] | [#xFDF0-#xFEFE]
             | [#xFF00-#xFFFD] | [#x10000-#xEFFFF]
blank      ::= space* break
```

### Block nodes

```ebnf
node(n)    ::= map(m) | seq(m) | indent(m) line-node(max(n, 0))    /* m > n */
line-node(n) ::= scalar eol | flow eol | reference eol | block-scalar(n)
scalar     ::= plain | double | single

map(m)     ::= indent(m) map-rest(m)
map-rest(m) ::= merge eol gap (indent(m) merge eol gap)* (indent(m) pair(m) gap)*
             | pair(m) gap (indent(m) pair(m) gap)*
merge      ::= "<<:" ws reference
pair(m)    ::= key ws? ":" (ws line-node(m) | eol gap (node(m) | seq(m))?)
key        ::= (plain - "<<") | double | single

seq(m)     ::= indent(m) seq-rest(m)
seq-rest(m) ::= item(m) gap (indent(m) item(m) gap)*
item(m)    ::= "-<<" ws reference eol
             | "-" (ws line-node(m) | ws-k compact(m + 1 + k) | eol gap node(m)?)
compact(c) ::= seq-rest(c) | map-rest(c)
```

In `ws-k`, `k` is the number of spaces.

### Block scalars

```ebnf
block-scalar(n) ::= ("|" | ">") "-"? eol block-text(n)?
block-text(n)   ::= blank* indent(m) [> printable - space] text-line
                    (blank | indent(m) text-line)*       /* m > n, m >= 1 */
text-line       ::= printable* (break | EOF)
```

In a folded scalar, a `text-line` must not start with a space or a tab.

### Flow collections

```ebnf
flow       ::= flow-seq | flow-map
fs         ::= (white | break | comment break)*
flow-seq   ::= "[" fs (flow-item fs ("," fs flow-item fs)* ("," fs)?)? "]"
flow-item  ::= "-<<" ws reference(flow) | flow-node
flow-node  ::= flow | flow-plain | double | single | reference(flow)
flow-map   ::= "{" fs (flow-pair fs ("," fs flow-pair fs)* ("," fs)?)? "}"
flow-pair  ::= "<<:" ws reference(flow)
             | (flow-plain - "<<") white* ":" ([> "," | "}"] | [> white | break] fs flow-node?)
             | (double | single) fs ":" fs flow-node?
```

### Scalars

```ebnf
plain          ::= [!> merge-item] plain-first(printable) plain-rest(printable)*
flow-plain     ::= [!> merge-item] plain-first(flow-safe) plain-rest(flow-safe)*
merge-item     ::= "-<<" ws "*"
flow-safe      ::= printable - ("," | "[" | "]" | "{" | "}")

plain-first(s) ::= s - indicator - space - #x9
                 | ("-" | "?" | ":") [> s - space - #x9]
indicator      ::= "," | "[" | "]" | "{" | "}" | "#" | "&" | "*" | "|" | ">"
                 | "'" | '"' | "-" | "?" | ":"
plain-rest(s)  ::= s - ":" - "#" - space - #x9
                 | [< printable - space - #x9] "#"
                 | ":" [> s - space - #x9]
                 | (space | #x9)+ [> plain-rest(s) - space - #x9]

double         ::= '"' (string-char - '"' - "\" | escape)* '"'
string-char    ::= printable | [#x7F-#x9F] | #x2028 | #x2029 | #xFEFF | #xFFFE | #xFFFF
escape         ::= "\" ('"' | "\" | "/" | "b" | "f" | "n" | "r" | "t"
                 | "u" hex hex hex hex)
hex            ::= [0-9A-Fa-f]
single         ::= "'" (printable - "'" | "''")* "'"
```

`<<` is only special as a key, and `-<<` only before a reference, so `-<<x` and
`<< a >>` stay plain text.

### References

```ebnf
reference      ::= "*" step(printable) (":" step(printable))*
reference(flow) ::= "*" step(ref-flow) (":" step(ref-flow))*
ref-flow       ::= printable - ("," | "]" | "}")
step(s)        ::= "<" (printable - ">")+ ">" | bare(s)
bare(s)        ::= (bare-char(s) - "<" | colons) (bare-char(s) | colons)*
bare-char(s)   ::= s - ":" - space - #x9
colons         ::= ":" ":"+
```

That is 59 productions. YAML 1.2 has 211, written at a finer grain, so the comparison
is rough.

## 13. Changes from YAML 1.2

Removed:

- Implicit typing, so `no`, `0755` and `2001-12-14` are text.
- Tags on nodes, `%TAG`, `!!`, and the schemas of 1.2.
- Anchors. Only the table can be referenced.
- `?`, and collections or references as keys.
- Multi-line plain and quoted scalars, and `\`-newline.
- `|+`, `>+`, `|1` to `|9`, and more-indented lines inside `>`.
- UTF-16, UTF-32, and the byte order mark outside double quotes.
- A lone CR as a line break.
- U+0085, U+2028 and U+2029, outside double quotes.
- Tabs as whitespace, except in a flow collection and after the last content on a line.
- One-pair `[a: b]`, and `{a}` with no `:`.
- Escapes JSON doesn't have.
- The bans on starting a plain scalar with `!`, `%`, `@` or `` ` ``.
- Bare documents after `...`, and any YAML after a final `...`.
- Tolerated duplicate keys, which are always refused.
- The 1024-character limit on keys, which only bounded lookahead for flow keys.

Added:

- A required `%YAML 2.0`.
- The table, `--- &`, and references as paths, with `<...>` for literal keys.
- Document names, `--- !name`.
- `<<:` as a defined part of the language, and `-<<`.
- Guaranteed key order.
- A size limit.

Kept: block and flow collections, plain, quoted and block scalars, comments, several
documents in a stream, trailing commas and compact forms like `- - x` and `- a: 1`.

### 13.1 What this costs

Existing files need converting. Of 4,651 public files, 3,558 read as written once
`%YAML 2.0` is added. The rest hit one of the changes above.

JSON is a subset of 2.0 once `%YAML 2.0` is on top, apart from repeated keys, which YAML
1.2 forbids too, and a lone CR between tokens. Without a schema, numbers, `true`, `false`
and `null` are text. A small schema restores them: a plain scalar takes its JSON type,
and a quoted scalar stays a string. That matched a JSON parser exactly on 994 real JSON
files, and on 93 of the 95 files in JSONTestSuite that every JSON parser must accept. The
other 2 are repeated keys.

A tool that turns YAML into JSON and decodes the result into typed structures, as
`sigs.k8s.io/yaml` does for Kubernetes, gets `replicas: 3` as a string unless it applies
a schema.

Formats built on tags each need a 2.0 spelling:

| 1.x | 2.0 |
|---|---|
| CloudFormation `!Ref name` | `Ref: name`, its long form |
| CloudFormation `!Sub "${a}-b"` | `Fn::Sub: ${a}-b`, its long form |
| GitLab `!reference [.setup, script]` | `*.setup:script`, or `-<< *.setup:script` in a list |
| Home Assistant `!include lights.yaml` | a key it would read, such as `include: lights.yaml` |
| Ansible `!vault \|` and its block | a key it would read, such as `vault: \|` and its block |

CloudFormation reads its long forms today. The last two need the application to change.

Data that names its own classes changes most. 1.x can put a class on any node, as
`!ruby/object:Point`, so a language can dump an object it knows nothing about. In 2.0 only a
document has a name:

- **A known shape,** such as a gem's metadata, works through a schema, which says which type
  sits where. The application binds each name to a class (YAML Schema, section 12).
- **A known set of classes** works the same way, with a union that lists them.
- **Any object, with no schema,** has nowhere to carry its class on a nested node. A dumper
  writes a key such as `class: Point`, and its loader checks that key against a list of its own.
- **A document name** can't hold `:`, so `--- !ruby/object:Gem::Specification` is refused, and
  `--- !rubygems.org/specification` reads.
- **Cycles** can't be written, because references only point backward.
- **Shared objects** read as copies, so which values were one object isn't kept.

A whole object graph, cycles included, is a job for a language's own format, such as Ruby's
`Marshal`.

## 14. Open points

**Left open on purpose:**

- Whether a null value is needed. So far, `key:` is the empty string, and a schema can
  give it a meaning.
- Whether the first document should need `---`. Leaving it optional has one use: npm
  `yaml` 2.9.0 reads a 2.0 stream as 1.2, with only a warning, but refuses one whose first
  document has no `---`.
- Sequence indices in paths. Allowing them later breaks no file, since a step through
  a sequence is an error today.
- Reference keys, `*foo: x`, which could serve Hashes with complex keys. Allowing them
  later breaks no file.
- Sets. `{a, b}` with no `:` is refused, so a later version could make it a set without
  breaking a file. For now a set is a sequence, and an application can treat it as one.
- Where `<<:` goes. This draft requires it before any other key, and that is the
  proposed rule, but it may be stricter than it needs to be. A rule saying what `<<:`
  means in each place could allow it anywhere. The case for first: parsers disagree on a
  late `<<` today, with PyYAML and go-yaml keeping the local value and Psych the merged
  one, and 276 of the 299 uses measured already come first. Allowing it elsewhere later
  breaks no file.
- The characters of a name. YAML 1.2 tags take URI characters. This draft takes fewer
  ASCII marks and more of Unicode. `:` and `%` escapes are the two that matter, for the
  reasons in section 4.3. The other marks, `# ; ? @ & = + $ ~ * ' ( )`, could be allowed
  without harm, and allowing them later breaks no file. Beyond ASCII this draft uses
  XML 1.0's ranges, and Unicode's own letter classes would be the alternative, at the
  cost of tables in every parser. A domain in Unicode and its `xn--` form are two
  different names.
- Bidirectional controls, U+202A to U+202E and U+2066 to U+2069. This draft allows them.
  Every parser reads them the same way, but they can make a line look unlike what it
  holds, which is how the Trojan Source attacks hid code. Translated text needs them: of
  32 right-to-left locale files from Rails, Mastodon and Discourse, 3 hold them in 38
  values, 33 of those around a placeholder, and 9 outside double quotes. None is in a
  key or a comment, so a rule could refuse them there and cost none of these.
- Lines of only spaces inside `|`. Spaces past the indent stay in the value, invisibly,
  so an editor that strips trailing spaces changes the data, and the same line in `>` is
  refused. Treating such lines as empty silently changed 3 real files when tried.
- The byte order mark. This draft refuses U+FEFF outside double quotes. YAML 1.2 also
  allows it at the start of a document, and 3 of 4,651 public files start with one.
- Margin strings, a block form that keeps its text exact. They aren't in this draft, so
  `|text` is refused, and adding them later breaks no file. The idea:

  ```text
  a: |this is the text
     |  and the front | marker
     |  sets the start.
  b: 1
  ```

  This would deliver:

  ```text
  {"a": "this is the text\n  and the front | marker\n  sets the start.", "b": "1"}
  ```

  The first `|` sets a column, and each later line has a `|` in that column. Everything
  after it is literal, so a `|` in the text or a leading space is fine, and `#` isn't a
  comment. Line breaks fall between lines, so an empty last `|` line gives a final
  newline. There is no chomping or indent detection: what you see is the value. A `|`
  followed by the end of the line, or by spaces and `#`, stays the ordinary header.

  Two costs. Renaming a key shifts the column, unless the string starts on its own line.
  And it can't replace `|-`, because pasted text would need every line touched.

  One catch: `|  # note` is a header with a comment, so a margin string can't start with
  spaces and then `#`. That may be a reason to allow no comment on a `|` line at all, so
  that everything after a `|` is text. The 103 of 4,213 real blocks with a header comment
  would have to move it, and a block that didn't would fail loudly, since its next line
  has no `|`.
- Leftover tags. `!` is an ordinary character in this draft, so a 1.x tag with its
  content on the same line reads as text: `!Ref foo`, `!Sub "x"`, `!reference [a, b]`.
  So does a tag with no content, `!Ref` alone. A tag with its content on the lines below
  is refused already, because a plain scalar can't continue onto the next line. That
  refusal depends on multi-line plain scalars staying out. The question is whether a
  parser should refuse any plain scalar starting with `!` outside the table, where YAML
  Schema needs it.

  For refusing:

  - A leftover tag would fail loudly, as a leftover `&` does, which is the rule in
    section 1: a loud refusal is acceptable, and a silent difference isn't.
  - It would be needed: 137 of the 3,544 public files this grammar reads hold such tags.
  - It costs few quotes: 60 strings in 36 of 4,241 public files start with `!`, and they
    are quoted today anyway.
  - Refusing can be relaxed later without breaking a file. The reverse breaks files.

  Against:

  - No file gets here by accident. A 1.x file has no `%YAML 2.0` and is refused, so
    someone has to add that line, and converting a file is the time to deal with its
    tags.
  - `!` would be the one exception left, after `%`, `@` and the backtick were freed.
  - The same text would be fine in the table and refused in a document.
  - It wouldn't close the gap: a tag in a table entry still reads as text, and a
    reference delivers it.

## 15. Security

A stream often comes from someone else. This section adds no rules. It says what the rules
above defend against, and what they leave to the application.

**What the rules defend against:**

- **Running code.** A node can't carry a tag, so a stream can't ask a parser to build an
  object or call a function. A parser delivers strings, sequences and mappings, with a
  document's name beside them (section 4.3).
- **Reaching outside the stream.** A parser reads no other file and fetches nothing. A name
  isn't an address.
- **Expansion.** A 702-byte chain of references can have a full size of 3.3 trillion. Section
  10 finds that by addition and refuses before building. A service reading untrusted input
  should lower the default limit.
- **Deep nesting.** A few kilobytes of `[`, or a chain of references, can go deeper than a
  parser's stack. Section 10 counts levels with references followed, and a parser must refuse
  rather than crash.
- **Forced collisions.** A parser usually finds repeated keys with a hash table. If its hash
  is predictable, a stream can hold keys that all collide, so each lookup walks all of them,
  and 100,000 keys take about 5 billion comparisons. Section 7.4 limits how that time grows,
  so a hash with a fixed seed isn't enough by itself.
- **Parsers that disagree.** When one program checks a file and another acts on it, a
  difference between their parsers is a way past the check. So there is one grammar and no
  lenient mode (section 2), a repeated key is refused (section 7.4), characters that some
  parsers treat as line breaks are refused outside double quotes (section 3), and comments
  are never data (section 11).

**What is left to the application:**

- **Values.** Every scalar is a string, and nothing checks what it says unless a schema does.
- **Text that misleads.** Keys and names are compared by code point, so `admin` with a Latin
  `a` and with a Cyrillic one are two keys. Bidirectional controls are allowed (section 3), so
  a line can display in a different order from how it reads. A tool that shows YAML for
  review should make both visible.
- **Names.** A name is advisory and comes from the stream. An application that picks a schema
  or a behaviour by name should check it against the names it expects (section 4.3).
- **Text after a stop.** What follows a final `...` isn't read or checked. An application
  that takes it (section 4.4) has to treat it as untrusted.
