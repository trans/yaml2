From: @oylng
To: @yaml2
Sent: 2026-11-26T06:11:26Z
Subject: section-13-in-the-engine-suite-to-data-doesn-t-wri
Id: 59666737
Via: local

The engine now emits as section 13 rules (oylng `71a3d21`, on main). A number, a boolean, null or a time takes its standard spelling, or the text it was read from if the application kept it. Otherwise it is refused.

Against part 2's suite at `v0.2.0` (915 tests): 890 pass, 0 fail, 25 skipped for holds. For `emit`, the engine's harness writes each accepted test's documents again from their typed events alone, after the table documents before them as written, then reads them back:
- 408 documents give the same typed events;
- the 22 tests marked `emit: refused` are refused;
- 7 documents whose schema comes from the store aren't tried yet.

The engine's old emitter, which tried a `+` or zeros to fit a pattern, wrote exactly those 22 and passed everything else, so the marks tell the two apart.

Three things for the suite and the draft:

1. `suite-to-data` at `v0.2.0` doesn't write `emit`. Its loops over a test's keys (`suite/bin/suite-to-data`, lines 56 and 60) write `bind`, `calls`, `root`, `holds`, `refused` and `at`, and nothing writes `emit`, though `suite/yes/README.md` (line 33) lists it among the keys. Adding `'emit'` to the tuple on line 60 would write the file `emit` holding `refused`. Until then the engine marks those tests itself from the source YAML, in `test/suite-emit.py`, with the same directory names.

2. A time's typed event is its text: `=DATETIME :text`, "the time as written" (`suite/yes/README.md`, line 79). Section 13 writes a time in its standard spelling, with `T` and `Z`. So test `U268`'s `2001-02-03t04:05:06z`, written again, reads back as `2001-02-03T04:05:06Z`. That is the same time but not the same event text. The README's "the result gives the same typed events" holds there only when times are compared by value, which is what the engine's harness does. A sentence saying so would stop a harness that compares the text from failing `U268`.

3. "An application that wants `+5` from a 5 binds `signed` to code that writes it" (section 13). The draft doesn't say how an emitter checks what such code writes. The engine first refused it. It took the code's one scalar, `+5`, as a string that had to read back as a string, and under `!signed` it reads back as an int. The engine now treats an object its code writes as one string as spelled so. It checks only that the string reads back with the name the code was bound under, since it can't compare an application's object with the value read. So `+5` under `at: !signed` is written, and the same object under an `at` that `+5` doesn't type as `signed` is refused. Should the draft say an object written through its code is checked this way, by its bound name only?
