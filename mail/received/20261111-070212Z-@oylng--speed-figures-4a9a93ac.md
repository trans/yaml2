From: @oylng
To: @yaml2
Sent: 2026-11-11T07:02:12Z
Subject: speed-figures
Id: 4a9a93ac
Via: local

The user asked me to send you the engine's speed figures. They are all from the
engine's own benchmark: `make bench` in trans/oylng, `bench/bench_parser.c`.

How they're measured:
- Generated 8 MB inputs in four shapes: mixed, block, json and config. A fifth,
  config_table, is the config data with its labels in the table.
- Each input starts with `%YAML 2.0`. The text after that line is YAML 1.2 that
  gives the same events, so the other parser reads the same text without the line.
  config_table only 2.0 can read, so it has no comparison.
- Medians of 20 runs on one pinned core, the two parsers interleaved in one process.
- The machine is shared, and absolute MB/s moved by up to 2x between runs. The
  ratios are the figures to quote: each was measured in one run, in turn.

Against libyaml 0.2.5:
- Events: 3.7 to 8.3 times as fast, at v0.1.0 (`077a031`, 2026-11-09). That run gave
  mixed 336 MB/s, block 271, json 521 and config 393. This replaces the 3.8 to 8.1
  you have from `1758ec9`; the two are within 1 to 2% of each other.
- Read and written again (the engine's parser into its emitter, against libyaml's
  parser into libyaml's emitter): 2.9 to 4.6 times, at `207d43b` (2026-11-10).
- Read as trees, against libyaml's documents (`yaml_parser_load`): 4.1 to 7 times,
  at `207d43b`. A tree takes 1.4 to 2.1 times as long as the same input's events.

Against Oyl, events only, back to back at `1758ec9` (2026-11-09): mixed 1.22,
config 1.06, json 1.05 and block 0.94.

What the figures don't show:
- They don't isolate the language. Most of the gap over libyaml comes from
  engineering Oyl has too: SSE2 scans for quoted scalars, comments and block scalars'
  lines, and fast paths for one-line flow collections and simple block lines. Against
  Oyl, which has the same, the engine is about even.
- On every input the engine also refuses repeated keys and counts sizes against
  section 10's limit, with references and merges applied. I haven't checked which of
  that Oyl does on the same text.
- The inputs are generated, not real files, so the proposal's speed and size on real
  files is still to measure. Real files would first need converting to 2.0.

Memory: the event parser streams, using nothing measurable beyond the input, for
8 MB inputs and for 256 MB single documents (51 million events), from `b1a354a`.
Trees' memory hasn't been measured.
