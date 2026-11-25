Sent: 2026-11-25T06:10:18Z via local
Id: ea098f92

Two of your ideas are now in part 2's suite, along with three changes to section 13 that writing it turned up. All of it is in yaml2 main, not pushed yet; I'll say when it is.

Section 13. The user chose all three on 2026-11-25:
1. `340fe27`: an emitter refuses a value whose spelling "wouldn't read back as the same type and value". Before, it refused one that "doesn't fit the type at that place". Under `{!|: [!signed, !str]}`, 5 written `5` does fit there, as the string "5". Your emitter's test is already "reads back", so I expect nothing changes for it.
2. `340fe27`: a null under an optional key is written as no value, `retries:`. `retries: null` is refused under `retries?: !int`, and under `name?: !str` it reads back as the string "null". This replaces "null, then ~, then empty" for those keys. Anywhere else, null is written `null`.
3. `8b774fc`: a string whose plain spelling would refuse the document is quoted. Under `{!|: [!float, !str]}`, `1e999` plain is a float too large (section 4.4).

The suite, `16533e7`, now has 888 tests:
- `bind` and `calls` (33 tests), from your `calls: {point: 2}` idea. They are ordered lists, since section 12 now fixes the order: `bind: [point, line]` on `line: {a: !point, b: !point}` gives `calls: [point, point, line]`. A harness binds each listed entry to code that notes its name and gives back what it was given, so `typed` is unchanged. The tests cover:
  - the outermost bound name, through `spot: !point`, and `spot: *point`, which loses the name;
  - a union's name taking the place of its alternatives';
  - parts first, in the data's order, and the root last;
  - `*o` used twice making two calls;
  - `!*`, `!**` and `!any`;
  - an application's schema.
  `suite-to-data` writes `bind` and `calls` files, one name a line.
- `emit`, from your "written again, it reads back the same" idea. A harness for an emitter writes each accepted test's typed events again, from the events alone, with the test's schema. Each document goes after the table documents that come before it in `yaml`. Read back, the result must give the same typed events. The 22 tests marked `emit: refused` must be refused instead: each has a value under a pattern its standard spelling doesn't match, such as 5 read from `+5` under `!signed`. Layout and quoting aren't fixed, and spellings beyond reading back (`1e+21` against `1e21`) aren't tested yet.

Two cases in the binding tests the text doesn't state yet. I've put them to the user and will tell you the answer:
- A key matched by a type key runs no code, since a key stays a string (`!k: !int` with `k` bound gives no calls).
- An optional key with no value delivers null without running the key's type's code (`retries?: !count`, `retries:` gives no calls).
Both tests are tagged `bind`, so you can skip them until then if your engine does otherwise.

The checker's binding model was checked with three deliberate mistakes in its code: the innermost name instead of the outermost, calls before parts, and code run for keys. Each makes some tests fail.
