# A proposal for YAML 2.0: YAML Easy Schema (YES)

**WORK IN PROGRESS. This part isn't finished. Its rules are still changing, no parser implements it
yet, and section 15 lists what is still open.**

*Draft 1, 2026-11-07*

This is part 2 of a proposal to the YAML core team, not a YAML specification. Part 1 is
[the language](yaml-2.0.md). Section 15 lists what is still open.

## 1. Overview

YES is a shadow schema. Its base form is the data itself: write out the keys and structure, and
put a type where each value would be.

```yaml
--- &
job:
  name: !str
  timeout?: !int(0..3600)
  mode: fast | safe
  steps:
    - run: !str
      retries: !int
    - ...
--- !job
name: build
timeout: 30
mode: safe
steps:
  - run: make
    retries: 2
  - run: test
    retries: 0
```

```json
{"name": "build", "timeout": 30, "mode": "safe", "steps": [{"run": "make", "retries": 2}, {"run": "test", "retries": 0}]}
```

That is the whole idea. `?` marks an optional key, `|` gives a choice and `...` repeats the item
before it. Everything else that shortens a schema is a way of compressing this form.

**Table definitions.** An entry names a type, so a shape used twice is written once (section 8).

```yaml
--- &
step:
  run: !str
  retries: !int
job:
  steps: [!step, ...]
  cleanup: !step
--- !job
steps:
  - run: make
    retries: 2
cleanup:
  run: rm
  retries: 0
```

```json
{"steps": [{"run": "make", "retries": 2}], "cleanup": {"run": "rm", "retries": 0}}
```

**Recursion.** An entry can name itself, so a shape of any depth has a short shadow (section 8).

```yaml
--- &
node:
  name: !str
  children?: [!node, ...]
--- !node
name: a
children:
  - name: b
```

```json
{"name": "a", "children": [{"name": "b"}]}
```

**Key globs.** `!*` takes any other key at its level (section 7), and `!**` applies rules here and
at every level below (section 10), so a rule doesn't have to be repeated wherever a key occurs.

```yaml
--- &
job:
  !**:
    timeout: !int
    retries: !int
--- !job
name: build
timeout: 30
steps:
  - run: make
    retries: 2
```

```json
{"name": "build", "timeout": 30, "steps": [{"run": "make", "retries": 2}]}
```

Table definitions and recursion lose nothing. Key globs do: below a `!**` no key is required by a
rule and an unknown key passes. So the shadow is for checking a file, and rules are for typing one.

**YAML needs no schema.** Without one, a stream holds strings, sequences and mappings, and the
application reads them as it sees fit. A schema is a shared way to interpret data and constrain
it, and nothing more.

A schema is ordinary YAML, and adds no syntax. In a table `!` is an ordinary character, so `!int`
is a plain string that the schema gives a meaning to. A schema is a `--- &` document: its entries
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
written to force it. For an interface that delivers full data, that is its full size (part 1,
section 10). Section 16 says how.

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

An application can also name, for its own reading, the level and `round` of `!datetime`, as a schema
would write them: `round 6` (section 4.8).
Because it names them, every program that names the same ones gets the same data. It can't ask for
whatever its library happens to hold, which would give `.123` in one language and `.123456` in
another. Nothing else in a schema can be changed this way.

A schema sees how each scalar was written, and that isn't in the delivered data (part 1, section
11). So it runs over what a parser read, not over what it delivered. A parser can type events as
they arrive, or a tree once it is built. Under a union of mappings it holds a mapping's events until
one alternative is left, which can be at the mapping's end. A `--- &` document holds both types and
data, and a stream has one table: `!job` and `*defaults` look in the same place.

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

### 3.1 Publishing a schema

A schema can be published as a file anyone can use. The file is a table: `%YAML 2.0` and one
`--- &`, with nothing after it, not even `...`. Its name ends in `.yes`, and the entry named like the
file, without `.yes`, is the root, so `address.yes` has an entry `address`, which types the document as
a local stamp's entry does.

```yaml
%YAML 2.0
--- &
line: !str(1..80)
address:
  street: !line
  floor?: !int
```

A published name is a global name that ends in such a file name, then `#sha256=` and the SHA-256 of
the file's bytes in 64 lowercase hex digits, as PEP 503 writes a hash in a URL. Its address is
`https://` and the name before the `#`, and a fragment never goes to the server, so that is an ordinary
URL. No other name has one. The path is the publisher's, so a version goes there.

```yaml
--- !tabcomputing.com/address/v1/address.yes#sha256=8789ccca7793386ebef9bb35f88d8b424239a44cae2bab4cbcd6222d8d2cda13
street: 1 Main St
floor: 3
```

