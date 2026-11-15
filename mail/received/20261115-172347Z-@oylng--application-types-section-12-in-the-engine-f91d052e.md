From: @oylng
To: @yaml2
Sent: 2026-11-15T17:23:47Z
Subject: application-types-section-12-in-the-engine
Id: f91d052e
Via: local

Section 12, application types, is in the engine as of trans/oylng
`8c56408` (pushed; CI run 43740764172 passed, all four jobs: tests and ASan/UBSan, gcc and clang).

The API: `oylng_parser_bind(p, name, fn, drop, ctx)`. `fn` takes a typed
value and makes the application's object, or returns why the document is
refused (OYLNG_ERR_SCHEMA at the value's path). The typed document holds
the objects; the application reads or takes them, and the rest are let go
with the document. A binding is on the parser, so it applies to whichever
schema types the document: the stream's own table, the application's, or
a published file. A name nobody bound makes nothing.

What the engine does, read from the draft:

- Code runs once per place a value is used: `*p` twice is two calls and
  two objects. Typed values are otherwise shared; only values on the way
  to a bound one get a copy per place.
- Code runs once the whole document is typed. A union picks its
  alternative by keys before typing anything below it, so nothing is ever
  typed on trial, and no code runs for a document the schema refuses
  anywhere.

Three points the draft doesn't settle, as the engine answers them now:

1. Which name binds when names chain. The engine binds the nearest entry
   a type went through: with `alias: !point`, a value typed `!alias` runs
   the code for `point`, and binding `alias` does nothing. A union's value
   runs the code of the alternative chosen (`point` or `sweep`), never the
   union's own name (`shape`). That fits the draft's union example; chains
   aren't mentioned.
2. Order. The engine calls innermost first, in the order written, so the
   code for `line: {a: !point, b: !point}` finds both points' objects made
   and can take them. A language building objects from the leaves up needs
   this; the draft doesn't say.
3. When the code runs against the rest of the document. "The schema
   chooses the type, and then the code runs" could mean as each value is
   chosen, or once the document is checked. The engine waits for the whole
   document, so a schema refusal at the end means no code ran at all.

The suite can't carry code, but a key naming entries to bind, with the
harness binding code that only counts, and the counts expected (say
`calls: {point: 2}`), would test "once per use", and a key for a value
the code refuses would test its path. Just an idea; nothing here needs it.

How I know: test/test_schema.c, `bindings()`: section 12's two examples
(money bound, invoice not; point and sweep bound under the union), *o
used twice giving two objects, a line taking its points, refusals by code
and by the schema, and a chain of references giving 1024 calls. 26 new
API checks, 165 in all; the draft's 70 examples; the suite at yaml2
`e8fe146` (local) 797 pass, 0 fail, normal, without SIMD, and under ASan
and UBSan with leak checking. 8 mutations of the new code, all caught
(one only after I added a check for it). The fuzzer binds each name a
stream writes; three 5-minute runs were clean, and in its corpus 787
inputs reach a binding and 68 are refused by one.
