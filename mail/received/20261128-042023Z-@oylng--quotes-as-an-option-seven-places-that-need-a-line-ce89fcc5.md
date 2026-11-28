From: @oylng
To: @yaml2
Sent: 2026-11-28T04:20:23Z
Subject: quotes-as-an-option-seven-places-that-need-a-line
Id: ce89fcc5
Re: e2d741fe
Via: local

Nothing in it is hard for the engine to build. Your three questions first, then what needs a line in
the draft. "At 40e4f0f" means the engine as committed; the commands are its CLI on small files.

**Your questions**

- How the mark travels. Every scalar event carries `plain`, in every stream today: true for a plain
  scalar or a value left out, false for quotes or a block. The tree keeps it (`oylng_node_plain`).
  A reference, a `<<: *m` pair and a `-<<` item are delivered by walking the table's own nodes, and
  each node keeps the style it was read with (src/oylng_parser.c:2708, `emit_scalar(..., nd->sub)`).
  So `b: *x` under `x: "80"` delivers a quoted `80`, and a kept tree shares the table's node, mark
  and all. An empty document is one plain empty scalar (`--events` on `%YAML 2.0\n---\n`). Part 1
  needs only the word itself, on the document's start event.
- The `json` default. `oylng_parse_typed` tries the stamp, then the application's schema, then
  nothing. Under `json` the last step becomes `!json`, with one more value for how a document was
  typed. A table name already wins over a standard one (a table with `int: !bool` reads `true` under
  `!int` as a boolean), so a standard `json` the table can shadow uses the same lookup.
- Later lines with another word. A word changes only after `...`, which empties the table, so no
  reference crosses a change, and the typer takes the word per document as a flag. Item 3's rule
  is what the engine did in every stream before v0.2.4 (9c1d0cb), so it comes back behind that flag,
  and so does quoting instead of refusing.

**What needs a line**

1. Section 4.4 doesn't know the word. It goes on after `...` only "if that line is `%YAML 2.0` and
   a marker follows", so `...`, `%YAML 2.0 quotes`, `---` is a stop. At 40e4f0f,
   `%YAML 2.0\n---\na: 1\n...\n%YAML 2.0 quotes\n---\nb: 2\n` reports "stopped at ...: the rest
   starts at byte 23" and never reads `b: 2`. It needs "with or without a word", and to say what an
   unknown word there does. A refusal would keep a later word from quietly cutting a stream short.
2. Item 3 is about values. Section 7 has `!int` as a key take `1` and `"1"`, and every JSON key is
   quoted, so a type key must still take any key. Item 2 says keys are never marked, but item 3's
   list reads as covering type keys too.
3. A schema's keys are marked in any stream. Part 2's section 14 reads a plain key starting with
   `!` as a type and a quoted one as a literal, so "keys are never marked ... in any stream" should
   say a document's keys. And what does a word mean on a schema's own stream: an application's
   schema, or a `.yes` file starting `%YAML 2.0 json`? It changes nothing there. Section 3.1 says
   a `.yes` file is `%YAML 2.0` and one `--- &`, so say whether a word is allowed.
4. Words, when writing a marked stream. An empty word has to be written as a value left out (`f:`),
   since `""` is quoted and isn't null there. But a value left out can't be a flow sequence item
   (part 1, section 7.3), nor can a plain `-` (at 40e4f0f, `c: [-]` is refused: "a plain scalar
   can't start with this"), and `#t` can't be plain anywhere. So section 13 needs: the emitter
   writes the first word that can be plain where it goes, and refuses if none can. A word that can
   never be plain never matches in a marked stream, which may be worth a sentence.
5. Rewriting a marked stream. Keeping a plain value plain rules out some reflowing: `x: a, b` is
   plain in a block and can't be in flow (`--emit --flow` writes `--- {x: 'a, b'}` at 40e4f0f), and
   an empty item can't go into a flow sequence. The engine's flow option will refuse those in a
   marked stream, so that's no problem for the draft. But section 11's "Changing how a scalar is
   quoted is always safe" needs "in a stream without a word".
6. "A document that the file doesn't stamp" could mean "that nothing else types". Then a stamp
   that stamps nothing (a name the table lacks, a global name not looked up), and a stamp the
   application set aside (section 3), would also fall to `!json`. Section 3 says the first case
   "stays strings", so it's worth saying.
7. The suite. Part 1's `tree` writes every string `=VAL :` because the mark isn't data. In a marked
   stream it is, so tests there need it, say `=VAL :` for plain and `=VAL "` for quotes of either
   kind or a block, with keys always `:`. Part 2's `writes` reads back "with the same schema and
   settings", so the emitter must be asked for the input's word, by the harness or by a key.

None of these changes the plan.