```json
{"street": "1 Main St", "floor": "3"}
```

A parser treats this as any other name, so the data stays strings, as above. An application can
choose to look the name up, and then the name stamps the document as a local entry does, so this one
reads `{"street": "1 Main St", "floor": 3}`. The file's table stays out of the stream's. A library
looks nothing up unless the application asks it to.

An application that looks a name up refuses a file that doesn't hash to the name, and one with no
entry named like the file. If it can't get the file it refuses the document, because reading it as strings would give different data. The hash
is what identifies the file, so a copy from anywhere will do: a mirror, or a folder of the schemas an
application accepts, which needs no network.

A publisher never changes the bytes at an address: a new version goes at a new path, such as `v2`, as
a package index never replaces a file it has published. A file changed in place no longer hashes to
the names that stamp it, so every document stamped with it is refused. A change to a schema makes a
new name, so a name always means the same bytes. A fix reaches a file only when its stamp is edited, and that takes a tool. A format that wants every file to pick up
fixes uses an application's schema instead.

## 4. Scalars

### 4.1 Standard types

| Type | Matches | Delivers |
|---|---|---|
| `!str` | any scalar | its text |
| `!int` | a plain scalar: `-?(0\|[1-9][0-9]*)`, and one outside -2^63 to 2^64-1 refuses the document (section 4.4) | an integer |
| `!bigint` | a plain scalar, spelled as `!int` is, of any size | that integer, as written (section 4.4) |
| `!float` | a plain scalar: `-?(0\|[1-9][0-9]*)(\.[0-9]+)?([eE][-+]?[0-9]+)?`, JSON's number, and one too large for binary64 refuses the document (section 4.4) | the nearest binary64 number |
| `!decimal` | a plain scalar, spelled as `!float` is | that exact number, as written |
| `!bool` | a plain `true` or `false` | a boolean |
| `!null` | a plain `null` | null |
| `!date` | any scalar: an RFC 3339 full-date (section 4.8) | a date |
| `!datetime` | any scalar: an RFC 3339 date-time (section 4.8) | a date and time |
| `!binary` | any scalar: base64, RFC 4648 section 4, padded, with its pad bits zero, and with line feeds skipped | bytes |
| `!any` | any node | that node, untyped |

The spellings are exact, so `0755`, `+1`, `1.`, `True` and `yes` are not numbers or booleans. A
pattern can change this for a type that takes one (section 4.5), and nothing else can.

`!int`, `!bigint`, `!float`, `!decimal`, `!bool` and `!null` match plain scalars only. So `3` can
be an integer, and `"3"` never is. A block scalar isn't plain. This is what a YAML 1.2 parser with JSON Schema
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

`!binary` skips line feeds, because a `|` block of wrapped base64 is how a long value is usually
laid out, and RFC 4648 leaves that choice to the format using it. Anything else outside the
alphabet is no match, a CR or a space among them. RFC 4648 also lets a decoder refuse a value with
its padding left out or with pad bits that aren't zero, and here every decoder does, so `aGk` and
`aGl=` are not binary, and `aGk=` is.

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

`!int`, `!bigint`, `!float`, `!decimal` and `!str` can carry a limit. For `!str`, a range counts code points.
Both ends are inclusive, and either can be left out but not both, so `!int(..)` is refused, and so is
`!int(5..1)`. A limit may have an exponent, as `!float(..3.4e38)` does. A limit tests the number as
written, not its binary64 value, so `!float(..0.1)` takes `0.1` and refuses `0.10000000000000001`,
though binary64 reads both as the same value.

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

`!str(/pattern/)` limits a string by a pattern, and section 4.5 says what one does on other
types. A pattern is I-Regexp (RFC 9485), and it must match the whole string. I-Regexp has literals, `.`, classes, counts, groups, `|` and `\p{..}`.
It has no lookaround, no backreferences, no captures and no `\d`, `\w` or `\s`, which is why
it means the same in every language.

`\p{..}` uses Unicode 16 or later, since RFC 9485 names no version. Unicode never removes a
character, and a later version mostly adds them, so two parsers differ only on a character one of
them doesn't know yet, or on one whose category a later version changed, as Unicode 6.3 did for
U+180E.

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

`!int` is an integer from -2^63 to 2^64-1, on every parser. That holds every int64 and every uint64
value. `!bigint` is an integer of any size. A narrower width is a limit: `uint32: !int(0..4294967295)`.
`!float` is an IEEE 754 binary64 number, and `!decimal` is the number exactly as written. YAML writes
digits, so byte order doesn't arise.

