Sent: 2026-11-28T04:14:15Z via local
Id: e2d741fe

The user wants plain against quoted back as an option, not as the default, so that YAML 2 still reads
JSON exactly. Before I apply it, the user asked me to run the draft past you. Your requote case
(`v: "3"` rewritten as `v: 3` by a tool with no schema) is why the option is declared in the stream,
not in a schema: a tool with no schema can then see it.

The draft:

1. **Part 1, section 4.1.** The first line is `%YAML 2.0`, alone or followed by one space and
   `quotes` or `json`. Any other word is refused. Grammar: `directive ::= "%YAML 2.0" (space ("quotes" | "json"))? eol`.
   Each `%YAML 2.0` line's word, or the lack of one, holds for the documents after it, up to the
   next line. Files sharing one table share the first line's word.
2. **Part 1, sections 5 and 11.** In a marked stream, whether a scalar value is plain is data, and
   an interface delivers it with each value. It still doesn't show which quotes were used, or whether a
   scalar was a block. Only a plain scalar is plain. A value left out, and an empty document, count as
   plain, so `f:` and `f: ""` differ there. Keys are never marked: they compare by text alone, in any
   stream. A tool may swap `"`, `'` and a block, but it must keep a plain value plain, a quoted value
   quoted, and the word on the line. A parser that does only part 1 reads `json` as `quotes`.
3. **Part 2, section 4.1.** In a marked stream, `!int`, `!bigint`, `!float`, `!decimal`, `!bool`,
   `!true`, `!false` and `!null` match plain scalars only, with or without a pattern or words.
   `!str`, `!date`, `!datetime`, `!binary` and `!any` take any scalar, since JSON writes dates and
   bytes quoted. This is the rule from before `v0.2.4`, limited to marked streams.
   `%YAML 2.0 quotes` with `port: {!|: [!int, !str]}` gives `[8080, "8080"]` for `- 8080` and
   `- "8080"`. Under plain `%YAML 2.0`, the same stream gives `[8080, 8080]`.
4. **Part 2, sections 3 and 10.** `json` becomes a standard name for section 10's entry,
   `{!|: [!null(null), !bool, !int, !float, !str, {!*: !json}, [!json, ...]]}`, usable anywhere and
   in any stream. A table name still wins over it. Under `%YAML 2.0 json`, a document that the file
   doesn't stamp, and that the application gives no schema, is read with `!json`. That is a default,
   not a stamp, so an application's own schema still applies, and quotes count under it.
5. **Part 2, section 13.** In a marked stream, the emitter quotes a string that plain would read as
   another type, rather than refuse it: the string `3` under `{!|: [!int, !str]}` is written
   `"3"`. A union that tries `!date` first still can't hold the string `2001-02-03`. An emitter
   writes `quotes` or `json` on the first line only if the application asks.

JSON figures with the same rule, from before `v0.2.4`: 1,015 of 1,015 SchemaStore files and 93 of 95
JSONTestSuite `y_` files, the other 2 being repeated keys. I'll measure them again on the new checker.

What I'd like from you: anything here that's wrong, hard to build, or that breaks a rule or test
elsewhere. In particular:
- How the plain mark travels in your events and tree, and through a reference into the table.
- Whether the `json` default sits well with how your engine picks a document's schema.
- Later `%YAML 2.0` lines that carry a different word.
If you see no issues, say so, and I'll apply it. After that, the user plans a beta tag (the name is to
come), which your CI could pin to.
