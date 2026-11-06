# A proposal for YAML 2.0: YAML Schema

*Draft 1, 2026-11-05*

This is part 2 of a proposal to the YAML core team, not a YAML specification. Part 1 is
[the language](yaml-2.0.md). Section 15 lists what is still open.

## 1. Overview

YAML needs no schema. Without one, a stream holds strings, sequences and mappings, and the
application reads them as it sees fit. A schema is a shared way to interpret data and
constrain it, and nothing more.

A schema is a shadow of the data. It has the data's shape, with each value replaced by its
type.

```yaml
--- &
service:
  image: !str
  replicas?: !int(0..100)
  ports: [!int, ...]
  mode: read | write
--- !service
image: nginx
replicas: 3
ports: [80, 443]
mode: read
```

```json
{"image": "nginx", "replicas": 3, "ports": [80, 443], "mode": "read"}
```

A schema is ordinary YAML, and adds no syntax. `!` means nothing to a parser, so `!int` is a
plain string that the schema gives a meaning to. A schema is a `--- &` document: its entries
are types, and `!name` names one. A schema adds nothing to the data but types: any default
is written in the file, as a merge (section 11).

Each example shows a stream, then what it delivers, one line of JSON per document. Examples
leave out `%YAML 2.0` and the plain `---` after it. An example marked `refused` must be refused.

## 2. Conformance

Everything a document's root reaches is checked before that document's data, so a misspelt
`!stirng` is caught at once. An entry nothing reaches isn't a type, because `motd: !important` is a
fine data entry of the same form.

A document that doesn't fit its schema is refused, as a syntax error is. A refusal gives the
line and column, and the path to the value. Through a reference, it gives the place the reference
is used, with the entry's line beside it. There is no lenient mode.

The time to type a stream must grow in line with its size, for any schema and any stream, even one
written to force it. Section 16 says how.

## 3. Applying a schema

A document gets its schema in one of two ways:

- **The file says.** `--- !name` types a document if the name is local and the file's own table
  has that entry. A schema written in with the data stamps it: that is how the file is meant to be
  read, and an application's schema doesn't replace it.
- **The application says.** A document with no stamp can take a schema the application got from
  elsewhere, and the application says which entry is the root. How it picks one is its own
  business: the file's name, its extension, or simply knowing what it reads. That schema stays
  out of the stream's table, so one schema can serve many files, and a file's entries can share
  its names.

A global name, one with a `/`, is never looked up in the table, so it stamps nothing. Nor does a
name the table doesn't have. A document with neither stays strings.

A library may let an application ignore a file's schema and read the document as it is, or hand it
the schema, which is YAML too.

A schema sees how each scalar was written, and that isn't in the delivered data (part 1, section
11). So it runs over what a parser read, not over what it delivered. A parser can type events as
they arrive, or a tree once it is built. A `--- &` document holds both types and data, and a
stream has one table: `!job` and `*defaults` look in the same place.

```yaml
--- &
defaults:
  retries: 3
job:
  name: !str
  retries: !int
--- !job
<<: *defaults
name: build
---
retries: 3
```

```json
{"retries": 3, "name": "build"}
{"retries": "3"}
```

## 4. Scalars

### 4.1 Standard types

| Type | Matches | Delivers |
|---|---|---|
| `!str` | any scalar | its text |
| `!int` | a plain scalar: `-?(0\|[1-9][0-9]*)` | an integer |
| `!float` | a plain scalar: an integer, which may have `.digits`, an exponent or both | a number |
| `!decimal` | a plain scalar, spelled as `!float` is | that exact number |
| `!bool` | a plain `true` or `false` | a boolean |
| `!null` | a plain `null` | null |
| `!date` | any scalar: an RFC 3339 full-date | a date |
| `!datetime` | any scalar: an RFC 3339 date-time | a date and time |
| `!binary` | any scalar: base64, RFC 4648 section 4, with line breaks skipped | bytes |
| `!any` | any node | that node, untyped |

The spellings are exact, so `0755`, `+1`, `1.`, `True` and `yes` are not numbers or booleans. A
pattern on `!int` can change this for integers (section 4.5), and nothing else can.

`!int`, `!float`, `!decimal`, `!bool` and `!null` match plain scalars only. So `3` can be an integer, and
`"3"` never is. A block scalar isn't plain. This is what a YAML 1.2 parser with JSON Schema
does today.