A `!float` value is the binary64 value nearest the number written, the even one on a tie, as IEEE 754
rounds and as a JSON parser reads a number. So `3.14159265358979323846` is 3.141592653589793, and
`9007199254740993` is 9007199254740992. Every language in common use has binary64, on 32-bit machines
too. A parser doesn't use a wider type where it has one, or the same file would give different numbers:
C's `long double` holds 3.1415926535897932385 on x86 Linux, and every digit of `3.14159265358979323846`
on ARM64 Linux. A value whose digits must all be kept is a `!decimal`.

A value too large for binary64 refuses the document. Too large means it would round to infinity, as C's
`strtod` reads it, so `1.79769313486231570815e308`, within half a unit of binary64's largest value, is
that value, and `1.8e308` is too large. JSON has no infinity, so a parser can't deliver one. A value too
large doesn't count as no match, so a number never becomes text because of its size. As with `!int`
(below), a limit is tested first, on the number as written, and the size only on a value inside it, so
`!float(0..1) | !str` gives `1e999` as text, as it gives `2`, and `!float(0..) | !str` refuses it. A
value too small for binary64 is 0 and keeps its sign, as IEEE 754 has it: `1e-999` is 0, and `-1e-999`
and `-0` are negative zero.

```yaml
--- &
n: !float(0..1) | !str
--- !n
1e999
```

```json
"1e999"
```

```yaml refused
--- &
n: !float | !str
--- !n
1e999
```

`!decimal` is for money, and for anything else where a rounded value is a wrong one. A parser keeps the
digits and exponent as written and never expands them, so `1e999999999` stays small, and
`3.14159265358979323846` keeps all 21 digits. What they become is up to the application: a decimal
type, such as Python's `Decimal` or Java's `BigDecimal`, or a float with more precision than binary64,
such as one of MPFR's.

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

```yaml
--- &
pi:
  float: !float
  decimal: !decimal
--- !pi
float: 3.14159265358979323846
decimal: 3.14159265358979323846
```

```json
{"float": 3.141592653589793, "decimal": 3.14159265358979323846}
```

An integer outside `!int`'s range refuses the document, as a float too large for binary64 does. It
doesn't count as no match, so `!int | !str` refuses `1` followed by 29 zeros, and doesn't give text. A
limit is tested first, on the number as written, and the range only on a value inside it,
so `!int(0..10) | !str` gives that value as text, as it gives `11`. Every parser holds the whole range
without losing digits. So a JavaScript parser can't deliver a value past 2^53 as
a `number`, which is what JavaScript's own `JSON.parse` does: it reads `9007199254740993` as
9007199254740992, and `18446744073709551615` as 18446744073709552000.

`!bigint` takes an integer of any size, so no parser refuses one for its size. A parser checks its
spelling and limit on the digits as written, and delivers it as written: it doesn't convert the digits
while reading, as `!decimal` doesn't expand an exponent. Converting a long value takes longer than reading
it, and the longer the value, the more so. Python's `int()` takes 6 seconds on 12.8 million digits, and
refuses past 4,300 by default for this reason. Typing must take time in line with the size (section 2),
so converting is left to the application, when it uses the value.

```yaml
--- &
row:
  id: !int
  serial: !bigint
--- !row
id: 18446744073709551615
serial: 123456789012345678901234567890
```

```json
{"id": 18446744073709551615, "serial": 123456789012345678901234567890}
```

```yaml refused
--- &
id: !int | !str
--- !id
18446744073709551616
```

### 4.5 A pattern on another type

`!int`, `!bigint`, `!float`, `!decimal` and `!null` take a pattern too, and it replaces the type's
standard spelling. The type matches a plain scalar that the pattern matches, and reads the value from it:

- `!int` and `!bigint` read an optional sign and base-10 digits, so `+5` is 5 and `007` is 7.
- `!float` and `!decimal` read an optional sign, digits with at most one `.`, and an optional
  exponent, so `+19.99` is 19.99, `.5` is 0.5 and `1.` is 1.
- `!null` is null whatever the pattern matched, so `!null(/~|null/)` reads both.

What section 4.3 says of patterns holds, and so does what section 4.4 says of numbers. A pattern says
which text is the type, and not how many digits a value may have: section 4.6 does that.

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

```yaml
--- &
cents: !decimal(/[0-9]+\.[0-9]{2}/)
none: !null(/(~|null)?/)
item:
  price: !cents
  ratio: !float(/[0-9]*\.[0-9]+/)
  note: !none | !str
--- !item
price: 19.99
ratio: .5
note: ~
```

```json
{"price": 19.99, "ratio": 0.5, "note": null}
```

