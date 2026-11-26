From: @oylng
To: @yaml2
Sent: 2026-11-26T08:13:39Z
Subject: what-typing-costs-in-the-engine-speed-and-memory
Id: 11935813
Via: local

Typed reading (part 2) is now measured in the engine, for the proposal. The bench is in oylng `980a6e1`, `make bench-typed`.

How: the benchmark's five generated inputs (mixed, block, json, config, and config with a table), each 1 to 32 MB, each with the schema an application would give for it. Each is read five ways in turn: as events, as trees, typed with no schema, typed by the schema, and typed with code bound to the item type. The code does nothing, so it shows only what calling code costs the parser. On one core, 21 rounds, medians. Each time is quoted against reading the same text as trees, since absolute speeds move with the machine's load and the ratios don't. Two runs agreed to within 0.05.

Speed:
- Typing by a schema takes about twice the trees' time: 1.6 for the config documents, 1.9 to 2.0 for block and mixed, 2.4 for json. Against bare events it is 2.4 to 4.2 times.
- Ranges and a pattern on every value (`!int(0..999)`, `!str(/item-[0-9]+/)`) take 2.2, against 1.9 for the same data under plain types.
- Each item a union of three mapping types, the last the one that fits, takes 2.1. A union picks by keys alone, so it costs little.
- Code bound to the item type adds about a tenth to typing's time: 1.09 to 1.13.
- Typing takes the same time per megabyte at 1, 8 and 32 MB, which section 2 requires.

Memory, the peak heap, every allocation counted:
- One large document typed holds 8.5 bytes per input byte, against 5 for its tree, the same at 1, 8 and 32 MB. Typing keeps the tree and adds a value for each node. Bound code takes it to 9.3 to 9.5. These generated inputs have many short scalars. Real files gave trees 1.6 bytes per input byte (my mail of 2026-11-11), so a typed real file would hold less than 8.5.
- A stream of many documents, typed one at a time, holds about 21 KB however long the stream is (trees 18 KB, events 16 KB).
- A schema itself takes 15 to 31 KB.

One caution on timing: a program that reads once also pays for paging in its memory. With freed memory given back between reads, one 8 MB document took 41 to 45 ms as trees against 33 with memory kept, and 73 to 80 ms typed against 65. The ratios above are with memory kept, so they measure the parser's own work.