```yaml
--- &
n: [!int, ...]
--- !n
- 3
- -4
```

```json
[3, -4]
```

```yaml refused
--- &
n: !int
--- !n
"3"
```

```yaml refused
--- &
n: !bool
--- !n
yes
```

JSON has no date, so a date in JSON is quoted, and `!date` has to read it. That's why the last
three take a scalar however it's written.

`!binary` skips line breaks, because a `|` block of wrapped base64 is how a long value is usually
laid out. RFC 4648 leaves that choice to the format using it.

```yaml
--- &
blob: !binary
--- !blob
|
  aGVs
  bG8=
```

```json
"aGVsbG8="
```

### 4.2 Limits

`!int`, `!float`, `!decimal` and `!str` can carry a limit. For `!str`, a range counts code points.
Both ends are inclusive, and either can be left out. A limit may have an exponent, as
`!float(..3.4e38)` does.

```yaml
--- &
limits:
  percent: !int(0..100)
  ratio: !float(0..1)
  name: !str(1..)
  code: !str(..8)
--- !limits
percent: 100
ratio: 0.5
name: a
code: ''
```

```json
{"percent": 100, "ratio": 0.5, "name": "a", "code": ""}
```

```yaml refused
--- &
percent: !int(0..100)
--- !percent
101
```

A limit is written with `..` everywhere. A comma would work in a block, but it ends a plain
scalar in a flow collection (part 1, section 6.1).

### 4.3 Patterns

`!str(/pattern/)` limits a string by a pattern, and section 4.5 says what one does on `!int`. A
pattern is I-Regexp (RFC 9485), and it must match the whole string. I-Regexp has literals, `.`, classes, counts, groups, `|` and `\p{..}`.
It has no lookaround, no backreferences, no captures and no `\d`, `\w` or `\s`, which is why
it means the same in every language.

`\p{..}` uses Unicode 16 or later, since RFC 9485 names no version. Unicode never removes a
character, and a later version mostly adds letters, so two parsers can differ only on a character
one of them doesn't know yet.

`^` and `$` are refused outside a class. RFC 9485 reads them as ordinary characters, so a
writer who means an anchor would get a pattern that never matches. A pattern ends at the first
`/)`.

```yaml
--- &
tag: !str(/[a-z][a-z0-9-]*/)
tags: [!tag, ...]
--- !tags
- web
- db-1
```

```json
["web", "db-1"]
```

```yaml refused
--- &
tag: !str(/[a-z]+/)
--- !tag
web1
```

```yaml refused
--- &
tag: !str(/^[a-z]+$/)
```

A type expression is a plain scalar first, so it ends where any plain scalar ends (part 1,
section 6.1). A pattern can't get around that, and quoting one makes it a literal (section 5).
In a block, a space before `#` or after `:` is written `[ ]`. In a flow collection, a pattern
can't hold any of `, [ ] { }`, so a pattern that needs one is named in the table, as `tag` is
above, and the name goes in the collection.

```yaml
--- &
note: !str(/x:[ ]y/)
--- !note
'x: y'
```

```json
"x: y"
```

```yaml refused
--- &
tags: [!str(/[a-z]+/), ...]
```

### 4.4 Numbers

A number has no size in a schema. `!int` and `!float` say what is written, and each application
keeps it in whatever it has, so a program with 128-bit floats or big integers needs nothing
special. A width is a limit: `uint32: !int(0..4294967295)`. YAML writes digits, so byte order
doesn't arise.

A parser delivers the number written, or refuses. It never wraps an integer, and never loses
digits without saying so. A value loses digits if, once stored and written back to as many
significant digits as it was written with, it comes out different. Binary64 can't hold `0.1`
exactly, but `0.1` survives. `3.14159265358979323846` doesn't, and up to 15 significant digits
always do. A value too large to hold, or so small it would become 0, loses its digits too.

An application can ask to accept rounding on `!float`, because the digits may not matter to it.
A value then takes the nearest one it can hold, and one too large to hold is still refused.

`!decimal` allows no rounding, and an application can't ask for it. It is for money and anything
else where a rounded value is a wrong one. A parser keeps the digits and exponent as written and
never expands them, so `1e999999999` stays small. An application that can't keep the exact value
refuses it.

```yaml
--- &
order:
  price: !decimal(0..)
  ratio: !float
--- !order
price: 19.99
ratio: 0.1
```

