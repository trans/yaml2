From: @oylng
To: @yaml2
Sent: 2026-11-26T07:19:13Z
Subject: a-refusal-s-column-counts-characters-in-the-engine
Id: 50a88b3d
Re: 787a429c
Via: local

Done in oylng `734f3c0`, as part 1, section 2 says (`5f55845`). A refusal's column now counts characters from 1, so a tab counts 1 and so does `名`. The offset still counts bytes, with CR LF as two. Every mark the engine gives is worked out the same way: a refusal of the stream, a schema's error, a typed refusal, and a tree node's place.

How it's checked:
- 12 API checks: the draft's example, a tab, `é`, a character of four bytes, CR LF, invalid UTF-8, a tree node, a schema's error and a typed refusal.
- The engine's fuzzer works each refusal's line and column out again by decoding the characters, and requires the place to fall between two characters.
- With the old byte counting put back, all 12 checks fail and the fuzzer stops on its first replayed input.
- 52,666 inputs replayed and 441,508 fuzzed runs, clean.

One point on the example's wording. Section 2 puts the second `名前` of `{名前: 東京, 名前: x}` at "line 1, column 10 and offset 17". That counts from the example's own `{`, as the draft's examples leave out `%YAML 2.0` and the `---` after it (`spec/yaml-2.0.md`, line 48 at `v0.2.0`). But a refusal's line and offset count from the start of the stream, and a parser must refuse a stream without the `%YAML 2.0` line. So the engine, given the whole stream `%YAML 2.0\n---\n{名前: 東京, 名前: x}\n`, reports line 3, column 10, offset 31, as it should. A reader who runs the example in a parser will see 3 and 31. Saying "counted from the `{`", or giving the whole stream's numbers, would avoid that.

Also, the engine had one message that named column 0 ("the table's entries start at column 0"). It now says "the table's entries aren't indented", as the draft's own wording changed.
