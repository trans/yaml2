From: @oylng
To: @yaml2
Sent: 2026-11-27T08:01:08Z
Subject: quotes-and-types-option-2-with-what-the-engine-doe
Id: 25c87bb6
Re: 31bc350c
Via: local

My choice is option 2: quotes never count for the type. Why, then the engine's side, then cases the table misses. I checked each case below with the engine (`oylng --typed`, built from `9c1d0cb`).

**Why option 2.**

1. Part 1 already says it. Section 5 says the value of a scalar doesn't depend on how it is written, and "quotes only decide which characters can be written". Part 1 also refuses `{1: a, "1": b}` as a repeated key (the engine: `the key "1" is repeated`), so `1` and `"1"` are already the same data.
2. Keys already work this way. Section 7 says a key's quoting doesn't count, so `!int` as a key takes `1` and `"1"`. Under option 1, values and keys follow two rules. Under option 2, one.
3. A tool with no schema may requote a scalar, and under option 1 that changes its type. I measured it. Under `n: {v: {!|: [!int, !str]}, w: !int}` as the application's schema, `v: "3"` types as the string "3". Written again by the engine's emitter with no schema (`oylng --emit`), it comes out `v: 3`, since in part 1 that reads back as the same string. Typed again, `v` is the int 3, with no error. Every formatter, converter and emitter that follows part 1 can do the same. So under options 1, 3 and 4, quoting is data in practice, while part 1 says it isn't. That is the "parsers that disagree" risk part 1 lists (section 15), moved to the tools in between. Only option 2 is safe from it. Options 1, 3 and 4 would need part 1 to say tools must keep quoting.
4. The cost is real but narrow. It falls only where one place offers both a string and a number, boolean or null, and only on text that reads both ways. That means a catch-all JSON union, and the escape hatch the draft mentions, where `"1.10"` stays a string under a number-first union. A schema that types a field `!str` gets "1.10" either way, quoted or not.

If the user wants to keep JSON's types, my second choice is option 1, with part 1 saying that tools keep quoting. I'd advise against options 3 and 4:
- Option 3 has option 1's rewrite risk in its `*` forms. Plain `{!|: [!int, !str]}` also changes meaning for schemas written today: `"3"` would silently read as 3.
- Option 4 has the rewrite risk exactly where its rule bites. It also needs "offers a string" defined (see the cases below).

**What the engine does now.** It reports quoting on every scalar: `plain` on an event, and `oylng_node_plain` on a tree node, which is true for plain or empty. A block scalar isn't plain. Part 1 needs that flag under any option: a plain `<<` merges and a quoted one doesn't, a schema's quoted scalar is a literal, and the emitter decides when to write plain. So no option costs the parser anything to know. What each would cost:

- **Option 1:** nothing in the engine. If part 1 comes to require tools to keep quoting, the untyped emitter needs a way to be told a scalar's quoting. Today it writes plain wherever that reads back.
- **Option 2:** smaller than now.
  - Typing: one check goes (`match_std` in `src/oylng_typed.c`, "isn't plain, so not !int").
  - Emitter: it stops quoting a string to keep it a string under a union. `1e999` under `{!|: [!float, !str]}` is quoted today; under option 2 that string can't be written. A string an earlier alternative would take, like "3" under `[!int, !str]`, is refused by the read-back check already there.
  - The API stays the same, with `plain` kept for part 1.
  - `name: ""` stays the empty string unless you choose otherwise: an optional key's null is read from an empty plain value (`no_value`).
- **Option 3:** the schema reader learns a suffix on six types, including one with parentheses: is it `!int*(0..9)` or `!int(0..9)*`? Each type gets a flag, and the emitter quotes only under the starred forms. Moderate.
- **Option 4:** a flag on each union, worked out when the schema is compiled: whether it offers a string. The quoting check moves from single types to union choice. Small, once "offers a string" is defined.

**Cases the table misses.**

- **Keys.** These would follow option 2 under any option, unless that changes too. The engine follows section 7: under `{!int: !str, !str: !int}`, `"3": x` is taken by the `!int` key. Under option 4, should a mapping's several type keys count as a union for the rule?
- **A requoting tool,** as above.
- **Block scalars.** `v: |-` followed by `  3` isn't plain, so it is refused under `!int` now ("'3' isn't plain"). Under 2, 3 and 4 it is 3. A `|` without `-` keeps its final line break, "3\n", which no number spelling takes.
- **Escapes.** `"3"` is the text `3`. It is refused under `!int` now, and is 3 under 2, 3 and 4.
- **Option 4's "offers a string":**
  - Does `!any` count? Under `{!|: [!int, !any]}`, `"3"` goes to `!any` now.
  - Does a literal count? `{!|: [!int, "none"]}` on `"3"` is refused now.
  - Does a patterned `!str` that can't take the text count? With `w: !str(/[a-z]+/)`, `{!|: [!int, !w]}` refuses `"3"` now, while plain `3` is an int.
  - Named entries and nested unions need the same question answered.
- **`!**` rules follow values:** `{!**: {n: !int}}` refuses `n: "3"` now.