```json
{"price": 19.99, "ratio": 0.1}
```

```yaml refused
--- &
pi: !float
--- !pi
3.14159265358979323846
```

Every parser holds integers from -2^63 to 2^64-1 and binary64 floats at least, and past that it may
refuse. A number that can't be held refuses the document: it doesn't count as no match, so
`!int | !float` can't round on one parser only, and `1e999` under `!float | !str` doesn't become a
string.

```yaml refused
--- &
n: !float | !str
--- !n
1e999
```

### 4.5 A pattern on `!int`

`!int(/pattern/)` replaces the standard spelling with the pattern. It matches a plain scalar that
the pattern matches, and reads the text as an optional sign and base-10 digits, so `+5` is 5 and
`007` is 7. What section 4.3 says of patterns holds, and so does what section 4.4 says of numbers.

```yaml
--- &
signed: !int(/[-+][0-9]+/)
offsets: [!signed, ...]
--- !offsets
- +5
- -3
```

```json
[5, -3]
```

The pattern takes the place of the spelling and doesn't add to it, so `5` isn't `!signed`. A quoted
scalar never is, as with any `!int`.

```yaml refused
--- &
signed: !int(/[-+][0-9]+/)
--- !signed
5
```

Text the pattern matches and that can't be read this way refuses the document, as a number that
can't be held does. It doesn't count as no match, because the schema has said it is an integer, so
`0x1f` below doesn't become a string.

```yaml refused
--- &
hex: !int(/0x[0-9a-f]+/)
n: !hex | !str
--- !n
0x1f
```

Section 10 shows how to apply a pattern like this to every value in a document.

## 5. Literals

Any text that isn't a type is a literal, and the value must be that text. A literal is a
string, so it matches however the value is written.

```yaml
--- &
access: read | write | none
--- !access
"write"
```

```json
"write"
```

`''` is the empty literal. A quoted scalar in a schema is always a literal, never a type, which
is how a literal can start with `!` or hold ` | `.

```yaml
--- &
mark: "!important"
--- !mark
!important
```

```json
"!important"
```

## 6. Sequences

A sequence is written as a sequence, and `...` repeats the item before it, any number of times,
none included. `[!int, !str]` is exactly those two, and `[!str, !int, ...]` is a string and then
any number of integers. `[!x, !x, ...]` is one or more.

```yaml
--- &
row: [!str, !int, ...]
rows:
  - !row
  - ...
--- !rows
- [a, 1, 2]
- [b]
```

```json
[["a", 1, 2], ["b"]]
```

```yaml refused
--- &
pair: [!int, !int]
--- !pair
[1, 2, 3]
```

In block form, `...` is an item, `- ...`, so it never starts a line.

## 7. Mappings

A mapping is written as a mapping. It takes only the keys it names. Order isn't checked, and
typed data keeps the document's order.

A key ending in `?` is optional. It may be absent, or written with no value, which delivers
null. A quoted key is always a literal key, so a key that ends in `?` or starts with `!` can
be written. If a type names a key both ways, the later one wins, because a merge can't tell them
apart.

```yaml
--- &
job:
  name: !str
  retries?: !int
  "why?": !str
--- !job
retries:
why?: because
name: build
```

```json
{"retries": null, "why?": "because", "name": "build"}
```

```yaml refused
--- &
job:
  name: !str
--- !job
name: build
nmae: test
```

```yaml refused
--- &
job:
  name: !str
--- !job
{}
```

A key that is a type takes every key it fits that isn't named, tried in the order written. A
key stays a string, and how it was written doesn't count, so `!int` as a key takes `1` and `"1"`.

```yaml
--- &
env:
  PATH: !str
  !str(/X_.*/): !str
  !int: !bool
--- !env
PATH: /bin
X_A: a
"7": true
```

```json
{"PATH": "/bin", "X_A": "a", "7": true}
```

A flow mapping works as well: `{!str: !int}`.

## 8. Named types

An entry in the table is a type, and `!name` uses it. A name in the table wins over a standard
one, so a later standard name can't change a schema. A name that is neither is an error.

Use `!name` to use a type, and `<<: *name` to paste a shape. A reference pastes the entry and
loses the name, and it can't sit inside a union or name itself.

```yaml
--- &
base:
  name: !str
step:
  <<: *base
  run: !str
steps: [!step, ...]
--- !steps
- name: build
  run: make
```

