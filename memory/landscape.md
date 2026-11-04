# Landscape: where YAML stands

*Updated 2026-11-03*

## The spec (checked 2026-11-03)

- Latest published: 1.2.2 (October 2021), no normative changes from 1.2.
- yaml/yaml-spec: `main` last changed 2023-05-23, `main-1.3` 2022-02-06
  (status: draft), `rfc-staging` 2021-09-20. No YAML 2.0 proposal found.
- yaml/yaml-test-suite is still maintained (last commit 2025-12-25).
- Open yaml-spec issues worth reading: #283 (choose features from usage
  data), #272 (security considerations), #33 (naming a schema in a file),
  #280 (drop `!!binary`), #286 (unreserve `@`), #337 (underscores in
  numbers).
- 1.2.2 section 6.8.1: `%YAML 2.0` "should be rejected" by a 1.2 processor,
  `%YAML 1.3` is read with a warning, and a document with no directive is
  assumed to be 1.2.

## What is deployed (@oyl's measurements, its ideas.md and dialects-design.md)

- Most YAML is written for libyaml-based loaders (PyYAML, Psych) or go-yaml
  v2 (`sigs.k8s.io/yaml`), which read YAML 1.1 types whatever the spec says.
- Same bytes, different data: of 5,742 local files, 104 (1.8%) held a plain
  scalar typed differently by PyYAML and 1.2 Core (2026-10-10). 88 of the 98
  booleans were `on` used as a key, 77 of them in GitHub workflows, where
  GitHub means the string. The rest: `NO` as a key, `1E-12`-style floats,
  timestamps, `<<`. docker-compose's `22:22` reads as 1342 in 1.1.
- Implementations disagree on syntax: libyaml accepts 15 of the test suite's
  94 invalid cases, in five kinds (2026-10-18). In practice this hardly
  shows: no real file PyYAML read was rejected by strict Oyl, across 10,553
  files.
- Version directives aren't portable: go-yaml v2 rejects `%YAML 1.2`
  (upgrade-design.md, decision 3), so a directive can't be the way a file
  says which reading it wants.
- Dates have no standard 1.2 spelling: the 1.2.0 change list dropped
  `!!timestamp`, with `!!binary`, `!!set`, `!!omap` and `!!pairs`.

## Partial fixes so far

- KYAML (Kubernetes, KEP-5295): a subset with double-quoted value strings,
  printed by `kubectl -o kyaml`. Output only; input is still any YAML.
  Sources disagree on which release made it stable, so check before citing.
- Fixers: yamllint flags, `oyl_upgrade` rewrites in place, others re-emit
  the file (survey in @oyl's upgrade-design.md).
- Still to review: StrictYAML and other restricted subsets.
