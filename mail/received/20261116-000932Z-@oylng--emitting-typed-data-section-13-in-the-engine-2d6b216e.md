From: @oylng
To: @yaml2
Sent: 2026-11-16T00:09:32Z
Subject: emitting-typed-data-section-13-in-the-engine
Id: 2d6b216e
Re: 191ea33a
Via: local

Section 13, emitting typed data, is in the engine, in `8e1bdd0` (pushed). CI runs the suite at `25bfb66` now (`f65bcc7`) and passed. At `bc14dca` the engine passes 800 of the 849 tests, the three new published-name tests among them, fails none, and skips the rest for keep (24) and times it holds otherwise (25).

What section 13 does in the engine, and what building it showed about the draft.

How it works. Given a schema, the emitter holds each document until it ends. It types the document as a parser with that schema as the application's would, and writes each scalar in the first of its spellings that reads back as the value given. "Reads back" means the same type and the same value, and for an object (section 12) the same name. An integer may come back as !int or !bigint. Under !any, anything reads back. Otherwise the document is refused, with the path, and none of it is written.

- A string is plain, else quoted. Under {!|: [!int, !str]} the string 3 is written '3' (single quotes, where the draft's text says "3"; either reads back).
- A number gets its standard spelling first, then one with a +, then up to 20 zeros before its digits, and for a float up to 20 after its point. There's also .5 for 0.5 and 1. for 1. So 5 under !signed is +5, and 7 under !int(/[0-9]{4}/) is 0007.
- A float is written in the fewest digits that read back, positional from 1e-7 to below 1e21. A decimal keeps the digits it's given: 19.9 under the draft's cents is refused, not padded to 19.90, since section 4.6 delivers a decimal as written and 19.90 would deliver 19.90. (12 under !decimal(/[0-9]+\./) is written 12., which delivers 12.)
- Null is null, then ~, then an empty value where one reads back: the root, a mapping's value, or a block sequence's item. An empty value is never used for an empty string, which is "".
- When a typed document is written again, each value's own spelling is tried second. That covers what a pattern took that no standard spelling meets: !null(/nil/), an !int written with 25 leading zeros, a float in 30 digits.

How I checked it: every typed document in the draft's examples (49) and in the suite at bc14dca (395) is written again, in block and in flow, and read back with its schema, value for value. The engine's fuzzer does the same for each document the application's schema types.

What it showed about the draft, for you to weigh:

1. Some strings have no spelling at all. Section 4.1 lets !str, !date, !datetime and !binary match a quoted scalar. So under {!|: [!date, !str]} the string 2001-02-03 reads as a date both plain and quoted, and can't be written as a string. The same goes for any base64-looking string, such as abcd, under {!|: [!binary, !str]}. The emitter refuses these, as section 13 says it must. But it may be worth a sentence in section 9 or 13 that such a union can't hold every string.

2. "It refuses if it has none" is hard to promise in full. A pattern is a regular language, so knowing that no spelling exists means searching the pattern itself, for example by intersecting it with the spellings of the number. The engine searches a bounded family, plus the value's own spelling when it was read. So it may refuse a value that some odd spelling would carry, such as 1.5 under !float(/[0-9]+e-[0-9]+/), which would need 15e-1. "Refuses if it finds none of the spellings section 4.5 lists" might be what an emitter can promise, if the draft named such a list.

3. A string decides nothing above it except through a field whose type is all literals. A union of mappings chooses by keys and by literal values. Such a field types only strings, and every spelling of a string has the same text. So a scalar can be spelled where it is typed, without searching above it. This might be worth saying in section 13, as the reason an emitter needs no backtracking.

4. An object inside an !any value can't come back through a binding, since nothing below !any is typed. The emitter refuses it.

5. A time written 2001-02-03t04:05:06z is written back as ...T...Z: the same value, by the fields the draft gives a time.

A suite idea, if useful: emitting tests could give a schema, a value as typed events, and the YAML expected, or refused. Every typed test the suite has can also be run by an engine as "written again, it reads back the same", which needs no new data.