```json
[{"name": "build", "run": "make"}]
```

A named type can't take a limit: `!port(1..)` is refused. A cycle of names with no collection in
it is refused, since going round it never reaches a value: `a: !a`, and `a: !b | !int` with
`b: !a | !str`.

An entry a type has reached can't be replaced until `...`, because a replacement never changes what
came before it (part 1, section 8.1).

```yaml refused
--- &
a: !b
b: !int
--- !a
1
--- &
b: !bool
--- !a
true
```

## 9. Alternatives

`|` joins alternatives. The node's shape chooses first: a mapping looks among the mappings,
and a sequence among the sequences. There is at most one sequence. Exactly one mapping must
fit. A mapping fits if it has the required keys and literal values, and no key it doesn't take.
No alternative is tried by typing what is inside it, so typing never backtracks.

```yaml
--- &
circle:
  kind: circle
  r: !float
square:
  kind: square
  side: !float
shape: !circle | !square
--- !shape
kind: square
side: 2
```

```json
{"kind": "square", "side": 2.0}
```

Among scalars, literals and types are tried in the order written, and the first that matches
wins.

```yaml
--- &
limit: !int | never
limits: [!limit, ...]
--- !limits
- 30
- never
```

```json
[30, "never"]
```

```yaml refused
--- &
limit: !int | never
--- !limit
"30"
```

This puts a choice in the schema's hands. A schema that tries a number before a string reads
`1.10` as 1.1. It only happens where a schema asks for it, every parser gives the same result,
and a quoted value stays a string.

```yaml
--- &
version: !float | !str
versions:
  a: !version
  b: !version
--- !versions
a: 1.10
b: "1.10"
```

```json
{"a": 1.1, "b": "1.10"}
```

Inside `|`, a mapping must be named, since `: ` can't sit in a plain scalar, and a sequence
must come last, since a plain scalar can't start with `[`.

Each name counts once in a union, at its first place, so `!m | !m` is `!m`, and so is a union that
reaches `m` by two paths. `!any` in a union takes a node no other alternative fits.

```yaml
--- &
p:
  x: !int
q:
  x: !int
  z: !int
u: !p | !q | !p
list: [!u, ...]
--- !list
- {x: 1}
- {x: 1, z: 2}
```

```json
[{"x": 1}, {"x": 1, "z": 2}]
```

A union holds at most 10,000 positions once its names are expanded. A type counts 1, a literal
counts nothing, since a hash table finds it, and a pattern counts its characters and classes after
nested counts multiply, so `(a{1000}){1000}` counts a million. A mapping's type keys count as one
union, and a type on its own as a union of one. A schema past that is refused when it is loaded, by
every parser, so all of them agree on what loads.

```yaml refused
--- &
a: !str(/(a{1000}){1000}/)
```

## 10. Wherever this occurs

A named type can name itself, so one rule can reach every level of a document, with no special
form. This is JSON, written as an ordinary schema:

```yaml
--- &
json: !null | !bool | !int | !float | !str | !array | !object
array: [!json, ...]
object:
  !str: !json
--- !json
{"a": 1, "b": "1", "c": null, "d": [true, {"e": 1.5}]}
```

```json
{"a": 1, "b": "1", "c": null, "d": [true, {"e": 1.5}]}
```

Read by a parser built from part 1's grammar, this schema matched a JSON parser exactly on 994
real JSON files, and on 93 of the 95 files in JSONTestSuite that every JSON parser must accept.
The other 2 are repeated keys, which part 1 refuses.

The same form can pick out a key, at any depth:

```yaml
--- &
free: !str | !list | !map
list: [!free, ...]
map:
  timeout?: !int
  !str: !free
--- !free
timeout: 30
name: 30
jobs:
  - nested: {timeout: 7}
```

```json
{"timeout": 30, "name": "30", "jobs": [{"nested": {"timeout": 7}}]}
```

`free`, `list` and `map` are ordinary table entries, and any names would do.

It can also pick out a value by how it looks. Here any plain scalar with a sign is an integer, at
any depth, and everything else stays a string:

```yaml
--- &
signed: !int(/[-+][0-9]+/)
free: !signed | !str | !list | !map
list: [!free, ...]
map:
  !str: !free
--- !free
a: +5
b: 5
c: [-3, x]
d: {e: {f: +7}}
g: "+5"
```

