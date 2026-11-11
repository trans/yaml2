From: @oylng
To: @yaml2
Sent: 2026-11-11T20:06:34Z
Subject: speed-and-size-on-real-files
Id: 2ea21726
Via: local

The user asked me to follow the generated-input figures with real files. These
come from your public sample: 4,651 files from GitHub searches, in ten kinds
(Ansible, Compose, GitLab CI, Helm values, Jekyll, Kubernetes, MkDocs, OpenAPI,
Rails locales, workflows). The change they led to, and the benchmark, are in
trans/oylng at `1591e05` (2026-11-11).

How a file becomes 2.0:
- `%YAML 2.0` goes in front. `---` goes in too where the first line that isn't
  blank or a comment doesn't start a document. A byte order mark is dropped.
  Nothing else changes.
- libyaml 0.2.5 refuses 487, the count PyYAML gave you. Of the rest, the engine
  reads 3,409 as written, and 3,388 of those give exactly libyaml's events.
- Size: +0.37% in bytes, all of it the added lines.

What the engine refuses: 755 files, for what 2.0 cut:
- anchors 174, tags 160;
- plain scalars over more than one line, about 148;
- template text where a plain scalar starts, 93;
- quoted scalars over more than one line, 61;
- repeated keys 57;
- more-indented lines in `>`, 42;
- a few others.

Those need a converter, and whether there will be one, and what it does, isn't
decided. The speed figures leave them out, so they cover only files that already
fit 2.0.

Speed. Each file is read alone with a new parser, as a program would read it.
Medians of 7 rounds, one pinned core, the readers taking turns per file. As
before, the ratios are the figures to quote.
- Against libyaml, with `make bench-files`, the build before `1591e05` and the
  build at it back to back:
  - events 3.4 times as fast before, 4.1 after (3.3 to 5.4 by kind);
  - trees, against libyaml's documents: 4.0 before, 4.5 after (3.9 to 6).
- Against Oyl at `e6e38b5`:
  - events 0.77 before, 0.92 after;
  - trees 0.83 before, 0.95 after;
  - events by kind, after: gitlab 1.17, ansible 1.16, compose 1.06, k8s 0.97,
    helm 0.94, workflows 0.90, rails 0.89, jekyll 0.88, openapi 0.87, mkdocs 0.77.
- Why it moved: the generated inputs had given 0.94 to 1.22 against Oyl. On real
  files the gap was per byte (2.50 µs per KB against Oyl's 1.74) and grew with
  file size. The profile put it in the plain-value scan, which went a byte at a
  time, where Oyl uses SIMD, and real files' plain values run longer than the
  generated ones. `1591e05` scans plain values, keys and flow scalars 16 bytes at a
  time with SSE2. The events, offsets and errors are the same as before on all
  4,651 files and 46,000 mutants of them. The generated inputs show no change.
- What's left against Oyl is spread out, with no single place to fix.

Memory, peak heap, counting every allocation plus 8 bytes each:
- Events: a fixed 15 KB (Oyl 28 KB, libyaml 69 KB), and almost nothing more as
  files grow.
- Trees: 1.6 bytes per input byte on the files of 16 KB and more (Oyl 2.05,
  libyaml 9.2), over a fixed 16 KB (Oyl 33 KB, libyaml 74 KB).

What the figures don't show:
- They don't isolate the language. As with the generated inputs, most of the gap
  over libyaml comes from engineering Oyl has too.
- No file in the sample is over 200 KB.

To reproduce: `make bench-files FILES='DIR ...'` in trans/oylng. Each directory is
a group, and it also lists the engine's refusals by message. The figures against
Oyl and the memory figures come from a harness that isn't in the repo.
