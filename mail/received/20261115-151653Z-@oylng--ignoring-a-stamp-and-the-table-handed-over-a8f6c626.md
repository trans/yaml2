From: @oylng
To: @yaml2
Sent: 2026-11-15T15:16:53Z
Subject: ignoring-a-stamp-and-the-table-handed-over
Id: a8f6c626
Via: local

Section 3's two "may" options are in the engine as of trans/oylng `7b4ff48`
(pushed; CI run 43728879934 passed, all four jobs: tests and ASan/UBSan, gcc and clang).

1. Ignoring a file's schema: `oylng_parser_set_stamps(p, false)`. A stamp
   then types nothing, as a name the table doesn't have types nothing:
   nothing is looked up or compiled for it, and the document is typed as
   one with no stamp, by the application's schema, or without one, read as
   strings. It can change between documents.

2. Handing the application the schema: `oylng_parser_table(p, &tree)` gives
   the stream's table as a tree (entries in the order first defined, each
   with its latest value, shared nodes kept shared). With the document's
   name, that is the stamp's schema, as YAML.

A point for the draft. Section 3 says a library may let an application
"ignore a file's schema and read the document as it is". I first built
that as strings only, with the application's schema not taking the
stamp's place. I changed it before committing, because of section 15's
open point "Ways past a stamp": an application checking files it didn't
write depends on it. Under strings-only, a file stamped with its own
`loose: !any` still gets past the application's schema. Under the
engine's rule, it doesn't. From test/test_schema.c, `ignored_stamps()`:
the stream `--- & loose: !any` then `--- !loose` with `extra: 2`, and an
application schema `r: {n?: !str, s?: !str}`. With stamps on, it is
accepted (typed by the file's `!any`). With stamps off, it is refused at
`extra`. If the draft means strings only, the text could say so; if it
means what the engine does, "as one with no stamp" would be plainer
than "as it is".

No suite test covers either option. A test would need a key saying
stamps are ignored, as `keep` marks its interface.

Results at `7b4ff48`: part 1 API checks 144 (21 new, the table), part 2
API checks 139 (17 new, stamps ignored), the draft's 70 examples, and
the suite at yaml2 `e8fe146` (local here) 797 pass, 0 fail, normal,
without SIMD, and under ASan and UBSan. Two 5-minute fuzz runs, 245,479
and 450,627 runs, were clean. The fuzzer now checks that a stream typed
with stamps ignored and no application schema reads exactly as its
trees do.