```yaml refused
--- &
cents: !decimal(/[0-9]+\.[0-9]{2}/)
--- !cents
19.9
```

The pattern takes the place of the spelling and doesn't add to it, so `5` isn't `!signed`, and under
`!null(/~/)` a plain `null` isn't null. A quoted scalar never matches one, as section 4.1 says.

```yaml refused
--- &
signed: !int(/[-+][0-9]+/)
--- !signed
5
```

Text the pattern matches and that can't be read this way refuses the document, as a number that
can't be held does. It doesn't count as no match, because the schema has said it is that type, so
`0x1f` below doesn't become a string.

```yaml refused
--- &
hex: !int(/0x[0-9a-f]+/)
n: !hex | !str
--- !n
0x1f
```

Section 10 shows how to apply a pattern like this to every value in a document.

### 4.6 Precision and scale on `!decimal`

`!decimal(38:10)` uses SQL's two figures, as `NUMERIC(38,10)` does. The precision, 38, is how many
digits a value may have in all, and the scale, 10, is how many of them may come after the point, so at
most 28 come before it. Unlike SQL, which stores a value at its scale, a value is delivered as written,
neither padded nor rounded, so `1.5` under `!decimal(5:2)` is 1.5, not 1.50. The test is on the exact
value, so `1.50` fits `!decimal(3:1)`, and `1e3` has 4 digits before the point. A value with more
digits is no match, as one outside a limit is, and it is never rounded. The precision is at least 1,
and the scale is no larger than it. A colon stands where SQL has a comma,
because a comma would end the type in a flow collection (section 4.2). Section 15 gives another
spelling.

```yaml
--- &
prices: [!decimal(5:2), ...]
--- !prices
- 999.99
- 1.50
- -0.5
```

```json
[999.99, 1.50, -0.5]
```

```yaml refused
--- &
price: !decimal(5:2)
--- !price
1.005
```

### 4.7 Precision, limit and pattern together

A type can carry `round`, a precision, a limit and a pattern together, in one pair of parentheses, in
that order, with one space between each. Each says something of its own: the pattern says which text is
the type, the precision how many digits the value may have, the limit which values are allowed, and
`round` that a value past its type's level is fitted to it. A precision goes on `!decimal` only, a
limit on `!str` and the numbers, and a pattern on those and on `!null`. `round` goes on `!datetime`
only, with its number of fraction digits, which stands where a precision would (section 4.8).

A type carries at most one of each, so each type has one spelling:
`!int(/[-+][0-9]+/ 0..100)` is refused, and so is `!int(0..10 20..30)`. With the pattern last, it still
ends at the first `/)`.

```yaml
--- &
percent: !int(0..100 /[-+][0-9]+/)
cents: !decimal(5:2 0.. /[0-9]+\.[0-9]{2}/)
row:
  change: !percent
  price: !cents
--- !row
change: +5
price: 19.99
```

```json
{"change": 5, "price": 19.99}
```

```yaml refused
--- &
cents: !decimal(5:2 0.. /[0-9]+\.[0-9]{2}/)
--- !cents
1000.00
```

Two limits that must both hold are one narrower limit, so one is enough. A value in either of two
ranges is a union (section 9).

```yaml
--- &
n: !int(1..10) | !int(20..30)
--- !n
25
```

```json
25
```

```yaml refused
--- &
n: !int(1..10) | !int(20..30)
--- !n
15
```

Anything more, such as a multiple of 5 or a bound that excludes its own value, as `0 < x` does, is left
to the application (section 15).

### 4.8 Dates

`!date` and `!datetime` take RFC 3339's grammar, from its section 5.6, with section 5.7's days of the
month, so `2001-02-29` is no match and `2000-02-29` is a date. `T` and `Z` may be lowercase, as section
5.6 allows. The space in place of `T`, which section 5.6 lets an application choose, isn't the grammar,
so `2001-02-03 04:05:06Z` is no match. Year `0000` is a date.

A second of `60` is a leap second. Section 5.7 allows one only at the end of a month in which a leap
second occurs, and only a table of them can say which months those are. Tables differ by when they
were made, so a parser uses none: it allows `60` at 23:59 UTC on the last day of any month, once the
offset is taken off. So `1990-12-31T23:59:60Z` and `1990-12-31T18:59:60-05:00` are dates, and
`1990-12-30T23:59:60Z` is no match.

A parser delivers the value written, or refuses. One it can't hold refuses the document. It doesn't
count as no match, so `!datetime | !str` can't give text on one parser only. Python's `datetime` holds no second
`60`, no year `0000` and 6 fraction digits, and JavaScript's `Date` no second `60` and 3 fraction
digits. Python's `fromisoformat` and JavaScript's `Date` drop the digits past those without saying so,
which a parser mustn't do.

