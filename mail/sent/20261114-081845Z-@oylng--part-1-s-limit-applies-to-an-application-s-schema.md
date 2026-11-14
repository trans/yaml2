Re: fb01f98f
Sent: 2026-11-14T08:18:45Z via local
Id: a5f344be

Your question went to the user, who took the agent's recommendation: part 1's limit applies to the text
of a schema from outside the stream, as the engine has it. An application's schema, or a published one,
is a stream of its own, read under the size limit, table counted, and its full size is then held to the
same limit. Section 3 says so in main `425db57`: `a: !str` holds 7 as text and has a full size of 1, so a
limit of 6 refuses it.

The suite follows in main `a7e2df6`, 808 tests:
- the checker's 22 tests of full size are gone, the ones under the text's held size, `BF3S` among them;
- 22 take their place, the same 11 schemas, each reached beside a mapping that names a 20-key mapping 40
  times, so full size (about 1,010) passes what the text holds (about 510). Each is at its full size,
  where it loads, and one under. The root is `r`;
- 2 test part 1's limit on an application's schema: `a: !str` from `a` loads at 7 and is refused at 6;
- the typed test across documents with an application's schema (`S7JA` before) now uses a 16-character
  string at limits 18 and 17, since the schema's text holds 14.

The checker reads an application's and a published schema under the limit as well, so a store's files
count too.

The `tags` file: `suite-to-data` writes one per test, the tags on one line, but that change waits for
the user and isn't committed yet. Making it found `tags: null` in `RP5Q`, which PyYAML reads as no tags;
it is quoted now, in `a7e2df6`.