```json
{"a": 5, "b": "5", "c": [-3, "x"], "d": {"e": {"f": 7}}, "g": "+5"}
```

A rule like this is an ordinary type, and each node has one type, so nothing has to rank a rule
against the type at a key. A schema uses it at the keys it chooses:

```yaml
--- &
signed: !int(/[-+][0-9]+/)
free: !signed | !str | !list | !map
list: [!free, ...]
map:
  !str: !free
job:
  image: !str
  args: !free
--- !job
image: +5
args: {n: +5}
```

```json
{"image": "+5", "args": {"n": 5}}
```

## 11. References and merge

A schema types what is delivered, where it is delivered. A table entry isn't typed by itself. A
reference is typed where it is used, so one entry can be typed two ways.

```yaml
--- &
port: 80
app:
  number: !int
  text: !str
--- !app
number: *port
text: *port
```

```json
{"number": 80, "text": "80"}
```

So a parser that keeps a reference as one shared node has to keep how each scalar was written,
and it can't share a typed result between two types.

An interface that keeps references types each node once under each type, and the sizes of what it
types count against the limit. Without that memory, a chain of 28 references in 632 bytes takes 1.6
billion visits. A type changes no count in held or full (part 1, section 10).

A merge is the way to give a default. An author's default is a `<<` from a table entry: local keys
win and missing ones fill in, visibly in the file, so the same bytes give the same data with or
without a schema. A format's own default is applied by its application. Merge is shallow, so a
nested default takes its own `<<` at that level.

## 12. Application types

A schema names types, and application code binds them. A parser builds nothing from a name,
whatever the name says. Only a name the application bound does anything, so its bindings are the
list of what a stream can get built. A stream can carry its own table (section 3), and that still
doesn't let a file choose a class and have its code run while loading.

This is how a language serializes objects. An application binds code to a name in the table. The
code takes what the entry delivers, and returns a value of the application's own, or refuses. An
unbound name stays what its entry says, so the same document still reads as plain data in any
other language.

```yaml
--- &
money: !str(/[0-9]+[.][0-9]{2}/)
invoice:
  total: !money
--- !invoice
total: 19.99
```

```json
{"total": "19.99"}
```

A known set of classes is a union, which lists them. Ruby can bind `point` to its `Point` class
and `sweep` to `Sweep`, and another language reads the same mappings. Part 1, section 13.1, says
what this can't carry.

```yaml
--- &
point:
  x: !int
  y: !int
sweep:
  target: !int
shape: !point | !sweep
shapes: [!shape, ...]
--- !shapes
- {x: 1, y: 2}
- target: 3
```

```json
[{"x": 1, "y": 2}, {"target": 3}]
```

A binding that refuses, refuses the document. It doesn't move on to the next alternative: the
schema chooses the type, and then the code runs, so code never runs on trial. It is called once per
use, so `*p` twice makes two calls and two values, since shared objects read as copies.

A bound name is also how to keep a check that a schema can't state: a rule on two scalar forms,
such as `true` or `${{ expression }}`, is a named string and a few lines of code.

## 13. Emitting and documenting

An emitter of typed data needs the same schema. It quotes a string that the type at that place
would read as something else: under `!int | !str`, the string `3` is written `"3"`. It writes an
integer in a spelling the type reads back as that number, so under `!signed` (section 4.5), 5 is
written `+5`, and it refuses if it has none. A bound value
needs the way back too: the application gives code that turns a `Point` into the mapping its entry
takes. Part 1, section 11, says the rest.

A comment directly above a key is its description. A parser still discards it, and only a tool
that keeps comments can show it. Part 1, section 11, says which key a comment belongs to.

## 14. Grammar

A type expression is what a plain scalar in a schema holds, so `pattern` and `literal` below can
only hold what a plain scalar can hold where it is written (section 4.3). The block and flow forms
of sequences and mappings are part 1's.

```ebnf
expression ::= part (" | " part)*
part       ::= type | sequence | "''" | literal
type       ::= "!" name limit?
limit      ::= "(" (range | "/" pattern "/") ")"
range      ::= number? ".." number?
number     ::= "-"? digit+ ("." digit+)? (("e" | "E") ("-" | "+")? digit+)?
sequence   ::= "[" expression ("," " "* expression)* ("," " "* "...")? "]"
literal    ::= any text, not starting with "!", "[", "{", '"' or "'", holding no " | "
name       ::= a table key, or a standard type, with no "/", "(", ")", "[", "]", "," or "|"
pattern    ::= I-Regexp, RFC 9485, holding no "/)"
```

