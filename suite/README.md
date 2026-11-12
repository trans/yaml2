# Test suite for part 1

Tests for [the language](../spec/yaml-2.0.md), Draft 1, in the format of the YAML project's
[yaml-test-suite](https://github.com/yaml/yaml-test-suite), with the changes below. There are 362:

- the draft's 59 examples, tagged `spec`;
- 250 edge cases from the draft's checker;
- 53 new ones: the size limit at each boundary and one under it, 256 levels of nesting, CR LF
  line breaks, the stop offset, a tab after a reference, key order, and a fragment in a name.

## Files

`src/` has one file per test, named by a four-character ID as yaml-test-suite's are. Each file is a
YAML 1.2 list of tests with these keys:

| Key | What it holds |
|---|---|
| `name` | what the test is about |
| `from` | the section of the draft it tests |
| `tags` | topics, separated by spaces |
| `fail` | `true` if a parser must refuse the stream |
| `limit` | the size limit for the test, if it isn't the default |
| `keep` | `true` if the test is for an interface that keeps references |
| `together` | `true` if the test is for an interface that delivers all the documents at once |
| `yaml` | the whole stream, including `%YAML 2.0` and the first `---` |
| `tree` | the events a parser delivers |
| `json` | the data, one line of JSON per document |
| `rest` | the text after a `...` that stopped the parser |

`bin/suite-to-data src data` writes each test to a directory of its own, as yaml-test-suite's data
branch has them: `===`, `in.yaml`, `test.event`, `in.json` and `error`, and `rest`, `limit`, `keep`
and `together` where a test has them. It needs PyYAML.

## How it differs from yaml-test-suite

2.0 delivers less than 1.2 does (section 11), so there are fewer events:

- `+STR` and `-STR` hold the stream, `+DOC` and `-DOC` a document, `+MAP` and `-MAP` a mapping,
  `+SEQ` and `-SEQ` a sequence, and `=VAL :` a string. There are no anchors, aliases, tags or
  styles. Every string is written `=VAL :`, as 1.2 writes a plain scalar, because the way a scalar
  was written isn't data. The `:` only marks where the string starts.
- A named document is `+DOC !name`. `+DOC` and `-DOC` don't show `---` or `...`: every document
  has a marker, and how a document ended isn't data, apart from a stop, which `rest` shows.
- Keys keep their order. A harness must compare the objects in `json` in order.
- A test that stops at `...` has `rest`, the text after the line with `...`. A parser reports
  where that text starts as an offset in bytes (section 4.4), so a harness takes the bytes of
  `in.yaml` from that offset and compares them with `rest`. A test without `rest` must not stop.
- A test without `limit` uses the default, 64 MiB (section 10). A test with `keep` or `together` is
  for that interface alone, and a parser that doesn't offer it skips the test. A test with `keep`
  has no `tree` or `json`: it checks only that the stream is accepted or refused.
- A test with `fail` has no `tree`. Section 2 requires a refusal to give the line and column, and
  the suite doesn't check them yet.

### Characters

`yaml`, `tree`, `json` and `rest` use yaml-test-suite's marks for characters that are hard to see:
`␣` for a space at the end of a line, `»` after any number of `—` for a tab, `←` for a carriage
return, `↵` for a line break that the block would otherwise drop, and `∎` at the end when there is
no final line break. `⇔` isn't used.

A stream holding a control character other than a tab, a line feed or a carriage return, or another
character from the list in the next paragraph, is written as a double-quoted string with escapes
instead. That covers every character a YAML 1.2 file can't hold, the three that YAML 1.1 reads as
line breaks, and the byte order mark.

In `tree`, a string is escaped as yaml-test-suite escapes it, with `\\`, `\0`, `\b`, `\t`, `\n` and
`\r`, and these characters are written as `\u` and four uppercase hex digits: the rest of U+0000 to
U+001F, U+007F to U+009F, U+00A0, U+00AD, U+1680, U+180E, U+2000 to U+200F, U+2028 to U+202F, U+205F
to U+206F, U+3000, U+FEFF, U+FFF9 to U+FFFB, U+FFFE, U+FFFF, and the seven marks above. `json`
escapes the same characters, so that they can be seen. A harness can write the same escapes in `tree`
and compare text, or read them and compare strings. It compares `json` by value, in order.

## Where the answers come from

The examples' data is the draft's own JSON. The edge cases' data was written by hand, test by test,
when each was added to the checker. The events, names and `rest` come from the checker, and the
names and `rest` are checked again against what the marker lines alone say (section 4.4). Every test
passes the checker, `draftcheck.py` on the `ai` branch, which also checks that each example in the
draft is a test here with the same result.

The checker is one reading of the draft, not a reference parser. A parser written from the draft
that disagrees with a test has found a mistake in the test, the checker or the draft.

## Not covered yet

- where a refusal is reported (section 2);
- a syntax tree that keeps comments, and the size they add (sections 10 and 11);
- emitters (section 11);
- nesting past 256 levels, where parsers may differ by refusing (section 10);
- sections 5, 6.3, 7.2 and 12, which have few tests of their own;
- part 2, YAML Easy Schema.

## License

© 2026 Thomas Sawyer. The suite is under the [MIT license](LICENSE), so a parser can copy
the tests into its own repository.