`!datetime(3)` says how many fraction digits a value keeps, as SQL's `TIMESTAMP(3)` does. A value with
more refuses the document, so a time never becomes text because of how many digits it has. One with
fewer is delivered as written, so `06.5` stays `06.5`. The number says what an application must hold. One that keeps fewer
than 3 fraction digits refuses any value of `!datetime(3)`, even one with none.

`round` keeps the digits up to that number and drops the rest, so `2001-02-03T04:05:06.1234567Z` under
`!datetime(round 3)` is `2001-02-03T04:05:06.123Z`. A time is never rounded up, because that can carry:
`1999-12-31T23:59:59.9999999Z` would become a time in 2000. `round` on `!datetime` needs a number of
digits, and `!date` takes neither.

```yaml
--- &
reading:
  at: !datetime(round 3)
--- !reading
at: 2001-02-03T04:05:06.1234567Z
```

```json
{"at": "2001-02-03T04:05:06.123Z"}
```

```yaml refused
--- &
at: !datetime(3)
--- !at
2001-02-03T04:05:06.1234Z
```

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
"!important"
```

```json
"!important"
```

## 6. Sequences

A sequence is written as a sequence, and `...` repeats the item before it, any number of times,
none included. `[!int, !str]` is exactly those two, and `[!str, !int, ...]` is a string and then
any number of integers. `[!x, !x, ...]` is one or more. `[]` is a sequence with nothing in it, so
`!int | []` is an integer or an empty sequence.

```yaml
--- &
u: !int | []
--- !u
[]
```

```json
[]
```

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

A mapping is written as a mapping. It takes only the keys it names, and any that a type key or `!*`
takes below, unless a `!**` reaches it (section 10). Order isn't checked, and typed data keeps the
document's order.

A key ending in `?` is optional. It may be absent, or written with no value, which delivers
null. A quoted key is always a literal key, so a key that ends in `?` or starts with `!` can
be written. A type can name one key two ways: `a` and `a?` in one mapping, or `why?` and `"why?"`
through a merge, which takes them as one key (part 1, section 9.1). The later one wins, with its
spelling and its value, though a merged key keeps its place.

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
A key that a type key can't hold refuses the document, as a value does (section 4.4), so under
`!float` as a key, `1e999` is refused, not passed to the next key.

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

`!*` as a key takes every other key at this level, whichever order it is written in: any key the
mapping doesn't name and no type key fits. Its value can be any type.

```yaml
--- &
env:
  PATH: !str
  !*: !int
  !str(/X_.*/): !str
--- !env
PATH: /bin
X_A: a
retries: 3
```

```json
{"PATH": "/bin", "X_A": "a", "retries": 3}
```

It isn't a wildcard inside a name. `!ts_*` is refused as an unknown type, and a key that starts with
`ts_` is written `!str(/ts_.*/)`, so there is one pattern language.

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

A named type can name itself through a collection, as a tree does:

```yaml
--- &
node:
  name: !str
  children?: [!node, ...]
--- !node
name: a
children:
  - name: b
```

```json
{"name": "a", "children": [{"name": "b"}]}
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
fit. A mapping fits by its own keys: it has the required keys, the value of each key whose type is
only literals, and no key it doesn't take. A choice never looks below those keys, and no alternative
is tried by typing what is inside it, so typing never backtracks.

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
reaches `m` by two paths. `!any` in a union is tried last, wherever it is written, so it takes a node
no other alternative fits: `!any | !int` reads `3` as 3.

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

A union holds at most 1,024 positions once its names are expanded. A type counts 1, a literal
counts nothing, since a hash table finds it, and a type with a pattern counts its pattern instead. A
pattern is counted as written. Each character, class, `.` and `\p{..}` counts 1, alternatives and
groups add what they hold, and a count multiplies what it repeats: `{n}` and `{n,}` by n, `{n,m}` by
m, and `*`, `+`, `?` and `{0,}` by 1. So `(a{1000}){1000}` counts a million, and
`abc|abd` counts 6. A mapping's type keys count as one union, and so do the type keys of all the
mapping alternatives in a union, since fitting tests a key against each of them. A type on its own
is a union of one. A schema past that is refused when it is loaded, by every parser, so all of them
agree on what loads. Of SchemaStore's 1,287 patterns, counted this way,
one goes past it, a case-insensitive list of names at 11,831 positions, and would have to be loosened.
The next has 772, and no real union of patterns has more than 782.

