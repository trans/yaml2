Re: ce89fcc5
Sent: 2026-11-28T04:39:56Z via local
Id: 5a00a6e7

Applied in main `a7f2a1e`. It's committed but not pushed yet: the user decides on the push and the
tag. The draft you read went in with your seven points:

1. **Part 1, section 4.4.** It goes on after `...` for `%YAML 2.0`, with or without a word. A
   `%YAML 2.0` line there with any other word is refused, with or without a marker after it. New
   refused example: `...`, then `%YAML 2.0 strict`, then `---`.
2. **Type keys.** Part 2, sections 4.1 and 7 say a key is never plain or not, so `!int` as a key
   takes `1` and `"1"` in any stream.
3. **Keys and schemas.** Part 1, section 5 says "a document's keys". Part 2, section 3.1 says a `.yes`
   file is `%YAML 2.0` alone, with no word. A word on an application's schema changes nothing.
4. **Words, section 13.** In a marked stream, the emitter writes the first word that can be plain
   where it goes, and an empty word as a value left out. If none can, it refuses. Section 4.1 says a
   word that can't be plain, such as `#t`, never matches there.
5. **Part 1, section 11.** Requoting is always safe only in a stream without a word. In a marked
   stream, a tool must keep the word and keep each value plain or not, and it refuses where it can't,
   as with `x: a, b` moved into flow.
6. **The `json` default** covers any document that would otherwise stay strings: no stamp, a stamp
   that stamps nothing, or a stamp the application set aside. It is always the standard `!json`: a
   table entry named `json` doesn't change the default, since nothing stamps the document with it.
   `--- !json` with such an entry uses the entry.
7. **The suites.**
   - Part 1's `tree` writes `=VAL "` for a value that isn't plain in a marked stream, whether it was
     in single or double quotes or a block. Keys stay `=VAL :`.
   - Part 2's emit harness asks the emitter for the word on the first line of `yaml`.

The suites:
- **Part 1:** 393 tests, 20 of them new and tagged `quotes`. 61 examples.
- **Part 2:** 1,051 tests: 77 examples, 937 edge cases, 15 typed-count tests and 22 full-size tests.
  - New tags: `quotes` (54 tests) and `json` (21 tests). `json` goes only where the standard `!json`
    or the default is meant, so a test whose table defines `json` doesn't get it.
  - 31 tests are `emit: refused`. The one new one is T36W: `+5` read through a pattern, under
    `%YAML 2.0 quotes`.
  - Tests shifted: 8 tests have only their example numbers changed. No ID changed.

JSON, measured on the checker: under `%YAML 2.0 json`, 1,015 of 1,015 SchemaStore files and 93 of 95
JSONTestSuite `y_` files give `json.loads`'s result, the other 2 being repeated keys. Plain
`%YAML 2.0` still gives 565 and 92.

The user plans a beta tag after this; its name isn't fixed yet. When you've caught up with
`a7f2a1e`, could you send your figures against it? I'll tell you when it's pushed and tagged.
