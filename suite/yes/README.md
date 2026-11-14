# Test suite for part 2

Tests for [YAML Easy Schema (YES)](../../spec/yaml-easy-schema.md), part 2 of the proposal, in the
format of [part 1's suite](../README.md), with the additions below. Part 2 is a work in progress, and
these tests will change with it. There are 842:

- the draft's 69 examples, tagged `spec`;
- 736 edge cases from the draft's checker;
- 15 tests of section 11's typed count, and 22 of section 9's full size, at limits a parser can reach
  (see below).

## Keys

`name`, `from`, `tags`, `fail`, `limit`, `keep`, `yaml` and `json` are part 1's. `json` is there to
read. It can't tell `2` from `2.0`, or a date from a string, so a harness compares `typed`. A test with
`keep` has no `typed` or `json`, as in part 1. It checks only that the stream is accepted or refused.

| Key | What it holds |
|---|---|
| `typed` | the typed events a parser delivers (below), in place of part 1's `tree` |
| `refused` | with `fail`: `schema` if a schema is refused, or `document` if a document doesn't fit its schema or holds a value the parser can't hold (section 2) |
| `at` | with `refused: document`: the path to the value, as the checker gives it |
| `schema` | an application's schema (section 3), as a whole stream |
| `root` | its root entry |
| `store` | the published files an application can get (section 3.1). Each key is a SHA-256 in lowercase hex, and its value is the file. In two tests a file doesn't hash to its key, on purpose |
| `cut` | `true` if the application turns on the cut (section 4.8) |
| `holds` | the fraction digits of a time that the parser holds (section 4.8) |
| `leap-second` | with `holds`: `true` if it holds a second `60` |
| `year-zero` | with `holds`: `true` if it holds the year `0000` |

- **`schema` and `root`.** A harness hands them to the parser before the stream. Some of these tests
  have a stream with no document. They check that the schema loads, or is refused, under the limit.
  That is what an application sees when it hands a schema over.
- **`holds`.** A test without it is for a parser that holds every time RFC 3339 allows, as one that
  delivers a date's text does. A parser that holds less runs the tests whose `holds`, `leap-second` and
  `year-zero` match its own, and skips the tests tagged for what it doesn't hold (below).
- **`refused`.** A refused test without it is also refused by part 1, through a syntax error or the
  size limit on the stream. The suite doesn't fix which refusal comes first.
- **`at`.** The path is `/` for the root, then each key or index after a `/`, unescaped. For a key
  the mapping doesn't take, or one it needs and doesn't have, it is the mapping's path (section 2). It
  is the first fault the checker meets. A parser that reports another fault in the same document first
  differs from the test in `at`, but not in whether the document is refused.

`bin/suite-to-data yes/src yes-data` writes each test to a directory as part 1's are, with `typed.event`
in place of `test.event`, and `schema.yaml`, `root`, `holds`, `refused`, `at`, `tags`, the flags `cut`,
`leap-second` and `year-zero`, and a `store/` with a file for each hash, where a test has them.

### Typed events

These are part 1's events. Where a scalar has a type, the type replaces `VAL`. Keys stay `=VAL`,
since a key is always a string.

| Event | For | Its text |
|---|---|---|
| `=VAL :text` | a string: `!str`, `!any`, a literal, or a value nothing types | the string |
| `=INT :n` | `!int` | the integer in base 10, with `-` if negative, no `+` and no leading zeros |
| `=BIG :n` | `!bigint` | the same |
| `=FLT :n` | `!float` | the binary64 value in the shortest digits that read back to it: `0.1`, `1e+23`, `-0.0`, `5e-324`. A harness reads it as binary64 and compares the bits, so the sign of zero counts |
| `=DEC :n` | `!decimal` | the number as written, after a pattern's reading (section 4.5): `+19.99` is `19.99`, `.5` is `0.5`, and `100e-2` stays `100e-2`. A harness compares the text |
| `=BOOL :b` | `!bool` | `true` or `false` |
| `=NULL` | `!null`, or an optional key with an empty value | none |
| `=DATE :text` | `!date` | the date as written |
| `=DATETIME :text` | `!datetime` | the time as written, or as cut (section 4.8) |
| `=BIN :hex` | `!binary` | the bytes, as two lowercase hex digits each |

### Tags

Each test is tagged with the standard types its roots reach. It also has a tag for each of the
following that it uses, so that a parser that does only part of the draft can skip the rest:

| Tag | What the test uses |
|---|---|
| `pattern` | a pattern (sections 4.3 and 4.5) |
| `range` | a limit such as `0..10` (section 4.2) |
| `precision` | precision and scale on `!decimal` (section 4.6) |
| `union` | a union (section 9), or ` \| ` in a plain scalar, which section 14 refuses |
| `sequence` | a sequence type (section 6) |
| `star` | `!*` (section 7) |
| `double-star` | `!**` (section 10) |
| `merge` | `<<` (section 11) |
| `reference` | a reference (section 11) |
| `published` | a published name (section 3.1) |
| `application` | an application's schema (section 3) |
| `typed` | section 11's typed count, with `keep` |
| `cut`, `holds` | what an application or a parser does with times (section 4.8) |
| `long-fraction`, `second-60`, `year-0000` | without `holds`: a time with more than 9 fraction digits, a second `60`, or the year `0000`, which a parser that holds less refuses (section 4.8) |
| `size` | a size limit other than the default |
| `spec` | an example from the draft |
| `error` | a refusal |
| `schema` | none of the above |

Tags come from the entries that the documents' roots reach, not the whole table, since an entry
that nothing reaches isn't a type (section 2).

## Where the answers come from

`suiteyes.py`, on the `ai` branch, writes the suite. It runs the tests of part 2's checker,
`schemacheck.py`, records each stream they type, and takes the checker's answer. Every one of those
tests passes, so each answer is also the result the test expected. `suiteyes.py --check` reads the
suite back the way `suite-to-data` reads the marks, and runs every test again.

The checker is one reading of the draft, not a reference parser. A parser written from the draft that
disagrees with a test has found a mistake in the test, the checker or the draft.

The checker takes three shortcuts, and the suite doesn't:

- **A table with no document.** The checker loads every entry of such a stream. But an entry that
  nothing reaches isn't a type (section 2), so a parser accepts the stream. 157 of these tests have a
  document added, stamped with an entry, and each one still gets the checker's answer: the schema is
  still refused, or still loads.
- **The size limit on a stream.** The checker applies a test's limit to the schema and to typed, but
  not to the stream. Part 1 applies it to the stream as well (part 1, section 10). So the suite also
  reads each stream under part 1's limit. It leaves out 17 tests that part 1 would refuse and the
  checker accepts. All 17 are section 11's tests of typed, and their limits are below the stream's
  held size, table included. In their place are 15 tests made from the same 11 streams, scaled so that
  typed can exceed held. They use a 400-character string or key where the checker uses 8 characters,
  and they turn the checker's 1 MB test into 1,000 types of a 1 KB string. Each one is set at the
  lowest limit that both held and typed allow. In the 4 where typed is what binds, it is also set at
  one less.
- **The size limit on a schema.** A schema from outside the stream is read under part 1's limit too
  (section 3), so `a: !str` holds 7 as text. The checker's 22 tests of a schema's full size load the
  schema without reading its text that way, at limits from 0 to 10, which no parser can pass. The
  suite leaves them out. In their place are 22 tests made from the same 11 schemas. Each is reached
  beside a mapping that names a 20-key mapping 40 times, and each name counts what it stands for, so
  full size passes what the text holds: about 1,010 against 510. Each is set at its full size, where
  it loads, and at one less.

The suite also leaves out 3 tests over 200 KB, and 7 that repeat another test.

## Not covered yet

- the line and column of a refusal, and its place through a reference (section 2);
- a library letting an application ignore a file's schema (section 3);
- application types and bindings (section 12), and emitting (section 13);
- an interface that delivers every document at once (`together` in part 1);
- section 15's open points.

## License

© 2026 Thomas Sawyer. Under the [MIT license](../LICENSE), as part 1's suite is.