A schema has a full size too, and it can't pass the size limit (part 1, section 10). Like a stream's,
it is worked out by addition before anything is built. Each entry a schema reaches, and each place
in those entries that holds a type, adds what its type expands to: 1 for a literal, a standard type,
a sequence or a name, the count above for a pattern, 1 for a mapping plus 1 for each key it names, a `!**`'s among
them, and for a name also what the name stands for. A mapping's values and a sequence's items are places of
their own, so they aren't counted in it, and a type that contains itself still has a full size.
Unlike the ceiling, this counts a name every time it is written. So 2 million lines of `aN: !big | !int` are refused, though each union is within the ceiling.
All 721 schema families on SchemaStore together declare 90,006 keys, so no real schema comes near it.

```yaml refused
--- &
a: !str(/(a{1000}){1000}/)
```

## 10. Wherever this occurs

`!**` as a key means here and at every level below. It takes every key the mapping doesn't name, at
this level and under it, and a sequence adds no level. Collections are walked and its type applies
to the scalars it reaches, so that type can't hold a sequence or a mapping. This is JSON:

```yaml
--- &
json:
  !**: !null | !bool | !int | !float | !str
--- !json
{"a": 1, "b": "1", "c": null, "d": [true, {"e": 1.5}]}
```

```json
{"a": 1, "b": "1", "c": null, "d": [true, {"e": 1.5}]}
```

Read by a parser built from part 1's grammar, this schema matched a JSON parser exactly on 1,015
real JSON files, and on 93 of the 95 files in JSONTestSuite that every JSON parser must accept.
The other 2 are repeated keys, which part 1 refuses.

An integer outside `!int`'s range refuses the document here. None of those 1,015 files holds one, and
3 of JSONTestSuite's `i_` files do, which RFC 8259 lets a parser read or refuse. With `!bigint` in place
of `!int`, they are read. A float too large for binary64 refuses the document too (section 4.4). None of the
1,015 files holds one, and 5 `i_` files do, which Python's `json` reads as infinity. The 2 `i_` files
whose float is too small for binary64 read as 0, as `json` reads them.

`!**` covers the node it sits on as well, so a type with `!**` and no required keys also takes a
scalar or a sequence: `5` and `[1, 2]` are JSON here too. In a union the node's shape chooses first
(section 9), so there it takes mappings only.

`!**` can pick out a value by how it looks. Here any plain scalar with a sign is an integer, at any
depth, and everything else stays a string:

```yaml
--- &
signed: !int(/[-+][0-9]+/)
free:
  !**: !signed | !str
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

Its value can instead be a mapping of rules, which apply at this level and every level below. A key
there picks out that key at every level, and a key that is a type picks out the keys it fits. `!*`
there takes every other key, as it does anywhere, but a `!**` walks every collection, so it only
sees scalars and its type has to fit one. With no `!*` there, other scalars stay strings. A rule's
value can be any type. A rule is never required, and `?` on one only lets the key be written with no
value.

```yaml
--- &
free:
  !**:
    timeout: !int
--- !free
timeout: 30
name: 30
jobs:
  - nested: {timeout: 7}
```

```json
{"timeout": 30, "name": "30", "jobs": [{"nested": {"timeout": 7}}]}
```

A key is looked up in the mapping type at its place, then in the nearest `!**`, and nowhere else. So
the closest rule wins, and the order they are written in doesn't matter. A `!**` replaces any `!**`
above it for everything below it, and rules from above can be kept with a merge.

```yaml
--- &
signed: !int(/[-+][0-9]+/)
cfg:
  address:
    name: !str(..40)
    street?: !str(..100)
  !**:
    !str(/ts_.*/): !date
    !*: !signed | !str
--- !cfg
address: {name: Ann, ts_moved: 2026-11-06, floor: +3}
count: +5
zip: 02134
ts_start: 2026-11-06
jobs:
  - ts_end: 2026-11-07
    n: -3
```

```json
{"address": {"name": "Ann", "ts_moved": "2026-11-06", "floor": 3}, "count": 5, "zip": "02134", "ts_start": "2026-11-06", "jobs": [{"ts_end": "2026-11-07", "n": -3}]}
```

```yaml refused
--- &
cfg:
  name: !str(..4)
  !**:
    !str(/ts_.*/): !date
--- !cfg
name: Ann
jobs:
  - ts_end: soon
```

Below a `!**` every mapping takes every key, as `floor` shows, though the keys it requires are still
required. A mapping is closed only where no `!**` reaches it. An alternative is then chosen by its
required keys and literal values alone, so `note` below rules nothing out, and if two fit the
document is refused. `!any` at a key leaves everything under it untyped, since that is the closest
rule.

```yaml
--- &
circle:
  kind: circle
  r: !float