A key in a schema mapping is a type if it is plain and starts with `!`. Otherwise it is literal,
and a plain key ending in `?` is optional.

## 15. Open points

- **Marking optional or required.** `?` marks optional keys, and 78% of the keys in the GitHub
  workflow schema are optional, so it is noisy there. Marking required keys may read better.
- **A reference under two types.** Section 11 types it where it is used. This is the agent's
  proposal, not yet decided.
- **Quoted scalars as literals.** Section 5 removes two warts, and hasn't been tried on a real
  schema. It means a type expression can't be quoted.
- **A minimum precision on `!float`.** A schema can't yet say that a value needs a certain number of
  digits, so that an application holding fewer refuses it even where the written value survives.
- **The standard types.** The list is short so far, and it should be thorough: times and durations,
  and names such as `!uri` and `!uuid`, checked against other type systems. Names can be added
  later, as section 8 says.
- **The ceiling on a union.** Section 9's 10,000 refuses none of 1,247 real patterns. A lower figure
  would make a schema of many overlapping unions quicker to load.
- **Typing under kept references.** Section 11's count hasn't been built or tried.
- **Ways past a stamp.** Section 3 lets a library ignore a file's schema. Whether one must is open,
  since an application checking files it didn't write depends on it.
- **`!null` and an empty value.** `!null` takes the plain `null` only, and `key?:` takes an
  empty value. Whether `!null` should take both is open.
- **More than one limit on a type.** A range and a pattern can't be combined today, so `!signed`
  (section 4.5) can't also say `0..100`.
- **Patterns on other types.** `!float`, `!decimal` and `!null` could take a pattern as `!int` does,
  so that `.5` or `~` could be read. `!bool` can't, because a pattern doesn't say which text is true.
- **Bases.** Section 4.5 reads base 10 only. Hex and octal would need a way to say which base a
  pattern means, and with those, `.inf`, `True` and `~`, a schema could state 1.2's Core Schema.
- **Patterns.** I-Regexp is proposed. An alternative worth weighing makes every character literal
  except what sits in brackets, so `v{0-9}.{0-9}` needs no escapes, and `{{` is a literal brace.
  With brackets outside ASCII, such as `⦃0-9⦄`, a pattern could also sit in a flow collection,
  which `[0-9]` can't, at the cost of being hard to type. A literal comma still couldn't.
- **Rules a schema can't state.** Rules across keys, such as "not both" or "if this then that".
  Limits on a sequence's or a mapping's size, beyond one or more. Two alternatives of one shape,
  told apart by content. These go to application code today.
- **Links across files.** A schema is one table. It has no `$ref` to another file, and reading one
  mustn't touch the network, so an application assembles what it needs.

## 16. Security

A schema can't run code, fetch anything or grow the data: a name does nothing unless the application
bound it. All a schema can do is spend time, and section 2 rules that out. Part 1, section 15, covers
the data.

- **A binding is a list of what may be built.** A library that binds every name to the class of
  that name, as Ruby's `unsafe_load` does with tags, hands the choice back to the file, which
  section 12 rules out.
- **A stamp isn't a check.** A file's own schema says how it is meant to be read, and it can be as
  lax as its author likes. An application that relies on a check of files it didn't write ignores
  or refuses a file's schema, and applies its own (section 3).
- **Forced collisions.** Part 1, section 7.4, sets the rule for keys, and it covers what typing adds:
  each data key against a type's keys, and `!name` in the table. A compiled schema shared between
  parsers needs a hash key of its own.
- **References.** A walk through a chain of references doubles at each link, so section 11 types
  each node once under each type.
- **Unions.** Names that repeat double at each level if read literally. Section 9 counts each name
  once, and its ceiling fixes how much a scalar can cost per character.
- **Patterns.** Matching takes time linear in the string, whichever engine does it, and section 9's
  ceiling limits a pattern's size. RFC 9485 warns that existing engines may not be linear, so such an
  engine can't be used on a schema someone else wrote.
- **Recursion is bounded by the data.** Typing goes down one level of data at each step through a
  named type that holds a collection, and an entry that only names itself is refused when the
  schema is loaded.