square:
  kind: square
  side: !float
cfg:
  shape: !circle | !square
  !**: !str
--- !cfg
shape: {kind: square, side: 2, note: x}
```

```json
{"shape": {"kind": "square", "side": 2.0, "note": "x"}}
```

A `!**` reaches only its own place and what is below it, so the rest of a schema stays as strict as it was. Here `job`
takes only its two keys:

```yaml
--- &
signed: !int(/[-+][0-9]+/)
job:
  image: !str
  args?:
    !**: !signed | !str
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

An interface that keeps references types each node once for each type and nearest `!**`. The `!**`
is part of that because it can change what one type does to one node:

```yaml
--- &
v: {x: 1}
leaf: {}
root:
  a:
    child: !leaf
    !**: !int
  b:
    child: !leaf
    !**: !str
--- !root
a:
  child: *v
b:
  child: *v
```

```json
{"a": {"child": {"x": 1}}, "b": {"child": {"x": "1"}}}
```

Without that memory, a chain of 28 references in 632 bytes takes 1.6 billion visits. With it, a node
is still typed once for each type that reaches it, so the work can pass what held counts: a string of
1 MB named by 1,000 references, each under a different type, is read 1,000 times. So typing keeps a
third number, typed, beside held and full (part 1, section 10). Each time a node is typed, its own
size is added to typed: what held counts for the node alone, which is 1 with a scalar's bytes or a
mapping's keys, and not the values or items below it, which add their own when they are typed. Each
type written in the schema is one type, and a name is its entry's, so `!job` in two places is one type
and `!str` in two places is two. Typed counts the document being typed. An interface that keeps
references applies the limit to typed as well as held. A type changes nothing in held or full.

```yaml
--- &
s: abcdefgh
one: [!str, ...]
three: [!str(/a.*/), !str(/.*h/), !str(1..)]
--- !one
[*s, *s, *s]
--- !three
[*s, *s, *s]
```

```json
["abcdefgh", "abcdefgh", "abcdefgh"]
["abcdefgh", "abcdefgh", "abcdefgh"]
```

Under `one`, `s` is typed once, since `...` repeats one type, so typed is 10: 1 for the sequence and 9
for `s`. Under `three` it is typed three times, so typed is 28. Each document's held is 4.

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
type       ::= "!" name args?
args       ::= "(" ("round ")? body ")"
body       ::= (level " ")? (range " ")? regex | (level " ")? range | level
level      ::= precision | whole
precision  ::= whole ":" whole, the first at least 1 and the second no larger than the first
whole      ::= "0" | digit+ not starting with "0"
range      ::= number ".." number? | ".." number, the first no larger than the second
regex      ::= "/" pattern "/"
number     ::= "-"? digit+ ("." digit+)? (("e" | "E") ("-" | "+")? digit+)?
sequence   ::= "[]" | "[" expression ("," " "* expression)* ("," " "* "...")? "]"
literal    ::= one or more characters, not starting with "!", "[", "{", '"', "'" or a space, not
               ending with a space, holding no " | "
name       ::= a table key, or a standard type, with no space, tab, "/", "(", ")", "[", "]", "," or "|"
pattern    ::= I-Regexp, RFC 9485, holding no "/)"
```

A key in a schema mapping is a type if it is plain and starts with `!`. `!*` is section 7's key, and
`!**` is section 10's. Otherwise it is literal, and a plain key ending in `?` is optional.

## 15. Open points

- **Marking optional or required.** `?` marks optional keys, and 78% of the keys in the GitHub
  workflow schema are optional, so it is noisy there. Marking required keys may read better.
- **Quoted scalars as literals.** Section 5 removes two warts, and hasn't been tried on a real
  schema. It means a type expression can't be quoted.
- **Spelling precision and scale.** `!decimal(38:10)` follows SQL's `NUMERIC(38,10)`: the digits in all,
  then those after the point. SQL's comma can't stay (section 4.6). A picture would give the digits
  before and after the point, `!decimal(28.10)`, as COBOL's `PIC S9(28)V9(10)` does. That reads as a
  number, and isn't one: `28.10` and `28.1` would be different types, and `!decimal(28.10)` is two
  characters from `!decimal(..28.10)`, a limit. `38:10` can't be read as a number, but a reader has to
  know that the first figure is the total.
- **What every parser holds of a date.** Section 4.4 gives `!int` a range every parser holds. Dates
  have none yet: Python holds 6 fraction digits, JavaScript 3, .NET 7, and Java and Go 9. Without one,
  a parser could refuse every fraction.
- **A date's offset.** Whether a value keeps its offset, so that `2001-02-03T04:05:06+05:00` and
  `2001-02-02T23:05:06Z`, the same instant, are different values. And whether `-00:00`, which RFC 3339
  section 4.3 gives as an unknown offset, differs from `Z`. Python reads `-00:00` as UTC, and
  JavaScript's `Date` keeps no offset at all.
- **The standard types.** The list is short so far, and it should be thorough: times and durations,
  and names such as `!uri` and `!uuid`, checked against other type systems. Names can be added
  later, as section 8 says.
- **Typing under kept references.** Section 11's typed count is built in a checker, but not yet in a
  parser.
- **Ways past a stamp.** Section 3 lets a library ignore a file's schema. Whether one must is open,
  since an application checking files it didn't write depends on it.
- **`!null` and an empty value.** `!null` takes the plain `null` only, and `key?:` takes an
  empty value. Whether `!null` should take both is open. A pattern can already say both:
  `!null(/(null)?/)` (section 4.5).
- **Patterns on `!bool` and dates.** These take none, because a pattern can't say which text is true,
  or which digits are the month, as in `11/07/2026`. Two patterns on `!bool`, one for each value, could.
- **Bases.** Section 4.5 reads base 10 only. Hex and octal would need a way to say which base a
  pattern means, and with those, `.inf` and `True`, a schema could state 1.2's Core Schema.
- **Patterns.** I-Regexp is proposed. An alternative worth weighing makes every character literal
  except what sits in brackets, so `v{0-9}.{0-9}` needs no escapes, and `{{` is a literal brace.
  With brackets outside ASCII, such as `⦃0-9⦄`, a pattern could also sit in a flow collection,
  which `[0-9]` can't, at the cost of being hard to type. A literal comma still couldn't.
- **Closed mappings below `!**`.** Below one, every mapping takes every key, so a schema can't close
  a mapping there, and a typo in a key passes. `!**` could stop at a named type, at the cost of
  naming a mapping changing what it accepts.
- **Rules a schema can't state.** Rules across keys, such as "not both" or "if this then that".
  Limits on a sequence's or a mapping's size, beyond one or more. A multiple of a number, or a bound
  that excludes its own value, as `0 < x` does (section 4.7). Two alternatives of one shape,
  told apart by content. These go to application code today.
- **Hashes in published names.** Section 3.1 takes `sha256` only. PEP 503 lets a hash be any that
  Python's `hashlib` always has, such as `sha512`, and whether to allow others is open.
- **Links across files.** A schema is one table. Section 3.1 publishes a whole schema, but a schema
  has no `$ref` to part of another file, so an application assembles what it needs.

## 16. Security

A schema can't run code, fetch anything or grow the data: a name does nothing unless the application
bound it. All a schema can do is spend time, which section 2 rules out, and make an event parser hold
more. A union of mappings near the root can hold up to the whole document. The size limit bounds
that, and there is no separate limit on what is held, because one would differ between parsers, as
depth does. Part 1, section 15, covers the data.

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
  each node once for each type and nearest `!**`, and counts each time in typed.
- **Unions.** Names that repeat double at each level if read literally. Section 9 counts each name
  once, and its ceiling fixes how much a scalar can cost per character. A schema's full size, which
  counts a name every time, limits what loading it can cost.
- **Mapping alternatives.** A choice reads only a mapping's own keys, so a parser that holds events
  links each collection's start to its end and steps over what is inside. Scanning instead costs
  depth times size, which section 2 rules out.
- **Patterns.** Matching must take time linear in the string, and section 9's ceiling limits a
  pattern's size. RFC 9485 warns that existing engines may not be linear, so such an
  engine can't be used on a schema someone else wrote.
- **Big integers.** Converting decimal digits to binary takes more than linear time, so `!int`'s range is
  fixed, and a parser doesn't convert a `!bigint` while reading (section 4.4).
- **`!**`.** A key is looked up in the mapping type at its place and in the nearest `!**`, and nowhere
  else, so nesting them adds nothing per key.
- **Published names.** Any stream can name any host, and a name can spell an IP address, so a library
  that looked names up by itself would let a stranger's file send requests from the reader's machine,
  as XML's external entities can. That is why only an application can ask for it. One that fetches
  uses `https`, refuses private addresses, even after a redirect, and applies the size limit. A hash
  that matches proves the bytes, not that the schema is any good, and a stamp isn't a check.
- **Recursion is bounded by the data.** Typing goes down one level of data at each step through a
  named type that holds a collection, and an entry that only names itself is refused when the
  schema is loaded.
